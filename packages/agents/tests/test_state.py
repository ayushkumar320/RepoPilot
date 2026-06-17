"""Validator tests for ``ArchaeologistState`` and its sub-models.

These tests pin the contract from ``docs/03_ARCHITECTURE.md`` § State schema.
If a validator stops failing on bad input, an upstream agent can emit a stat
dump (or an unguarded suspicion, or a goal-orphaned insight) and the whole
trust spine collapses silently. So: failure cases get tests too.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from repopilot_agents.state import (
    ArchaeologistState,
    CapabilityPlan,
    Claim,
    Insight,
    IntentProfile,
    Opportunity,
    QAExchange,
    TourSection,
    VerifierObjection,
)
from repopilot_agents.types import CodeRef


def _ref() -> CodeRef:
    return CodeRef(file_path="x.py", start_line=1, end_line=2)


# ─── Claim ───────────────────────────────────────────────────────────────


def test_claim_requires_at_least_one_ref() -> None:
    with pytest.raises(ValidationError):
        Claim(text="hello", refs=[])


def test_claim_rejects_relevance_out_of_unit_interval() -> None:
    with pytest.raises(ValidationError):
        Claim(text="hello", refs=[_ref()], relevance=1.5)


def test_claim_defaults_unverified() -> None:
    c = Claim(text="hello", refs=[_ref()])
    assert c.status == "unverified"
    assert c.relevance == 1.0


# ─── Insight ─────────────────────────────────────────────────────────────


def test_insight_rejects_empty_so_what() -> None:
    with pytest.raises(ValidationError):
        Insight(
            finding="X imports Y",
            because="AST import edge",
            so_what="",
            refs=[_ref()],
            goal_link="user wants understand",
        )


def test_insight_rejects_empty_goal_link() -> None:
    with pytest.raises(ValidationError):
        Insight(
            finding="X imports Y",
            because="AST import edge",
            so_what="touching X reaches Y",
            refs=[_ref()],
            goal_link="",
        )


def test_insight_accepts_complete_fields() -> None:
    ins = Insight(
        finding="X imports Y",
        because="AST import edge",
        so_what="touching X reaches Y",
        refs=[_ref()],
        goal_link="user asked about Y",
    )
    assert ins.so_what.startswith("touching")


# ─── Opportunity (Lane C confirm_before_pr) ──────────────────────────────


def test_lane_c_requires_confirm_before_pr() -> None:
    with pytest.raises(ValidationError):
        Opportunity(
            lane="C_suspicion",
            title="possible race in foo",
            evidence_refs=[_ref()],
            why_this_matters="two writers, no lock",
            blast_radius="module-scoped",
            difficulty="M",
            suggested_first_step="reproduce under contention",
        )


def test_lane_b_does_not_require_confirm_before_pr() -> None:
    opp = Opportunity(
        lane="B_quality",
        title="cleanup",
        evidence_refs=[_ref()],
        why_this_matters="dead branch",
        blast_radius="isolated",
        difficulty="S",
        suggested_first_step="delete branch",
    )
    assert opp.confirm_before_pr is None


def test_lane_c_with_confirm_succeeds() -> None:
    opp = Opportunity(
        lane="C_suspicion",
        title="possible race",
        evidence_refs=[_ref()],
        why_this_matters="two writers, no lock",
        blast_radius="module-scoped",
        difficulty="M",
        suggested_first_step="reproduce under contention",
        confirm_before_pr="confirm with maintainer before filing PR",
    )
    assert opp.confirm_before_pr is not None


# ─── IntentProfile ───────────────────────────────────────────────────────


def test_intent_profile_rejects_out_of_unit_modality_weights() -> None:
    with pytest.raises(ValidationError):
        IntentProfile(raw_text="hi", modality_weights={"understand": 1.5})


def test_intent_profile_defaults() -> None:
    p = IntentProfile(raw_text="I want to understand X")
    assert p.modality_weights == {}
    assert p.output_shape_preference == "unspecified"
    assert p.focus_keywords == []


# ─── CapabilityPlan ──────────────────────────────────────────────────────


def test_plan_rejects_dependency_on_inactive_capability() -> None:
    with pytest.raises(ValidationError):
        CapabilityPlan(
            active=["cartographer"],
            dependencies={"cartographer": ["flow_tracer"]},
            output_shape="narrative",
        )


def test_plan_rejects_dependency_for_inactive_capability() -> None:
    with pytest.raises(ValidationError):
        CapabilityPlan(
            active=["cartographer"],
            dependencies={"flow_tracer": []},
            output_shape="narrative",
        )


def test_plan_requires_at_least_one_active_capability() -> None:
    with pytest.raises(ValidationError):
        CapabilityPlan(active=[], output_shape="narrative")


def test_plan_accepts_valid_dependencies() -> None:
    plan = CapabilityPlan(
        active=["cartographer", "teacher"],
        dependencies={"teacher": ["cartographer"]},
        output_shape="narrative",
    )
    assert plan.dependencies["teacher"] == ["cartographer"]


# ─── State + reducer behavior ────────────────────────────────────────────


def test_state_defaults_are_empty() -> None:
    s = ArchaeologistState(repo_id="r1", repo_url="https://example.com/r1")
    assert s.intent_profile is None
    assert s.capability_plan is None
    assert s.system_map == []
    assert s.qa_history == []
    assert s.errors == []


def test_state_accepts_full_intent_layer() -> None:
    s = ArchaeologistState(
        repo_id="r1",
        repo_url="https://example.com/r1",
        intent_profile=IntentProfile(raw_text="understand auth flow"),
        capability_plan=CapabilityPlan(active=["cartographer"], output_shape="narrative"),
    )
    assert s.intent_profile is not None
    assert s.capability_plan is not None
    assert s.capability_plan.active == ["cartographer"]


def test_qa_exchange_round_trip() -> None:
    ex = QAExchange(
        question="what does foo do?",
        answer_claims=[Claim(text="foo does X", refs=[_ref()])],
        asked_at=datetime.now(UTC),
    )
    assert ex.answer_claims[0].text == "foo does X"


def test_tour_section_and_objection_round_trip() -> None:
    section = TourSection(
        title="Overview",
        order=0,
        claims=[Claim(text="hello", refs=[_ref()])],
    )
    objection = VerifierObjection(section_order=0, claim_text="hello", reason="ungrounded")
    assert section.order == 0
    assert objection.reason == "ungrounded"
