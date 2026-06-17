"""Capability Planner tests.

The eval-runner accuracy gate (F1 ≥ 90% on ``planner_correctness_v1.jsonl``)
lives in the harness lane. These unit tests pin three load-bearing
properties:

1. Divergent profiles produce **structurally different** plans (Phase 3
   gate: ≥ 50% divergence on flask). We check shape-of-output here; the
   harness checks accuracy.
2. Every plan's ``dependencies`` are a subgraph of ``active`` (encoded
   already in ``CapabilityPlan`` validators, but we still want the
   planner to never construct a plan that fails that check).
3. The inclusive default fires on the minimal profile so the system is
   open, not closed.
"""

from __future__ import annotations

from repopilot_agents.intent.planner import plan
from repopilot_agents.state import CapabilityPlan, IntentProfile


def _profile(**kwargs: object) -> IntentProfile:
    base: dict[str, object] = {"raw_text": "anything"}
    base.update(kwargs)
    return IntentProfile.model_validate(base)


def test_minimal_profile_falls_through_to_inclusive_default() -> None:
    p = _profile(raw_text="hello")
    cp = plan(p)

    assert "cartographer" in cp.active
    assert "lane_b_code_health" in cp.active
    assert cp.active[-1] == "teacher", "teacher is the terminal capability"
    assert cp.lane_b_framing == "cleanup_opportunities"


def test_teacher_is_always_terminal() -> None:
    p = _profile(
        raw_text="understand the lifecycle of a request",
        modality_weights={"understand": 0.9},
    )
    cp = plan(p)
    assert cp.active[-1] == "teacher"


def test_understanding_intent_activates_cartographer_and_flow_tracer() -> None:
    p = _profile(
        raw_text="I want to understand how httpx handles connection pooling",
        modality_weights={"understand": 0.8},
        focus_keywords=["connection_pool"],
    )
    cp = plan(p)
    assert "cartographer" in cp.active
    assert "flow_tracer" in cp.active
    # focus_keywords seed flow targets → soft dep skipped.
    assert "flow_tracer" not in cp.dependencies
    assert cp.flow_tracer_targets == ["connection_pool"]


def test_flow_tracer_depends_on_cartographer_when_no_target_seed() -> None:
    p = _profile(
        raw_text="trace the lifecycle of a request",
        modality_weights={"understand": 0.7},
        # no focus_keywords → no seed → soft dep must fire
    )
    cp = plan(p)
    assert "flow_tracer" in cp.active
    assert cp.dependencies.get("flow_tracer") == ["cartographer"]


def test_change_plus_issue_activates_lane_a_with_ranker_weights() -> None:
    p = _profile(
        raw_text="I want to ship a PR for an open issue about retries",
        modality_weights={"change": 0.7},
        focus_keywords=["retry"],
    )
    cp = plan(p)
    assert "lane_a_issue_triage" in cp.active
    assert cp.ranker_weights.get("A") == 0.6


def test_evaluate_intent_activates_lane_b_with_tradeoff_framing() -> None:
    p = _profile(
        raw_text="how solid is their async story?",
        modality_weights={"evaluate": 0.7, "change": 0.2},
    )
    cp = plan(p)
    assert "lane_b_code_health" in cp.active
    assert cp.lane_b_framing == "tradeoffs_visible_in_code"


def test_fragility_signal_activates_lane_c() -> None:
    p = _profile(
        raw_text="hunt for fragile code around the auth path",
        modality_weights={"change": 0.5},
        focus_keywords=["auth"],
    )
    cp = plan(p)
    assert "lane_c_suspicion" in cp.active
    # confirm_before_pr lives on Opportunity, not on the plan; planner
    # surfaces the keyword filter only.
    assert cp.tilts["lane_c_suspicion"]["keyword_filter"] == ["auth"]


def test_compare_intent_picks_comparison_table_shape() -> None:
    p = _profile(
        raw_text="compare httpx vs requests for our use case",
        modality_weights={"compare": 0.7, "understand": 0.3},
    )
    cp = plan(p)
    assert cp.output_shape == "comparison_table"


def test_explicit_shape_preference_wins_over_inference() -> None:
    p = _profile(
        raw_text="hunt for fragile auth code",
        modality_weights={"change": 0.6},
        focus_keywords=["auth"],
        output_shape_preference="dossier",
    )
    cp = plan(p)
    assert cp.output_shape == "dossier"


def test_dependencies_are_subset_of_active_for_diverse_profiles() -> None:
    profiles = [
        _profile(raw_text="explain the request lifecycle", modality_weights={"understand": 0.9}),
        _profile(raw_text="hunt for fragile auth code", modality_weights={"change": 0.6}),
        _profile(
            raw_text="ship a PR for issue #123 about retries",
            modality_weights={"change": 0.8},
            focus_keywords=["retry"],
        ),
        _profile(raw_text="how solid is the async story", modality_weights={"evaluate": 0.7}),
        _profile(raw_text="compare httpx and requests", modality_weights={"compare": 0.6}),
        _profile(raw_text="find the auth code", modality_weights={"locate": 0.6}),
        _profile(raw_text="hello"),
    ]
    for p in profiles:
        cp = plan(p)
        assert isinstance(cp, CapabilityPlan)
        active = set(cp.active)
        for cap, deps in cp.dependencies.items():
            assert cap in active, f"{cap} declared deps but not active"
            for d in deps:
                assert d in active, f"{cap} depends on inactive {d}"


def test_two_divergent_intents_produce_structurally_different_plans() -> None:
    # The Phase 3 entry gate (two-intent divergence ≥ 50% on flask)
    # measures this empirically; the unit test pins it on a chosen pair
    # so the rule changes that destroy divergence fail in CI.
    learner = _profile(
        raw_text="explain the lifecycle of an httpx request",
        modality_weights={"understand": 0.9},
    )
    auditor = _profile(
        raw_text="hunt for fragile, security-sensitive code paths",
        modality_weights={"change": 0.6},
        focus_keywords=["auth"],
    )
    learner_plan = plan(learner)
    auditor_plan = plan(auditor)

    learner_caps = set(learner_plan.active)
    auditor_caps = set(auditor_plan.active)

    # symmetric difference ≥ 1 distinct capability is enough at the unit
    # level — the real divergence gate scores tilts + shape + ranker too.
    diff = learner_caps.symmetric_difference(auditor_caps)
    assert diff, "divergent intents produced identical active capability sets"

    # flow_tracer should attach to the learner intent but not the auditor.
    assert "flow_tracer" in learner_caps
    assert "lane_c_suspicion" in auditor_caps
