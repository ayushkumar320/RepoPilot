"""Capability Planner — deterministic ``IntentProfile`` → ``CapabilityPlan``.

The Planner is the **deterministic heart of elasticity**: a pure Python
function that reads an ``IntentProfile`` and decides which subset of the
capability library to activate and how to tilt each member. No LLM, no
state mutation, no IO. Implements ``docs/03_ARCHITECTURE.md`` § "The
Capability Planner" rules verbatim, with one exception called out below.

Why deterministic:
- An LLM planner makes every quota outage a planning failure, not just a
  generation failure. Far cheaper to verify rules in milliseconds.
- A labeled `(profile, expected plan)` set is the gate; LLM planners
  can't be graded that way without grading a second LLM.

Why this is enough flexibility:
- Two materially different intents on the same repo still produce
  materially different plans (the Phase 3 divergence gate ≥ 50%).
- Anything the rules don't catch falls through to the inclusive default
  plan (``cartographer + lane_b_code_health + teacher``), so the system
  is open, not closed. New capabilities = one new rule, not a refactor.
"""

from __future__ import annotations

from typing import Any

from repopilot_agents.state import (
    CapabilityName,
    CapabilityPlan,
    IntentProfile,
    OutputShape,
)

# Keyword signals lifted from the rule sketch. Lower-cased once at module
# load so each call is just a substring scan over a small set.
_FRAGILITY_TERMS = ("fragile", "problem", "audit", "security", "vulnerab")
_ISSUE_TERMS = ("issue",)
_PR_TERMS = ("pr",)  # checked separately so we don't match generic prose


def _pick_hub_bias(p: IntentProfile) -> str:
    """Pick a hub-bias tilt for the Cartographer.

    Data-heavy intents → "data_hubs"; decision/strategy intents →
    "decision_hubs"; perf/latency intents → "hot_path"; everything else →
    "balanced". Reads ``focus_keywords`` and ``raw_text`` in tandem so a
    one-word keyword and a verbose statement both work.
    """
    haystack = " ".join([p.raw_text.lower(), *(k.lower() for k in p.focus_keywords)])
    if any(t in haystack for t in ("data", "schema", "model", "table", "storage")):
        return "data_hubs"
    if any(t in haystack for t in ("decision", "strategy", "tradeoff", "policy")):
        return "decision_hubs"
    if any(t in haystack for t in ("latency", "throughput", "hot path", "performance", "perf")):
        return "hot_path"
    return "balanced"


def _infer_flow_targets(p: IntentProfile) -> list[str]:
    """Seed flow-tracer targets from focus_keywords when they look like symbols.

    A focus_keyword counts as a candidate symbol if it has no whitespace.
    The downstream node will further resolve it against the symbol table;
    here we just hand it the strings the user named.
    """
    return [k for k in p.focus_keywords if k and " " not in k]


def _derive_ranker_weights(p: IntentProfile) -> dict[str, float]:
    """Lane-A ranker tilt. Bias toward C if the intent emphasises hunting,
    toward A if PR-shaped, otherwise an even-handed split. Kept tiny on
    purpose — Lane A's full ranker lives downstream."""
    raw = p.raw_text.lower()
    if "hunt" in raw or any(t in raw for t in _FRAGILITY_TERMS):
        return {"A": 0.3, "B": 0.3, "C": 0.4}
    if any(t in raw for t in _ISSUE_TERMS) or "pr" in raw.split():
        return {"A": 0.6, "B": 0.3, "C": 0.1}
    return {"A": 0.4, "B": 0.4, "C": 0.2}


def _infer_shape(active: list[CapabilityName], p: IntentProfile) -> OutputShape:
    """When the profiler didn't set a preference, pick the shape that the
    plan's active set best fits.

    Narrative is the default; a Lane A/B/C-heavy plan reads better as a
    ranked list; comparative intents go to a comparison_table; explicit
    decision/audit intents (which would have been DA in v0.2) → dossier.
    """
    raw = p.raw_text.lower()
    compare_weight = p.modality_weights.get("compare", 0.0)
    if compare_weight >= 0.3 or "compare" in raw or "vs " in raw or "versus" in raw:
        return "comparison_table"
    contribute_active = {
        "lane_a_issue_triage",
        "lane_b_code_health",
        "lane_c_suspicion",
    }
    if any(c in contribute_active for c in active):
        return "ranked_list"
    if "audit" in raw or "decision" in raw or "dossier" in raw:
        return "dossier"
    return "narrative"


def plan(p: IntentProfile) -> CapabilityPlan:
    """Deterministic planner. See ``docs/03_ARCHITECTURE.md`` § "The
    Capability Planner" for the full rule rationale."""
    active: list[CapabilityName] = []
    tilts: dict[CapabilityName, dict[str, Any]] = {}

    understand = p.modality_weights.get("understand", 0.0)
    change = p.modality_weights.get("change", 0.0)
    evaluate = p.modality_weights.get("evaluate", 0.0)
    locate = p.modality_weights.get("locate", 0.0)
    # compare is read inside _infer_shape; no rule activates on it in v1.

    raw_lc = p.raw_text.lower()

    # Cartographer: structural understanding, narrowing, or pure locating.
    if understand >= 0.2 or evaluate >= 0.2 or locate >= 0.3 or p.focus_keywords:
        active.append("cartographer")
        tilts["cartographer"] = {
            "hub_bias": _pick_hub_bias(p),
            "narrow_to": list(p.focus_keywords),
        }

    # Flow Tracer: explicit understanding of a path / lifecycle.
    if understand >= 0.4 or "lifecycle" in raw_lc or "flow" in raw_lc:
        active.append("flow_tracer")
        tilts["flow_tracer"] = {"targets": _infer_flow_targets(p)}

    # Lane A: issue-driven PR work.
    if change >= 0.4 and (any(t in raw_lc for t in _ISSUE_TERMS) or "pr" in raw_lc.split()):
        active.append("lane_a_issue_triage")

    # Lane B: cleanup + tradeoff surfacing.
    if change >= 0.3 or evaluate >= 0.4:
        active.append("lane_b_code_health")
        tilts["lane_b_code_health"] = {
            "framing": "tradeoffs_visible_in_code"
            if evaluate > change
            else "cleanup_opportunities",
        }

    # Lane C: fragility / problem hunting / security audits.
    fragility_signal = any(t in raw_lc for t in _FRAGILITY_TERMS)
    if change >= 0.3 and (fragility_signal or "hunt" in raw_lc):
        active.append("lane_c_suspicion")
        tilts["lane_c_suspicion"] = {"keyword_filter": list(p.focus_keywords)}

    # Inclusive default: the planner never returns an empty plan. If no
    # rule fired, fall through to cartographer + lane_b_code_health so the
    # user always sees the system's strongest moves, not just structure.
    if not active:
        active.extend(["cartographer", "lane_b_code_health"])
        tilts.setdefault(
            "cartographer",
            {"hub_bias": _pick_hub_bias(p), "narrow_to": list(p.focus_keywords)},
        )
        tilts["lane_b_code_health"] = {
            "framing": "cleanup_opportunities",
            "lightweight": True,
        }

    # Teacher: terminal capability; always last, always activated.
    active.append("teacher")

    shape: OutputShape = (
        p.output_shape_preference
        if p.output_shape_preference != "unspecified"
        else _infer_shape(active, p)
    )

    # Dependency DAG. See docs/03 § "Capability dependencies".
    dependencies: dict[CapabilityName, list[CapabilityName]] = {}
    if (
        "flow_tracer" in active
        and "cartographer" in active
        and not tilts.get("flow_tracer", {}).get("targets")
    ):
        # Soft dep: skip when focus_keywords already seed a starting symbol.
        dependencies["flow_tracer"] = ["cartographer"]
    # Teacher needs at least one upstream capability's output to narrate.
    upstream: list[CapabilityName] = [c for c in active if c != "teacher"]
    if upstream:
        dependencies["teacher"] = upstream

    return CapabilityPlan(
        active=active,
        dependencies=dependencies,
        tilts=tilts,
        output_shape=shape,
        cartographer_tilt=tilts.get("cartographer", {}).get("hub_bias"),
        flow_tracer_targets=list(tilts.get("flow_tracer", {}).get("targets", [])),
        lane_b_framing=tilts.get("lane_b_code_health", {}).get("framing"),
        ranker_weights=(_derive_ranker_weights(p) if "lane_a_issue_triage" in active else {}),
    )


__all__ = ["plan"]
