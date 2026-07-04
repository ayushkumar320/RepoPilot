"""Unit tests for the pure retrieval-metric math (no DB, no LLM)."""

from __future__ import annotations

import pytest

from repopilot_agents.types import ChunkHit, CodeRef
from repopilot_evals.runners.latency import percentile
from repopilot_evals.runners.retrieval import (
    mrr,
    ndcg_at_k,
    recall_at_k,
    ref_matches,
    relevance_vector,
    score_case,
)
from repopilot_evals.runners.significance import paired_bootstrap


def _ref(path: str, start: int, end: int) -> CodeRef:
    return CodeRef(file_path=path, start_line=start, end_line=end, symbol=None)


class TestRefMatches:
    def test_overlapping_ranges_match(self) -> None:
        assert ref_matches(_ref("a.py", 10, 50), _ref("a.py", 40, 60))

    def test_disjoint_ranges_do_not_match(self) -> None:
        assert not ref_matches(_ref("a.py", 10, 20), _ref("a.py", 30, 40))

    def test_different_files_do_not_match(self) -> None:
        assert not ref_matches(_ref("a.py", 10, 50), _ref("b.py", 10, 50))


class TestRelevanceVector:
    def test_each_expected_credits_one_hit(self) -> None:
        expected = [_ref("a.py", 1, 100)]
        hits = [_ref("a.py", 1, 50), _ref("a.py", 60, 100)]
        assert relevance_vector(hits, expected) == [1, 0]

    def test_ranked_order_preserved(self) -> None:
        expected = [_ref("a.py", 1, 10), _ref("b.py", 1, 10)]
        hits = [_ref("c.py", 1, 10), _ref("b.py", 5, 8), _ref("a.py", 2, 4)]
        assert relevance_vector(hits, expected) == [0, 1, 1]


class TestMetrics:
    def test_perfect_recall(self) -> None:
        assert recall_at_k([1, 1, 0], n_expected=2, k=5) == 1.0

    def test_partial_recall(self) -> None:
        assert recall_at_k([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], n_expected=2, k=10) == 0.5

    def test_no_expected_is_perfect(self) -> None:
        assert recall_at_k([], 0, 10) == 1.0
        assert ndcg_at_k([], 0, 5) == 1.0

    def test_ndcg_ideal_ranking_is_one(self) -> None:
        assert ndcg_at_k([1, 1, 0, 0, 0], n_expected=2, k=5) == pytest.approx(1.0)

    def test_ndcg_penalizes_low_positions(self) -> None:
        good = ndcg_at_k([1, 0, 0, 0, 0], 1, 5)
        bad = ndcg_at_k([0, 0, 0, 0, 1], 1, 5)
        assert good == pytest.approx(1.0)
        assert bad < good

    def test_mrr_first_hit_position(self) -> None:
        assert mrr([0, 0, 1]) == pytest.approx(1 / 3)
        assert mrr([0, 0, 0]) == 0.0


class TestScoreCase:
    def test_end_to_end(self) -> None:
        expected = [_ref("a.py", 1, 20)]
        hits = [
            ChunkHit(ref=_ref("b.py", 1, 5), distance=0.1, summary=None, kind="function"),
            ChunkHit(ref=_ref("a.py", 10, 30), distance=0.2, summary=None, kind="class"),
        ]
        case = score_case("q", hits, expected, ks=(5, 10, 20))
        assert case.recall[5] == 1.0
        assert case.mrr == pytest.approx(0.5)


class TestSignificance:
    def test_self_comparison_not_significant(self) -> None:
        scores = [0.4, 0.6, 0.5, 0.7, 0.3, 0.8, 0.5, 0.6]
        result = paired_bootstrap(scores, scores)
        assert not result.significant
        assert result.verdict == "not significant"

    def test_large_lift_is_significant(self) -> None:
        before = [0.2] * 30
        after = [0.8] * 30
        result = paired_bootstrap(before, after)
        assert result.significant
        assert result.verdict == "significant improvement"

    def test_mismatched_lengths_raise(self) -> None:
        with pytest.raises(ValueError):
            paired_bootstrap([0.1], [0.1, 0.2])

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            paired_bootstrap([], [])


class TestPercentile:
    def test_p50_p95(self) -> None:
        values = sorted(float(i) for i in range(1, 101))
        assert percentile(values, 50) == pytest.approx(50.0, abs=1.0)
        assert percentile(values, 95) == pytest.approx(95.0, abs=1.0)

    def test_empty(self) -> None:
        assert percentile([], 95) == 0.0
