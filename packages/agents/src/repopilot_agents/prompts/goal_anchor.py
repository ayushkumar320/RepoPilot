"""Goal-anchor prompt block — shared across every generation node.

Every generation prompt in the system (Cartographer, Flow Tracer, lane
A/B/C, Teacher, Q&A) opens with this block. The point is twofold:

1. **Goal-anchored output.** The model sees the user's exact raw text and
   the planner-derived tilts up front, so the answer is shaped to the
   user's stated intent — not to a generic "explain this repo" prior.
2. **Iteration-2 contract on every prompt.** The three laws (goal-
   anchored / numbers carry consequences / sections end in motion) live
   here too, with one contrastive ❌/✅ pair, so they cannot drift
   between nodes.

The output is deterministic given (``IntentProfile``, ``CapabilityPlan``).
A snapshot test pins the exact rendered string — if you change this
helper, the snapshot fails and every downstream prompt is audited.
"""

from __future__ import annotations

from repopilot_agents.state import CapabilityPlan, IntentProfile

# The Iteration-2 contract restated as part of every generation prompt.
# Verbatim from docs/03_ARCHITECTURE.md "Iteration 2" sidebar so writers
# can't quietly water it down per-node.
_THREE_LAWS = (
    "THREE LAWS (do not violate):\n"
    "  1. Every observation is anchored to the user's goal above.\n"
    "  2. Numbers carry consequences — never emit a raw count, churn "
    "figure, or fan-in without saying what it MEANS for the goal.\n"
    "  3. Every section ends in motion — what the reader does next.\n\n"
    "❌ BAD: 'pkg/foo.py is imported by 23 files.'\n"
    "✅ GOOD: 'pkg/foo.py is a hub (23 importers). Since you said you're "
    "evaluating extensibility, a signature change here ripples broadly — "
    "treat it as a tradeoff to flag, not a refactor target.'"
)


def _format_weights(weights: dict[str, float]) -> str:
    if not weights:
        return "(none stated)"
    items = sorted(weights.items(), key=lambda kv: (-kv[1], kv[0]))
    return ", ".join(f"{k}={v:.2f}" for k, v in items)


def _format_keywords(keywords: list[str]) -> str:
    return ", ".join(keywords) if keywords else "(none)"


def _format_active(plan: CapabilityPlan) -> str:
    return ", ".join(plan.active)


def _format_tilt_line(label: str, value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    return f"  - {label}: {value.strip()}"


def render_goal_anchor(
    profile: IntentProfile,
    plan: CapabilityPlan,
) -> str:
    """Render the goal-anchor block for the given (profile, plan) pair.

    Output is a single string with three sections: the user goal, the
    planner-derived tilts (only the non-empty ones), and the three-laws
    block. Designed to fit comfortably under the 2000-input-token budget
    for every node.
    """
    user_goal_lines = [
        "USER GOAL (verbatim, do not rephrase):",
        f'  "{profile.raw_text.strip()}"',
        f"  modality_weights: {_format_weights({str(k): v for k, v in profile.modality_weights.items()})}",
        f"  focus_keywords:   {_format_keywords(profile.focus_keywords)}",
    ]
    if profile.audience_framing:
        user_goal_lines.append(f"  audience:         {profile.audience_framing.strip()}")
    if profile.success_criterion:
        user_goal_lines.append(f"  success looks like: {profile.success_criterion.strip()}")

    plan_lines: list[str] = [
        "PLAN TILT (set by the deterministic planner — honor it):",
        f"  - active capabilities: {_format_active(plan)}",
        f"  - output shape:        {plan.output_shape}",
    ]
    optional = [
        _format_tilt_line("cartographer hub bias", plan.cartographer_tilt),
        _format_tilt_line(
            "flow-tracer targets",
            ", ".join(plan.flow_tracer_targets) if plan.flow_tracer_targets else None,
        ),
        _format_tilt_line("lane-B framing", plan.lane_b_framing),
    ]
    plan_lines.extend(line for line in optional if line is not None)

    return "\n".join(["\n".join(user_goal_lines), "", "\n".join(plan_lines), "", _THREE_LAWS])


__all__ = ["render_goal_anchor"]
