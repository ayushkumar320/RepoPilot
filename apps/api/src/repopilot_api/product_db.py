"""Product-layer tables for anonymous sessions, entitlements, and usage."""

from __future__ import annotations

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

metadata = MetaData()

product_accounts = Table(
    "product_accounts",
    metadata,
    Column("session_id", UUID(as_uuid=False), primary_key=True),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("last_seen_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    # Null for anonymous visitors; set once the reader signs in with GitHub.
    Column("provider", Text, nullable=True),
    Column("provider_account_id", Text, nullable=True),
    Column("display_name", Text, nullable=True),
    Column("email", Text, nullable=True),
    Column("avatar_url", Text, nullable=True),
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
    # No ForeignKey object here: `repos` lives in the ingestion MetaData. The
    # constraint itself is created by migration 0006 (ON DELETE SET NULL).
    Column("snapshot_repo_id", Text, nullable=True),
    Column("intent_profile", JSONB, nullable=False),
    Column("title", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Index("ix_product_tours_session_updated", "session_id", "updated_at"),
)

product_tour_messages = Table(
    "product_tour_messages",
    metadata,
    Column("id", UUID(as_uuid=False), primary_key=True),
    Column(
        "tour_id",
        String(64),
        ForeignKey("product_tours.tour_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("ordinal", Integer, nullable=False),
    Column("question", Text, nullable=False),
    Column("answer", Text, nullable=False),
    Column("claims", JSONB, nullable=False),
    Column("persona_label", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    UniqueConstraint("tour_id", "ordinal", name="uq_tour_message_ordinal"),
)

product_credentials = Table(
    "product_credentials",
    metadata,
    # Keyed by the *account*, not the session: a reader who signs out and back
    # in gets a new session id, and their provider key has to follow them.
    Column("provider", Text, primary_key=True),
    Column("provider_account_id", Text, primary_key=True),
    # Fernet ciphertext, never the raw key.
    Column("groq_api_key", Text, nullable=False),
    Column("huggingface_api_key", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

__all__ = [
    "metadata",
    "product_accounts",
    "product_credentials",
    "product_tour_messages",
    "product_tours",
    "usage_events",
]
