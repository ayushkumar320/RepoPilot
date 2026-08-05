"""Anonymous product sessions, free allowances, and session-only BYOK providers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol
from uuid import uuid4

import httpx
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncEngine

from repopilot_api.product_db import product_accounts, usage_events
from repopilot_core.llm.provider import LLMProvider
from repopilot_core.settings import Settings

CredentialSource = Literal["platform", "user"]


class AllowanceExceededError(RuntimeError):
    """Raised when a session has no free allowance and no user provider key."""

    def __init__(self, action: Literal["repository"]) -> None:
        self.action = action
        super().__init__(f"{action} allowance exhausted")


@dataclass(frozen=True, slots=True)
class AccountUsage:
    free_repositories_remaining: int
    provider_connected: bool
    groq_connected: bool
    huggingface_connected: bool


@dataclass(frozen=True, slots=True)
class UsageReservation:
    id: str
    source: CredentialSource


class AccessService(Protocol):
    async def status(self, session_id: str) -> AccountUsage: ...

    async def connect_provider(
        self, session_id: str, *, groq_api_key: str, huggingface_api_key: str | None
    ) -> AccountUsage: ...

    async def disconnect_provider(self, session_id: str) -> AccountUsage: ...

    async def provider_for(self, session_id: str) -> LLMProvider | None: ...

    async def reserve_repository(self, session_id: str, repo_id: str) -> UsageReservation: ...

    async def reserve_question(self, session_id: str, repo_id: str) -> UsageReservation: ...

    async def complete(self, reservation: UsageReservation) -> None: ...

    async def release(self, reservation: UsageReservation) -> None: ...

    async def aclose(self) -> None: ...


@dataclass(slots=True)
class ProductAccessService:
    """Postgres-backed allowances with credentials retained only in process memory."""

    engine: AsyncEngine
    settings: Settings
    providers: dict[str, LLMProvider] = field(default_factory=dict)
    connected: dict[str, tuple[bool, bool]] = field(default_factory=dict)

    async def _ensure_account(self, session_id: str) -> None:
        async with self.engine.begin() as conn:
            await conn.execute(
                insert(product_accounts)
                .values(session_id=session_id)
                .on_conflict_do_update(
                    index_elements=[product_accounts.c.session_id],
                    set_={"last_seen_at": func.now()},
                )
            )

    async def status(self, session_id: str) -> AccountUsage:
        await self._ensure_account(session_id)
        async with self.engine.connect() as conn:
            repo_count = await conn.scalar(
                select(func.count())
                .select_from(usage_events)
                .where(
                    usage_events.c.session_id == session_id,
                    usage_events.c.action == "repository",
                    usage_events.c.credential_source == "platform",
                    usage_events.c.status.in_(["reserved", "completed"]),
                )
            )
        groq, huggingface = self.connected.get(session_id, (False, False))
        return AccountUsage(
            free_repositories_remaining=max(0, 1 - int(repo_count or 0)),
            provider_connected=groq,
            groq_connected=groq,
            huggingface_connected=huggingface,
        )

    async def connect_provider(
        self, session_id: str, *, groq_api_key: str, huggingface_api_key: str | None
    ) -> AccountUsage:
        await self._ensure_account(session_id)
        clean_groq = groq_api_key.strip()
        clean_hf = (huggingface_api_key or "").strip() or None
        if len(clean_groq) < 12:
            raise ValueError("Enter a complete Groq API key.")
        if clean_hf is not None and len(clean_hf) < 8:
            raise ValueError("Enter a complete Hugging Face token or leave it blank.")

        await self._validate_provider_key(
            provider="Groq",
            base_url=self.settings.groq_base_url,
            api_key=clean_groq,
        )
        if clean_hf is not None:
            await self._validate_provider_key(
                provider="Hugging Face",
                base_url=self.settings.huggingface_base_url,
                api_key=clean_hf,
            )

        previous = self.providers.pop(session_id, None)
        if previous is not None:
            await previous.aclose()
        user_settings = self.settings.model_copy(
            update={
                "groq_api_key": clean_groq,
                "cerebras_api_key": None,
                "huggingface_api_key": clean_hf,
                "llm_hf_chat_fallback": clean_hf is not None,
            }
        )
        self.providers[session_id] = LLMProvider.build(settings=user_settings)
        self.connected[session_id] = (True, clean_hf is not None)
        return await self.status(session_id)

    async def _validate_provider_key(self, *, provider: str, base_url: str, api_key: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{base_url.rstrip('/')}/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
        except httpx.HTTPError as exc:
            raise ValueError(f"Could not reach {provider} to validate this key.") from exc
        if response.status_code in {401, 403}:
            raise ValueError(f"{provider} rejected this key.")
        if response.is_error:
            raise ValueError(
                f"{provider} key validation failed with status {response.status_code}."
            )

    async def disconnect_provider(self, session_id: str) -> AccountUsage:
        provider = self.providers.pop(session_id, None)
        self.connected.pop(session_id, None)
        if provider is not None:
            await provider.aclose()
        return await self.status(session_id)

    async def provider_for(self, session_id: str) -> LLMProvider | None:
        return self.providers.get(session_id)

    async def _reserve(
        self,
        session_id: str,
        *,
        action: Literal["repository", "question"],
        resource_id: str,
        free_limit: int | None,
    ) -> UsageReservation:
        await self._ensure_account(session_id)
        source: CredentialSource = "user" if session_id in self.providers else "platform"
        reservation_id = str(uuid4())
        async with self.engine.begin() as conn:
            await conn.execute(
                select(product_accounts.c.session_id)
                .where(product_accounts.c.session_id == session_id)
                .with_for_update()
            )
            existing = await conn.scalar(
                select(usage_events.c.id).where(
                    usage_events.c.session_id == session_id,
                    usage_events.c.action == action,
                    usage_events.c.resource_id == resource_id,
                    usage_events.c.status.in_(["reserved", "completed"]),
                )
            )
            if existing is not None and action == "repository":
                return UsageReservation(id=str(existing), source=source)
            if source == "platform" and free_limit is not None:
                used = await conn.scalar(
                    select(func.count())
                    .select_from(usage_events)
                    .where(
                        usage_events.c.session_id == session_id,
                        usage_events.c.action == action,
                        usage_events.c.credential_source == "platform",
                        usage_events.c.status.in_(["reserved", "completed"]),
                    )
                )
                if int(used or 0) >= free_limit:
                    raise AllowanceExceededError("repository")
            await conn.execute(
                insert(usage_events).values(
                    id=reservation_id,
                    session_id=session_id,
                    action=action,
                    resource_id=resource_id,
                    credential_source=source,
                    status="reserved",
                )
            )
        return UsageReservation(id=reservation_id, source=source)

    async def reserve_repository(self, session_id: str, repo_id: str) -> UsageReservation:
        return await self._reserve(
            session_id, action="repository", resource_id=repo_id, free_limit=1
        )

    async def reserve_question(self, session_id: str, repo_id: str) -> UsageReservation:
        # Questions are unmetered; the row is still written for usage history.
        return await self._reserve(
            session_id, action="question", resource_id=repo_id, free_limit=None
        )

    async def complete(self, reservation: UsageReservation) -> None:
        async with self.engine.begin() as conn:
            await conn.execute(
                update(usage_events)
                .where(usage_events.c.id == reservation.id)
                .values(status="completed")
            )

    async def release(self, reservation: UsageReservation) -> None:
        async with self.engine.begin() as conn:
            await conn.execute(
                update(usage_events)
                .where(
                    usage_events.c.id == reservation.id,
                    usage_events.c.status == "reserved",
                )
                .values(status="failed")
            )

    async def aclose(self) -> None:
        for provider in self.providers.values():
            await provider.aclose()
        self.providers.clear()
        self.connected.clear()
        await self.engine.dispose()


@dataclass(slots=True)
class InMemoryAccessService:
    """Contract-test access service; live deployments use ProductAccessService."""

    repository_events: dict[str, set[str]] = field(default_factory=dict)
    question_counts: dict[str, int] = field(default_factory=dict)
    connected_sessions: dict[str, bool] = field(default_factory=dict)

    async def status(self, session_id: str) -> AccountUsage:
        groq = session_id in self.connected_sessions
        return AccountUsage(
            free_repositories_remaining=max(
                0, 1 - len(self.repository_events.get(session_id, set()))
            ),
            provider_connected=groq,
            groq_connected=groq,
            huggingface_connected=self.connected_sessions.get(session_id, False),
        )

    async def connect_provider(
        self, session_id: str, *, groq_api_key: str, huggingface_api_key: str | None
    ) -> AccountUsage:
        if len(groq_api_key.strip()) < 12:
            raise ValueError("Enter a complete Groq API key.")
        self.connected_sessions[session_id] = bool(huggingface_api_key)
        return await self.status(session_id)

    async def disconnect_provider(self, session_id: str) -> AccountUsage:
        self.connected_sessions.pop(session_id, None)
        return await self.status(session_id)

    async def provider_for(self, session_id: str) -> LLMProvider | None:
        return None

    async def reserve_repository(self, session_id: str, repo_id: str) -> UsageReservation:
        repos = self.repository_events.setdefault(session_id, set())
        connected = session_id in self.connected_sessions
        if repo_id not in repos and len(repos) >= 1 and not connected:
            raise AllowanceExceededError("repository")
        repos.add(repo_id)
        return UsageReservation(str(uuid4()), "user" if connected else "platform")

    async def reserve_question(self, session_id: str, repo_id: str) -> UsageReservation:
        if session_id in self.connected_sessions:
            return UsageReservation(str(uuid4()), "user")
        self.question_counts[session_id] = self.question_counts.get(session_id, 0) + 1
        return UsageReservation(str(uuid4()), "platform")

    async def complete(self, reservation: UsageReservation) -> None:
        return None

    async def release(self, reservation: UsageReservation) -> None:
        return None

    async def aclose(self) -> None:
        return None


__all__ = [
    "AccessService",
    "AccountUsage",
    "AllowanceExceededError",
    "InMemoryAccessService",
    "ProductAccessService",
    "UsageReservation",
]
