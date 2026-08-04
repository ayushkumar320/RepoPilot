"""Latency runner: p50/p95 wall-clock timings around ``answer_question``."""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass
from dataclasses import field as dataclass_field

from repopilot_agents.qa.graph import (
    NON_SOURCE_PATH_PREFIXES,
    RECALL_K,
    STAGES,
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
    # One dict per question, keyed by the stage names in ``STAGES``. A stage
    # the run never reached (no rerank, no hops) is simply absent for that
    # question and contributes 0.0 to its percentile.
    stage_timings_ms: list[dict[str, float]] = dataclass_field(default_factory=list)

    @property
    def p50_ms(self) -> float:
        return percentile(sorted(self.timings_ms), 50)

    @property
    def p95_ms(self) -> float:
        return percentile(sorted(self.timings_ms), 95)

    def stage_p50_ms(self, stage: str) -> float:
        return percentile(sorted(d.get(stage, 0.0) for d in self.stage_timings_ms), 50)

    def stage_p95_ms(self, stage: str) -> float:
        return percentile(sorted(d.get(stage, 0.0) for d in self.stage_timings_ms), 95)

    def stage_mean_share(self, stage: str) -> float:
        """Mean fraction of a question's total wall-clock spent in ``stage``.

        Computed per question then averaged, so one slow outlier can't
        dominate the way a ratio-of-sums would. This is the number that
        answers "which stage should I attack first?".
        """
        shares = [
            d.get(stage, 0.0) / total
            for d, total in zip(self.stage_timings_ms, self.timings_ms, strict=False)
            if total > 0
        ]
        return sum(shares) / len(shares) if shares else 0.0

    def as_dict(self) -> dict[str, float | int]:
        out: dict[str, float | int] = {
            "total": self.total,
            "latency_p50_ms": self.p50_ms,
            "latency_p95_ms": self.p95_ms,
        }
        if not self.stage_timings_ms:
            return out
        for stage in STAGES:
            out[f"stage_{stage}_p50_ms"] = self.stage_p50_ms(stage)
            out[f"stage_{stage}_p95_ms"] = self.stage_p95_ms(stage)
            out[f"stage_{stage}_share"] = self.stage_mean_share(stage)
        # Time inside answer_question not attributed to any stage (parsing,
        # token estimation, glue). A large value means the breakdown is
        # lying by omission and needs another timer.
        accounted = [sum(d.values()) for d in self.stage_timings_ms]
        unaccounted = [
            t - a for t, a in zip(self.timings_ms, accounted, strict=False) if t > 0
        ]
        out["stage_unaccounted_p95_ms"] = percentile(sorted(unaccounted), 95)
        return out


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
    use_query_understanding: bool = True,
) -> LatencyEvalMetrics:
    rows = take_rows(load_grounding_dataset(dataset_path(dataset_name)), sample_limit)
    ctx = build_eval_context(settings)
    try:
        resolved = await resolve_repo_id(ctx.engine, repo_slug=repo_slug, repo_id=repo_id)
        timings: list[float] = []
        stage_timings: list[dict[str, float]] = []
        for row in rows:
            start = time.perf_counter()
            result = await answer_question(
                row.question,
                engine=ctx.engine,
                provider=ctx.provider,
                repo_id=resolved,
                recall_k=recall_k,
                exclude_path_prefixes=exclude_path_prefixes,
                use_compress=use_compress,
                use_query_understanding=use_query_understanding,
            )
            timings.append((time.perf_counter() - start) * 1000)
            stage_timings.append(dict(result.stage_timings_ms))
        return LatencyEvalMetrics(
            total=len(timings),
            timings_ms=timings,
            stage_timings_ms=stage_timings,
        )
    finally:
        await ctx.aclose()


__all__ = ["LatencyEvalMetrics", "percentile", "run_latency_eval"]
