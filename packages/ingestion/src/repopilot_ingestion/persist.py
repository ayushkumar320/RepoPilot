"""Persist Phase 1 pipeline output to Postgres + pgvector.

The functions here are the only place that writes to the ingestion tables.
Everything else (clone, parse, chunk, graph, summary, embed) produces typed
objects in memory; this module pushes them through SQLAlchemy.

Embeddings go in via parameterised raw SQL using pgvector's text literal
format (``'[0.1, 0.2, ...]'::vector``). That keeps the migration env free of
the ``pgvector.sqlalchemy`` runtime dependency.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass

import structlog
from sqlalchemy import insert, select, text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from repopilot_core.settings import Settings
from repopilot_ingestion.db import (
    EMBEDDING_DIM,
)
from repopilot_ingestion.db import (
    chunks as chunks_table,
)
from repopilot_ingestion.db import (
    graph_adjacency as graph_table,
)
from repopilot_ingestion.db import (
    repos as repos_table,
)
from repopilot_ingestion.embed import EmbeddedChunk
from repopilot_ingestion.summary import SummarisedChunk

log = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class PersistResult:
    repo_id: str
    chunk_count: int
    edge_count: int


def make_engine(settings: Settings) -> AsyncEngine:
    """Build an async engine from ``Settings.postgres_dsn``.

    Accepts a bare ``postgresql://`` DSN (e.g. a Neon connection string) and
    rewrites it to ``postgresql+psycopg://`` so SQLAlchemy uses psycopg3's
    async driver instead of defaulting to psycopg2.
    """
    dsn = settings.postgres_dsn
    if dsn.startswith("postgresql://"):
        dsn = "postgresql+psycopg://" + dsn[len("postgresql://") :]
    elif dsn.startswith("postgres://"):
        dsn = "postgresql+psycopg://" + dsn[len("postgres://") :]
    # Neon's pooler drops idle connections; pre-ping recycles dead ones
    # instead of failing mid-transaction with an SSL EOF.
    return create_async_engine(dsn, future=True, pool_pre_ping=True, pool_recycle=300)


async def repo_already_indexed(engine: AsyncEngine, *, repo_url: str, head_sha: str) -> bool:
    async with engine.connect() as conn:
        row = await conn.execute(
            select(repos_table.c.id).where(
                repos_table.c.url == repo_url,
                repos_table.c.head_sha == head_sha,
            )
        )
        return row.first() is not None


async def known_head_sha(engine: AsyncEngine, *, repo_url: str) -> str | None:
    """Return the most recently indexed head_sha for ``repo_url``, if any."""
    async with engine.connect() as conn:
        row = await conn.execute(
            select(repos_table.c.head_sha)
            .where(repos_table.c.url == repo_url)
            .order_by(repos_table.c.indexed_at.desc())
            .limit(1)
        )
        first = row.first()
        return None if first is None else str(first[0])


async def persist_index(
    *,
    engine: AsyncEngine,
    repo_id: str,
    repo_url: str,
    head_sha: str,
    summarised: Iterable[SummarisedChunk],
    embedded: dict[tuple[str, int, int], EmbeddedChunk],
    adjacency: dict[str, dict[str, list[str]]],
    loc_total: int,
) -> PersistResult:
    """Write the full Phase 1 output for one indexed snapshot.

    ``embedded`` is keyed by ``(file_path, start_line, end_line)`` so the
    chunk row's primary key can be paired with its vector after insertion.
    """
    summarised_list = list(summarised)
    chunk_count = 0
    edge_count = sum(len(v.get("calls", [])) for v in adjacency.values())

    SessionMaker = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionMaker.begin() as session:
        await session.execute(
            insert(repos_table).values(
                id=repo_id,
                url=repo_url,
                head_sha=head_sha,
                status="indexed",
                loc_total=loc_total,
                file_count=len({s.chunk.file_path for s in summarised_list}),
            )
        )

        for s in summarised_list:
            key = (s.chunk.file_path, s.chunk.start_line, s.chunk.end_line)
            result = await session.execute(
                insert(chunks_table)
                .values(
                    repo_id=repo_id,
                    file_path=s.chunk.file_path,
                    start_line=s.chunk.start_line,
                    end_line=s.chunk.end_line,
                    symbol=s.chunk.symbol,
                    kind=s.chunk.kind,
                    summary=s.summary,
                    content=s.chunk.content,
                )
                .returning(chunks_table.c.id)
            )
            chunk_id = int(result.scalar_one())
            chunk_count += 1

            emb = embedded.get(key)
            if emb is None:
                log.warning(
                    "persist.embedding_missing",
                    repo_id=repo_id,
                    symbol=s.chunk.symbol,
                )
                continue
            if len(emb.vector) != EMBEDDING_DIM:
                raise ValueError(
                    f"embedding dim {len(emb.vector)} != {EMBEDDING_DIM} "
                    f"for chunk {s.chunk.symbol!r}"
                )
            literal = "[" + ",".join(repr(float(x)) for x in emb.vector) + "]"
            await session.execute(
                text(
                    "INSERT INTO chunk_embeddings (chunk_id, embedding) "
                    "VALUES (:chunk_id, CAST(:literal AS vector))"
                ),
                {"chunk_id": chunk_id, "literal": literal},
            )

        node_count = len(adjacency)
        await session.execute(
            insert(graph_table).values(
                repo_id=repo_id,
                adjacency=json.loads(json.dumps(adjacency)),
                node_count=node_count,
                edge_count=edge_count,
            )
        )

    return PersistResult(repo_id=repo_id, chunk_count=chunk_count, edge_count=edge_count)


__all__ = [
    "PersistResult",
    "known_head_sha",
    "make_engine",
    "persist_index",
    "repo_already_indexed",
]
