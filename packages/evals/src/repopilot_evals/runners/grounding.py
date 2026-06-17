"""Grounding eval runner for the Phase 2 Q&A gate."""

from __future__ import annotations

from dataclasses import dataclass

from repopilot_agents.qa.graph import NOT_FOUND_SENTINEL, QAResult, answer_question
from repopilot_agents.types import CodeRef
from repopilot_core.settings import Settings
from repopilot_evals.datasets import (
    GroundingEvalRow,
    dataset_path,
    load_grounding_dataset,
    take_rows,
)
from repopilot_evals.runners.common import build_eval_context, resolve_repo_id


@dataclass(slots=True)
class GroundingEvalCaseResult:
    question: str
    grounded: bool
    keyword_match: bool
    ref_match: bool
    hallucination_pass: bool
    hops: int


@dataclass(slots=True)
class GroundingEvalMetrics:
    total: int
    grounded_correct: int
    keyword_correct: int
    ref_correct: int
    hallucination_correct: int
    multi_hop_questions: int
    multi_hop_correct: int
    cases: list[GroundingEvalCaseResult]

    @property
    def grounding_accuracy(self) -> float:
        return self.grounded_correct / self.total if self.total else 0.0

    @property
    def keyword_accuracy(self) -> float:
        return self.keyword_correct / self.total if self.total else 0.0

    @property
    def ref_recall(self) -> float:
        return self.ref_correct / self.total if self.total else 0.0

    @property
    def hallucination_rate(self) -> float:
        misses = self.total - self.hallucination_correct
        return misses / self.total if self.total else 0.0

    @property
    def multi_hop_accuracy(self) -> float:
        return (
            self.multi_hop_correct / self.multi_hop_questions if self.multi_hop_questions else 0.0
        )


def _contains_all_keywords(answer: str, keywords: list[str]) -> bool:
    if not keywords:
        return True
    lowered = answer.lower()
    return all(keyword.lower() in lowered for keyword in keywords)


def _has_expected_refs(result: QAResult, expected_refs: list[CodeRef]) -> bool:
    if not expected_refs:
        return True
    actual = {
        (ref.file_path, ref.start_line, ref.end_line)
        for claim in result.claims
        for ref in claim.refs
    }
    wanted = {(ref.file_path, ref.start_line, ref.end_line) for ref in expected_refs}
    return wanted.issubset(actual)


def _is_hallucination_safe(row: GroundingEvalRow, result: QAResult) -> bool:
    if not row.not_in_repo:
        return True
    answer = result.answer.strip()
    return answer == NOT_FOUND_SENTINEL or "not in the repo" in answer.lower()


async def run_grounding_eval(
    *,
    dataset_name: str = "httpx_qa_v1.jsonl",
    repo_slug: str = "httpx",
    repo_id: str | None = None,
    sample_limit: int | None = None,
    settings: Settings | None = None,
) -> GroundingEvalMetrics:
    rows = take_rows(load_grounding_dataset(dataset_path(dataset_name)), sample_limit)
    return await run_grounding_eval_rows(
        rows=rows,
        repo_slug=repo_slug,
        repo_id=repo_id,
        settings=settings,
    )


async def run_grounding_eval_rows(
    *,
    rows: list[GroundingEvalRow],
    repo_slug: str,
    repo_id: str | None = None,
    settings: Settings | None = None,
) -> GroundingEvalMetrics:
    ctx = build_eval_context(settings)
    try:
        resolved_repo_id = await resolve_repo_id(ctx.engine, repo_slug=repo_slug, repo_id=repo_id)
        cases: list[GroundingEvalCaseResult] = []
        for row in rows:
            result = await answer_question(
                row.question,
                engine=ctx.engine,
                provider=ctx.provider,
                repo_id=resolved_repo_id,
            )
            grounded = all(claim.status == "verified" for claim in result.claims)
            keyword_match = _contains_all_keywords(result.answer, row.expected_answer_keywords)
            ref_match = _has_expected_refs(result, row.expected_refs)
            hallucination_pass = _is_hallucination_safe(row, result)
            cases.append(
                GroundingEvalCaseResult(
                    question=row.question,
                    grounded=grounded,
                    keyword_match=keyword_match,
                    ref_match=ref_match,
                    hallucination_pass=hallucination_pass,
                    hops=result.hops,
                )
            )

        total = len(cases)
        multi_hop = [case for case in cases if case.hops > 0]
        return GroundingEvalMetrics(
            total=total,
            grounded_correct=sum(1 for case in cases if case.grounded and case.hallucination_pass),
            keyword_correct=sum(1 for case in cases if case.keyword_match),
            ref_correct=sum(1 for case in cases if case.ref_match),
            hallucination_correct=sum(1 for case in cases if case.hallucination_pass),
            multi_hop_questions=len(multi_hop),
            multi_hop_correct=sum(1 for case in multi_hop if case.grounded and case.ref_match),
            cases=cases,
        )
    finally:
        await ctx.aclose()


__all__ = [
    "GroundingEvalCaseResult",
    "GroundingEvalMetrics",
    "run_grounding_eval",
    "run_grounding_eval_rows",
]
