"""Phase 5 Contribute-mode unit tests."""

from __future__ import annotations

from typing import cast

from repopilot_agents.contribute.briefing import build_opportunity_briefing
from repopilot_agents.contribute.lane_a_triage import triage_issues
from repopilot_agents.contribute.lane_b_quality import (
    QualityCandidate,
    detect_quality_opportunities,
)
from repopilot_agents.contribute.lane_c_suspicion import (
    lane_c_language_violation,
    run_lane_c_suspicion,
)
from repopilot_agents.contribute.ranker import rank_opportunities
from repopilot_agents.state import CapabilityPlan, CodeRef, IntentProfile, Opportunity
from repopilot_agents.tools.github_issues import Issue
from repopilot_agents.types import SymbolMetrics


def _ref(symbol: str = "pkg.foo", file_path: str = "pkg/foo.py") -> CodeRef:
    return CodeRef(file_path=file_path, start_line=1, end_line=5, symbol=symbol)


def _profile(raw: str = "find me a first PR") -> IntentProfile:
    return IntentProfile(raw_text=raw, modality_weights={"change": 0.8})


def _metrics(symbol: str, *, fan_in: int, has_tests: bool = True) -> SymbolMetrics:
    return SymbolMetrics(
        symbol=symbol,
        fan_in=fan_in,
        fan_out=1,
        cyclomatic=2,
        churn=0,
        has_tests=has_tests,
    )


def _opp(lane: str, title: str) -> Opportunity:
    payload = {
        "lane": lane,
        "title": title,
        "evidence_refs": [_ref()],
        "why_this_matters": "matters",
        "blast_radius": "isolated",
        "difficulty": "S",
        "suggested_first_step": "open the file",
        "files_to_touch": ["pkg/foo.py"],
        "mergeability": 0.5,
        "approachability": 0.5,
        "evidence_strength": 0.5,
    }
    if lane == "C_suspicion":
        payload["confirm_before_pr"] = "to_confirm: reproduce first"
    return Opportunity.model_validate(payload)


def test_lane_c_banned_vocabulary_rejected() -> None:
    assert lane_c_language_violation("this bug will crash") == "bug"
    assert lane_c_language_violation("worth investigating before a PR") is None


def test_lane_c_outputs_guarded_confirm_steps() -> None:
    diff = run_lane_c_suspicion(
        [_ref("pkg.auth.check", "pkg/auth.py")], profile=_profile("hunt fragility in auth")
    )
    opp = diff["opportunity_list"][0]
    assert opp.lane == "C_suspicion"
    assert opp.confirm_before_pr is not None
    assert "to_confirm:" in opp.confirm_before_pr
    assert lane_c_language_violation(opp.title) is None
    assert lane_c_language_violation(opp.why_this_matters) is None


def test_lane_a_approachability_uses_graph_not_labels() -> None:
    labeled_hub = Issue(
        number=1,
        title="Fix hub issue",
        body="touches pkg.hub",
        state="open",
        labels=["good first issue"],
        referenced_files=["pkg/hub.py"],
    )
    unlabeled_isolated = Issue(
        number=2,
        title="Fix small issue",
        body="touches pkg.leaf",
        state="open",
        labels=[],
        referenced_files=["pkg/leaf.py"],
    )
    opportunities, rejected = triage_issues(
        [labeled_hub, unlabeled_isolated],
        metrics_by_symbol={
            "pkg.hub": _metrics("pkg.hub", fan_in=35),
            "pkg.leaf": _metrics("pkg.leaf", fan_in=1),
        },
        profile=_profile(),
        limit=1,
    )
    assert opportunities[0].title.startswith("#2")
    assert rejected[0].title.startswith("#1")
    assert "fan-in 35" in rejected[0].reason


def test_lane_b_dead_code_excludes_entry_points() -> None:
    candidates = [
        QualityCandidate(
            detector="dead_code",
            ref=_ref("pkg.cli.main"),
            metrics=_metrics("pkg.cli.main", fan_in=0),
            is_entry_point=True,
        ),
        QualityCandidate(
            detector="dead_code",
            ref=_ref("pkg.unused"),
            metrics=_metrics("pkg.unused", fan_in=0),
        ),
    ]
    opportunities = detect_quality_opportunities(candidates, profile=_profile("find cleanup"))
    assert [opp.title for opp in opportunities] == ["Dead Code in pkg.unused"]


def test_ranker_deterministic() -> None:
    plan = CapabilityPlan(active=["lane_a_issue_triage", "teacher"], output_shape="ranked_list")
    items = [_opp("B_quality", "b"), _opp("A_issue", "a")]
    assert rank_opportunities(items, plan=plan) == rank_opportunities(items, plan=plan)


def test_ranker_respects_planner_weights() -> None:
    issue = _opp("A_issue", "issue")
    suspicion = _opp("C_suspicion", "suspicion")
    a_heavy = CapabilityPlan(
        active=["lane_a_issue_triage", "lane_c_suspicion", "teacher"],
        output_shape="ranked_list",
        ranker_weights={"A": 0.7, "B": 0.2, "C": 0.1},
    )
    c_heavy = CapabilityPlan(
        active=["lane_a_issue_triage", "lane_c_suspicion", "teacher"],
        output_shape="ranked_list",
        ranker_weights={"A": 0.1, "B": 0.2, "C": 0.7},
    )
    assert rank_opportunities([issue, suspicion], plan=a_heavy)[0].lane == "A_issue"
    assert rank_opportunities([issue, suspicion], plan=c_heavy)[0].lane == "C_suspicion"


def test_briefing_surfaces_intent_match_and_rationale() -> None:
    profile = _profile("show me fragility")
    plan = CapabilityPlan(
        active=["lane_c_suspicion", "teacher"],
        output_shape="ranked_list",
        ranker_weights={"A": 0.2, "B": 0.2, "C": 0.6},
    )
    briefing = build_opportunity_briefing(
        [_opp("C_suspicion", "check auth")], profile=profile, plan=plan
    )
    assert "problem-hunting" in str(briefing["rationale"])
    opportunities = cast(list[Opportunity], briefing["opportunities"])
    assert "show me fragility" in str(opportunities[0].intent_match)
