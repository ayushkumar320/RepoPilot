"""``vector_search`` — pgvector cosine k-NN over indexed chunks.

Embeds the query through ``LLMProvider.embed()`` (Ollama nomic-embed-text in
v1) so the embedding cache + fallback chain apply automatically. Returns
``ChunkHit[]`` with the chunk's ``CodeRef`` and the cosine distance.

The query operator is pgvector's ``<=>`` (cosine distance). ``WHERE
repo_id = ...`` is non-negotiable — we never mix corpora across repos.

This is one half of the hybrid-retrieval spine. The other half is
``graph_traverse``: vector_search finds the candidate hits; graph_traverse
completes the context (callers/callees/inheritance, ≤ 3 hops).
"""

from __future__ import annotations

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from repopilot_agents.types import ChunkHit, CodeRef
from repopilot_core.llm.provider import LLMProvider

log = structlog.get_logger(__name__)


async def vector_search(
    query: str,
    *,
    engine: AsyncEngine,
    provider: LLMProvider,
    repo_id: str,
    k: int = 8,
) -> list[ChunkHit]:
    """Return the top-``k`` chunks for ``query`` in ``repo_id``."""
    if not query.strip():
        return []
    if k <= 0:
        return []

    embedding = await provider.embed(query)
    literal = "[" + ",".join(repr(float(x)) for x in embedding.vector) + "]"

    # Cosine distance via pgvector's `<=>` operator. We need the vector cast
    # done in SQL so the planner can use the ivfflat index.
    sql = text(
        """
        SELECT c.file_path, c.start_line, c.end_line, c.symbol, c.kind, c.summary,
               (ce.embedding <=> CAST(:vec AS vector)) AS distance
        FROM chunks c
        JOIN chunk_embeddings ce ON ce.chunk_id = c.id
        WHERE c.repo_id = :repo_id
        ORDER BY ce.embedding <=> CAST(:vec AS vector)
        LIMIT :k
        """
    )

    async with engine.connect() as conn:
        rows = (await conn.execute(sql, {"vec": literal, "repo_id": repo_id, "k": k})).all()

    hits: list[ChunkHit] = []
    for file_path, start_line, end_line, symbol, kind, summary, distance in rows:
        hits.append(
            ChunkHit(
                ref=CodeRef(
                    file_path=file_path,
                    start_line=int(start_line),
                    end_line=int(end_line),
                    symbol=symbol,
                ),
                distance=float(distance),
                summary=summary,
                kind=kind,
            )
        )
    log.debug("vector_search.done", repo_id=repo_id, k=k, hits=len(hits))
    return hits


__all__ = ["vector_search"]
