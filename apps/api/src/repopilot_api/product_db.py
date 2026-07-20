"""Product-layer tables for sessions, entitlements, usage, and tours."""

from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Index, MetaData, String, Table, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

metadata = MetaData()

product_accounts = Table(
    "product_accounts",
    metadata,
    Column("session_id", UUID(as_uuid=False), primary_key=True),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("last_seen_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

product_tours = Table(
    "product_tours",
    metadata,
    Column("tour_id", String(64), primary_key=True),
    Column(
        "session_id",
        UUID(as_uuid=False),
        ForeignKey("product_accounts.session_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("repo_id", Text, nullable=False),
    Column("snapshot_repo_id", Text, ForeignKey("repos.id", ondelete="CASCADE"), nullable=False),
    Column("intent_profile", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Index("ix_product_tours_session", "session_id"),
)

usage_events = Table(
    "usage_events",
    metadata,
    Column("id", UUID(as_uuid=False), primary_key=True),
    Column(
        "session_id",
        UUID(as_uuid=False),
        ForeignKey("product_accounts.session_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("action", String(24), nullable=False),
    Column("resource_id", Text, nullable=False),
    Column("credential_source", String(16), nullable=False),
    Column("status", String(16), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Index("ix_usage_session_action_status", "session_id", "action", "status"),
    Index("ix_usage_session_resource", "session_id", "action", "resource_id"),
)

__all__ = ["metadata", "product_accounts", "product_tours", "usage_events"]
