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

# Version of the *recipe* that produced an index: chunk shape, embedding text,
# and embedding prefixes. ``repos`` is keyed on (url, head_sha), so without
# this a recipe change leaves every existing snapshot in place and silently
# mismatched — documents embedded under the old rules, queries issued under the
# new ones. Bump this whenever chunking or embedding input changes; snapshots
# at an older version stop counting as indexed and are rebuilt on next visit.
#
#   1 — nomic ``search_document:``/``search_query:`` prefixes; method chunks
#       carry their file + owning-class header; oversized symbols are split.
#   2 — parser slices spans by tree-sitter's byte offsets instead of indexing
#       the decoded str with them. Every symbol after a file's first non-ASCII
#       character was previously truncated or shifted, so ``chunks.symbol`` —
#       the join key from a graph node to its file:line — is different at rest.
#   3 — modules are named from their package root rather than the repo-relative
#       path, and relative imports resolve instead of being dropped. Renames
#       every symbol in a src-layout repo (``src.pkg.mod`` -> ``pkg.mod``) and
#       rewrites ``graph_adjacency`` plus ``chunks.neighbor_symbols`` for all.
#   4 — namespace subpackages (a directory with no ``__init__.py`` nested in a
#       real package, e.g. flask's ``src/flask/sansio/``) are named as part of
#       their package instead of by basename. Renames every symbol under one,
#       which is what makes a graph node join its chunk.
#   5 — the graph resolver types instance attributes and locals from declared
#       types, so ``self._transport.handle_request(...)`` and
#       ``t = self._pick(); t.handle(...)`` produce call edges instead of being
#       dropped. Adds edges to ``graph_adjacency`` and ``chunks.neighbor_symbols``
#       (+4% on httpx, +1% on flask); no symbol is renamed and none is invented.
#   6 — the graph carries ``defines`` edges: a module or class is linked to the
#       symbols nested inside it. Purely additive, and read only by the
#       "Related code" panel — ``tools/_adjacency.py`` whitelists the other
#       kinds, so fan-in, hubs and entry points are unchanged. Snapshots below
#       this rebuild so a class can list its own methods.
INDEX_RECIPE_VERSION: int = 6


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
    Column("index_version", Integer, nullable=False, server_default="0"),
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
    Column("enriched_text", Text, nullable=True),
    Column("signature", Text, nullable=True),
    Column("decorators", JSONB, nullable=False, server_default="[]"),
    Column("neighbor_symbols", JSONB, nullable=False, server_default="[]"),
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
