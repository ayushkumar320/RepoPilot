"""Index a split form of each symbol so prose queries can hit code identifiers.

``content_tsv`` was built as ``symbol`` (band A) + ``content`` (band D) under
the ``simple`` config, which lowercases but never splits. ``HTTPTransport``
indexes as one lexeme ``httptransport`` and ``handle_request`` as one lexeme
``handle_request``, so the question "how does the transport handle a request"
shares no lexeme at all with ``HTTPTransport.handle_request`` — the sparse lane
cannot match prose to code, which is most of what users type.

This adds a band-B component holding the symbol with its boundaries opened up:
acronym→word, word→Capital, and ``.``/``_`` separators. ``HTTPTransport`` also
indexes as ``http transport``; ``handle_request`` also as ``handle request``.
Band A keeps the exact symbol, so rare-symbol retrieval is unchanged and still
outranks the looser split match (rank weights ``{D,C,B,A}`` =
``{0.1, 0.2, 0.4, 1.0}`` in ``bm25_search``).

Derived entirely from columns already stored: this needs a table rewrite but no
re-embedding and no re-index of the repo.

Revision ID: 0009_tsv_identifier_split
Revises: 0008_index_recipe_version
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0009_tsv_identifier_split"
down_revision: str | Sequence[str] | None = "0008_index_recipe_version"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# HTTPTransport -> HTTP Transport -> HTTP Transport; handle_request -> handle request
_SPLIT_SYMBOL = r"""
    regexp_replace(
        regexp_replace(
            regexp_replace(coalesce(symbol, ''), '([A-Z]+)([A-Z][a-z])', '\1 \2', 'g'),
            '([a-z0-9])([A-Z])', '\1 \2', 'g'),
        '[._]+', ' ', 'g')
"""

_NEW_TSV = f"""
    setweight(to_tsvector('simple', coalesce(symbol, '')), 'A') ||
    setweight(to_tsvector('simple', {_SPLIT_SYMBOL}), 'B') ||
    setweight(to_tsvector('simple', coalesce(content, '')), 'D')
"""

_OLD_TSV = """
    setweight(to_tsvector('simple', coalesce(symbol, '')), 'A') ||
    setweight(to_tsvector('simple', coalesce(content, '')), 'D')
"""


def _rebuild_tsv(expression: str) -> None:
    # A generated column's expression cannot be altered in place.
    op.execute("DROP INDEX IF EXISTS ix_chunks_content_tsv")
    op.execute("ALTER TABLE chunks DROP COLUMN IF EXISTS content_tsv")
    op.execute(
        f"ALTER TABLE chunks ADD COLUMN content_tsv tsvector "
        f"GENERATED ALWAYS AS ({expression}) STORED"
    )
    op.execute("CREATE INDEX ix_chunks_content_tsv ON chunks USING gin(content_tsv)")


def upgrade() -> None:
    _rebuild_tsv(_NEW_TSV)


def downgrade() -> None:
    _rebuild_tsv(_OLD_TSV)
