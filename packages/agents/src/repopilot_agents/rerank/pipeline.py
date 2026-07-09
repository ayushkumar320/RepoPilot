"""``rerank_and_diversify`` — compose cross-encoder + MMR over a hit pool.

Input: the query, the ranked ``ChunkHit`` pool from ``hybrid_search``, and
the chunk contents (the caller already fetches them via ``read_chunks``).
Output: up to ``k`` (hit, content) pairs, cross-encoder-scored and
MMR-diversified, best-first.

Pool truncation: only the top ``max_pool`` hits are scored (retrieval already
front-loads the good stuff; scoring all 50 buys little and costs latency).
"""

from __future__ import annotations

from collections.abc import Sequence

import structlog

from repopilot_agents.rerank.cross_encoder import (
    DEFAULT_RERANK_MODEL,
    rerank_text,
    shared_reranker,
)
from repopilot_agents.rerank.mmr import mmr_select
from repopilot_agents.types import ChunkContent, ChunkHit

log = structlog.get_logger(__name__)

DEFAULT_MAX_POOL = 30
DEFAULT_LAMBDA = 0.7


def rerank_and_diversify(
    query: str,
    hits: Sequence[ChunkHit],
    contents: Sequence[ChunkContent],
    *,
    k: int = 8,
    lambda_: float = DEFAULT_LAMBDA,
    max_pool: int = DEFAULT_MAX_POOL,
    model_name: str = DEFAULT_RERANK_MODEL,
) -> list[tuple[ChunkHit, ChunkContent]]:
    """Cross-encoder rerank + MMR diversify; returns top-``k`` best-first.

    ``hits`` and ``contents`` must be parallel (same chunk at each index) —
    that's what ``read_chunks`` over the hit refs yields.
    """
    if not hits or k <= 0:
        return []
    if len(hits) != len(contents):
        raise ValueError("hits and contents must be parallel sequences")

    pool = min(len(hits), max_pool)
    texts = [rerank_text(contents[i]) for i in range(pool)]
    scores = shared_reranker(model_name).score(query, texts)
    order = mmr_select(texts, scores, k=k, lambda_=lambda_)
    log.debug("rerank.done", pool=pool, k=len(order), model=model_name)
    return [(hits[i], contents[i]) for i in order]


__all__ = ["DEFAULT_LAMBDA", "DEFAULT_MAX_POOL", "rerank_and_diversify"]
