"""Add repos.index_version so a recipe change invalidates old snapshots.

``repos`` is unique on (url, head_sha), so an unchanged repo counts as
already-indexed forever. That is correct while the *inputs* are fixed, but a
change to how chunks are cut or embedded produces a corpus the current query
path no longer matches. ``index_version`` records the recipe that built the
snapshot; ``INDEX_RECIPE_VERSION`` in ``db.py`` records the one the code
speaks today. Rows below it are treated as not indexed and rebuilt.

Existing rows default to 0, which is below every future recipe — so the first
visit after this migration re-indexes them.

Revision ID: 0008_index_recipe_version
Revises: 0007_product_credentials
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_index_recipe_version"
down_revision: str | Sequence[str] | None = "0007_product_credentials"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "repos",
        sa.Column("index_version", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("repos", "index_version")
