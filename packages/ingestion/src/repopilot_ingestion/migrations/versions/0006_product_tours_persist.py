"""Persist tours per user: identity columns plus tour + message tables.

``product_tours`` comes back (it was dropped in 0005) because a signed-in
reader now has history worth keeping: the repo they pasted, the persona they
read it through, and every question/answer pair. ``product_tour_messages``
holds those exchanges in ask order.

``snapshot_repo_id`` is nullable and ``ON DELETE SET NULL`` — unlike the 0004
version, which cascaded. A snapshot row is per-commit and gets replaced when a
repo is re-indexed; cascading would silently delete a user's history every
time upstream moved forward.

Revision ID: 0006_product_tours_persist
Revises: 0005_drop_product_tours
Create Date: 2026-08-04
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_product_tours_persist"
down_revision: str | Sequence[str] | None = "0005_drop_product_tours"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_IDENTITY_COLUMNS = ("provider", "provider_account_id", "display_name", "email", "avatar_url")


def upgrade() -> None:
    for column in _IDENTITY_COLUMNS:
        op.add_column("product_accounts", sa.Column(column, sa.Text(), nullable=True))

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
            sa.ForeignKey("repos.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("intent_profile", postgresql.JSONB(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_product_tours_session_updated",
        "product_tours",
        ["session_id", sa.text("updated_at DESC")],
    )

    op.create_table(
        "product_tour_messages",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "tour_id",
            sa.String(length=64),
            sa.ForeignKey("product_tours.tour_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("claims", postgresql.JSONB(), nullable=False),
        sa.Column("persona_label", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("tour_id", "ordinal", name="uq_tour_message_ordinal"),
    )


def downgrade() -> None:
    op.drop_table("product_tour_messages")
    op.drop_index("ix_product_tours_session_updated", table_name="product_tours")
    op.drop_table("product_tours")
    for column in _IDENTITY_COLUMNS:
        op.drop_column("product_accounts", column)
