"""``read_chunks`` — the ONLY tool that returns source text.

Per Phase 2 decision **D1**: reads ``chunks.content`` from the indexed snapshot
(written by Phase 1) rather than re-reading source from disk. The snapshot is
immutable by design — Phase 1's idempotency on ``(repo_url, head_sha)`` means
``content`` is byte-exact to what was indexed.

Read by both the Q&A nodes (for answer generation) and the Verifier (for
grounding checks). Centralising the source-text path here is what lets the
Verifier reuse the exact same input the answerer saw.
"""

from __future__ import annotations

from collections.abc import Sequence

import structlog
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncEngine

from repopilot_agents.types import ChunkContent, CodeRef
from repopilot_ingestion.db import chunks as chunks_table

log = structlog.get_logger(__name__)


async def read_chunks(
    refs: Sequence[CodeRef],
    *,
    engine: AsyncEngine,
    repo_id: str,
) -> list[ChunkContent]:
    """Fetch the content of every chunk whose ``(file_path, start_line, end_line)``
    matches one of ``refs``. Order preserved.

    Missing refs are silently skipped — the caller decides what "missing" means
    (the Verifier treats it as ``rejected``; the answerer drops the claim).
    """
    if not refs:
        return []

    clauses = [
        and_(
            chunks_table.c.file_path == ref.file_path,
            chunks_table.c.start_line == ref.start_line,
            chunks_table.c.end_line == ref.end_line,
        )
        for ref in refs
    ]
    query = select(
        chunks_table.c.file_path,
        chunks_table.c.start_line,
        chunks_table.c.end_line,
        chunks_table.c.symbol,
        chunks_table.c.kind,
        chunks_table.c.summary,
        chunks_table.c.content,
        chunks_table.c.signature,
        chunks_table.c.decorators,
        chunks_table.c.neighbor_symbols,
    ).where(and_(chunks_table.c.repo_id == repo_id, or_(*clauses)))

    async with engine.connect() as conn:
        rows = (await conn.execute(query)).all()

    by_key: dict[tuple[str, int, int], ChunkContent] = {}
    for (
        file_path,
        start_line,
        end_line,
        symbol,
        kind,
        summary,
        content,
        signature,
        decorators,
        neighbor_symbols,
    ) in rows:
        ref = CodeRef(
            file_path=file_path,
            start_line=int(start_line),
            end_line=int(end_line),
            symbol=symbol,
        )
        by_key[(ref.file_path, ref.start_line, ref.end_line)] = ChunkContent(
            ref=ref,
            content=content,
            summary=summary,
            kind=kind,
            signature=signature,
            decorators=list(decorators or []),
            neighbor_symbols=list(neighbor_symbols or []),
        )

    out: list[ChunkContent] = []
    for ref in refs:
        key = (ref.file_path, ref.start_line, ref.end_line)
        hit = by_key.get(key)
        if hit is None:
            log.warning("read_chunks.missing", repo_id=repo_id, ref=ref.model_dump())
            continue
        out.append(hit)
    return out


__all__ = ["read_chunks"]
