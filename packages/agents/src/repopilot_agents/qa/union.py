"""Reciprocal Rank Fusion (RRF) — fuse multiple ranked ``ChunkHit`` lists.

Used by ``hybrid_search`` to combine the dense (vector) and sparse (BM25)
retrieval lanes into one ranking. RRF is score-agnostic: it fuses on **rank
position only**, so a cosine distance and a ``ts_rank_cd`` score — which live
on completely different scales — combine without normalization.

For a chunk appearing at rank ``r`` (0-indexed) in a lane, that lane
contributes ``1 / (k_constant + r + 1)`` to the chunk's fused score. Scores
sum across lanes, so a chunk found high by *both* lanes beats one found high
by only one. ``k_constant`` (default 60, the standard) damps the influence of
top ranks — larger values flatten the contribution curve.

This module was slated for Phase 2 (multi-query union); Phase 2 was deferred,
so Phase 3 owns it. It stays lane-count-agnostic so a future Phase 2 can feed
N dense rewrite-lanes through the same fusion.
"""

from __future__ import annotations

from collections.abc import Sequence

from repopilot_agents.types import ChunkHit

DEFAULT_K_CONSTANT = 60


def _ref_key(hit: ChunkHit) -> tuple[str, int, int]:
    return (hit.ref.file_path, hit.ref.start_line, hit.ref.end_line)


def reciprocal_rank_fusion(
    pools: Sequence[Sequence[ChunkHit]],
    *,
    k_constant: int = DEFAULT_K_CONSTANT,
    weights: Sequence[float] | None = None,
) -> list[ChunkHit]:
    """Fuse ranked hit lists into one ranking, best-first.

    Each input pool must already be ordered best-first. The returned list is
    deduplicated by ``(file_path, start_line, end_line)`` and ordered by
    descending fused RRF score. The kept ``ChunkHit`` carries a synthetic
    ``distance = 1 / (1 + score)`` so it sorts consistently with the
    dense-only path (ascending distance = better) for any downstream code
    that still reads ``distance``.

    ``weights`` (one per pool, default all-1.0) scales each lane's rank
    contribution. Weighting the dense lane above the sparse lane keeps an
    already-strong dense ranking from being reordered by a weaker sparse lane,
    while sparse still surfaces chunks dense missed (the whole point of BM25).
    """
    if weights is not None and len(weights) != len(pools):
        raise ValueError("weights must have one entry per pool")

    scores: dict[tuple[str, int, int], float] = {}
    best_hit: dict[tuple[str, int, int], ChunkHit] = {}

    for lane, pool in enumerate(pools):
        weight = weights[lane] if weights is not None else 1.0
        for rank, hit in enumerate(pool):
            key = _ref_key(hit)
            scores[key] = scores.get(key, 0.0) + weight / (k_constant + rank + 1)
            # Keep the richest representative (prefer one that has a symbol).
            existing = best_hit.get(key)
            if existing is None or (existing.ref.symbol is None and hit.ref.symbol is not None):
                best_hit[key] = hit

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    fused: list[ChunkHit] = []
    for key, score in ranked:
        hit = best_hit[key]
        fused.append(
            hit.model_copy(update={"distance": 1.0 / (1.0 + score)}),
        )
    return fused


__all__ = ["DEFAULT_K_CONSTANT", "reciprocal_rank_fusion"]
