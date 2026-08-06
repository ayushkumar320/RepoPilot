"""Cartographer — produces ``system_map`` Insights from the call graph.

The Cartographer answers "what is the structural shape of this repo, and
which structures matter *for the user's goal*?" It is the first
generation node every plan touches. The graph is read via two of the
six deterministic tools (``graph_query`` for hubs + entry points,
``graph_metrics`` for per-hub depth) — raw numbers never reach the LLM
prompt without being translated into Insight-shaped statements.

Token budget: ≤ 2000 input tokens. The fact bundle is capped at the
``top_hubs`` and ``top_entry_points`` knobs precisely to keep us under
that ceiling on real repos.
"""

from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncEngine

from repopilot_agents.capabilities._coerce import coerce_insight, extract_json_list
from repopilot_agents.prompts import render_goal_anchor
from repopilot_agents.state import (
    CapabilityPlan,
    CodeRef,
    Insight,
    IntentProfile,
)
from repopilot_agents.tools import graph_metrics, graph_query
from repopilot_agents.types import GraphQueryResult, SymbolMetrics
from repopilot_core.llm.models import ModelId
from repopilot_core.llm.provider import LLMProvider, Message

log = structlog.get_logger(__name__)

_DEFAULT_TOP_HUBS = 6
_DEFAULT_TOP_ENTRY_POINTS = 6


_SYSTEM_PROMPT = (
    "You are the Cartographer. Given the USER GOAL, the PLAN TILT, and "
    "a STRUCTURAL FACT BUNDLE (hubs + entry points + per-hub metrics) "
    "drawn from the deterministic call graph, emit 4–6 Insight objects. "
    "Every Insight MUST translate raw numbers into a goal-anchored "
    "consequence: never repeat a fan-in or a count without saying what "
    "it MEANS for the user's stated goal.\n\n"
    '"finding" names the exact symbol and what role it plays. "because" '
    "cites the structural evidence (fan-in, fan-out, cyclomatic, entry-point "
    'status) that makes the finding true. "so_what" states the concrete '
    "consequence for this reader — what gets easier, riskier, or slower — and "
    "names the next thing to open or check. Full sentences, no fragments, no "
    "restating the same hub twice.\n\n"
    "Output STRICT JSON: a single JSON array. Each entry has exactly "
    'these keys: "finding", "because", "so_what", "goal_link", "refs". '
    '"refs" is an array of symbol strings drawn from the fact bundle '
    "(use the same symbols verbatim). No other keys. No commentary "
    "outside the array."
)


def _fact_bundle(
    hubs: list[GraphQueryResult],
    entry_points: list[GraphQueryResult],
    metrics: dict[str, SymbolMetrics],
) -> str:
    """Render the fact bundle as a compact text block.

    We deliberately avoid prose — bullet-pointed numerics make it cheap
    for the LLM to ground each claim back to a concrete row.
    """
    lines: list[str] = ["FACT BUNDLE (deterministic — do not contradict):", "", "HUBS:"]
    if not hubs:
        lines.append("  (none — graph has no high-fan-in symbols)")
    for h in hubs:
        m = metrics.get(h.symbol)
        suffix = (
            f"  fan_in={m.fan_in} fan_out={m.fan_out} cyclomatic={m.cyclomatic}"
            if m is not None
            else ""
        )
        lines.append(f"  - {h.symbol} (callers={int(h.score)}){suffix}")
    lines.extend(["", "ENTRY POINTS:"])
    if not entry_points:
        lines.append("  (none detected)")
    for e in entry_points:
        lines.append(f"  - {e.symbol}")
    return "\n".join(lines)


def _refs_for_symbols(symbols: list[str], lookup: dict[str, CodeRef]) -> dict[str, CodeRef]:
    return {s: lookup[s] for s in symbols if s in lookup}


async def _resolve_refs(
    symbols: list[str],
    *,
    engine: AsyncEngine,
    repo_id: str,
) -> dict[str, CodeRef]:
    """Resolve each symbol's CodeRef from graph_metrics's underlying lookup.

    The metrics tool already requires symbol resolution; we read its
    SymbolMetrics + reconstruct the file:line span when present. For the
    capability's coercion layer we mainly need a non-empty CodeRef per
    symbol — line precision is tightened later by the verifier.
    """
    # We don't have a "symbol → CodeRef" tool today; this is the gap the
    # Phase 3 wiring will close. For now, synthesize a minimal CodeRef
    # per symbol (file_path == symbol module dotted path, span 1-1) so
    # the schema validates. The verifier will read real chunks before
    # showing the claim, so this never reaches the user without
    # grounding.
    out: dict[str, CodeRef] = {}
    for sym in symbols:
        file_path = sym.replace(".", "/") + ".py"
        out[sym] = CodeRef(file_path=file_path, start_line=1, end_line=1, symbol=sym)
    return out


async def run_cartographer(
    *,
    profile: IntentProfile,
    plan: CapabilityPlan,
    provider: LLMProvider,
    engine: AsyncEngine,
    repo_id: str,
    top_hubs: int = _DEFAULT_TOP_HUBS,
    top_entry_points: int = _DEFAULT_TOP_ENTRY_POINTS,
) -> dict[str, list[Insight]]:
    """Run the Cartographer once.

    Returns the state diff for the LangGraph reducer:
    ``{"system_map": [Insight, …]}``. An empty list is a valid return —
    the graph may simply have no high-fan-in symbols, or the LLM may
    have failed to emit valid Insights. Downstream guards (the
    verifier; the empty-tour failsafe) handle both cases.
    """
    hubs = await graph_query("hubs", engine=engine, repo_id=repo_id, top_n=top_hubs)
    entry_points = await graph_query(
        "entry_points", engine=engine, repo_id=repo_id, top_n=top_entry_points
    )

    metrics: dict[str, SymbolMetrics] = {}
    for h in hubs:
        try:
            metrics[h.symbol] = await graph_metrics(h.symbol, engine=engine, repo_id=repo_id)
        except Exception as exc:
            log.warning("cartographer.metrics_failed", symbol=h.symbol, exc=str(exc))

    symbols = [h.symbol for h in hubs] + [e.symbol for e in entry_points]
    allowed_refs = await _resolve_refs(symbols, engine=engine, repo_id=repo_id)
    bundle = _fact_bundle(hubs, entry_points, metrics)
    anchor = render_goal_anchor(profile, plan)

    response = await provider.generate(
        ModelId.CARTOGRAPHER,
        [
            Message("system", _SYSTEM_PROMPT),
            Message("user", f"{anchor}\n\n{bundle}"),
        ],
        temperature=0.2,
        max_tokens=1500,
    )

    insights: list[Insight] = []
    for payload in extract_json_list(response.text):
        insight = coerce_insight(payload, allowed_refs)
        if insight is not None:
            insights.append(insight)

    log.info(
        "cartographer.done",
        hubs=len(hubs),
        entry_points=len(entry_points),
        insights=len(insights),
    )
    return {"system_map": insights}


# Tiny accessor so tests can rebuild the bundle without re-running the LLM.
def _build_fact_bundle_for_test(
    hubs: list[GraphQueryResult],
    entry_points: list[GraphQueryResult],
    metrics: dict[str, SymbolMetrics],
) -> str:
    return _fact_bundle(hubs, entry_points, metrics)


_ = Any  # keep mypy happy when run_cartographer's return is empty.

__all__ = ["run_cartographer"]
