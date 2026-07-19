"""``hybrid_search`` — fuse the dense (vector) and sparse (BM25) lanes.

Runs ``vector_search`` and ``bm25_search`` concurrently, then fuses their
rankings with Reciprocal Rank Fusion so a chunk found by *either* lane
surfaces, and one found by *both* ranks highest. Same ``list[ChunkHit]``
return shape as ``vector_search``, so the Q&A graph swaps one call for the
other.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence

import structlog
from sqlalchemy.ext.asyncio import AsyncEngine

from repopilot_agents.qa.union import DEFAULT_K_CONSTANT, reciprocal_rank_fusion
from repopilot_agents.tools.bm25_search import bm25_search
from repopilot_agents.tools.vector_search import vector_search
from repopilot_agents.types import ChunkHit
from repopilot_core.llm.provider import LLMProvider

log = structlog.get_logger(__name__)

# Dense is weighted above sparse in RRF. The lanes are complementary but their
# balance is repo-dependent: on httpx dense is near-perfect (so fusion must not
# reorder it), while on fastapi dense fails on rare symbols and BM25 rescues
# them (+42pp). A single global weight can't be optimal for both — that needs
# query-adaptive routing or reranking. 3.0 is the balance chosen for a Q&A
# product: it protects natural-language questions while still giving rare
# symbols enough sparse-lane lift.
DENSE_WEIGHT = 3.0
SPARSE_WEIGHT = 1.0


async def hybrid_search(
    query: str,
    *,
    engine: AsyncEngine,
    provider: LLMProvider,
    repo_id: str,
    recall_k: int = 50,
    kind: str | None = None,
    path_prefix: str | None = None,
    exclude_path_prefixes: Sequence[str] = (),
    k_constant: int = DEFAULT_K_CONSTANT,
    dense_weight: float = DENSE_WEIGHT,
    sparse_weight: float = SPARSE_WEIGHT,
) -> list[ChunkHit]:
    """Return up to ``recall_k`` chunks fused from the dense + sparse lanes."""
    if not query.strip() or recall_k <= 0:
        return []

    dense, sparse = await asyncio.gather(
        vector_search(
            query,
            engine=engine,
            provider=provider,
            repo_id=repo_id,
            recall_k=recall_k,
            kind=kind,
            path_prefix=path_prefix,
            exclude_path_prefixes=exclude_path_prefixes,
        ),
        bm25_search(
            query,
            engine=engine,
            repo_id=repo_id,
            k=recall_k,
            kind=kind,
            path_prefix=path_prefix,
            exclude_path_prefixes=exclude_path_prefixes,
        ),
    )

    if not dense and not sparse and exclude_path_prefixes:
        log.warning(
            "hybrid_search.retry_without_path_exclusions",
            repo_id=repo_id,
            excluded=list(exclude_path_prefixes),
        )
        dense, sparse = await asyncio.gather(
            vector_search(
                query,
                engine=engine,
                provider=provider,
                repo_id=repo_id,
                recall_k=recall_k,
                kind=kind,
                path_prefix=path_prefix,
            ),
            bm25_search(
                query,
                engine=engine,
                repo_id=repo_id,
                k=recall_k,
                kind=kind,
                path_prefix=path_prefix,
            ),
        )

    fused = reciprocal_rank_fusion(
        [dense, sparse],
        k_constant=k_constant,
        weights=[dense_weight, sparse_weight],
    )[:recall_k]
    log.debug(
        "hybrid_search.done",
        repo_id=repo_id,
        dense=len(dense),
        sparse=len(sparse),
        fused=len(fused),
    )
    return fused


__all__ = ["hybrid_search"]
