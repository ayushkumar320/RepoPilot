"""SQLAlchemy schema for Phase 1 ingestion.

Tables:
    repos              one row per (repo_url, head_sha) — the indexed snapshot
    chunks             structural chunks (function/class) with exact line spans
    chunk_embeddings   pgvector column over chunks (768-dim, nomic-embed-text)
    graph_adjacency    one JSONB sidecar per repo_id holding the NetworkX graph

The schema is the contract between Phase 1 (writes) and Phase 2 (reads via
the deterministic tools layer). Keep changes additive — Phase 2 tests will
build on these names.
"""

from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import UserDefinedType

EMBEDDING_DIM: int = 768


class Vector(UserDefinedType[list[float]]):
    """Minimal pgvector type so alembic can emit `vector(N)` without importing
    the `pgvector.sqlalchemy` runtime dependency in migration env.

    We don't need ORM-level value processing in Phase 1 — `persist.py` writes
    embeddings via parameterised raw SQL using the pgvector text format.
    """

    cache_ok = True

    def __init__(self, dim: int) -> None:
        self.dim = dim

    def get_col_spec(self, **_: object) -> str:
        return f"vector({self.dim})"


metadata = MetaData()


repos = Table(
    "repos",
    metadata,
    Column("id", Text, primary_key=True),  # canonical "owner/name@sha" id
    Column("url", Text, nullable=False),
    Column("head_sha", String(40), nullable=False),
    Column("status", String(32), nullable=False, server_default="indexed"),
    Column(
        "indexed_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    ),
    Column("loc_total", Integer, nullable=False, server_default="0"),
    Column("file_count", Integer, nullable=False, server_default="0"),
    UniqueConstraint("url", "head_sha", name="uq_repos_url_sha"),
)


chunks = Table(
    "chunks",
    metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column(
        "repo_id",
        Text,
        ForeignKey("repos.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("file_path", Text, nullable=False),
    Column("start_line", Integer, nullable=False),
    Column("end_line", Integer, nullable=False),
    # Dotted symbol path: "pkg.mod.Class.method"
    Column("symbol", Text, nullable=False),
    # "module" | "function" | "class" | "method"
    Column("kind", String(16), nullable=False),
    Column("summary", Text, nullable=True),
    Column("content", Text, nullable=False),
    Index("ix_chunks_repo_symbol", "repo_id", "symbol"),
    Index("ix_chunks_repo_file", "repo_id", "file_path"),
)


chunk_embeddings = Table(
    "chunk_embeddings",
    metadata,
    Column(
        "chunk_id",
        BigInteger,
        ForeignKey("chunks.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
)


graph_adjacency = Table(
    "graph_adjacency",
    metadata,
    Column(
        "repo_id",
        Text,
        ForeignKey("repos.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("adjacency", JSONB, nullable=False),
    Column("node_count", Integer, nullable=False, server_default="0"),
    Column("edge_count", Integer, nullable=False, server_default="0"),
)


__all__ = [
    "EMBEDDING_DIM",
    "chunk_embeddings",
    "chunks",
    "graph_adjacency",
    "metadata",
    "repos",
]
