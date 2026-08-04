"""Product-layer tables for anonymous sessions, entitlements, and usage."""

from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Index, MetaData, String, Table, Text, func
from sqlalchemy.dialects.postgresql import UUID

metadata = MetaData()

product_accounts = Table(
    "product_accounts",
    metadata,
    Column("session_id", UUID(as_uuid=False), primary_key=True),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("last_seen_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
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

__all__ = ["metadata", "product_accounts", "usage_events"]
