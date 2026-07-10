"""Claim → ref attribution via the Phase 4 cross-encoder.

The verifier judges each claim against *its attributed chunks* — so a claim
pinned to the wrong chunk is rejected even when a supporting chunk sits right
next to it in the context. The original token-overlap heuristic in
``_parse_claims`` (docstring: "false-positive ref attribution is harmless")
turned out to be the single answer-side weakness in the eval matrix: per-claim
grounding 0.43–0.79 while keyword accuracy said the answers themselves were
right.

Fix: score every ``(claim_text, chunk)`` pair with the in-process
cross-encoder (the same MiniLM that reranks retrieval — ~460 pairs/s, score
cache shared) and attach the top-``k`` chunks. The verifier reads the union
of a claim's ref chunks, so attribution only has to get the supporting chunk
*into* the top-k, not rank it first.
"""

from __future__ import annotations

from collections.abc import Sequence

import structlog

from repopilot_agents.rerank.cross_encoder import (
    DEFAULT_RERANK_MODEL,
    rerank_text,
    shared_reranker,
)
from repopilot_agents.types import ChunkContent, CodeRef

log = structlog.get_logger(__name__)


def attribute_refs(
    claim_text: str,
    chunks: Sequence[ChunkContent],
    *,
    k: int = 2,
    model_name: str = DEFAULT_RERANK_MODEL,
) -> list[CodeRef]:
    """Return the refs of the ``k`` chunks most relevant to ``claim_text``.

    Best-first by cross-encoder score. Empty input → empty output; the caller
    decides the no-chunks policy.
    """
    if not claim_text.strip() or not chunks:
        return []
    texts = [rerank_text(c) for c in chunks]
    scores = shared_reranker(model_name).score(claim_text, texts)
    order = sorted(range(len(chunks)), key=lambda i: scores[i], reverse=True)
    return [chunks[i].ref for i in order[:k]]


__all__ = ["attribute_refs"]
