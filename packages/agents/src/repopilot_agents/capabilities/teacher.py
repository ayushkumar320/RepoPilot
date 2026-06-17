"""Teacher — weaves Insights into goal-anchored ``TourSection``s.

The Teacher is terminal: it consumes the upstream capabilities' Insights
(``system_map`` + ``traced_flows`` for v1; lane outputs in later
iterations) and emits ``TourSection`` objects containing ``Claim``s.
Each section is a narrative beat anchored back to ``intent_profile``.

The Teacher never invents refs. It can only cite what the upstream
capabilities already grounded. Coercion enforces that explicitly: any
ref the LLM emits that isn't in the upstream Insight set is dropped.
"""

from __future__ import annotations

import structlog

from repopilot_agents.capabilities._coerce import coerce_claim, extract_json_list
from repopilot_agents.prompts import render_goal_anchor
from repopilot_agents.state import (
    CapabilityPlan,
    Claim,
    CodeRef,
    Insight,
    IntentProfile,
    TourSection,
)
from repopilot_core.llm.models import ModelId
from repopilot_core.llm.provider import LLMProvider, Message

log = structlog.get_logger(__name__)


_SYSTEM_PROMPT = (
    "You are the Teacher. Given the USER GOAL, the PLAN TILT, and a "
    "SOURCE BUNDLE of grounded Insights produced by upstream capabilities, "
    "weave them into 2–4 short tour sections. Each section must be "
    "goal-anchored, narratable in 2–4 sentences, and end in motion "
    "(what the reader does next).\n\n"
    "Output STRICT JSON: a single array. Each entry is a SECTION object "
    'with exactly these keys: "title" (string), "order" (integer, 0-based), '
    '"claims" (array). Each claim has exactly "text" (string) and "refs" '
    "(array of symbol strings drawn ONLY from the source bundle — DO NOT "
    "invent refs). No other keys. No commentary outside the array."
)


def _format_source_bundle(insights: list[Insight]) -> str:
    if not insights:
        return "SOURCE BUNDLE: (empty — upstream produced no grounded insights)"
    lines = ["SOURCE BUNDLE (grounded — reuse refs verbatim):", ""]
    for i, ins in enumerate(insights, start=1):
        ref_symbols = ", ".join(ref.symbol or ref.file_path for ref in ins.refs)
        lines.extend(
            [
                f"[{i}] finding: {ins.finding}",
                f"    because: {ins.because}",
                f"    so_what: {ins.so_what}",
                f"    goal_link: {ins.goal_link}",
                f"    refs: {ref_symbols}",
                "",
            ]
        )
    return "\n".join(lines)


def _collect_refs(insights: list[Insight]) -> dict[str, CodeRef]:
    """Index every CodeRef from upstream insights by symbol so the Teacher
    can only cite what's already grounded."""
    out: dict[str, CodeRef] = {}
    for ins in insights:
        for ref in ins.refs:
            key = ref.symbol or f"{ref.file_path}:{ref.start_line}-{ref.end_line}"
            out.setdefault(key, ref)
    return out


def _coerce_section(
    payload: dict[str, object],
    allowed_refs: dict[str, CodeRef],
    next_order: int,
) -> TourSection | None:
    title = str(payload.get("title", "")).strip()
    if not title:
        return None
    order_value = payload.get("order")
    if isinstance(order_value, int):
        order = order_value
    elif isinstance(order_value, str):
        try:
            order = int(order_value)
        except ValueError:
            order = next_order
    else:
        order = next_order
    if order < 0:
        order = next_order

    raw_claims = payload.get("claims")
    if not isinstance(raw_claims, list):
        return None
    claims: list[Claim] = []
    for raw in raw_claims:
        if not isinstance(raw, dict):
            continue
        c = coerce_claim(raw, allowed_refs)
        if c is not None:
            claims.append(c)
    if not claims:
        return None
    try:
        return TourSection(title=title, order=order, claims=claims)
    except Exception:
        return None


async def run_teacher(
    *,
    profile: IntentProfile,
    plan: CapabilityPlan,
    provider: LLMProvider,
    insights: list[Insight],
) -> dict[str, list[TourSection]]:
    """Run the Teacher once.

    Returns ``{"draft_tour": [TourSection, …]}``. Empty list is valid
    when there are no upstream Insights to weave (e.g., a quota outage
    upstream); the orchestrator will surface a typed error rather than
    show an empty tour to the user.
    """
    if not insights:
        log.info("teacher.no_upstream_insights")
        return {"draft_tour": []}

    allowed_refs = _collect_refs(insights)
    bundle = _format_source_bundle(insights)
    anchor = render_goal_anchor(profile, plan)

    response = await provider.generate(
        ModelId.TEACHER,
        [
            Message("system", _SYSTEM_PROMPT),
            Message("user", f"{anchor}\n\n{bundle}"),
        ],
        temperature=0.3,
        max_tokens=1200,
    )

    sections: list[TourSection] = []
    for idx, payload in enumerate(extract_json_list(response.text)):
        section = _coerce_section(payload, allowed_refs, next_order=idx)
        if section is not None:
            sections.append(section)

    # Re-order sequentially so the UI doesn't see gaps even if the LLM
    # emitted non-monotonic orders.
    sections.sort(key=lambda s: s.order)
    normalised = [section.model_copy(update={"order": i}) for i, section in enumerate(sections)]
    log.info(
        "teacher.done",
        upstream_insights=len(insights),
        sections=len(normalised),
    )
    return {"draft_tour": normalised}


__all__ = ["run_teacher"]
