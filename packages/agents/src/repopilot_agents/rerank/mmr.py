"""Maximal Marginal Relevance — diversity-aware top-k selection (pure).

``MMR(c) = lambda * relevance(c) - (1 - lambda) * max(sim(c, chosen))``

``lambda=1.0`` is pure relevance; ``0.0`` pure diversity. Code retrieval
wants relevance-heavy selection because multiple methods of one class are
sometimes the answer, so the default stays relevance-biased.

Similarity: token-set Jaccard over the item texts. ``ChunkHit`` does not carry
vectors and the reranker already needs chunk text in hand; near-duplicates in
code share most identifier tokens, which Jaccard captures directly.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _tokens(text: str) -> frozenset[str]:
    return frozenset(t.lower() for t in _TOKEN_RE.findall(text))


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def mmr_select(
    texts: Sequence[str],
    relevance: Sequence[float],
    *,
    k: int,
    lambda_: float = 0.7,
) -> list[int]:
    """Return indices of up to ``k`` items, MMR-ordered (pure function).

    ``relevance`` is min-max normalised internally so the lambda trade-off is
    scale-free (cross-encoder logits are unbounded).
    """
    if not texts or k <= 0:
        return []
    if len(texts) != len(relevance):
        raise ValueError("texts and relevance must be the same length")

    lo, hi = min(relevance), max(relevance)
    span = hi - lo
    rel = [(r - lo) / span if span > 0 else 1.0 for r in relevance]
    toks = [_tokens(t) for t in texts]

    chosen: list[int] = []
    remaining = list(range(len(texts)))
    while remaining and len(chosen) < k:
        best_i, best_score = remaining[0], float("-inf")
        for i in remaining:
            penalty = max((jaccard(toks[i], toks[j]) for j in chosen), default=0.0)
            score = lambda_ * rel[i] - (1.0 - lambda_) * penalty
            if score > best_score:
                best_i, best_score = i, score
        chosen.append(best_i)
        remaining.remove(best_i)
    return chosen


__all__ = ["jaccard", "mmr_select"]
