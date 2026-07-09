"""RAG Phase 4: cross-encoder wrapper + rerank pipeline (stubbed encoder).

The real ONNX model stays out of the fast lane (80 MB download, slow import);
these tests stub ``TextCrossEncoder`` to verify caching, symbol-prefixing,
and pipeline composition. The real-model pairwise self-test is a slow-lane /
bench concern (docs/rag/04 §4).
"""

from __future__ import annotations

import pytest

from repopilot_agents.rerank.cross_encoder import CrossEncoderReranker, rerank_text
from repopilot_agents.rerank.pipeline import rerank_and_diversify
from repopilot_agents.types import ChunkContent, ChunkHit, CodeRef


class _StubEncoder:
    """Scores by keyword overlap with the query; counts calls."""

    def __init__(self) -> None:
        self.calls = 0

    def rerank(self, query: str, texts: list[str]) -> list[float]:
        self.calls += 1
        q = set(query.lower().split())
        return [sum(1.0 for w in t.lower().split() if w in q) for t in texts]


@pytest.fixture()
def reranker() -> tuple[CrossEncoderReranker, _StubEncoder]:
    r = CrossEncoderReranker("stub-model")
    stub = _StubEncoder()
    r._encoder = stub  # bypass lazy fastembed load
    return r, stub


def test_scores_relevant_text_higher(reranker: tuple[CrossEncoderReranker, _StubEncoder]) -> None:
    r, _ = reranker
    scores = r.score("gzip decoder", ["the gzip decoder class", "unrelated proxy config"])
    assert scores[0] > scores[1]


def test_score_cache_avoids_recompute(
    reranker: tuple[CrossEncoderReranker, _StubEncoder],
) -> None:
    r, stub = reranker
    r.score("q", ["a", "b"])
    r.score("q", ["a", "b"])
    assert stub.calls == 1
    r.score("q", ["a", "c"])  # only 'c' is fresh
    assert stub.calls == 2


def test_empty_texts_no_model_load() -> None:
    r = CrossEncoderReranker("stub-model")  # _encoder stays None
    assert r.score("q", []) == []


def _hit_and_content(path: str, symbol: str, content: str) -> tuple[ChunkHit, ChunkContent]:
    ref = CodeRef(file_path=path, start_line=1, end_line=10, symbol=symbol)
    return ChunkHit(ref=ref, distance=0.5), ChunkContent(ref=ref, content=content)


def test_rerank_text_prefixes_symbol() -> None:
    _, content = _hit_and_content("a.py", "pkg.mod.GZipDecoder", "def decode(): ...")
    assert rerank_text(content).startswith("pkg.mod.GZipDecoder\n")


def test_pipeline_reorders_by_relevance(
    monkeypatch: pytest.MonkeyPatch,
    reranker: tuple[CrossEncoderReranker, _StubEncoder],
) -> None:
    r, _ = reranker
    from repopilot_agents.rerank import pipeline as pl

    monkeypatch.setattr(pl, "shared_reranker", lambda model_name: r)
    pairs = [
        _hit_and_content("noise.py", "noise", "totally unrelated words here"),
        _hit_and_content("gzip.py", "GZipDecoder", "gzip decoder implementation"),
    ]
    ranked = pl.rerank_and_diversify(
        "gzip decoder", [h for h, _ in pairs], [c for _, c in pairs], k=2
    )
    assert ranked[0][0].ref.file_path == "gzip.py"


def test_pipeline_parallel_mismatch_raises() -> None:
    hit, content = _hit_and_content("a.py", "s", "x")
    with pytest.raises(ValueError, match="parallel"):
        rerank_and_diversify("q", [hit], [content, content], k=1)


def test_pipeline_empty_pool() -> None:
    assert rerank_and_diversify("q", [], [], k=8) == []
