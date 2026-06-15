"""Phase 1 — initial ingestion schema.

Creates: repos, chunks, chunk_embeddings (pgvector(768)), graph_adjacency.
Adds an ivfflat index for cosine similarity per the Phase 1 spec
(`WITH (lists = 100)` — adjust if recall < 95%).

Revision ID: 0001_ingestion_schema
Revises:
Create Date: 2026-06-15
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_ingestion_schema"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Extensions are also created by infra/postgres/init.sql on a fresh DB,
    # but migration replays (e.g. CI) need this safety net.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "repos",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("head_sha", sa.String(length=40), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="indexed",
        ),
        sa.Column(
            "indexed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("loc_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("file_count", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("url", "head_sha", name="uq_repos_url_sha"),
    )

    op.create_table(
        "chunks",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "repo_id",
            sa.Text(),
            sa.ForeignKey("repos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("start_line", sa.Integer(), nullable=False),
        sa.Column("end_line", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.Text(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
    )
    op.create_index("ix_chunks_repo_symbol", "chunks", ["repo_id", "symbol"], unique=False)
    op.create_index("ix_chunks_repo_file", "chunks", ["repo_id", "file_path"], unique=False)

    # `vector(768)` — emitted as raw SQL because the migration env must not
    # depend on pgvector's SQLAlchemy types.
    op.execute(
        "CREATE TABLE chunk_embeddings ("
        "  chunk_id BIGINT PRIMARY KEY REFERENCES chunks(id) ON DELETE CASCADE,"
        "  embedding vector(768) NOT NULL"
        ")"
    )
    op.execute(
        "CREATE INDEX ix_chunk_embeddings_cosine "
        "ON chunk_embeddings USING ivfflat (embedding vector_cosine_ops) "
        "WITH (lists = 100)"
    )

    op.create_table(
        "graph_adjacency",
        sa.Column(
            "repo_id",
            sa.Text(),
            sa.ForeignKey("repos.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("adjacency", postgresql.JSONB, nullable=False),
        sa.Column("node_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("edge_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("graph_adjacency")
    op.execute("DROP INDEX IF EXISTS ix_chunk_embeddings_cosine")
    op.execute("DROP TABLE IF EXISTS chunk_embeddings")
    op.drop_index("ix_chunks_repo_file", table_name="chunks")
    op.drop_index("ix_chunks_repo_symbol", table_name="chunks")
    op.drop_table("chunks")
    op.drop_table("repos")
