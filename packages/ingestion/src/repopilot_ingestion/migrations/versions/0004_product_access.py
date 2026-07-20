"""Product sessions, tour ownership, and usage ledger.

Revision ID: 0004_product_access
Revises: 0003_chunks_enrichment
Create Date: 2026-07-20
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_product_access"
down_revision: str | Sequence[str] | None = "0003_chunks_enrichment"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "product_accounts",
        sa.Column("session_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_table(
        "product_tours",
        sa.Column("tour_id", sa.String(length=64), primary_key=True),
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
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_product_tours_session", "product_tours", ["session_id"])
    op.create_table(
        "usage_events",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("product_accounts.session_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action", sa.String(length=24), nullable=False),
        sa.Column("resource_id", sa.Text(), nullable=False),
        sa.Column("credential_source", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_usage_session_action_status",
        "usage_events",
        ["session_id", "action", "status"],
    )
    op.create_index(
        "ix_usage_session_resource",
        "usage_events",
        ["session_id", "action", "resource_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_usage_session_resource", table_name="usage_events")
    op.drop_index("ix_usage_session_action_status", table_name="usage_events")
    op.drop_table("usage_events")
    op.drop_index("ix_product_tours_session", table_name="product_tours")
    op.drop_table("product_tours")
    op.drop_table("product_accounts")
