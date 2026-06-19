"""Deterministic Phase 5 opportunity ranker."""

from __future__ import annotations

from repopilot_agents.state import CapabilityPlan, Opportunity

_LANE_KEY = {
    "A_issue": "A",
    "B_quality": "B",
    "C_suspicion": "C",
    "D_feature": "D",
}


def _lane_weight(opp: Opportunity, plan: CapabilityPlan) -> float:
    weights = plan.ranker_weights or {"A": 0.34, "B": 0.33, "C": 0.33}
    return float(weights.get(_LANE_KEY[opp.lane], 0.0))


def opportunity_score(opp: Opportunity, plan: CapabilityPlan) -> float:
    """Compute a deterministic weighted score for one opportunity."""
    lane_bias = _lane_weight(opp, plan)
    base = 0.4 * opp.mergeability + 0.35 * opp.approachability + 0.25 * opp.evidence_strength
    return base + lane_bias


def rank_opportunities(
    opportunities: list[Opportunity],
    *,
    plan: CapabilityPlan,
    limit: int | None = None,
) -> list[Opportunity]:
    """Return opportunities in stable best-first order. No LLM reranking."""
    ranked = sorted(
        opportunities,
        key=lambda opp: (
            -opportunity_score(opp, plan),
            opp.difficulty,
            opp.lane,
            opp.title,
        ),
    )
    if limit is None:
        return ranked
    return ranked[:limit]


__all__ = ["opportunity_score", "rank_opportunities"]
