"""Pure-retrieval metrics: recall@k, NDCG@k, MRR over a labeled QA dataset.

Runs the current ``vector_search`` (no answerer, no verifier) and scores the
ranked hit list against each row's ``expected_refs``. A hit "matches" an
expected ref when the file paths agree and the line ranges overlap — chunk
boundaries drift across re-indexes, so exact (start, end) equality would
under-count.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from math import log2
from typing import Literal

from repopilot_agents.tools.bm25_search import bm25_search
from repopilot_agents.tools.hybrid_search import hybrid_search
from repopilot_agents.tools.vector_search import vector_search
from repopilot_agents.types import ChunkHit, CodeRef
from repopilot_core.settings import Settings
from repopilot_evals.datasets import (
    dataset_path,
    load_grounding_dataset,
    take_rows,
)
from repopilot_evals.runners.common import build_eval_context, resolve_repo_id

SearchMode = Literal["dense", "sparse", "hybrid"]

DEFAULT_KS = (5, 10, 20)


def ref_matches(hit: CodeRef, expected: CodeRef) -> bool:
    if hit.file_path != expected.file_path:
        return False
    return hit.start_line <= expected.end_line and hit.end_line >= expected.start_line


def relevance_vector(hits: list[CodeRef], expected: list[CodeRef]) -> list[int]:
    """1/0 per ranked hit; each expected ref credits at most one hit."""
    remaining = list(expected)
    rels: list[int] = []
    for hit in hits:
        matched = next((exp for exp in remaining if ref_matches(hit, exp)), None)
        if matched is not None:
            remaining.remove(matched)
            rels.append(1)
        else:
            rels.append(0)
    return rels


def recall_at_k(rels: list[int], n_expected: int, k: int) -> float:
    if n_expected == 0:
        return 1.0
    return sum(rels[:k]) / n_expected


def ndcg_at_k(rels: list[int], n_expected: int, k: int) -> float:
    if n_expected == 0:
        return 1.0
    dcg = sum(rel / log2(i + 2) for i, rel in enumerate(rels[:k]))
    ideal = sum(1 / log2(i + 2) for i in range(min(n_expected, k)))
    return dcg / ideal if ideal else 0.0


def mrr(rels: list[int]) -> float:
    for i, rel in enumerate(rels):
        if rel:
            return 1.0 / (i + 1)
    return 0.0


@dataclass(slots=True)
class RetrievalCaseResult:
    question: str
    n_expected: int
    recall: dict[int, float]
    ndcg: dict[int, float]
    mrr: float


@dataclass(slots=True)
class RetrievalEvalMetrics:
    total: int
    ks: tuple[int, ...]
    cases: list[RetrievalCaseResult] = field(default_factory=list)

    def mean_recall(self, k: int) -> float:
        return sum(c.recall[k] for c in self.cases) / self.total if self.total else 0.0

    def mean_ndcg(self, k: int) -> float:
        return sum(c.ndcg[k] for c in self.cases) / self.total if self.total else 0.0

    @property
    def mean_mrr(self) -> float:
        return sum(c.mrr for c in self.cases) / self.total if self.total else 0.0

    def as_dict(self) -> dict[str, float | int]:
        out: dict[str, float | int] = {"total": self.total, "mrr": self.mean_mrr}
        for k in self.ks:
            out[f"recall@{k}"] = self.mean_recall(k)
        for k in self.ks:
            if k <= 10:
                out[f"ndcg@{k}"] = self.mean_ndcg(k)
        return out


def score_case(
    question: str, hits: list[ChunkHit], expected: list[CodeRef], ks: tuple[int, ...]
) -> RetrievalCaseResult:
    rels = relevance_vector([h.ref for h in hits], expected)
    n = len(expected)
    return RetrievalCaseResult(
        question=question,
        n_expected=n,
        recall={k: recall_at_k(rels, n, k) for k in ks},
        ndcg={k: ndcg_at_k(rels, n, k) for k in ks},
        mrr=mrr(rels),
    )


async def run_retrieval_eval(
    *,
    dataset_name: str = "httpx_qa_v1.jsonl",
    repo_slug: str = "httpx",
    repo_id: str | None = None,
    ks: tuple[int, ...] = DEFAULT_KS,
    sample_limit: int | None = None,
    settings: Settings | None = None,
    recall_k: int | None = None,
    exclude_path_prefixes: Sequence[str] = (),
    search_mode: SearchMode = "dense",
) -> RetrievalEvalMetrics:
    rows = take_rows(load_grounding_dataset(dataset_path(dataset_name)), sample_limit)
    # Not-in-repo rows have no expected_refs; retrieval metrics skip them.
    rows = [row for row in rows if not row.not_in_repo and row.expected_refs]
    ctx = build_eval_context(settings)
    pool = recall_k if recall_k is not None else max(ks)
    try:
        resolved = await resolve_repo_id(ctx.engine, repo_slug=repo_slug, repo_id=repo_id)
        cases: list[RetrievalCaseResult] = []
        for row in rows:
            if search_mode == "sparse":
                hits = await bm25_search(
                    row.question,
                    engine=ctx.engine,
                    repo_id=resolved,
                    k=pool,
                    exclude_path_prefixes=exclude_path_prefixes,
                )
            elif search_mode == "hybrid":
                hits = await hybrid_search(
                    row.question,
                    engine=ctx.engine,
                    provider=ctx.provider,
                    repo_id=resolved,
                    recall_k=pool,
                    exclude_path_prefixes=exclude_path_prefixes,
                )
            else:
                hits = await vector_search(
                    row.question,
                    engine=ctx.engine,
                    provider=ctx.provider,
                    repo_id=resolved,
                    k=max(ks),
                    recall_k=recall_k,
                    exclude_path_prefixes=exclude_path_prefixes,
                )
            cases.append(score_case(row.question, hits, row.expected_refs, ks))
        return RetrievalEvalMetrics(total=len(cases), ks=ks, cases=cases)
    finally:
        await ctx.aclose()


__all__ = [
    "DEFAULT_KS",
    "RetrievalCaseResult",
    "RetrievalEvalMetrics",
    "mrr",
    "ndcg_at_k",
    "recall_at_k",
    "ref_matches",
    "relevance_vector",
    "run_retrieval_eval",
    "score_case",
]
