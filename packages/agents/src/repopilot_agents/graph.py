"""LangGraph wiring — the full ``StateGraph[ArchaeologistState]``.

This is the orchestrator. Earlier phases shipped capability building
blocks; Phase 3 step 7 ties them together into one runnable graph:

    intent_profiler → capability_planner → (cartographer ‖ flow_tracer)
                                          → teacher → END

Edges are conditional on ``state.capability_plan.active``: a capability
that isn't activated is skipped. ``recursion_limit=15`` (the docs/03 §
"State rules" hard ceiling — anything more is a loop bug).

The Q&A subgraph from Phase 2 (``qa/graph.py``) is exposed as a separate
graph here. It is **not** wired into the main StateGraph — Q&A is a
universal, side-channel capability (docs/03 § "Q&A multi-turn") and
runs on its own state shape. The main graph never enters it.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Hashable
from typing import Any, cast

import structlog
from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncEngine

from repopilot_agents.capabilities import (
    run_cartographer,
    run_flow_tracer,
    run_teacher,
)
from repopilot_agents.intent.planner import plan as plan_intent
from repopilot_agents.intent.profiler import profile_intent
from repopilot_agents.state import ArchaeologistState, IntentProfile
from repopilot_core.llm.provider import LLMProvider

log = structlog.get_logger(__name__)


# Default ceiling — both docs/03 § "State rules" and the recursion_limit
# expression. Anything beyond is a loop bug; this constant exists so
# callers (UI, eval harness) can pin it in one place.
RECURSION_LIMIT: int = 15


# ─── Node implementations ───────────────────────────────────────────────


async def _intent_profiler_node(
    state: ArchaeologistState,
    *,
    provider: LLMProvider,
) -> dict[str, IntentProfile]:
    """If the state already carries a confirmed profile (the chip strip
    case), skip the LLM call. Otherwise profile from ``user_question``
    or the repo URL as last-resort raw text."""
    if state.intent_profile is not None:
        return {}
    raw = (state.user_question or state.repo_url).strip()
    profile = await profile_intent(raw, provider=provider)
    log.info("intent_profiler.done", raw=raw[:60])
    return {"intent_profile": profile}


def _capability_planner_node(state: ArchaeologistState) -> dict[str, Any]:
    """Deterministic — no LLM. Plans only when not already planned."""
    if state.capability_plan is not None or state.intent_profile is None:
        return {}
    plan = plan_intent(state.intent_profile)
    log.info("capability_planner.done", active=plan.active)
    return {"capability_plan": plan}


async def _cartographer_node(
    state: ArchaeologistState,
    *,
    provider: LLMProvider,
    engine: AsyncEngine,
) -> dict[str, Any]:
    if state.intent_profile is None or state.capability_plan is None:
        raise RuntimeError(
            "cartographer requires intent_profile + capability_plan — "
            "generic intent layer guard violated"
        )
    return await run_cartographer(
        profile=state.intent_profile,
        plan=state.capability_plan,
        provider=provider,
        engine=engine,
        repo_id=state.repo_id,
    )


async def _flow_tracer_node(
    state: ArchaeologistState,
    *,
    provider: LLMProvider,
    engine: AsyncEngine,
) -> dict[str, Any]:
    if state.intent_profile is None or state.capability_plan is None:
        raise RuntimeError(
            "flow_tracer requires intent_profile + capability_plan — "
            "generic intent layer guard violated"
        )
    # Use cartographer's hubs as fallback flow targets when the planner
    # didn't set any.
    fallback = [ref.symbol for ins in state.system_map for ref in ins.refs if ref.symbol]
    return await run_flow_tracer(
        profile=state.intent_profile,
        plan=state.capability_plan,
        provider=provider,
        engine=engine,
        repo_id=state.repo_id,
        fallback_targets=fallback,
    )


async def _teacher_node(
    state: ArchaeologistState,
    *,
    provider: LLMProvider,
) -> dict[str, Any]:
    if state.intent_profile is None or state.capability_plan is None:
        raise RuntimeError("teacher requires intent_profile + capability_plan")
    # Concatenate every upstream insight bucket the planner produced.
    upstream = list(state.system_map) + list(state.traced_flows) + list(state.decision_dossier)
    return await run_teacher(
        profile=state.intent_profile,
        plan=state.capability_plan,
        provider=provider,
        insights=upstream,
    )


# ─── Conditional routing ────────────────────────────────────────────────


def _route_after_planner(state: ArchaeologistState) -> list[str]:  # type: ignore[unused-ignore]
    """Fan out to every active generation capability the v1 graph knows
    about. Capabilities not yet implemented are skipped here, but their
    rows still appear in ``plan.active`` (the schema is honest about
    what was planned even when the wiring is partial)."""
    if state.capability_plan is None:
        return ["teacher"]
    active = set(state.capability_plan.active)
    targets: list[str] = []
    if "cartographer" in active:
        targets.append("cartographer")
    if "flow_tracer" in active:
        targets.append("flow_tracer")
    if not targets:
        # No generation capability planned (rare — the inclusive default
        # always activates cartographer). Fall straight through to the
        # teacher so we always return something.
        targets.append("teacher")
    return targets


def _route_after_generation(state: ArchaeologistState) -> str:
    """Generation nodes converge on the teacher (or END if the plan
    doesn't include it — which the schema technically allows even if
    the planner never produces such a plan)."""
    if state.capability_plan is None:
        return END
    return "teacher" if "teacher" in state.capability_plan.active else END


# ─── Public builders ────────────────────────────────────────────────────


def build_graph(
    *,
    provider: LLMProvider,
    engine: AsyncEngine,
    checkpointer: Any | None = None,
) -> Any:
    """Build + compile the full ``ArchaeologistState`` LangGraph.

    Pass a Postgres checkpointer in production for kill-resume; tests
    and the dev loop can pass ``None`` (MemorySaver semantics).
    """
    graph = StateGraph(ArchaeologistState)

    async def profiler(state: ArchaeologistState) -> dict[str, Any]:
        return await _intent_profiler_node(state, provider=provider)

    def planner(state: ArchaeologistState) -> dict[str, Any]:
        return _capability_planner_node(state)

    async def cartographer(state: ArchaeologistState) -> dict[str, Any]:
        return await _cartographer_node(state, provider=provider, engine=engine)

    async def flow_tracer(state: ArchaeologistState) -> dict[str, Any]:
        return await _flow_tracer_node(state, provider=provider, engine=engine)

    async def teacher(state: ArchaeologistState) -> dict[str, Any]:
        return await _teacher_node(state, provider=provider)

    graph.add_node("intent_profiler", profiler)
    graph.add_node("capability_planner", planner)
    graph.add_node("cartographer", cartographer)
    graph.add_node("flow_tracer", flow_tracer)
    graph.add_node("teacher", teacher)

    graph.add_edge(START, "intent_profiler")
    graph.add_edge("intent_profiler", "capability_planner")
    graph.add_conditional_edges(
        "capability_planner",
        cast(
            Callable[[ArchaeologistState], Hashable | list[Hashable]],
            _route_after_planner,
        ),
        # Mapped names = node names; LangGraph fans out to all returned
        # values, then waits for them all before the next step.
        ["cartographer", "flow_tracer", "teacher"],
    )
    graph.add_conditional_edges(
        "cartographer",
        _route_after_generation,
        ["teacher", END],
    )
    graph.add_conditional_edges(
        "flow_tracer",
        _route_after_generation,
        ["teacher", END],
    )
    graph.add_edge("teacher", END)

    if checkpointer is not None:
        return graph.compile(checkpointer=checkpointer)
    return graph.compile()


# ─── Convenience: expose Q&A from Phase 2 alongside ─────────────────────

# Re-export the Phase 2 Q&A entry point so callers have one import surface.
from repopilot_agents.qa import answer_question as answer_question  # noqa: E402

QAEntry = Callable[..., Awaitable[Any]]


__all__ = [
    "RECURSION_LIMIT",
    "answer_question",
    "build_graph",
]
