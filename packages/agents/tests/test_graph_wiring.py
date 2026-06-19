"""End-to-end LangGraph wiring tests.

Mock the per-node bodies so the graph runs in-memory without Postgres.
What we care about here is the *wiring*: that the right nodes fire in
the right order, that conditional edges respect ``capability_plan.active``,
and that the typed state diffs land where the schema expects them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import pytest

from repopilot_agents import graph as graph_mod
from repopilot_agents.graph import RECURSION_LIMIT, build_graph
from repopilot_agents.state import (
    ArchaeologistState,
    CapabilityPlan,
    Claim,
    CodeRef,
    Insight,
    IntentProfile,
    Opportunity,
    TourSection,
)
from repopilot_core.llm.provider import LLMProvider


@dataclass(slots=True)
class _StubResponse:
    text: str

    @property
    def total_tokens(self) -> int:
        return 0


class _NullProvider:
    async def generate(self, *args: Any, **kwargs: Any) -> _StubResponse:
        raise AssertionError("provider should not be called when nodes are mocked")


@pytest.fixture
def fake_engine() -> Any:
    class _E:
        async def dispose(self) -> None:
            return None

    return _E()


# ─── Helpers ────────────────────────────────────────────────────────────


def _ref(sym: str = "pkg.foo") -> CodeRef:
    return CodeRef(file_path="pkg/foo.py", start_line=1, end_line=2, symbol=sym)


def _insight(sym: str = "pkg.foo") -> Insight:
    return Insight(
        finding="finding",
        because="reason",
        so_what="consequence",
        refs=[_ref(sym)],
        goal_link="ties to goal",
    )


def _section(sym: str = "pkg.foo") -> TourSection:
    return TourSection(
        title="Overview",
        order=0,
        claims=[Claim(text="x", refs=[_ref(sym)])],
    )


def _opportunity(lane: str = "B_quality") -> Opportunity:
    payload: dict[str, Any] = {
        "lane": lane,
        "title": f"{lane} opportunity",
        "evidence_refs": [_ref()],
        "why_this_matters": "matters",
        "blast_radius": "isolated",
        "difficulty": "S",
        "suggested_first_step": "open the file",
        "files_to_touch": ["pkg/foo.py"],
    }
    if lane == "C_suspicion":
        payload["confirm_before_pr"] = "to_confirm: reproduce first"
    return Opportunity.model_validate(payload)


# ─── Wiring smoke tests ─────────────────────────────────────────────────


def test_recursion_limit_is_pinned_at_fifteen() -> None:
    assert RECURSION_LIMIT == 15


@pytest.mark.asyncio
async def test_full_graph_runs_intent_then_cartographer_then_teacher(
    monkeypatch: pytest.MonkeyPatch,
    fake_engine: Any,
) -> None:
    """Confirmed-profile path: profile + plan are already set, so the
    profiler is a no-op. The cartographer + teacher fire in order; the
    state ends with a non-empty system_map and draft_tour."""

    async def fake_profile(raw: str, *, provider: Any) -> IntentProfile:
        raise AssertionError("profiler should be a no-op when profile is preset")

    async def fake_cartographer(**kwargs: Any) -> dict[str, Any]:
        return {"system_map": [_insight()]}

    async def fake_flow_tracer(**kwargs: Any) -> dict[str, Any]:
        return {"traced_flows": []}

    async def fake_teacher(**kwargs: Any) -> dict[str, Any]:
        return {"draft_tour": [_section()]}

    monkeypatch.setattr(graph_mod, "profile_intent", fake_profile)
    monkeypatch.setattr(graph_mod, "run_cartographer", fake_cartographer)
    monkeypatch.setattr(graph_mod, "run_flow_tracer", fake_flow_tracer)
    monkeypatch.setattr(graph_mod, "run_teacher", fake_teacher)

    compiled = build_graph(
        provider=cast(LLMProvider, _NullProvider()),
        engine=fake_engine,
    )

    profile = IntentProfile(raw_text="understand foo")
    plan = CapabilityPlan(
        active=["cartographer", "teacher"],
        dependencies={"teacher": ["cartographer"]},
        output_shape="narrative",
    )
    start = ArchaeologistState(
        repo_id="r1",
        repo_url="https://example.com/r1",
        intent_profile=profile,
        capability_plan=plan,
    )

    final = await compiled.ainvoke(start, config={"recursion_limit": RECURSION_LIMIT})

    assert isinstance(final, dict)
    assert len(final["system_map"]) == 1
    assert len(final["draft_tour"]) == 1
    assert final["draft_tour"][0].claims[0].refs[0].symbol == "pkg.foo"


@pytest.mark.asyncio
async def test_graph_runs_profiler_and_planner_for_cold_start(
    monkeypatch: pytest.MonkeyPatch,
    fake_engine: Any,
) -> None:
    """Cold-start path: no profile, no plan. The profiler must run, the
    planner must run, then generation."""

    async def fake_profile(raw: str, *, provider: Any) -> IntentProfile:
        return IntentProfile(
            raw_text=raw,
            modality_weights={"understand": 0.9},
            focus_keywords=["request"],
        )

    async def fake_cartographer(**kwargs: Any) -> dict[str, Any]:
        return {"system_map": [_insight()]}

    async def fake_flow_tracer(**kwargs: Any) -> dict[str, Any]:
        return {"traced_flows": [_insight("pkg.bar")]}

    async def fake_teacher(**kwargs: Any) -> dict[str, Any]:
        return {"draft_tour": [_section()]}

    monkeypatch.setattr(graph_mod, "profile_intent", fake_profile)
    monkeypatch.setattr(graph_mod, "run_cartographer", fake_cartographer)
    monkeypatch.setattr(graph_mod, "run_flow_tracer", fake_flow_tracer)
    monkeypatch.setattr(graph_mod, "run_teacher", fake_teacher)

    compiled = build_graph(
        provider=cast(LLMProvider, _NullProvider()),
        engine=fake_engine,
    )
    start = ArchaeologistState(
        repo_id="r1",
        repo_url="https://example.com/r1",
        user_question="walk me through the request lifecycle",
    )

    final = await compiled.ainvoke(start, config={"recursion_limit": RECURSION_LIMIT})

    assert final["intent_profile"] is not None
    assert final["capability_plan"] is not None
    assert "cartographer" in final["capability_plan"].active
    assert len(final["system_map"]) >= 1
    assert len(final["draft_tour"]) >= 1


@pytest.mark.asyncio
async def test_router_skips_flow_tracer_when_not_active(
    monkeypatch: pytest.MonkeyPatch,
    fake_engine: Any,
) -> None:
    async def fake_cartographer(**kwargs: Any) -> dict[str, Any]:
        return {"system_map": [_insight()]}

    async def fake_flow_tracer(**kwargs: Any) -> dict[str, Any]:
        raise AssertionError("flow_tracer must not run when not active")

    async def fake_teacher(**kwargs: Any) -> dict[str, Any]:
        return {"draft_tour": [_section()]}

    monkeypatch.setattr(graph_mod, "run_cartographer", fake_cartographer)
    monkeypatch.setattr(graph_mod, "run_flow_tracer", fake_flow_tracer)
    monkeypatch.setattr(graph_mod, "run_teacher", fake_teacher)

    compiled = build_graph(
        provider=cast(LLMProvider, _NullProvider()),
        engine=fake_engine,
    )

    profile = IntentProfile(raw_text="x")
    plan = CapabilityPlan(active=["cartographer", "teacher"], output_shape="narrative")
    start = ArchaeologistState(
        repo_id="r1",
        repo_url="https://example.com/r1",
        intent_profile=profile,
        capability_plan=plan,
    )
    final = await compiled.ainvoke(start, config={"recursion_limit": RECURSION_LIMIT})
    assert len(final["draft_tour"]) == 1


def test_build_graph_accepts_checkpointer(fake_engine: Any) -> None:
    """Smoke test for the checkpointer plumbing — pass MemorySaver and
    confirm compile doesn't raise. The Phase 6 hardening pass swaps this
    for an AsyncPostgresSaver."""
    from langgraph.checkpoint.memory import MemorySaver

    compiled = build_graph(
        provider=cast(LLMProvider, _NullProvider()),
        engine=fake_engine,
        checkpointer=MemorySaver(),
    )
    # Compiled object has an invoke / ainvoke surface — confirm typed.
    assert hasattr(compiled, "ainvoke")


@pytest.mark.asyncio
async def test_contribute_lanes_converge_on_ranker_then_teacher(
    monkeypatch: pytest.MonkeyPatch,
    fake_engine: Any,
) -> None:
    async def fake_teacher(**kwargs: Any) -> dict[str, Any]:
        return {"draft_tour": [_section()]}

    def fake_lane_a(*args: Any, **kwargs: Any) -> dict[str, Any]:
        opp = _opportunity("A_issue")
        return {"triaged_issues": [opp], "opportunity_list": [opp]}

    def fake_lane_b(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"opportunity_list": [_opportunity("B_quality")]}

    def fake_lane_c(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"opportunity_list": [_opportunity("C_suspicion")]}

    monkeypatch.setattr(graph_mod, "run_teacher", fake_teacher)
    monkeypatch.setattr(graph_mod, "run_lane_a_triage", fake_lane_a)
    monkeypatch.setattr(graph_mod, "run_lane_b_quality", fake_lane_b)
    monkeypatch.setattr(graph_mod, "run_lane_c_suspicion", fake_lane_c)

    compiled = build_graph(
        provider=cast(LLMProvider, _NullProvider()),
        engine=fake_engine,
    )
    profile = IntentProfile(raw_text="find me a first PR and hunt fragility")
    plan = CapabilityPlan(
        active=[
            "lane_a_issue_triage",
            "lane_b_code_health",
            "lane_c_suspicion",
            "teacher",
        ],
        dependencies={
            "teacher": [
                "lane_a_issue_triage",
                "lane_b_code_health",
                "lane_c_suspicion",
            ]
        },
        output_shape="ranked_list",
        ranker_weights={"A": 0.6, "B": 0.3, "C": 0.1},
    )
    start = ArchaeologistState(
        repo_id="r1",
        repo_url="https://example.com/r1",
        intent_profile=profile,
        capability_plan=plan,
    )

    final = await compiled.ainvoke(start, config={"recursion_limit": RECURSION_LIMIT})

    assert len(final["opportunity_list"]) == 3
    assert len(final["ranked_opportunity_list"]) == 3
    assert final["ranked_opportunity_list"][0].lane == "A_issue"
    assert len(final["draft_tour"]) == 1


def test_answer_question_is_re_exported() -> None:
    # Q&A entry point is exposed via the same module so callers have a
    # single import surface (docs/03 § "Q&A is universal").
    assert graph_mod.answer_question is not None
