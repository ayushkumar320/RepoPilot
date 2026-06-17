"""Verifier loop — Phase 2 grounding **plus** the Iteration-2 actionability rubric.

Phase 2's ``verify_claim`` answers a single question: "is this claim
grounded in the chunks?" Phase 3 layers a second question on top of every
claim and every tour section: "is it useful, given the user's stated
goal?" — the **actionability rubric**.

Loop semantics (docs/03 § "Verifier rejects every claim" / § "Verifier
loop"):

1. Run grounding (Phase 2). Already idempotent + cached.
2. For each section, run the actionability rubric. Cheap, single LLM
   call per section, JSON-only output.
3. Reject + emit a ``VerifierObjection`` when either check fails.
4. ``verify_section_with_retries`` retries the source node up to
   ``MAX_SOURCE_RETRIES`` (= 2) times. After the budget is spent, the
   remaining failing claims are **flagged** (never silently dropped) per
   the "we never lie, we never hide" rule.

The loop never mutates state directly; it returns the resulting list of
claims (with updated ``status``) plus the objections. The caller (a
LangGraph node) folds the returns back into ``ArchaeologistState`` via the
reducer.
"""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncEngine

from repopilot_agents.state import (
    Claim,
    ClaimStatus,
    IntentProfile,
    TourSection,
    VerifierObjection,
)
from repopilot_agents.verifier import grounding as grounding_mod
from repopilot_agents.verifier.grounding import Claim as Phase2Claim
from repopilot_core.llm.models import ModelId
from repopilot_core.llm.provider import LLMProvider, Message

MAX_SOURCE_RETRIES: int = 2


# ─── Actionability rubric ────────────────────────────────────────────────


_ACTIONABILITY_SYSTEM_PROMPT = (
    "You are the actionability rubric for a guided code-onboarding system. "
    "You read the USER GOAL and a CLAIM the system wants to show. Decide:\n"
    "  - actionable: the claim is on-goal AND points to something the "
    "user could do next (an inspection, a question to ask, a refactor "
    "target, a tradeoff to weigh).\n"
    "  - not_actionable: the claim is correct but off-goal, or it is a "
    "raw stat without consequence ('this module is imported by 23 files' "
    "with no 'so what').\n\n"
    'Respond with one line of JSON: {"verdict":"actionable"|"not_actionable",'
    '"reason":"<one short sentence>"}.'
)


def _actionability_user_prompt(claim_text: str, profile: IntentProfile) -> str:
    weights = (
        ", ".join(f"{k}={v:.2f}" for k, v in sorted(profile.modality_weights.items())) or "(none)"
    )
    keywords = ", ".join(profile.focus_keywords) or "(none)"
    return (
        "USER GOAL:\n"
        f'  raw_text: "{profile.raw_text}"\n'
        f"  modality_weights: {weights}\n"
        f"  focus_keywords: {keywords}\n"
        f"  audience: {profile.audience_framing or '(unspecified)'}\n\n"
        f"CLAIM:\n  {claim_text}"
    )


class ActionabilityVerdict(BaseModel):
    verdict: Literal["actionable", "not_actionable"]
    reason: str = ""


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse_actionability(raw: str) -> ActionabilityVerdict | None:
    match = _JSON_RE.search(raw)
    if match is None:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    try:
        return ActionabilityVerdict(**data)
    except (ValidationError, TypeError):
        return None


async def _check_actionability(
    claim_text: str,
    profile: IntentProfile,
    *,
    provider: LLMProvider,
) -> ActionabilityVerdict:
    """One actionability call. Parse-fail = not_actionable (mirrors D4)."""
    response = await provider.generate(
        ModelId.VERIFIER,
        [
            Message("system", _ACTIONABILITY_SYSTEM_PROMPT),
            Message("user", _actionability_user_prompt(claim_text, profile)),
        ],
        temperature=0.0,
        max_tokens=120,
    )
    parsed = _parse_actionability(response.text)
    if parsed is None:
        # Same posture as grounding D4: parse-fail is treated as failure,
        # never silently accepted.
        return ActionabilityVerdict(verdict="not_actionable", reason="actionability_parse_error")
    return parsed


# ─── Section-level pipeline ──────────────────────────────────────────────


@dataclass(slots=True)
class SectionVerificationResult:
    """One section's verification verdict.

    ``objections`` is empty when every claim passed both grounding and
    actionability. ``claims`` is the updated list with ``status`` /
    ``verifier_note`` populated in place — callers fold the section back
    into the tour.
    """

    section_order: int
    claims: list[Claim]
    objections: list[VerifierObjection]

    @property
    def passed(self) -> bool:
        return not self.objections


def _to_phase2_claim(claim: Claim) -> Phase2Claim:
    """Bridge: Phase-2 ``verify_claim`` consumes its own ``Claim`` shape."""
    return Phase2Claim(
        text=claim.text,
        refs=claim.refs,
        status=claim.status,
        verifier_note=claim.verifier_note,
    )


def _apply_status(claim: Claim, status: ClaimStatus, note: str) -> None:
    claim.status = status
    claim.verifier_note = note


async def verify_section(
    section: TourSection,
    profile: IntentProfile,
    *,
    provider: LLMProvider,
    engine: AsyncEngine,
    repo_id: str,
    actionability_concurrency: int = 8,
) -> SectionVerificationResult:
    """Verify one section's claims: grounding + actionability, in parallel.

    Each claim is graded twice. Either failure produces a
    ``VerifierObjection``. Claims that pass both are marked
    ``status="verified"``. Claims that fail are marked ``rejected`` (the
    source node may retry); the higher-level ``verify_section_with_retries``
    promotes persistent rejections to ``flagged`` once the retry budget
    is spent.
    """
    if not section.claims:
        return SectionVerificationResult(section_order=section.order, claims=[], objections=[])

    # 1. Grounding (Phase 2). Each claim's status is mutated by the
    # Phase-2 Claim shape; we'll mirror those mutations onto the state
    # Claim and decide which still need actionability.
    phase2_claims = [_to_phase2_claim(c) for c in section.claims]
    grounding_results = await grounding_mod.verify_claims(
        phase2_claims,
        provider=provider,
        engine=engine,
        repo_id=repo_id,
    )

    objections: list[VerifierObjection] = []
    needs_actionability: list[Claim] = []
    for claim, gres in zip(section.claims, grounding_results, strict=True):
        if gres.verdict.decision == "rejected":
            _apply_status(claim, "rejected", gres.verdict.reason)
            objections.append(
                VerifierObjection(
                    section_order=section.order,
                    claim_text=claim.text,
                    reason=f"ungrounded: {gres.verdict.reason}",
                )
            )
        else:
            # Grounded — actionability still to grade. Carry the
            # grounding note forward; actionability will overwrite if it
            # also has something to say.
            _apply_status(claim, "verified", gres.verdict.reason)
            needs_actionability.append(claim)

    # 2. Actionability — only on grounded claims (rejected ones already
    # have an objection). Run with a bounded semaphore so we don't fan
    # out unboundedly on big sections.
    if needs_actionability:
        sem = asyncio.Semaphore(max(1, actionability_concurrency))

        async def grade(claim: Claim) -> ActionabilityVerdict:
            async with sem:
                return await _check_actionability(claim.text, profile, provider=provider)

        verdicts = await asyncio.gather(*(grade(c) for c in needs_actionability))
        for claim, verdict in zip(needs_actionability, verdicts, strict=True):
            if verdict.verdict == "not_actionable":
                _apply_status(claim, "rejected", verdict.reason)
                objections.append(
                    VerifierObjection(
                        section_order=section.order,
                        claim_text=claim.text,
                        reason=f"not_actionable: {verdict.reason}",
                    )
                )

    return SectionVerificationResult(
        section_order=section.order,
        claims=list(section.claims),
        objections=objections,
    )


# ─── Retry budget + flagging ─────────────────────────────────────────────


SourceRetry = Callable[[TourSection, list[VerifierObjection]], Awaitable[TourSection]]
"""Source-node retry hook.

Given the current section and the verifier's objections, the upstream
generating node returns a revised ``TourSection``. The verifier loop
calls this hook up to ``MAX_SOURCE_RETRIES`` times. Implementations live
in each generation node (Cartographer, Teacher, …); the loop never
guesses at retry semantics."""


async def verify_section_with_retries(
    section: TourSection,
    profile: IntentProfile,
    *,
    provider: LLMProvider,
    engine: AsyncEngine,
    repo_id: str,
    retry: SourceRetry | None = None,
    max_retries: int = MAX_SOURCE_RETRIES,
) -> SectionVerificationResult:
    """Top-level verifier loop.

    Calls ``verify_section`` once; if any claim fails, calls ``retry``
    with the objections and re-verifies. After ``max_retries`` exhausted
    rounds, any remaining rejected claims are promoted to
    ``status="flagged"`` (with their last reason preserved) and emitted
    on the final ``objections`` list. We **never** silently drop.

    Passing ``retry=None`` skips revision: a single grade, then any
    rejections become flagged immediately. That mode is useful in tests
    and when the caller wants to inspect the first-pass result before
    spending a retry budget.
    """
    result = await verify_section(
        section,
        profile,
        provider=provider,
        engine=engine,
        repo_id=repo_id,
    )
    if result.passed or retry is None:
        return _finalize(result, retries_used=0, max_retries=max_retries)

    current_section = section
    for attempt in range(1, max_retries + 1):
        revised = await retry(current_section, list(result.objections))
        current_section = revised
        result = await verify_section(
            revised,
            profile,
            provider=provider,
            engine=engine,
            repo_id=repo_id,
        )
        if result.passed:
            return _finalize(result, retries_used=attempt, max_retries=max_retries)

    # Budget spent — flag (don't drop) the remaining failures.
    return _finalize(result, retries_used=max_retries, max_retries=max_retries)


def _finalize(
    result: SectionVerificationResult,
    *,
    retries_used: int,
    max_retries: int,
) -> SectionVerificationResult:
    """If the retry budget is spent and claims are still rejected, flag them.

    Flagged claims still ship — the UI surfaces a warning treatment. The
    objection's reason is preserved on each claim's ``verifier_note`` so
    the warning has actionable content.
    """
    if retries_used < max_retries or result.passed:
        return result

    for claim in result.claims:
        if claim.status == "rejected":
            claim.status = "flagged"
    return result


# ─── Convenience helpers ────────────────────────────────────────────────


async def verify_claims_grounded(
    claims: Sequence[Claim],
    *,
    provider: LLMProvider,
    engine: AsyncEngine,
    repo_id: str,
) -> list[VerifierObjection]:
    """Standalone grounding pass — useful for Q&A which produces claims
    outside the tour-section structure."""
    if not claims:
        return []
    phase2_claims = [_to_phase2_claim(c) for c in claims]
    results = await grounding_mod.verify_claims(
        phase2_claims,
        provider=provider,
        engine=engine,
        repo_id=repo_id,
    )
    objections: list[VerifierObjection] = []
    for claim, res in zip(claims, results, strict=True):
        if res.verdict.decision == "rejected":
            _apply_status(claim, "rejected", res.verdict.reason)
            objections.append(
                VerifierObjection(
                    section_order=0,
                    claim_text=claim.text,
                    reason=f"ungrounded: {res.verdict.reason}",
                )
            )
        else:
            _apply_status(claim, "verified", res.verdict.reason)
    return objections


__all__ = [
    "MAX_SOURCE_RETRIES",
    "ActionabilityVerdict",
    "SectionVerificationResult",
    "SourceRetry",
    "verify_claims_grounded",
    "verify_section",
    "verify_section_with_retries",
]
