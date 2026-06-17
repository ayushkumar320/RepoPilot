"""FastAPI app for the Phase 4 API contract."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import cast

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from repopilot_api.models import (
    AskTourRequest,
    ChunkPayload,
    CreateRepoRequest,
    CreateRepoResponse,
    CreateTourRequest,
    CreateTourResponse,
    QAAnswerResponse,
    RepoStatusResponse,
)
from repopilot_api.services import AppServices, close_live_services, create_live_services
from repopilot_api.sse import format_sse_event
from repopilot_core.logging import configure_logging
from repopilot_core.settings import get_settings


def create_app(*, services: AppServices | None = None) -> FastAPI:
    configure_logging()
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[dict[str, AppServices]]:
        resolved = services or await create_live_services()
        try:
            yield {"services": resolved}
        finally:
            if services is None:
                await close_live_services(resolved)

    app = FastAPI(
        title="RepoPilot API",
        version="0.0.1",
        docs_url="/docs" if settings.repopilot_env != "production" else None,
        lifespan=lifespan,
    )
    if services is not None:
        app.state.services = services

    def get_services() -> AppServices:
        return cast(AppServices, app.state.services)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "env": settings.repopilot_env}

    @app.post("/repos", response_model=CreateRepoResponse, status_code=202)
    async def create_repo(request: CreateRepoRequest) -> CreateRepoResponse:
        record = await get_services().repos.enqueue(request.repo_url)
        return CreateRepoResponse(repo_id=record.repo_id, status=record.status)

    @app.get("/repos/{repo_id}/status", response_model=RepoStatusResponse)
    async def repo_status(repo_id: str) -> RepoStatusResponse:
        try:
            record = await get_services().repos.get(repo_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="repo not found") from exc
        return RepoStatusResponse(
            status=record.status,
            progress=record.progress,
            error=record.error,
            indexed_sha=record.indexed_sha,
            remote_sha=record.remote_sha,
            commits_behind_estimate=record.commits_behind_estimate,
        )

    @app.get("/repos/{repo_id}/first-impression")
    async def repo_first_impression(repo_id: str) -> StreamingResponse:
        async def event_generator() -> AsyncIterator[str]:
            try:
                async for event in get_services().repos.first_impression_stream(repo_id):
                    yield format_sse_event(event)
            except KeyError as exc:
                raise HTTPException(status_code=404, detail="repo not found") from exc

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    @app.post("/tours", response_model=CreateTourResponse, status_code=201)
    async def create_tour(request: CreateTourRequest) -> CreateTourResponse:
        record = await get_services().tours.create(request.repo_id, request.intent_profile)
        return CreateTourResponse(
            tour_id=record.tour_id,
            stream_url=f"/tours/{record.tour_id}/stream",
        )

    @app.get("/tours/{tour_id}/stream")
    async def stream_tour(tour_id: str) -> StreamingResponse:
        async def event_generator() -> AsyncIterator[str]:
            try:
                async for event in get_services().tours.stream(tour_id):
                    yield format_sse_event(event)
            except KeyError as exc:
                raise HTTPException(status_code=404, detail="tour not found") from exc

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    @app.post("/tours/{tour_id}/ask", response_model=QAAnswerResponse)
    async def ask_tour(tour_id: str, request: AskTourRequest) -> QAAnswerResponse:
        try:
            return await get_services().tours.ask(tour_id, request.question)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="tour not found") from exc

    @app.get("/chunks/{chunk_id}", response_model=ChunkPayload)
    async def get_chunk(chunk_id: str) -> ChunkPayload:
        try:
            return await get_services().chunks.get(chunk_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="chunk not found") from exc

    return app


app = create_app()
