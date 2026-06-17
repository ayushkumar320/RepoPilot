"""Snapshot + invariant tests for the shared goal-anchor block.

These tests are deliberately strict: a generation prompt that no longer
opens with the goal-anchor block is broken by definition. The eval-runner
gates downstream measure quality; these tests pin shape.
"""

from __future__ import annotations

from textwrap import dedent

from repopilot_agents.intent.planner import plan as plan_fn
from repopilot_agents.prompts import render_goal_anchor
from repopilot_agents.state import CapabilityPlan, IntentProfile


def _profile() -> IntentProfile:
    return IntentProfile(
        raw_text="I want to understand how httpx handles connection pooling.",
        modality_weights={"understand": 0.8, "locate": 0.4},
        focus_keywords=["connection_pool", "leak"],
        audience_framing="for a PR review",
        output_shape_preference="narrative",
        success_criterion="can trace a request through the pool",
    )


def test_snapshot_for_a_canonical_understand_intent() -> None:
    profile = _profile()
    plan = plan_fn(profile)
    rendered = render_goal_anchor(profile, plan)

    expected = dedent(
        """\
        USER GOAL (verbatim, do not rephrase):
          "I want to understand how httpx handles connection pooling."
          modality_weights: understand=0.80, locate=0.40
          focus_keywords:   connection_pool, leak
          audience:         for a PR review
          success looks like: can trace a request through the pool

        PLAN TILT (set by the deterministic planner — honor it):
          - active capabilities: cartographer, flow_tracer, teacher
          - output shape:        narrative
          - cartographer hub bias: balanced
          - flow-tracer targets: connection_pool, leak

        THREE LAWS (do not violate):
          1. Every observation is anchored to the user's goal above.
          2. Numbers carry consequences — never emit a raw count, churn figure, or fan-in without saying what it MEANS for the goal.
          3. Every section ends in motion — what the reader does next.

        ❌ BAD: 'pkg/foo.py is imported by 23 files.'
        ✅ GOOD: 'pkg/foo.py is a hub (23 importers). Since you said you're evaluating extensibility, a signature change here ripples broadly — treat it as a tradeoff to flag, not a refactor target.'"""
    )
    assert rendered == expected


def test_goal_anchor_includes_raw_text_verbatim() -> None:
    profile = _profile()
    plan = plan_fn(profile)
    rendered = render_goal_anchor(profile, plan)
    assert profile.raw_text in rendered


def test_goal_anchor_starts_with_user_goal_block() -> None:
    profile = _profile()
    plan = plan_fn(profile)
    rendered = render_goal_anchor(profile, plan)
    assert rendered.startswith("USER GOAL"), rendered[:80]


def test_three_laws_appear_at_the_end() -> None:
    profile = _profile()
    plan = plan_fn(profile)
    rendered = render_goal_anchor(profile, plan)
    assert "THREE LAWS" in rendered
    assert "❌ BAD" in rendered and "✅ GOOD" in rendered
    # Three laws live at the tail so the model sees the contract last.
    laws_index = rendered.index("THREE LAWS")
    goal_index = rendered.index("USER GOAL")
    plan_index = rendered.index("PLAN TILT")
    assert goal_index < plan_index < laws_index


def test_minimal_profile_does_not_render_optional_lines() -> None:
    profile = IntentProfile(raw_text="hello world")
    plan = plan_fn(profile)
    rendered = render_goal_anchor(profile, plan)
    assert "audience:" not in rendered
    assert "success looks like:" not in rendered
    assert "flow-tracer targets:" not in rendered
    # Default plan from minimal profile uses lane B → cleanup framing.
    assert "lane-B framing: cleanup_opportunities" in rendered


def test_compare_intent_renders_comparison_table_shape() -> None:
    profile = IntentProfile(
        raw_text="compare httpx vs requests",
        modality_weights={"compare": 0.7, "understand": 0.3},
    )
    plan = plan_fn(profile)
    rendered = render_goal_anchor(profile, plan)
    assert "output shape:        comparison_table" in rendered


def test_capabilities_appear_in_planner_order() -> None:
    profile = _profile()
    plan = plan_fn(profile)
    rendered = render_goal_anchor(profile, plan)
    line = next(line for line in rendered.splitlines() if "active capabilities:" in line)
    assert line.endswith("cartographer, flow_tracer, teacher")


def test_render_accepts_explicit_plan_objects() -> None:
    profile = IntentProfile(raw_text="standalone test")
    custom_plan = CapabilityPlan(
        active=["cartographer", "teacher"],
        dependencies={"teacher": ["cartographer"]},
        output_shape="narrative",
        cartographer_tilt="data_hubs",
    )
    rendered = render_goal_anchor(profile, custom_plan)
    assert "cartographer hub bias: data_hubs" in rendered
    assert "active capabilities: cartographer, teacher" in rendered
