"""Flow Tracer — produces ``traced_flows`` Insights from call-graph paths.

Reads ``capability_plan.flow_tracer_targets`` (or the Cartographer's
``system_map`` if no targets were planted by the planner) and runs
``graph_traverse`` on each. Each traced path becomes one or more
``Insight`` objects after the LLM translates the structural path into a
goal-anchored consequence.
"""

from __future__ import annotations

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
from repopilot_agents.tools import graph_traverse
from repopilot_agents.types import Path
from repopilot_core.llm.models import ModelId
from repopilot_core.llm.provider import LLMProvider, Message

log = structlog.get_logger(__name__)

_DEFAULT_MAX_DEPTH = 3
_DEFAULT_PATHS_PER_TARGET = 3


_SYSTEM_PROMPT = (
    "You are the Flow Tracer. Given the USER GOAL, the PLAN TILT, and a "
    "TRACED PATHS bundle (each path is an ordered chain of symbols from "
    "the deterministic call graph), emit 2–3 Insight objects per traced "
    "path. Every Insight MUST tie the structural shape of the path to "
    "the user's stated goal.\n\n"
    'Walk the path in order: "finding" says what the chain does end to end, '
    'naming each hop\'s symbol. "because" points at the specific hop that '
    "explains it — where the branch, the retry, the transform, or the I/O "
    'sits. "so_what" says where this reader would join the path to make their '
    "change, and what breaks downstream if they get it wrong. Full sentences.\n\n"
    "Output STRICT JSON: a single JSON array. Each entry has exactly "
    'these keys: "finding", "because", "so_what", "goal_link", "refs". '
    '"refs" is an array of symbol strings drawn from the bundle. No other '
    "keys. No commentary outside the array."
)


def _format_paths(paths: list[tuple[str, list[Path]]]) -> str:
    lines: list[str] = ["TRACED PATHS (deterministic):", ""]
    for target, target_paths in paths:
        lines.append(f"FROM {target}:")
        if not target_paths:
            lines.append("  (no outgoing call edges)")
            continue
        for path in target_paths:
            chain = " → ".join(step.symbol or step.file_path for step in path.steps)
            lines.append(f"  - depth={path.depth}: {chain}")
        lines.append("")
    return "\n".join(lines)


def _seed_targets(plan: CapabilityPlan, fallback_symbols: list[str], limit: int = 5) -> list[str]:
    """Choose which symbols to trace. Prefer the planner's explicit
    targets; otherwise fall back to whatever the Cartographer surfaced."""
    if plan.flow_tracer_targets:
        return list(plan.flow_tracer_targets)[:limit]
    return fallback_symbols[:limit]


async def run_flow_tracer(
    *,
    profile: IntentProfile,
    plan: CapabilityPlan,
    provider: LLMProvider,
    engine: AsyncEngine,
    repo_id: str,
    fallback_targets: list[str] | None = None,
    max_depth: int = _DEFAULT_MAX_DEPTH,
    paths_per_target: int = _DEFAULT_PATHS_PER_TARGET,
) -> dict[str, list[Insight]]:
    """Run the Flow Tracer once.

    Returns ``{"traced_flows": [Insight, …]}``. Empty list is valid when
    no target produced any outgoing edges (or when the LLM emitted no
    valid Insights — verifier loop handles).
    """
    targets = _seed_targets(plan, fallback_targets or [])
    if not targets:
        log.info("flow_tracer.no_targets")
        return {"traced_flows": []}

    paths_bundle: list[tuple[str, list[Path]]] = []
    allowed_refs: dict[str, CodeRef] = {}
    for target in targets:
        try:
            paths = await graph_traverse(
                target,
                edge_types=["calls"],
                engine=engine,
                repo_id=repo_id,
                max_depth=max_depth,
            )
        except Exception as exc:
            log.warning("flow_tracer.traverse_failed", target=target, exc=str(exc))
            paths = []

        # Cap to paths_per_target so the prompt budget stays sane.
        capped = paths[:paths_per_target]
        paths_bundle.append((target, capped))
        for path in capped:
            for step in path.steps:
                if step.symbol and step.symbol not in allowed_refs:
                    allowed_refs[step.symbol] = step

    bundle_text = _format_paths(paths_bundle)
    anchor = render_goal_anchor(profile, plan)

    response = await provider.generate(
        ModelId.FLOW_TRACER,
        [
            Message("system", _SYSTEM_PROMPT),
            Message("user", f"{anchor}\n\n{bundle_text}"),
        ],
        temperature=0.2,
        max_tokens=1400,
    )

    insights: list[Insight] = []
    for payload in extract_json_list(response.text):
        insight = coerce_insight(payload, allowed_refs)
        if insight is not None:
            insights.append(insight)

    log.info("flow_tracer.done", targets=len(targets), insights=len(insights))
    return {"traced_flows": insights}


__all__ = ["run_flow_tracer"]
