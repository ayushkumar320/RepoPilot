"""Drop product_tours.

The tour entity is gone from the product: a repository plus the reader's
``IntentProfile`` is all a question needs, and the profile now travels with
each ``/repos/{repo_id}/ask`` request instead of being frozen into a row at
"create tour" time. Nothing reads this table any more.

The downgrade recreates the table but not its rows — tours were ephemeral
per-session artifacts, so there is no data worth round-tripping.

Revision ID: 0005_drop_product_tours
Revises: 0004_product_access
Create Date: 2026-08-04
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_drop_product_tours"
down_revision: str | Sequence[str] | None = "0004_product_access"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("ix_product_tours_session", table_name="product_tours")
    op.drop_table("product_tours")


def downgrade() -> None:
    op.create_table(
        "product_tours",
        sa.Column("tour_id", sa.String(64), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("product_accounts.session_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("repo_id", sa.Text(), nullable=False),
        sa.Column(
            "snapshot_repo_id",
            sa.Text(),
            sa.ForeignKey("repos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("intent_profile", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_product_tours_session", "product_tours", ["session_id"])
