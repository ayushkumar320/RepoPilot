"""Service seams and live-ish implementations behind the Phase 4 routes."""

from __future__ import annotations

import asyncio
import base64
import binascii
import json
import re
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol
from urllib.parse import quote, unquote
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine

from repopilot_agents.qa import QAResult, answer_question
from repopilot_agents.state import Claim as StateClaim
from repopilot_agents.state import IntentProfile
from repopilot_agents.tools.graph_query import graph_query
from repopilot_agents.tools.read_chunks import read_chunks
from repopilot_agents.types import CodeRef
from repopilot_agents.verifier.grounding import Claim as QAClaim
from repopilot_api.models import (
    BaseTourEvent,
    ChunkPayload,
    QAAnswerResponse,
    RepoStatus,
    TourClaimEvent,
    TourClaimPayload,
    TourDiagramEvent,
    TourDoneEvent,
    TourErrorEvent,
    TourEventType,
    TourFirstImpressionEvent,
    TourSectionEndEvent,
    TourSectionStartEvent,
    TourTokenEvent,
)
from repopilot_core.llm.provider import LLMProvider
from repopilot_core.settings import Settings, get_settings
from repopilot_ingestion.clone import parse_github_url
from repopilot_ingestion.db import chunk_embeddings as embeddings_table
from repopilot_ingestion.db import chunks as chunks_table
from repopilot_ingestion.db import repos as repos_table
from repopilot_ingestion.persist import make_engine
from repopilot_ingestion.pipeline import index_repo, revisit_status


def repo_slug(repo_url: str) -> str:
    owner, name = parse_github_url(repo_url)
    return quote(f"{owner}/{name}", safe="")


def decode_repo_slug(repo_id: str) -> str:
    return unquote(repo_id)


def normalize_repo_id(repo_id: str) -> str:
    return quote(decode_repo_slug(repo_id), safe="")


@dataclass(slots=True)
class RepoRecord:
    repo_id: str
    repo_url: str
    status: RepoStatus
    progress: int | None = None
    error: str | None = None
    indexed_sha: str | None = None
    remote_sha: str | None = None
    commits_behind_estimate: int | None = None
    indexed_repo_id: str | None = None
    first_impression: str | None = None


@dataclass(slots=True)
class TourRecord:
    tour_id: str
    repo_id: str
    created_at: datetime
    intent_profile: IntentProfile
    snapshot_repo_id: str


@dataclass(slots=True)
class TourSectionData:
    title: str
    summary: str
    claims: list[SectionClaimData]
    diagram: str | None = None


@dataclass(slots=True)
class SectionClaimData:
    claim: StateClaim
    retrieval_path: list[str]


class RepoService(Protocol):
    async def enqueue(self, repo_url: str) -> RepoRecord: ...

    async def get(self, repo_id: str) -> RepoRecord: ...

    def first_impression_stream(self, repo_id: str) -> AsyncIterator[BaseTourEvent]: ...


class TourService(Protocol):
    async def create(self, repo_id: str, intent_profile: IntentProfile) -> TourRecord: ...

    async def get(self, tour_id: str) -> TourRecord: ...

    def stream(self, tour_id: str) -> AsyncIterator[BaseTourEvent]: ...

    async def ask(self, tour_id: str, question: str) -> QAAnswerResponse: ...


class ChunkService(Protocol):
    async def get(self, chunk_id: str) -> ChunkPayload: ...


class RepoNotReadyError(Exception):
    """Raised when a tour is requested before a repo has an indexed snapshot."""

    def __init__(self, repo_id: str, status: RepoStatus) -> None:
        self.repo_id = repo_id
        self.status = status
        super().__init__(f"repo {repo_id!r} is not ready for tours; status={status!r}")


@dataclass(slots=True)
class AppServices:
    repos: RepoService
    tours: TourService
    chunks: ChunkService


@dataclass(slots=True)
class RepoSnapshot:
    repo_id: str
    repo_url: str
    head_sha: str


@dataclass(slots=True)
class Runtime:
    settings: Settings
    provider: LLMProvider


async def build_runtime() -> Runtime:
    settings = get_settings()
    provider = LLMProvider.build(settings=settings)
    return Runtime(settings=settings, provider=provider)


async def shutdown_runtime(runtime: Runtime) -> None:
    await runtime.provider.aclose()


@dataclass(slots=True)
class LiveRepoService:
    runtime: Runtime
    records: dict[str, RepoRecord] = field(default_factory=dict)
    tasks: dict[str, asyncio.Task[None]] = field(default_factory=dict)

    async def enqueue(self, repo_url: str) -> RepoRecord:
        slug = repo_slug(repo_url)
        existing = await self._load_record_from_db(slug, repo_url=repo_url)
        if existing is not None and existing.status in {"ready", "stale"}:
            self.records[slug] = existing
            return existing

        record = self.records.get(slug)
        if record is None:
            record = RepoRecord(repo_id=slug, repo_url=repo_url, status="queued", progress=5)
            self.records[slug] = record
        if slug not in self.tasks or self.tasks[slug].done():
            self.tasks[slug] = asyncio.create_task(self._index(slug, repo_url))
        return record

    async def get(self, repo_id: str) -> RepoRecord:
        normalized_repo_id = normalize_repo_id(repo_id)
        record = self.records.get(normalized_repo_id)
        if record is not None:
            return record
        loaded = await self._load_record_from_db(normalized_repo_id)
        if loaded is None:
            raise KeyError(normalized_repo_id)
        self.records[normalized_repo_id] = loaded
        return loaded

    async def _index(self, slug: str, repo_url: str) -> None:
        record = self.records[slug]
        record.status = "indexing"
        record.progress = 15
        record.first_impression = "Cloning the repository and building a structural snapshot."
        progress_task = asyncio.create_task(self._advance_progress(record))
        try:
            result = await index_repo(
                repo_url, provider=self.runtime.provider, settings=self.runtime.settings
            )
            progress_task.cancel()
            if result.status == "too_large":
                record.status = "error"
                record.progress = None
                record.error = (
                    f"Repository has {result.loc_total or 0} indexable lines, exceeding the "
                    f"configured limit of {self.runtime.settings.ingestion_max_repo_loc}."
                )
                return
            if result.status == "unsupported":
                record.status = "error"
                record.progress = None
                record.error = "Repository contains no supported source or context files."
                return
            record.progress = 100
            record.indexed_sha = result.head_sha
            record.remote_sha = result.head_sha
            record.indexed_repo_id = result.repo_id
            record.first_impression = (
                f"Indexed {repo_url}. Structural snapshot is ready with "
                f"{result.chunk_count or 0} chunks and {result.edge_count or 0} graph edges."
            )
            record.status = "ready"
        except Exception as exc:
            progress_task.cancel()
            record.status = "error"
            record.progress = None
            record.error = str(exc)

    async def _advance_progress(self, record: RepoRecord) -> None:
        while record.status == "indexing":
            await asyncio.sleep(10)
            if record.progress is None:
                record.progress = 15
            elif record.progress < 90:
                record.progress += 5

    async def _load_record_from_db(
        self,
        repo_id: str,
        *,
        repo_url: str | None = None,
    ) -> RepoRecord | None:
        normalized_repo_id = normalize_repo_id(repo_id)
        engine = make_engine(self.runtime.settings)
        try:
            resolved_url = repo_url
            if resolved_url is None:
                async with engine.connect() as conn:
                    row = (
                        await conn.execute(
                            select(repos_table.c.url)
                            .where(
                                repos_table.c.id.like(f"{decode_repo_slug(normalized_repo_id)}@%")
                            )
                            .order_by(repos_table.c.indexed_at.desc())
                            .limit(1)
                        )
                    ).first()
                resolved_url = None if row is None else str(row[0])
            if resolved_url is None:
                return None

            status = await revisit_status(repo_url=resolved_url, settings=self.runtime.settings)
            indexed_repo_id = await self._latest_repo_snapshot_id(engine, resolved_url)
            if status.status == "already_indexed":
                return RepoRecord(
                    repo_id=normalized_repo_id,
                    repo_url=resolved_url,
                    status="ready",
                    progress=100,
                    indexed_sha=status.indexed_sha,
                    remote_sha=status.remote_sha,
                    commits_behind_estimate=0,
                    indexed_repo_id=indexed_repo_id,
                    first_impression=await self._compose_first_impression(engine, indexed_repo_id),
                )
            if status.status == "stale" and indexed_repo_id is not None:
                return RepoRecord(
                    repo_id=normalized_repo_id,
                    repo_url=resolved_url,
                    status="stale",
                    progress=100,
                    indexed_sha=status.indexed_sha,
                    remote_sha=status.remote_sha,
                    commits_behind_estimate=1,
                    indexed_repo_id=indexed_repo_id,
                    first_impression=await self._compose_first_impression(engine, indexed_repo_id),
                )
            return None
        finally:
            await engine.dispose()

    async def _latest_repo_snapshot_id(self, engine: AsyncEngine, repo_url: str) -> str | None:
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    select(repos_table.c.id)
                    .join(chunks_table, chunks_table.c.repo_id == repos_table.c.id)
                    .outerjoin(
                        embeddings_table,
                        embeddings_table.c.chunk_id == chunks_table.c.id,
                    )
                    .where(repos_table.c.url == repo_url)
                    .group_by(repos_table.c.id, repos_table.c.indexed_at)
                    .having(func.count(chunks_table.c.id) > 0)
                    .having(
                        func.count(embeddings_table.c.chunk_id)
                        == func.count(chunks_table.c.id)
                    )
                    .order_by(repos_table.c.indexed_at.desc())
                    .limit(1)
                )
            ).first()
        return None if row is None else str(row[0])

    async def _compose_first_impression(
        self, engine: AsyncEngine, snapshot_repo_id: str | None
    ) -> str | None:
        if snapshot_repo_id is None:
            return None
        hubs = await graph_query("hubs", engine=engine, repo_id=snapshot_repo_id, top_n=3)
        entry_points = await graph_query(
            "entry_points",
            engine=engine,
            repo_id=snapshot_repo_id,
            top_n=3,
        )
        async with engine.connect() as conn:
            file_count_row = (
                await conn.execute(
                    select(repos_table.c.file_count, repos_table.c.loc_total).where(
                        repos_table.c.id == snapshot_repo_id
                    )
                )
            ).first()
        file_count = 0 if file_count_row is None else int(file_count_row[0])
        loc_total = 0 if file_count_row is None else int(file_count_row[1])
        hub_names = ", ".join(h.symbol.rsplit(".", 1)[-1] for h in hubs) or "no dominant hubs yet"
        entry_names = (
            ", ".join(e.symbol.rsplit(".", 1)[-1] for e in entry_points) or "no clear entry points"
        )
        return (
            f"Indexed snapshot across {file_count} files and {loc_total} lines. "
            f"Primary entry points: {entry_names}. Structural hubs: {hub_names}."
        )

    async def first_impression(self, repo_id: str) -> str:
        record = await self.get(repo_id)
        return (
            record.first_impression
            or "Indexing has started; first structural signals will appear shortly."
        )

    async def _first_impression_events(self, repo_id: str) -> AsyncIterator[TourEventType]:
        text = await self.first_impression(repo_id)
        yield TourFirstImpressionEvent(text=text)
        yield TourDoneEvent()

    def first_impression_stream(self, repo_id: str) -> AsyncIterator[TourEventType]:
        return self._first_impression_events(repo_id)


@dataclass(slots=True)
class LiveTourService:
    runtime: Runtime
    repos: LiveRepoService
    records: dict[str, TourRecord] = field(default_factory=dict)

    async def create(self, repo_id: str, intent_profile: IntentProfile) -> TourRecord:
        repo = await self.repos.get(repo_id)
        snapshot_repo_id = repo.indexed_repo_id
        if snapshot_repo_id is None:
            raise RepoNotReadyError(repo_id, repo.status)
        record = TourRecord(
            tour_id=f"tour-{uuid4().hex[:8]}",
            repo_id=repo_id,
            created_at=datetime.now(tz=UTC),
            intent_profile=intent_profile,
            snapshot_repo_id=snapshot_repo_id,
        )
        self.records[record.tour_id] = record
        return record

    async def get(self, tour_id: str) -> TourRecord:
        return self.records[tour_id]

    async def _build_sections(self, record: TourRecord) -> list[TourSectionData]:
        engine = make_engine(self.runtime.settings)
        try:
            snapshot = await load_snapshot(engine, record.snapshot_repo_id)
            hubs = await graph_query("hubs", engine=engine, repo_id=snapshot.repo_id, top_n=4)
            entry_points = await graph_query(
                "entry_points", engine=engine, repo_id=snapshot.repo_id, top_n=4
            )
            layers = await graph_query("layers", engine=engine, repo_id=snapshot.repo_id, top_n=6)

            entry_claims = await build_claims_for_symbols(
                engine,
                snapshot.repo_id,
                [item.symbol for item in entry_points[:3]],
                note="Identified from graph entry points.",
                path=["graph_query:entry_points", "chunks:symbol_lookup"],
            )
            hub_claims = await build_claims_for_symbols(
                engine,
                snapshot.repo_id,
                [item.symbol for item in hubs[:3]],
                note="Identified from graph hubs.",
                path=["graph_query:hubs", "chunks:symbol_lookup"],
            )
            layer_claims = await build_claims_for_symbols(
                engine,
                snapshot.repo_id,
                [item.symbol for item in layers[:3]],
                note="Representative symbols from structural layers.",
                path=["graph_query:layers", "chunks:symbol_lookup"],
            )
        finally:
            await engine.dispose()

        focus = ", ".join(record.intent_profile.focus_keywords) or "system shape"
        return [
            TourSectionData(
                title="Where To Start",
                summary=(
                    f"For your goal around {focus}, the clearest entry points are the outward-facing "
                    "functions that begin real work in the indexed graph."
                ),
                claims=entry_claims,
            ),
            TourSectionData(
                title="Structural Hubs",
                summary=(
                    "These symbols attract the highest fan-in, so they’re the places where reading effort "
                    "compounds fastest."
                ),
                claims=hub_claims,
                diagram=build_mermaid(hubs[:3]),
            ),
            TourSectionData(
                title="Reading Path",
                summary=(
                    "This final section gives you a concrete traversal path through representative symbols "
                    "so the code viewer can stay synchronized with the tour."
                ),
                claims=layer_claims,
            ),
        ]

    async def _stream_impl(self, tour_id: str) -> AsyncIterator[TourEventType]:
        record = await self.get(tour_id)
        try:
            sections = await self._build_sections(record)
        except Exception as exc:
            yield TourErrorEvent(code="TOUR_BUILD_FAILED", message=str(exc))
            return
        for order, section in enumerate(sections):
            yield TourSectionStartEvent(order=order, title=section.title)
            for sentence in split_sentences(section.summary):
                yield TourTokenEvent(text=sentence + " ")
            for idx, claim in enumerate(section.claims):
                yield TourClaimEvent(
                    id=f"{tour_id}-section-{order}-claim-{idx}",
                    text=claim.claim.text,
                    refs=claim.claim.refs,
                    status=claim.claim.status,
                    verifier_note=claim.claim.verifier_note,
                    retrieval_path=claim.retrieval_path,
                )
            if section.diagram is not None:
                yield TourDiagramEvent(mermaid=section.diagram)
            yield TourSectionEndEvent(order=order)
        yield TourDoneEvent()

    def stream(self, tour_id: str) -> AsyncIterator[TourEventType]:
        return self._stream_impl(tour_id)

    async def ask(self, tour_id: str, question: str) -> QAAnswerResponse:
        record = await self.get(tour_id)
        engine = make_engine(self.runtime.settings)
        try:
            try:
                result = await answer_question(
                    question,
                    engine=engine,
                    provider=self.runtime.provider,
                    repo_id=record.snapshot_repo_id,
                )
            except Exception as exc:
                result = await answer_deterministically(
                    engine=engine,
                    snapshot_repo_id=record.snapshot_repo_id,
                    question=question,
                    fallback_reason=str(exc),
                )
        finally:
            await engine.dispose()
        return QAAnswerResponse(
            answer=result.answer,
            claims=[
                TourClaimPayload(
                    id=f"{tour_id}-qa-{index}",
                    text=claim.text,
                    refs=claim.refs,
                    status=claim.status,
                    verifier_note=claim.verifier_note,
                    retrieval_path=result.retrieval_path,
                )
                for index, claim in enumerate(result.claims)
            ],
            retrieval_path=result.retrieval_path,
        )


@dataclass(slots=True)
class LiveChunkService:
    runtime: Runtime

    async def get(self, chunk_id: str) -> ChunkPayload:
        repo_id, ref = decode_chunk_id(chunk_id)
        engine = make_engine(self.runtime.settings)
        try:
            chunks = await read_chunks([ref], engine=engine, repo_id=repo_id)
        finally:
            await engine.dispose()
        if not chunks:
            raise KeyError(chunk_id)
        chunk = chunks[0]
        return ChunkPayload(
            chunk_id=chunk_id,
            repo_id=repo_id,
            ref=chunk.ref,
            content=chunk.content,
            summary=chunk.summary,
        )


async def create_live_services() -> AppServices:
    runtime = await build_runtime()
    repos = LiveRepoService(runtime=runtime)
    tours = LiveTourService(runtime=runtime, repos=repos)
    chunks = LiveChunkService(runtime=runtime)
    return AppServices(repos=repos, tours=tours, chunks=chunks)


async def close_live_services(services: AppServices) -> None:
    repo_service = services.repos
    if isinstance(repo_service, LiveRepoService):
        for task in repo_service.tasks.values():
            if not task.done():
                task.cancel()
        await shutdown_runtime(repo_service.runtime)


async def load_snapshot(engine: AsyncEngine, snapshot_repo_id: str) -> RepoSnapshot:
    async with engine.connect() as conn:
        row = (
            await conn.execute(
                select(repos_table.c.id, repos_table.c.url, repos_table.c.head_sha).where(
                    repos_table.c.id == snapshot_repo_id
                )
            )
        ).first()
    if row is None:
        raise KeyError(snapshot_repo_id)
    return RepoSnapshot(repo_id=str(row[0]), repo_url=str(row[1]), head_sha=str(row[2]))


async def build_claims_for_symbols(
    engine: AsyncEngine,
    snapshot_repo_id: str,
    symbols: list[str],
    *,
    note: str,
    path: list[str],
) -> list[SectionClaimData]:
    refs = await resolve_symbol_refs(engine, snapshot_repo_id, symbols)
    chunks = await read_chunks(refs, engine=engine, repo_id=snapshot_repo_id)
    by_symbol = {chunk.ref.symbol or chunk.ref.file_path: chunk for chunk in chunks}
    claims: list[SectionClaimData] = []
    for symbol in symbols:
        chunk = by_symbol.get(symbol)
        if chunk is None:
            continue
        first_line = chunk.content.strip().splitlines()[0] if chunk.content.strip() else symbol
        claim = StateClaim(
            text=(
                f"`{symbol}` is worth reading early because it anchors a real code path in "
                f"`{chunk.ref.file_path}` and begins with `{first_line[:72]}`."
            ),
            refs=[chunk.ref],
            status="verified",
            verifier_note=note,
        )
        claims.append(SectionClaimData(claim=claim, retrieval_path=path))
    return claims


async def resolve_symbol_refs(
    engine: AsyncEngine, snapshot_repo_id: str, symbols: list[str]
) -> list[CodeRef]:
    if not symbols:
        return []
    async with engine.connect() as conn:
        rows = (
            await conn.execute(
                select(
                    chunks_table.c.file_path,
                    chunks_table.c.start_line,
                    chunks_table.c.end_line,
                    chunks_table.c.symbol,
                )
                .where(
                    chunks_table.c.repo_id == snapshot_repo_id,
                    chunks_table.c.symbol.in_(symbols),
                )
                .order_by(chunks_table.c.file_path, chunks_table.c.start_line)
            )
        ).all()
    by_symbol: dict[str, CodeRef] = {}
    for file_path, start_line, end_line, symbol in rows:
        key = str(symbol)
        by_symbol.setdefault(
            key,
            CodeRef(
                file_path=str(file_path),
                start_line=int(start_line),
                end_line=int(end_line),
                symbol=key,
            ),
        )
    return [by_symbol[symbol] for symbol in symbols if symbol in by_symbol]


def build_mermaid(hubs: Sequence[object]) -> str:
    lines = ["graph TD"]
    for index, hub in enumerate(hubs):
        name = getattr(hub, "symbol", f"hub{index}")
        node = name.rsplit(".", 1)[-1]
        lines.append(f'  H{index}["{node}"]')
        if index > 0:
            lines.append(f"  H0 --> H{index}")
    return "\n".join(lines)


def split_sentences(text: str) -> list[str]:
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    return sentences or [text]


def encode_chunk_id(repo_id: str, ref: CodeRef) -> str:
    payload = {
        "repo_id": repo_id,
        "file_path": ref.file_path,
        "start_line": ref.start_line,
        "end_line": ref.end_line,
        "symbol": ref.symbol,
    }
    return base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")


def decode_chunk_id(chunk_id: str) -> tuple[str, CodeRef]:
    padded = chunk_id + "=" * (-len(chunk_id) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))
        repo_id = str(payload["repo_id"])
        ref = CodeRef(
            file_path=str(payload["file_path"]),
            start_line=int(payload["start_line"]),
            end_line=int(payload["end_line"]),
            symbol=None if payload.get("symbol") is None else str(payload["symbol"]),
        )
    except (binascii.Error, KeyError, UnicodeDecodeError, ValueError, TypeError) as exc:
        raise ValueError("invalid chunk id; use a chunk id emitted by a tour or ask claim") from exc
    return repo_id, ref


async def answer_deterministically(
    *,
    engine: AsyncEngine,
    snapshot_repo_id: str,
    question: str,
    fallback_reason: str | None = None,
) -> QAResult:
    tokens = {token.lower() for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]+", question)}
    async with engine.connect() as conn:
        rows = (
            await conn.execute(
                select(
                    chunks_table.c.file_path,
                    chunks_table.c.start_line,
                    chunks_table.c.end_line,
                    chunks_table.c.symbol,
                    chunks_table.c.summary,
                    chunks_table.c.content,
                ).where(chunks_table.c.repo_id == snapshot_repo_id)
            )
        ).all()
    scored: list[tuple[int, CodeRef, str | None, str]] = []
    for file_path, start_line, end_line, symbol, summary, content in rows:
        haystack = " ".join(part for part in [str(symbol), str(summary), str(content)] if part)
        words = {token.lower() for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]+", haystack)}
        overlap = len(tokens & words)
        if overlap == 0:
            continue
        ref = CodeRef(
            file_path=str(file_path),
            start_line=int(start_line),
            end_line=int(end_line),
            symbol=str(symbol),
        )
        scored.append((overlap, ref, None if summary is None else str(summary), str(content)))
    scored.sort(key=lambda item: (-item[0], item[1].file_path, item[1].start_line))
    top = scored[:3]
    if not top:
        retrieval_path = ["deterministic_text_overlap"]
        if fallback_reason:
            retrieval_path.insert(0, f"rag_fallback:{fallback_reason[:160]}")
        return QAResult(
            question=question,
            answer="I couldn't find a strong match in the indexed snapshot yet. Try asking about a concrete symbol or file.",
            claims=[],
            objections=[],
            hops=0,
            retrieval_path=retrieval_path,
        )
    claims = [
        QAClaim(
            text=(
                f"`{ref.symbol}` in `{ref.file_path}` looks relevant because it overlaps with your question "
                f"and is summarized as {summary or 'an implementation chunk worth reading directly'}."
            ),
            refs=[ref],
            status="verified",
            verifier_note="Matched by deterministic text overlap against the indexed snapshot.",
        )
        for _, ref, summary, _ in top
    ]
    answer = "Start with " + ", ".join(f"`{claim.refs[0].symbol}`" for claim in claims) + "."
    retrieval_path = ["deterministic_text_overlap"]
    if fallback_reason:
        retrieval_path.insert(0, f"rag_fallback:{fallback_reason[:160]}")
    return QAResult(
        question=question,
        answer=answer,
        claims=claims,
        objections=[],
        hops=0,
        retrieval_path=retrieval_path,
    )


__all__ = [
    "AppServices",
    "ChunkService",
    "LiveChunkService",
    "LiveRepoService",
    "LiveTourService",
    "RepoRecord",
    "RepoService",
    "TourRecord",
    "TourService",
    "build_runtime",
    "close_live_services",
    "create_live_services",
    "decode_chunk_id",
    "encode_chunk_id",
]
