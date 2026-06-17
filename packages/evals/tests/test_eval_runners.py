"""Phase-gating eval runner tests."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path

import pytest

from repopilot_agents.qa.graph import QAResult
from repopilot_agents.types import ChunkContent, CodeRef
from repopilot_agents.verifier.grounding import Claim, VerifierVerdict
from repopilot_evals.datasets import DATASETS_DIR, GroundingEvalRow, VerifierEvalRow
from repopilot_evals.runners import grounding as grounding_runner
from repopilot_evals.runners import verifier as verifier_runner


def _dataset_path(name: str) -> Path:
    return DATASETS_DIR / name


def _skip_if_missing(name: str) -> None:
    path = _dataset_path(name)
    if not path.exists():
        pytest.skip(
            f"eval dataset {name!r} not yet available at {path}; "
            "the eval harness is wired and will activate when the file lands."
        )


@dataclass(slots=True)
class _FakeVerifyResult:
    claim: Claim
    verdict: VerifierVerdict


@pytest.mark.eval_sampled
def test_sampled_eval_workflow_is_collectible() -> None:
    assert True


@pytest.mark.eval_sampled
@pytest.mark.asyncio
async def test_httpx_qa_grounding_accuracy_sampled(monkeypatch: pytest.MonkeyPatch) -> None:
    _skip_if_missing("httpx_qa_v1.jsonl")

    async def _fake_answer_question(
        question: str,
        *,
        engine: object,
        provider: object,
        repo_id: str,
        k: int = 8,
        max_hops: int = 3,
    ) -> QAResult:
        ref = CodeRef(
            file_path="httpx/_client.py", start_line=10, end_line=20, symbol="httpx.Client"
        )
        if "not in repo" in question.lower():
            return QAResult(
                question=question, answer="I couldn't find that in the repo.", claims=[]
            )
        return QAResult(
            question=question,
            answer="Client sends requests through transports.",
            claims=[Claim(text="supported", refs=[ref], status="verified")],
            objections=[],
            hops=1,
            retrieval_path=["vector_search", "graph_traverse"],
        )

    monkeypatch.setattr(grounding_runner, "answer_question", _fake_answer_question)
    monkeypatch.setattr(
        grounding_runner, "build_eval_context", lambda settings=None: _DummyContext()
    )
    monkeypatch.setattr(grounding_runner, "resolve_repo_id", _async_return("encode/httpx@sha"))

    metrics = await grounding_runner.run_grounding_eval(
        dataset_name="httpx_qa_v1.jsonl",
        sample_limit=5,
    )
    assert metrics.total == 5
    assert metrics.grounding_accuracy >= 0.9


@pytest.mark.eval_sampled
@pytest.mark.asyncio
async def test_verifier_quality_sampled(monkeypatch: pytest.MonkeyPatch) -> None:
    _skip_if_missing("verifier_quality_v1.jsonl")

    async def _fake_verify_claim(
        claim: Claim, *, provider: object, engine: object, repo_id: str
    ) -> _FakeVerifyResult:
        decision = "rejected" if "reject" in claim.text.lower() else "supported"
        return _FakeVerifyResult(
            claim=claim,
            verdict=VerifierVerdict(decision=decision, reason="stub"),
        )

    monkeypatch.setattr(verifier_runner, "verify_claim", _fake_verify_claim)
    monkeypatch.setattr(
        verifier_runner, "build_eval_context", lambda settings=None: _DummyContext()
    )
    monkeypatch.setattr(verifier_runner, "resolve_repo_id", _async_return("encode/httpx@sha"))

    metrics = await verifier_runner.run_verifier_eval(
        dataset_name="verifier_quality_v1.jsonl",
        sample_limit=5,
    )
    assert metrics.total == 5
    assert metrics.accuracy >= 0.92


@pytest.mark.eval_full
def test_full_eval_workflow_is_collectible() -> None:
    assert True


@pytest.mark.eval_full
@pytest.mark.parametrize("eval_repo", ["fastapi", "httpx", "flask"])
def test_full_grounding_per_repo(eval_repo: str) -> None:
    dataset = f"{eval_repo}_qa_v1.jsonl"
    _skip_if_missing(dataset)
    pytest.skip(
        f"full per-repo eval dataset {dataset} present but full-matrix gate belongs to Phase 6"
    )


@pytest.mark.asyncio
async def test_run_grounding_eval_rows_computes_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        GroundingEvalRow(
            question="How does Client send?",
            expected_answer_keywords=["transports"],
            expected_refs=[CodeRef(file_path="httpx/_client.py", start_line=10, end_line=20)],
        ),
        GroundingEvalRow(question="This is not in repo", not_in_repo=True),
    ]

    async def _fake_answer_question(
        question: str,
        *,
        engine: object,
        provider: object,
        repo_id: str,
        k: int = 8,
        max_hops: int = 3,
    ) -> QAResult:
        if "not in repo" in question.lower():
            return QAResult(
                question=question, answer="I couldn't find that in the repo.", claims=[]
            )
        ref = CodeRef(
            file_path="httpx/_client.py", start_line=10, end_line=20, symbol="httpx.Client"
        )
        return QAResult(
            question=question,
            answer="Client sends requests through transports.",
            claims=[Claim(text="supported", refs=[ref], status="verified")],
            objections=[],
            hops=1,
            retrieval_path=[],
        )

    monkeypatch.setattr(grounding_runner, "answer_question", _fake_answer_question)
    monkeypatch.setattr(
        grounding_runner, "build_eval_context", lambda settings=None: _DummyContext()
    )
    monkeypatch.setattr(grounding_runner, "resolve_repo_id", _async_return("encode/httpx@sha"))

    metrics = await grounding_runner.run_grounding_eval_rows(rows=rows, repo_slug="httpx")
    assert metrics.total == 2
    assert metrics.grounding_accuracy == 1.0
    assert metrics.keyword_accuracy == 1.0
    assert metrics.ref_recall == 1.0
    assert metrics.hallucination_rate == 0.0
    assert metrics.multi_hop_accuracy == 1.0


@pytest.mark.asyncio
async def test_run_verifier_eval_rows_supports_embedded_chunks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ref = CodeRef(file_path="httpx/_client.py", start_line=10, end_line=20, symbol="httpx.Client")
    rows = [
        VerifierEvalRow(
            claim="This should pass",
            expected_verdict="supported",
            chunks=[ChunkContent(ref=ref, content="class Client: ...")],
        ),
        VerifierEvalRow(
            claim="Reject this claim",
            expected_verdict="rejected",
            chunks=[ChunkContent(ref=ref, content="class Client: ...")],
        ),
    ]

    async def _fake_verify_claim(
        claim: Claim, *, provider: object, engine: object, repo_id: str
    ) -> _FakeVerifyResult:
        decision = "rejected" if "reject" in claim.text.lower() else "supported"
        return _FakeVerifyResult(
            claim=claim, verdict=VerifierVerdict(decision=decision, reason="stub")
        )

    monkeypatch.setattr(verifier_runner, "verify_claim", _fake_verify_claim)
    monkeypatch.setattr(
        verifier_runner, "build_eval_context", lambda settings=None: _DummyContext()
    )
    monkeypatch.setattr(verifier_runner, "resolve_repo_id", _async_return("encode/httpx@sha"))

    metrics = await verifier_runner.run_verifier_eval_rows(rows=rows, repo_slug="httpx")
    assert metrics.total == 2
    assert metrics.accuracy == 1.0


class _DummyProvider:
    async def aclose(self) -> None:
        return None


class _DummyEngine:
    async def dispose(self) -> None:
        return None


class _DummyContext:
    def __init__(self) -> None:
        self.engine = _DummyEngine()
        self.provider = _DummyProvider()

    async def aclose(self) -> None:
        return None


def _async_return(value: str) -> Callable[..., Awaitable[str]]:
    async def _inner(*args: object, **kwargs: object) -> str:
        return value

    return _inner
