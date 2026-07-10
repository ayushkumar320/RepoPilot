"""Latency runner: p50/p95 wall-clock timings around ``answer_question``."""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass

from repopilot_agents.qa.graph import (
    NON_SOURCE_PATH_PREFIXES,
    RECALL_K,
    answer_question,
)
from repopilot_core.settings import Settings
from repopilot_evals.datasets import (
    dataset_path,
    load_grounding_dataset,
    take_rows,
)
from repopilot_evals.runners.common import build_eval_context, resolve_repo_id


def percentile(sorted_values: list[float], pct: float) -> float:
    """Nearest-rank percentile over a pre-sorted list."""
    if not sorted_values:
        return 0.0
    rank = max(0, min(len(sorted_values) - 1, round(pct / 100 * (len(sorted_values) - 1))))
    return sorted_values[rank]


@dataclass(slots=True)
class LatencyEvalMetrics:
    total: int
    timings_ms: list[float]

    @property
    def p50_ms(self) -> float:
        return percentile(sorted(self.timings_ms), 50)

    @property
    def p95_ms(self) -> float:
        return percentile(sorted(self.timings_ms), 95)

    def as_dict(self) -> dict[str, float | int]:
        return {
            "total": self.total,
            "latency_p50_ms": self.p50_ms,
            "latency_p95_ms": self.p95_ms,
        }


async def run_latency_eval(
    *,
    dataset_name: str = "httpx_qa_v1.jsonl",
    repo_slug: str = "httpx",
    repo_id: str | None = None,
    sample_limit: int | None = None,
    settings: Settings | None = None,
    recall_k: int | None = RECALL_K,
    exclude_path_prefixes: Sequence[str] = NON_SOURCE_PATH_PREFIXES,
    use_compress: bool = True,
) -> LatencyEvalMetrics:
    rows = take_rows(load_grounding_dataset(dataset_path(dataset_name)), sample_limit)
    ctx = build_eval_context(settings)
    try:
        resolved = await resolve_repo_id(ctx.engine, repo_slug=repo_slug, repo_id=repo_id)
        timings: list[float] = []
        for row in rows:
            start = time.perf_counter()
            await answer_question(
                row.question,
                engine=ctx.engine,
                provider=ctx.provider,
                repo_id=resolved,
                recall_k=recall_k,
                exclude_path_prefixes=exclude_path_prefixes,
                use_compress=use_compress,
            )
            timings.append((time.perf_counter() - start) * 1000)
        return LatencyEvalMetrics(total=len(timings), timings_ms=timings)
    finally:
        await ctx.aclose()


__all__ = ["LatencyEvalMetrics", "percentile", "run_latency_eval"]
