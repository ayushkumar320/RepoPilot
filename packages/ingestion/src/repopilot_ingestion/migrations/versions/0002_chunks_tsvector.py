"""Phase 3 — BM25/keyword lane: chunks.content_tsv tsvector + GIN index.

Adds a GENERATED STORED ``tsvector`` column over ``content || ' ' || symbol``
and a GIN index for Postgres full-text search (``bm25_search`` tool).

Analyzer choice: ``simple`` (not ``english``). Code retrieval keys on exact
identifiers — ``english`` stems and drops stopwords, which helps prose but
hurts rare symbols; ``simple`` lowercases without stemming, preserving
identifier tokens. See docs/rag/03 §Honest notes (english is the A/B
alternative if rare-symbol recall underperforms).

Because the column is ``GENERATED ALWAYS AS ... STORED``, it backfills for
already-indexed repos on migration and auto-populates on future inserts —
so ``persist.py`` needs no change.

Revision ID: 0002_chunks_tsvector
Revises: 0001_ingestion_schema
Create Date: 2026-07-09
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0002_chunks_tsvector"
down_revision: str | Sequence[str] | None = "0001_ingestion_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Field-weighted tsvector: the symbol goes in band 'A', the body in 'D'.
    # Postgres ts_rank_cd has no IDF, so without this a chunk that merely
    # *mentions* a common word outranks the chunk that *defines* the rare
    # symbol. Weighting symbol matches to band A (queried with a {D,C,B,A}
    # weight array favouring A) makes the defining chunk win — which is
    # exactly what rare-symbol retrieval needs. See docs/rag/03.
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


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_chunks_content_tsv")
    op.execute("ALTER TABLE chunks DROP COLUMN IF EXISTS content_tsv")
