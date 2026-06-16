"""Verifier-quality eval runner for the Phase 2 gate."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from repopilot_agents.verifier import grounding as grounding_mod
from repopilot_agents.verifier.grounding import Claim, verify_claim
from repopilot_core.settings import Settings
from repopilot_evals.datasets import (
    VerifierEvalRow,
    dataset_path,
    load_verifier_dataset,
    take_rows,
)
from repopilot_evals.runners.common import build_eval_context, resolve_repo_id


@dataclass(slots=True)
class VerifierEvalCaseResult:
    claim: str
    expected_verdict: str
    actual_verdict: str
    correct: bool


@dataclass(slots=True)
class VerifierEvalMetrics:
    total: int
    correct: int
    cases: list[VerifierEvalCaseResult]

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0


@contextmanager
def _patched_read_chunks(row: VerifierEvalRow):
    if not row.chunks:
        yield
        return

    original = grounding_mod.read_chunks

    async def _fake_read_chunks(refs: Any, *, engine: Any, repo_id: str) -> list[Any]:
        return row.chunks

    grounding_mod.read_chunks = _fake_read_chunks
    try:
        yield
    finally:
        grounding_mod.read_chunks = original


async def run_verifier_eval(
    *,
    dataset_name: str = "verifier_quality_v1.jsonl",
    repo_slug: str = "httpx",
    repo_id: str | None = None,
    sample_limit: int | None = None,
    settings: Settings | None = None,
) -> VerifierEvalMetrics:
    rows = take_rows(load_verifier_dataset(dataset_path(dataset_name)), sample_limit)
    return await run_verifier_eval_rows(
        rows=rows,
        repo_slug=repo_slug,
        repo_id=repo_id,
        settings=settings,
    )


async def run_verifier_eval_rows(
    *,
    rows: list[VerifierEvalRow],
    repo_slug: str,
    repo_id: str | None = None,
    settings: Settings | None = None,
) -> VerifierEvalMetrics:
    ctx = build_eval_context(settings)
    try:
        resolved_repo_id = await resolve_repo_id(ctx.engine, repo_slug=repo_slug, repo_id=repo_id)
        cases: list[VerifierEvalCaseResult] = []
        for row in rows:
            refs = row.refs or [chunk.ref for chunk in row.chunks]
            claim = Claim(text=row.claim, refs=refs)
            with _patched_read_chunks(row):
                result = await verify_claim(
                    claim,
                    provider=ctx.provider,
                    engine=ctx.engine,
                    repo_id=resolved_repo_id,
                )
            actual = result.verdict.decision
            cases.append(
                VerifierEvalCaseResult(
                    claim=row.claim,
                    expected_verdict=row.expected_verdict,
                    actual_verdict=actual,
                    correct=actual == row.expected_verdict,
                )
            )
        return VerifierEvalMetrics(
            total=len(cases),
            correct=sum(1 for case in cases if case.correct),
            cases=cases,
        )
    finally:
        await ctx.aclose()


__all__ = [
    "VerifierEvalCaseResult",
    "VerifierEvalMetrics",
    "run_verifier_eval",
    "run_verifier_eval_rows",
]
