"""Per-session tour history: the repo, the persona, and every Q/A exchange.

Ownership is the whole authorization story. Every query filters on the
``session_id`` resolved from the signed cookie, and a tour belonging to
somebody else reads as absent (404) rather than forbidden (403) — a 403 would
confirm the id exists.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol
from uuid import uuid4

from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncEngine

from repopilot_api.product_db import product_accounts, product_tour_messages, product_tours


@dataclass(frozen=True, slots=True)
class TourMessage:
    ordinal: int
    question: str
    answer: str
    claims: list[dict[str, Any]]
    persona_label: str


@dataclass(frozen=True, slots=True)
class TourSummary:
    tour_id: str
    repo_id: str
    title: str | None
    created_at: datetime
    updated_at: datetime
    message_count: int


@dataclass(frozen=True, slots=True)
class TourDetail:
    tour_id: str
    repo_id: str
    snapshot_repo_id: str | None
    title: str | None
    intent_profile: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
    messages: list[TourMessage]


@dataclass(frozen=True, slots=True)
class Identity:
    session_id: str
    provider: str | None = None
    provider_account_id: str | None = None
    display_name: str | None = None
    email: str | None = None
    avatar_url: str | None = None


class TourService(Protocol):
    async def create_tour(
        self,
        session_id: str,
        *,
        repo_id: str,
        snapshot_repo_id: str | None,
        intent_profile: dict[str, Any] | None,
        title: str | None,
    ) -> str: ...

    async def list_tours(self, session_id: str) -> list[TourSummary]: ...

    async def get_tour(self, session_id: str, tour_id: str) -> TourDetail | None: ...

    async def append_message(
        self,
        session_id: str,
        tour_id: str,
        *,
        question: str,
        answer: str,
        claims: list[dict[str, Any]],
        persona_label: str,
    ) -> int | None: ...

    async def delete_tour(self, session_id: str, tour_id: str) -> bool: ...

    async def identity(self, session_id: str) -> Identity: ...

    async def set_identity(self, session_id: str, identity: Identity) -> Identity: ...


def _tour_id(repo_id: str) -> str:
    """Readable-ish id: repo slug prefix plus enough entropy to be unique."""
    slug = "".join(char if char.isalnum() else "-" for char in repo_id)[:40].strip("-")
    return f"{slug or 'tour'}-{uuid4().hex[:12]}"


@dataclass(slots=True)
class PostgresTourService:
    engine: AsyncEngine

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

    async def create_tour(
        self,
        session_id: str,
        *,
        repo_id: str,
        snapshot_repo_id: str | None,
        intent_profile: dict[str, Any] | None,
        title: str | None,
    ) -> str:
        await self._ensure_account(session_id)
        tour_id = _tour_id(repo_id)
        async with self.engine.begin() as conn:
            await conn.execute(
                product_tours.insert().values(
                    tour_id=tour_id,
                    session_id=session_id,
                    repo_id=repo_id,
                    snapshot_repo_id=snapshot_repo_id,
                    intent_profile=intent_profile or {},
                    title=title,
                )
            )
        return tour_id

    async def list_tours(self, session_id: str) -> list[TourSummary]:
        counts = (
            select(
                product_tour_messages.c.tour_id,
                func.count().label("message_count"),
            )
            .group_by(product_tour_messages.c.tour_id)
            .subquery()
        )
        async with self.engine.connect() as conn:
            rows = (
                await conn.execute(
                    select(
                        product_tours.c.tour_id,
                        product_tours.c.repo_id,
                        product_tours.c.title,
                        product_tours.c.created_at,
                        product_tours.c.updated_at,
                        func.coalesce(counts.c.message_count, 0),
                    )
                    .outerjoin(counts, counts.c.tour_id == product_tours.c.tour_id)
                    .where(product_tours.c.session_id == session_id)
                    .order_by(product_tours.c.updated_at.desc())
                )
            ).all()
        return [
            TourSummary(
                tour_id=str(row[0]),
                repo_id=str(row[1]),
                title=None if row[2] is None else str(row[2]),
                created_at=row[3],
                updated_at=row[4],
                message_count=int(row[5]),
            )
            for row in rows
        ]

    async def get_tour(self, session_id: str, tour_id: str) -> TourDetail | None:
        async with self.engine.connect() as conn:
            row = (
                await conn.execute(
                    select(
                        product_tours.c.tour_id,
                        product_tours.c.repo_id,
                        product_tours.c.snapshot_repo_id,
                        product_tours.c.title,
                        product_tours.c.intent_profile,
                        product_tours.c.created_at,
                        product_tours.c.updated_at,
                    ).where(
                        product_tours.c.tour_id == tour_id,
                        product_tours.c.session_id == session_id,
                    )
                )
            ).first()
            if row is None:
                return None
            message_rows = (
                await conn.execute(
                    select(
                        product_tour_messages.c.ordinal,
                        product_tour_messages.c.question,
                        product_tour_messages.c.answer,
                        product_tour_messages.c.claims,
                        product_tour_messages.c.persona_label,
                    )
                    .where(product_tour_messages.c.tour_id == tour_id)
                    .order_by(product_tour_messages.c.ordinal)
                )
            ).all()
        return TourDetail(
            tour_id=str(row[0]),
            repo_id=str(row[1]),
            snapshot_repo_id=None if row[2] is None else str(row[2]),
            title=None if row[3] is None else str(row[3]),
            intent_profile=row[4],
            created_at=row[5],
            updated_at=row[6],
            messages=[
                TourMessage(
                    ordinal=int(message[0]),
                    question=str(message[1]),
                    answer=str(message[2]),
                    claims=list(message[3] or []),
                    persona_label=str(message[4]),
                )
                for message in message_rows
            ],
        )

    async def append_message(
        self,
        session_id: str,
        tour_id: str,
        *,
        question: str,
        answer: str,
        claims: list[dict[str, Any]],
        persona_label: str,
    ) -> int | None:
        async with self.engine.begin() as conn:
            # Lock the tour row so two concurrent asks cannot pick the same
            # ordinal (the unique constraint would reject the loser outright).
            owned = await conn.scalar(
                select(product_tours.c.tour_id)
                .where(
                    product_tours.c.tour_id == tour_id,
                    product_tours.c.session_id == session_id,
                )
                .with_for_update()
            )
            if owned is None:
                return None
            used = await conn.scalar(
                select(func.count())
                .select_from(product_tour_messages)
                .where(product_tour_messages.c.tour_id == tour_id)
            )
            ordinal = int(used or 0)
            await conn.execute(
                product_tour_messages.insert().values(
                    id=str(uuid4()),
                    tour_id=tour_id,
                    ordinal=ordinal,
                    question=question,
                    answer=answer,
                    claims=claims,
                    persona_label=persona_label,
                )
            )
            await conn.execute(
                update(product_tours)
                .where(product_tours.c.tour_id == tour_id)
                .values(updated_at=func.now())
            )
        return ordinal

    async def delete_tour(self, session_id: str, tour_id: str) -> bool:
        async with self.engine.begin() as conn:
            result = await conn.execute(
                delete(product_tours).where(
                    product_tours.c.tour_id == tour_id,
                    product_tours.c.session_id == session_id,
                )
            )
        return result.rowcount > 0

    async def identity(self, session_id: str) -> Identity:
        await self._ensure_account(session_id)
        async with self.engine.connect() as conn:
            row = (
                await conn.execute(
                    select(
                        product_accounts.c.provider,
                        product_accounts.c.provider_account_id,
                        product_accounts.c.display_name,
                        product_accounts.c.email,
                        product_accounts.c.avatar_url,
                    ).where(product_accounts.c.session_id == session_id)
                )
            ).first()
        if row is None:
            return Identity(session_id=session_id)
        return Identity(
            session_id=session_id,
            provider=row[0],
            provider_account_id=row[1],
            display_name=row[2],
            email=row[3],
            avatar_url=row[4],
        )

    async def set_identity(self, session_id: str, identity: Identity) -> Identity:
        values = {
            "provider": identity.provider,
            "provider_account_id": identity.provider_account_id,
            "display_name": identity.display_name,
            "email": identity.email,
            "avatar_url": identity.avatar_url,
        }
        async with self.engine.begin() as conn:
            await conn.execute(
                insert(product_accounts)
                .values(session_id=session_id, **values)
                .on_conflict_do_update(
                    index_elements=[product_accounts.c.session_id],
                    set_={**values, "last_seen_at": func.now()},
                )
            )
        return Identity(session_id=session_id, **values)


@dataclass(slots=True)
class InMemoryTourService:
    """Contract-test tour store; live deployments use PostgresTourService."""

    tours: dict[str, TourDetail] = field(default_factory=dict)
    owners: dict[str, str] = field(default_factory=dict)
    identities: dict[str, Identity] = field(default_factory=dict)
    order: list[str] = field(default_factory=list)

    async def create_tour(
        self,
        session_id: str,
        *,
        repo_id: str,
        snapshot_repo_id: str | None,
        intent_profile: dict[str, Any] | None,
        title: str | None,
    ) -> str:
        tour_id = _tour_id(repo_id)
        now = datetime.now().astimezone()
        self.tours[tour_id] = TourDetail(
            tour_id=tour_id,
            repo_id=repo_id,
            snapshot_repo_id=snapshot_repo_id,
            title=title,
            intent_profile=intent_profile or {},
            created_at=now,
            updated_at=now,
            messages=[],
        )
        self.owners[tour_id] = session_id
        self.order.insert(0, tour_id)
        return tour_id

    async def list_tours(self, session_id: str) -> list[TourSummary]:
        return [
            TourSummary(
                tour_id=tour.tour_id,
                repo_id=tour.repo_id,
                title=tour.title,
                created_at=tour.created_at,
                updated_at=tour.updated_at,
                message_count=len(tour.messages),
            )
            for tour_id in self.order
            if self.owners.get(tour_id) == session_id
            for tour in [self.tours[tour_id]]
        ]

    async def get_tour(self, session_id: str, tour_id: str) -> TourDetail | None:
        if self.owners.get(tour_id) != session_id:
            return None
        return self.tours.get(tour_id)

    async def append_message(
        self,
        session_id: str,
        tour_id: str,
        *,
        question: str,
        answer: str,
        claims: list[dict[str, Any]],
        persona_label: str,
    ) -> int | None:
        tour = await self.get_tour(session_id, tour_id)
        if tour is None:
            return None
        ordinal = len(tour.messages)
        tour.messages.append(
            TourMessage(
                ordinal=ordinal,
                question=question,
                answer=answer,
                claims=claims,
                persona_label=persona_label,
            )
        )
        return ordinal

    async def delete_tour(self, session_id: str, tour_id: str) -> bool:
        if self.owners.get(tour_id) != session_id:
            return False
        self.owners.pop(tour_id, None)
        self.tours.pop(tour_id, None)
        self.order.remove(tour_id)
        return True

    async def identity(self, session_id: str) -> Identity:
        return self.identities.get(session_id, Identity(session_id=session_id))

    async def set_identity(self, session_id: str, identity: Identity) -> Identity:
        stored = Identity(
            session_id=session_id,
            provider=identity.provider,
            provider_account_id=identity.provider_account_id,
            display_name=identity.display_name,
            email=identity.email,
            avatar_url=identity.avatar_url,
        )
        self.identities[session_id] = stored
        return stored


__all__ = [
    "Identity",
    "InMemoryTourService",
    "PostgresTourService",
    "TourDetail",
    "TourMessage",
    "TourService",
    "TourSummary",
]
