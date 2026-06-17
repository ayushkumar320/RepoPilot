"""Unit tests for the Cartographer / Flow Tracer / Teacher nodes.

These tests pin the **shape** of each node's return — the diff dict, the
typed objects, the ref-grounding rule. End-to-end quality (e.g.
actionability ≥ 80%) lives in the eval-runner lane.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import pytest

from repopilot_agents.capabilities import (
    run_cartographer,
    run_flow_tracer,
    run_teacher,
)
from repopilot_agents.capabilities._coerce import (
    coerce_insight,
    extract_json_list,
)
from repopilot_agents.state import (
    CapabilityPlan,
    CodeRef,
    Insight,
    IntentProfile,
    TourSection,
)
from repopilot_agents.types import GraphQueryResult, Path, SymbolMetrics
from repopilot_core.llm.provider import LLMProvider

# ─── Helpers ────────────────────────────────────────────────────────────


@dataclass(slots=True)
class _StubResponse:
    text: str

    @property
    def total_tokens(self) -> int:
        return 0


class _ScriptedProvider:
    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    async def generate(self, model: Any, messages: Any, **kwargs: Any) -> _StubResponse:
        self.calls.append(
            {
                "model": model,
                "system": next(m for m in messages if m.role == "system").content[:30],
                "user_len": len(next(m for m in messages if m.role == "user").content),
            }
        )
        if not self._responses:
            raise AssertionError("scripted provider exhausted")
        return _StubResponse(text=self._responses.pop(0))


def _profile(raw: str = "understand the request lifecycle") -> IntentProfile:
    return IntentProfile(
        raw_text=raw,
        modality_weights={"understand": 0.8},
        focus_keywords=["foo"],
    )


def _plan(**overrides: object) -> CapabilityPlan:
    base: dict[str, object] = {
        "active": ["cartographer", "teacher"],
        "output_shape": "narrative",
    }
    base.update(overrides)
    return CapabilityPlan.model_validate(base)


# ─── Coercion layer ─────────────────────────────────────────────────────


def test_extract_json_list_handles_code_fences() -> None:
    out = extract_json_list('```json\n[{"a":1},{"b":2}]\n```')
    assert out == [{"a": 1}, {"b": 2}]


def test_extract_json_list_returns_empty_on_garbage() -> None:
    assert extract_json_list("not JSON at all") == []


def test_extract_json_list_drops_non_dict_entries() -> None:
    out = extract_json_list('[{"a":1}, 42, "stringy", {"b":2}]')
    assert out == [{"a": 1}, {"b": 2}]


def test_coerce_insight_rejects_unknown_symbol() -> None:
    ref = CodeRef(file_path="x.py", start_line=1, end_line=2, symbol="pkg.foo")
    payload = {
        "finding": "fact",
        "because": "reason",
        "so_what": "matters",
        "goal_link": "links to goal",
        "refs": ["pkg.does_not_exist"],
    }
    assert coerce_insight(payload, {"pkg.foo": ref}) is None


def test_coerce_insight_accepts_symbol_strings() -> None:
    ref = CodeRef(file_path="x.py", start_line=1, end_line=2, symbol="pkg.foo")
    payload = {
        "finding": "fact",
        "because": "reason",
        "so_what": "matters",
        "goal_link": "links to goal",
        "refs": ["pkg.foo"],
    }
    insight = coerce_insight(payload, {"pkg.foo": ref})
    assert insight is not None
    assert insight.refs[0].symbol == "pkg.foo"


def test_coerce_insight_rejects_empty_so_what() -> None:
    ref = CodeRef(file_path="x.py", start_line=1, end_line=2, symbol="pkg.foo")
    payload = {
        "finding": "fact",
        "because": "reason",
        "so_what": "",
        "goal_link": "links to goal",
        "refs": ["pkg.foo"],
    }
    assert coerce_insight(payload, {"pkg.foo": ref}) is None


# ─── Cartographer ───────────────────────────────────────────────────────


@pytest.fixture
def patched_carto_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub the deterministic tools the Cartographer calls.

    The fact bundle is small and verifiable without spinning up
    SQLAlchemy: two hubs + one entry point + one metrics row.
    """
    from repopilot_agents.capabilities import cartographer as carto

    async def fake_query(
        kind: str, *, engine: Any, repo_id: str, top_n: int = 20
    ) -> list[GraphQueryResult]:
        if kind == "hubs":
            return [
                GraphQueryResult(symbol="pkg.foo", kind="function", score=12.0),
                GraphQueryResult(symbol="pkg.bar", kind="function", score=7.0),
            ]
        if kind == "entry_points":
            return [GraphQueryResult(symbol="pkg.main", kind="function", score=0.0)]
        return []

    async def fake_metrics(symbol: str, *, engine: Any, repo_id: str) -> SymbolMetrics:
        return SymbolMetrics(
            symbol=symbol, fan_in=12, fan_out=3, cyclomatic=5, churn=2, has_tests=True
        )

    monkeypatch.setattr(carto, "graph_query", fake_query)
    monkeypatch.setattr(carto, "graph_metrics", fake_metrics)


@pytest.mark.asyncio
async def test_cartographer_returns_typed_system_map_diff(
    patched_carto_tools: None,
) -> None:
    payload = (
        "[{"
        '"finding":"pkg.foo is the central call hub",'
        '"because":"12 callers — fan-in dominates the call subgraph",'
        '"so_what":"a signature change here ripples through 12 sites",'
        '"goal_link":"matches the user goal of understanding request lifecycle",'
        '"refs":["pkg.foo"]'
        "}]"
    )
    provider = _ScriptedProvider([payload])
    diff = await run_cartographer(
        profile=_profile(),
        plan=_plan(),
        provider=cast(LLMProvider, provider),
        engine=cast(Any, None),
        repo_id="r1",
    )
    assert list(diff.keys()) == ["system_map"]
    assert len(diff["system_map"]) == 1
    insight = diff["system_map"][0]
    assert isinstance(insight, Insight)
    assert insight.refs[0].symbol == "pkg.foo"


@pytest.mark.asyncio
async def test_cartographer_drops_insights_with_unknown_refs(
    patched_carto_tools: None,
) -> None:
    # First entry references an unknown symbol → dropped. Second cites
    # known one → kept.
    payload = (
        "["
        "{"
        '"finding":"x","because":"y","so_what":"z","goal_link":"w",'
        '"refs":["pkg.UNKNOWN"]'
        "},"
        "{"
        '"finding":"hub","because":"fan_in=12","so_what":"changes ripple",'
        '"goal_link":"links to goal","refs":["pkg.bar"]'
        "}"
        "]"
    )
    provider = _ScriptedProvider([payload])
    diff = await run_cartographer(
        profile=_profile(),
        plan=_plan(),
        provider=cast(LLMProvider, provider),
        engine=cast(Any, None),
        repo_id="r1",
    )
    assert len(diff["system_map"]) == 1
    assert diff["system_map"][0].refs[0].symbol == "pkg.bar"


@pytest.mark.asyncio
async def test_cartographer_returns_empty_on_unparseable_llm_response(
    patched_carto_tools: None,
) -> None:
    provider = _ScriptedProvider(["I cannot help with that."])
    diff = await run_cartographer(
        profile=_profile(),
        plan=_plan(),
        provider=cast(LLMProvider, provider),
        engine=cast(Any, None),
        repo_id="r1",
    )
    assert diff == {"system_map": []}


# ─── Flow Tracer ────────────────────────────────────────────────────────


@pytest.fixture
def patched_traverse(monkeypatch: pytest.MonkeyPatch) -> None:
    from repopilot_agents.capabilities import flow_tracer as ft

    async def fake_traverse(
        start: str,
        *,
        edge_types: list[str],
        engine: Any,
        repo_id: str,
        max_depth: int = 3,
    ) -> list[Path]:
        steps = [
            CodeRef(file_path="pkg/foo.py", start_line=1, end_line=2, symbol="pkg.foo"),
            CodeRef(file_path="pkg/bar.py", start_line=10, end_line=20, symbol="pkg.bar"),
        ]
        return [Path(steps=steps, edge_types=["calls"])]

    monkeypatch.setattr(ft, "graph_traverse", fake_traverse)


@pytest.mark.asyncio
async def test_flow_tracer_uses_planner_targets(patched_traverse: None) -> None:
    payload = (
        '[{"finding":"pkg.foo reaches pkg.bar in one hop","because":"single call edge",'
        '"so_what":"changes to pkg.bar surface in the lifecycle the user asked about",'
        '"goal_link":"matches request lifecycle","refs":["pkg.foo","pkg.bar"]}]'
    )
    provider = _ScriptedProvider([payload])
    diff = await run_flow_tracer(
        profile=_profile(),
        plan=_plan(flow_tracer_targets=["pkg.foo"]),
        provider=cast(LLMProvider, provider),
        engine=cast(Any, None),
        repo_id="r1",
    )
    assert list(diff.keys()) == ["traced_flows"]
    assert len(diff["traced_flows"]) == 1
    assert {r.symbol for r in diff["traced_flows"][0].refs} == {"pkg.foo", "pkg.bar"}


@pytest.mark.asyncio
async def test_flow_tracer_no_targets_returns_empty() -> None:
    provider = _ScriptedProvider([])  # must never be called
    diff = await run_flow_tracer(
        profile=_profile(),
        plan=_plan(),  # no flow_tracer_targets
        provider=cast(LLMProvider, provider),
        engine=cast(Any, None),
        repo_id="r1",
    )
    assert diff == {"traced_flows": []}


# ─── Teacher ────────────────────────────────────────────────────────────


def _insight(symbol: str = "pkg.foo") -> Insight:
    ref = CodeRef(file_path="pkg/foo.py", start_line=1, end_line=2, symbol=symbol)
    return Insight(
        finding="pkg.foo is the central call hub",
        because="12 callers concentrate here",
        so_what="changes ripple through 12 sites",
        refs=[ref],
        goal_link="ties to request lifecycle goal",
    )


@pytest.mark.asyncio
async def test_teacher_empties_when_no_upstream_insights() -> None:
    provider = _ScriptedProvider([])
    diff = await run_teacher(
        profile=_profile(), plan=_plan(), provider=cast(LLMProvider, provider), insights=[]
    )
    assert diff == {"draft_tour": []}


@pytest.mark.asyncio
async def test_teacher_emits_tour_sections_with_grounded_claims() -> None:
    payload = (
        '[{"title":"Where it starts","order":0,"claims":['
        '{"text":"pkg.foo is the entry to the lifecycle","refs":["pkg.foo"]}'
        "]}]"
    )
    provider = _ScriptedProvider([payload])
    diff = await run_teacher(
        profile=_profile(),
        plan=_plan(),
        provider=cast(LLMProvider, provider),
        insights=[_insight("pkg.foo")],
    )
    assert list(diff.keys()) == ["draft_tour"]
    assert len(diff["draft_tour"]) == 1
    section = diff["draft_tour"][0]
    assert isinstance(section, TourSection)
    assert section.order == 0
    assert section.claims[0].refs[0].symbol == "pkg.foo"


@pytest.mark.asyncio
async def test_teacher_drops_claims_with_invented_refs() -> None:
    payload = (
        '[{"title":"Section","order":0,"claims":['
        '{"text":"hallucinated","refs":["pkg.DOES_NOT_EXIST"]},'
        '{"text":"grounded","refs":["pkg.foo"]}'
        "]}]"
    )
    provider = _ScriptedProvider([payload])
    diff = await run_teacher(
        profile=_profile(),
        plan=_plan(),
        provider=cast(LLMProvider, provider),
        insights=[_insight("pkg.foo")],
    )
    section = diff["draft_tour"][0]
    assert len(section.claims) == 1
    assert section.claims[0].text == "grounded"


@pytest.mark.asyncio
async def test_teacher_normalises_section_order() -> None:
    payload = (
        "["
        '{"title":"second","order":5,"claims":[{"text":"a","refs":["pkg.foo"]}]},'
        '{"title":"first","order":0,"claims":[{"text":"b","refs":["pkg.foo"]}]}'
        "]"
    )
    provider = _ScriptedProvider([payload])
    diff = await run_teacher(
        profile=_profile(),
        plan=_plan(),
        provider=cast(LLMProvider, provider),
        insights=[_insight("pkg.foo")],
    )
    sections = diff["draft_tour"]
    assert [s.order for s in sections] == [0, 1]
    assert sections[0].title == "first"
