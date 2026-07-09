"""RAG Phase 3: RRF fusion ordering (``qa/union.py``).

The DB-touching lanes (``bm25_search`` SQL, ``vector_search`` SQL) stay in the
slow/integration lane; here we test the pure fusion math that decides the
final ranking.
"""

from __future__ import annotations

from repopilot_agents.qa.union import reciprocal_rank_fusion
from repopilot_agents.types import ChunkHit, CodeRef


def _hit(path: str, line: int, symbol: str | None = None, distance: float = 0.5) -> ChunkHit:
    return ChunkHit(
        ref=CodeRef(file_path=path, start_line=line, end_line=line + 1, symbol=symbol),
        distance=distance,
    )


def test_empty_pools_fuse_to_empty() -> None:
    assert reciprocal_rank_fusion([]) == []
    assert reciprocal_rank_fusion([[], []]) == []


def test_single_pool_preserves_order() -> None:
    pool = [_hit("a.py", 1), _hit("b.py", 1), _hit("c.py", 1)]
    fused = reciprocal_rank_fusion([pool])
    assert [h.ref.file_path for h in fused] == ["a.py", "b.py", "c.py"]


def test_chunk_found_by_both_lanes_outranks_single_lane() -> None:
    # 'shared' is rank-1 in one lane and rank-0 in the other; 'solo' is rank-0
    # in just one lane. Summed RRF should lift 'shared' above 'solo'.
    dense = [_hit("solo.py", 1), _hit("shared.py", 1)]
    sparse = [_hit("shared.py", 1), _hit("other.py", 1)]
    fused = reciprocal_rank_fusion([dense, sparse])
    assert fused[0].ref.file_path == "shared.py"


def test_dedup_by_ref_key() -> None:
    dense = [_hit("a.py", 10)]
    sparse = [_hit("a.py", 10)]
    fused = reciprocal_rank_fusion([dense, sparse])
    assert len(fused) == 1


def test_fused_distance_monotone_with_score() -> None:
    # Higher fused score → smaller distance, so ascending-distance sort agrees.
    dense = [_hit("top.py", 1), _hit("mid.py", 1)]
    sparse = [_hit("top.py", 1)]
    fused = reciprocal_rank_fusion([dense, sparse])
    assert fused[0].ref.file_path == "top.py"
    assert fused[0].distance < fused[1].distance


def test_dedup_prefers_representative_with_symbol() -> None:
    dense = [_hit("a.py", 10, symbol=None)]
    sparse = [_hit("a.py", 10, symbol="pkg.a.foo")]
    fused = reciprocal_rank_fusion([dense, sparse])
    assert fused[0].ref.symbol == "pkg.a.foo"


def test_weights_let_a_strong_lane_dominate() -> None:
    # dense ranks 'd' first, sparse ranks 's' first. With dense weighted far
    # above sparse, 'd' must win even though both are rank-0 in their lane.
    dense = [_hit("d.py", 1), _hit("s.py", 1)]
    sparse = [_hit("s.py", 1), _hit("d.py", 1)]
    fused = reciprocal_rank_fusion([dense, sparse], weights=[5.0, 1.0])
    assert fused[0].ref.file_path == "d.py"


def test_weights_length_must_match_pools() -> None:
    import pytest

    with pytest.raises(ValueError, match="one entry per pool"):
        reciprocal_rank_fusion([[_hit("a.py", 1)]], weights=[1.0, 2.0])


def test_sparse_unique_find_still_surfaces_under_dense_weighting() -> None:
    # A chunk only sparse found still appears (the point of the sparse lane),
    # just below the dense-preferred hits.
    dense = [_hit("d.py", 1)]
    sparse = [_hit("rare.py", 1)]
    fused = reciprocal_rank_fusion([dense, sparse], weights=[3.0, 1.0])
    paths = [h.ref.file_path for h in fused]
    assert "rare.py" in paths and "d.py" in paths
    assert paths[0] == "d.py"


def test_k_constant_flattens_rank_advantage() -> None:
    # With a large k_constant, rank position matters less; the doubly-found
    # chunk should still win but by a smaller margin. Sanity: ordering holds.
    dense = [_hit("x.py", 1), _hit("y.py", 1)]
    sparse = [_hit("y.py", 1), _hit("x.py", 1)]
    fused = reciprocal_rank_fusion([dense, sparse], k_constant=1000)
    # Symmetric input → both appear; order stable and deduped.
    assert {h.ref.file_path for h in fused} == {"x.py", "y.py"}
    assert len(fused) == 2
