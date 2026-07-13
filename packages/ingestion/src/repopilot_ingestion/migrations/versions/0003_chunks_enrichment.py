"""Phase 6 — ingestion enrichment metadata and enriched FTS text.

Revision ID: 0003_chunks_enrichment
Revises: 0002_chunks_tsvector
Create Date: 2026-07-13
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_chunks_enrichment"
down_revision: str | Sequence[str] | None = "0002_chunks_tsvector"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("chunks", sa.Column("enriched_text", sa.Text(), nullable=True))
    op.add_column("chunks", sa.Column("signature", sa.Text(), nullable=True))
    op.add_column(
        "chunks",
        sa.Column(
            "decorators",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "chunks",
        sa.Column(
            "neighbor_symbols",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )

    op.execute("DROP INDEX IF EXISTS ix_chunks_content_tsv")
    op.execute("ALTER TABLE chunks DROP COLUMN IF EXISTS content_tsv")
    op.execute(
        """
        ALTER TABLE chunks ADD COLUMN content_tsv tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('simple', coalesce(symbol, '')), 'A') ||
            setweight(to_tsvector('simple', coalesce(enriched_text, content, '')), 'D')
        ) STORED
        """
    )
    op.execute("CREATE INDEX ix_chunks_content_tsv ON chunks USING gin(content_tsv)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_chunks_content_tsv")
    op.execute("ALTER TABLE chunks DROP COLUMN IF EXISTS content_tsv")
    op.execute(
        """
        ALTER TABLE chunks ADD COLUMN content_tsv tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('simple', coalesce(symbol, '')), 'A') ||
            setweight(to_tsvector('simple', coalesce(content, '')), 'D')
        ) STORED
        """
    )
    op.execute("CREATE INDEX ix_chunks_content_tsv ON chunks USING gin(content_tsv)")
    op.drop_column("chunks", "neighbor_symbols")
    op.drop_column("chunks", "decorators")
    op.drop_column("chunks", "signature")
    op.drop_column("chunks", "enriched_text")
