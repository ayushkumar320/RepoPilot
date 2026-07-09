"""RAG Phase 4: MMR diversity selection (pure function)."""

from __future__ import annotations

import pytest

from repopilot_agents.rerank.mmr import jaccard, mmr_select


def test_empty_and_zero_k() -> None:
    assert mmr_select([], [], k=5) == []
    assert mmr_select(["a"], [1.0], k=0) == []


def test_length_mismatch_raises() -> None:
    with pytest.raises(ValueError, match="same length"):
        mmr_select(["a", "b"], [1.0], k=2)


def test_pure_relevance_at_lambda_one() -> None:
    texts = ["def alpha(): pass", "def beta(): pass", "def gamma(): pass"]
    order = mmr_select(texts, [0.2, 0.9, 0.5], k=3, lambda_=1.0)
    assert order == [1, 2, 0]  # strictly by relevance


def test_near_duplicate_is_demoted() -> None:
    # Items 0 and 1 are near-identical methods of one class; item 2 is a
    # different file's content with mid relevance. With diversity on, the
    # duplicate (1) must NOT be picked second despite higher raw relevance.
    dup_a = "class GZipDecoder:\n    def decode(self, data): return inflate(data)"
    dup_b = "class GZipDecoder:\n    def flush(self, data): return inflate(data)"
    other = "def build_request(url, headers): return Request(url, headers)"
    decoy = "zzz qqq unrelated floor item"  # anchors min-max so `other` isn't zeroed
    order = mmr_select([dup_a, dup_b, other, decoy], [1.0, 0.95, 0.9, 0.1], k=2, lambda_=0.5)
    assert order == [0, 2]


def test_high_lambda_keeps_relevant_duplicates() -> None:
    # Code retrieval sometimes WANTS two methods of the same class — a
    # relevance-heavy lambda must allow that.
    dup_a = "class Pool:\n    def acquire(self): ..."
    dup_b = "class Pool:\n    def release(self): ..."
    other = "unrelated numeric helper zeta"
    order = mmr_select([dup_a, dup_b, other], [1.0, 0.98, 0.05], k=2, lambda_=0.9)
    assert order == [0, 1]


def test_constant_relevance_normalises_safely() -> None:
    order = mmr_select(["aaa bbb", "aaa bbb", "ccc ddd"], [0.5, 0.5, 0.5], k=3, lambda_=0.5)
    assert len(order) == 3  # no div-by-zero; all selected


def test_jaccard_bounds() -> None:
    a = frozenset({"x", "y"})
    assert jaccard(a, a) == 1.0
    assert jaccard(a, frozenset()) == 0.0
    assert jaccard(a, frozenset({"y", "z"})) == pytest.approx(1 / 3)
