"""Bind BYOK provider keys to the signed-in account instead of the session.

Until now a connected Groq key lived only in the API process, keyed by session
id — so signing out (new session cookie) or restarting the API silently lost
it. This table keeps the key encrypted at rest against the identity that
connected it, so it survives both.

Revision ID: 0007_product_credentials
Revises: 0006_product_tours_persist
Create Date: 2026-08-06
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_product_credentials"
down_revision: str | Sequence[str] | None = "0006_product_tours_persist"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "product_credentials",
        sa.Column("provider", sa.Text(), primary_key=True),
        sa.Column("provider_account_id", sa.Text(), primary_key=True),
        sa.Column("groq_api_key", sa.Text(), nullable=False),
        sa.Column("huggingface_api_key", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )


def downgrade() -> None:
    op.drop_table("product_credentials")
