"""``hybrid_search`` — fuse the dense (vector) and sparse (BM25) lanes.

Runs ``vector_search`` and ``bm25_search`` concurrently, then fuses their
rankings with Reciprocal Rank Fusion so a chunk found by *either* lane
surfaces, and one found by *both* ranks highest. Same ``list[ChunkHit]``
return shape as ``vector_search``, so the Q&A graph swaps one call for the
other.
"""

from __future__ import annotations

import asyncio
import re
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
# symbols enough sparse-lane lift. Still the default for prose questions.
DENSE_WEIGHT = 3.0
SPARSE_WEIGHT = 1.0

# The query-adaptive routing the note above asks for, in its cheapest honest
# form. A query that spells an actual identifier
# (``HTTPTransport``, ``handle_request``, ``httpx.Client``, ``max_redirects``)
# is a lexical query — the exact token exists in the corpus and BM25 finds it
# by construction, while the dense lane is at its weakest on rare symbols
# (fastapi dense recall@10 `0.333` vs `0.556` hybrid). A prose question has no
# such anchor and dense must lead. Deterministic, no LLM, testable in CI.
IDENTIFIER_DENSE_WEIGHT = 1.0
IDENTIFIER_SPARSE_WEIGHT = 2.0

# CamelCase with an internal capital, snake_case, or a dotted path. Deliberately
# NOT plain lowercase words: "request" is prose, "handle_request" is a symbol.
_IDENTIFIER_RE = re.compile(
    r"(?:[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*)"  # dotted.path
    r"|(?:[A-Za-z0-9]+_[A-Za-z0-9_]+)"  # snake_case
    r"|(?:\b[A-Z][a-z0-9]+[A-Z][A-Za-z0-9]*)"  # CamelCase
    r"|(?:\b[A-Z]{2,}[a-z][A-Za-z0-9]*)"  # HTTPTransport
)


def looks_lexical(query: str) -> bool:
    """True when the query names a code identifier rather than describing one."""
    return _IDENTIFIER_RE.search(query) is not None


def lane_weights(query: str) -> tuple[float, float]:
    """Return ``(dense_weight, sparse_weight)`` for ``query``."""
    if looks_lexical(query):
        return IDENTIFIER_DENSE_WEIGHT, IDENTIFIER_SPARSE_WEIGHT
    return DENSE_WEIGHT, SPARSE_WEIGHT


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
    dense_weight: float | None = None,
    sparse_weight: float | None = None,
    sparse_query: str | None = None,
) -> list[ChunkHit]:
    """Return up to ``recall_k`` chunks fused from the dense + sparse lanes.

    ``sparse_query`` lets the caller hand BM25 a lexically richer string than
    the dense lane gets — the question plus the identifiers it named. The dense
    lane always sees the raw question: paraphrase-driven dense retrieval is
    what cost recall in Phase 2.

    ``dense_weight``/``sparse_weight`` default to ``lane_weights()`` over the
    sparse query; pass both explicitly to pin the fusion (the evals do, to A/B
    the router).
    """
    if not query.strip() or recall_k <= 0:
        return []

    bm25_query = sparse_query.strip() if sparse_query and sparse_query.strip() else query
    routed_dense, routed_sparse = lane_weights(bm25_query)
    dense_weight = routed_dense if dense_weight is None else dense_weight
    sparse_weight = routed_sparse if sparse_weight is None else sparse_weight

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
            bm25_query,
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
                bm25_query,
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


__all__ = ["hybrid_search", "lane_weights", "looks_lexical"]
