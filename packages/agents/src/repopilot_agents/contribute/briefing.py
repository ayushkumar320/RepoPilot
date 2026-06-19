"""Teacher-facing briefing helpers for Phase 5 opportunity cards."""

from __future__ import annotations

from repopilot_agents.state import CapabilityPlan, IntentProfile, Opportunity


def ranker_rationale(plan: CapabilityPlan, profile: IntentProfile) -> str:
    """Plain-English explanation of planner-derived ranker weights."""
    weights = plan.ranker_weights
    if not weights:
        return f"weighted evenly because you said {profile.raw_text!r}"
    strongest = max(weights.items(), key=lambda item: item[1])[0]
    labels = {"A": "reported issues", "B": "cleanup", "C": "problem-hunting"}
    return (
        f"weighted toward {labels.get(strongest, strongest)} because you said {profile.raw_text!r}"
    )


def build_opportunity_briefing(
    opportunities: list[Opportunity],
    *,
    profile: IntentProfile,
    plan: CapabilityPlan,
) -> dict[str, object]:
    """Attach the UI-visible Phase 5 briefing surfaces without reranking."""
    return {
        "rationale": ranker_rationale(plan, profile),
        "opportunities": [
            opp.model_copy(
                update={"intent_match": opp.intent_match or f"matches: {profile.raw_text!r}"}
            )
            for opp in opportunities
        ],
    }


__all__ = ["build_opportunity_briefing", "ranker_rationale"]
