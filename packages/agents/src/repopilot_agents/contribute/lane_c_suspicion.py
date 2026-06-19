"""Lane C — guarded structural suspicions."""

from __future__ import annotations

import re

from repopilot_agents.state import CodeRef, IntentProfile, Opportunity

BANNED_LANE_C_RE = re.compile(
    r"\b(?:bug|broken|will\s+crash|obviously\s+wrong)\b",
    re.IGNORECASE,
)


def lane_c_language_violation(text: str) -> str | None:
    """Return the banned phrase when Lane C language is too certain."""
    match = BANNED_LANE_C_RE.search(text)
    return None if match is None else match.group(0)


def _matches_focus(ref: CodeRef, profile: IntentProfile) -> bool:
    if not profile.focus_keywords:
        return True
    haystack = " ".join([ref.file_path, ref.symbol or ""]).lower()
    return any(keyword.lower() in haystack for keyword in profile.focus_keywords)


def run_lane_c_suspicion(
    candidates: list[CodeRef],
    *,
    profile: IntentProfile,
    limit: int = 5,
) -> dict[str, list[Opportunity]]:
    """Build guarded suspicion opportunities from deterministic candidates.

    Phase 5's production scanner will pre-filter structural patterns from AST
    facts. This core keeps the post-filter contract testable: guarded wording,
    focus filtering, and a required confirmation step.
    """
    opportunities: list[Opportunity] = []
    for ref in candidates:
        if not _matches_focus(ref, profile):
            continue
        symbol = ref.symbol or ref.file_path
        title = f"Investigate structural risk around {symbol}"
        why = (
            f"{symbol} is worth investigating because deterministic structural "
            "signals marked it as fragile-shaped; confirm before treating it as a defect."
        )
        if lane_c_language_violation(title) or lane_c_language_violation(why):
            continue
        opportunities.append(
            Opportunity(
                lane="C_suspicion",
                title=title,
                evidence_refs=[ref],
                why_this_matters=why,
                blast_radius="module-scoped",
                difficulty="M",
                suggested_first_step=f"Read {ref.file_path} and write a failing reproduction if the concern holds.",
                files_to_touch=[ref.file_path],
                nearest_tests=[],
                confirm_before_pr=f"to_confirm: reproduce the behavior around {symbol} before opening a PR.",
                mergeability=0.45,
                approachability=0.55,
                evidence_strength=0.65,
                intent_match=f"matches: {profile.raw_text!r}",
            )
        )
        if len(opportunities) >= limit:
            break
    return {"opportunity_list": opportunities}


__all__ = ["BANNED_LANE_C_RE", "lane_c_language_violation", "run_lane_c_suspicion"]
