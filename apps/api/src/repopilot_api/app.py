"""FastAPI app for the Phase 4 API contract."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import cast
from uuid import uuid4

import structlog
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from repopilot_agents.qa import TokenSink
from repopilot_agents.rerank.cross_encoder import shared_reranker
from repopilot_agents.state import IntentProfile
from repopilot_api.access import AccountUsage, AllowanceExceededError
from repopilot_api.models import (
    AccountUsageResponse,
    AnswerDoneEvent,
    AnswerTokenEvent,
    AppendTourMessageRequest,
    AppendTourMessageResponse,
    AskRequest,
    BaseTourEvent,
    ChunkPayload,
    ClaimPayload,
    CreateRepoRequest,
    CreateRepoResponse,
    CreateTourRequest,
    CreateTourResponse,
    GraphModulesResponse,
    GraphNeighboursResponse,
    IdentityRequest,
    IdentityResponse,
    IntentDraftRequest,
    ProviderCredentialsRequest,
    QAAnswerResponse,
    RepoStatusResponse,
    TourDetailResponse,
    TourErrorEvent,
    TourMessagePayload,
    TourSummaryResponse,
)
from repopilot_api.services import (
    MAX_MODULES,
    MAX_NEIGHBOURS,
    AppServices,
    RepoNotReadyError,
    close_live_services,
    create_live_services,
    repo_slug,
)
from repopilot_api.sse import with_heartbeats
from repopilot_api.tours import Identity
from repopilot_core.logging import configure_logging
from repopilot_core.settings import get_settings

log = structlog.get_logger(__name__)


def create_app(*, services: AppServices | None = None) -> FastAPI:
    configure_logging()
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[dict[str, AppServices]]:
        resolved = services or await create_live_services()
        app.state.services = resolved
        # Pull the cross-encoder into memory in the background so the first
        # question doesn't wait on a ~91 MB cold download mid-request.
        warm = asyncio.create_task(
            asyncio.to_thread(shared_reranker(settings.rerank_model).warm),
            name="rerank-warmup",
        )
        app.state.rerank_warm = warm
        try:
            yield {"services": resolved}
        finally:
            warm.cancel()
            try:
                await warm
            except asyncio.CancelledError:
                pass
            except Exception:
                log.exception("rerank.warmup_failed")
            if services is None:
                await close_live_services(resolved)

    app = FastAPI(
        title="RepoPilot API",
        version="0.0.1",
        docs_url="/docs" if settings.repopilot_env != "production" else None,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.repopilot_web_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    if services is not None:
        app.state.services = services

    def get_services() -> AppServices:
        return cast(AppServices, app.state.services)

    async def rerank_ready() -> None:
        """Hold a question until the startup cross-encoder warm-up finishes.

        Without this the first question races the ~91 MB ONNX load and pays it
        inside the request, which the web proxy sees as a hang. Waiting here is
        the same wall-clock, but it happens before we reserve usage or spend a
        provider call. A failed warm-up is not fatal — the lazy load inside
        ``score`` retries — so the error is logged and the question proceeds.
        """
        warm = getattr(app.state, "rerank_warm", None)
        if warm is None or warm.done():
            return
        try:
            await asyncio.shield(warm)
        except Exception:
            log.exception("rerank.warmup_failed")

    session_cookie = "repopilot_session"

    def signed_session(session_id: str) -> str:
        signature = hmac.new(
            settings.repopilot_session_secret.encode(),
            session_id.encode(),
            hashlib.sha256,
        ).hexdigest()
        return f"{session_id}.{signature}"

    def resolve_session(request: Request, response: Response) -> str:
        raw = request.cookies.get(session_cookie, "")
        session_id, separator, signature = raw.partition(".")
        expected = signed_session(session_id).partition(".")[2] if session_id else ""
        if not separator or not signature or not hmac.compare_digest(signature, expected):
            session_id = str(uuid4())
            response.set_cookie(
                session_cookie,
                signed_session(session_id),
                httponly=True,
                secure=settings.repopilot_session_cookie_secure,
                samesite="none" if settings.repopilot_session_cookie_secure else "lax",
                max_age=60 * 60 * 24 * 30,
                path="/",
            )
        return session_id

    def usage_response(usage: AccountUsage) -> AccountUsageResponse:
        return AccountUsageResponse(
            free_repositories_remaining=usage.free_repositories_remaining,
            provider_connected=usage.provider_connected,
            groq_connected=usage.groq_connected,
            huggingface_connected=usage.huggingface_connected,
        )

    def allowance_error(exc: AllowanceExceededError) -> HTTPException:
        return HTTPException(
            status_code=402,
            detail={
                "code": "PROVIDER_KEY_REQUIRED",
                "action": exc.action,
                "message": (
                    "Your free repository is used. Connect your Groq key to analyze another."
                ),
            },
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "env": settings.repopilot_env}

    @app.get("/account/usage", response_model=AccountUsageResponse)
    async def account_usage(
        session_id: str = Depends(resolve_session),
    ) -> AccountUsageResponse:
        return usage_response(await get_services().access.status(session_id))

    @app.post("/account/provider", response_model=AccountUsageResponse)
    async def connect_provider(
        request: ProviderCredentialsRequest,
        session_id: str = Depends(resolve_session),
    ) -> AccountUsageResponse:
        try:
            usage = await get_services().access.connect_provider(
                session_id,
                groq_api_key=request.groq_api_key.get_secret_value(),
                huggingface_api_key=(
                    request.huggingface_api_key.get_secret_value()
                    if request.huggingface_api_key is not None
                    else None
                ),
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return usage_response(usage)

    @app.delete("/account/provider", response_model=AccountUsageResponse)
    async def disconnect_provider(
        session_id: str = Depends(resolve_session),
    ) -> AccountUsageResponse:
        return usage_response(await get_services().access.disconnect_provider(session_id))

    @app.post("/repos", response_model=CreateRepoResponse, status_code=202)
    async def create_repo(
        request: CreateRepoRequest,
        session_id: str = Depends(resolve_session),
    ) -> CreateRepoResponse:
        try:
            normalized_repo_id = repo_slug(request.repo_url)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        try:
            reservation = await get_services().access.reserve_repository(
                session_id, normalized_repo_id
            )
        except AllowanceExceededError as exc:
            raise allowance_error(exc) from exc
        provider = (
            await get_services().access.provider_for(session_id)
            if reservation.source == "user"
            else None
        )
        try:
            record = await get_services().repos.enqueue(request.repo_url, provider=provider)
        except Exception:
            await get_services().access.release(reservation)
            raise
        await get_services().access.complete(reservation)
        return CreateRepoResponse(repo_id=record.repo_id, status=record.status)

    @app.get("/repos/{repo_id:path}/status", response_model=RepoStatusResponse)
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

    @app.get("/repos/{repo_id:path}/first-impression")
    async def repo_first_impression(repo_id: str) -> StreamingResponse:
        async def event_source() -> AsyncIterator[BaseTourEvent]:
            # Failures ride the stream, as they do on /ask/stream: by the time
            # this generator runs the 200 and the SSE headers are already sent,
            # so a raised HTTPException reaches nobody and the reader just sees
            # the stream stop.
            try:
                async for event in get_services().repos.first_impression_stream(repo_id):
                    yield event
            except KeyError:
                yield TourErrorEvent(code="REPO_NOT_FOUND", message="repo not found")
            except Exception:
                log.exception("repo.first_impression_failed", repo_id=repo_id)
                yield TourErrorEvent(
                    code="FIRST_IMPRESSION_FAILED",
                    message="RepoPilot could not read this repository right now.",
                )

        return StreamingResponse(
            with_heartbeats(event_source()),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    @app.post("/intent", response_model=IntentProfile)
    async def draft_intent(
        request: IntentDraftRequest,
        session_id: str = Depends(resolve_session),
    ) -> IntentProfile:
        """Turn a free-text persona description into a structured profile.

        Not metered: this is one small call that makes the *next* question
        better, and charging for it would push users toward the presets for
        the wrong reason. Falls back to a raw_text-only profile internally,
        so it never fails the caller.
        """
        provider = await get_services().access.provider_for(session_id)
        return await get_services().qa.draft_intent(request.raw_text, provider=provider)

    async def answer_metered(
        repo_id: str,
        request: AskRequest,
        session_id: str,
        on_token: TokenSink | None = None,
    ) -> QAAnswerResponse:
        """Reserve the question, answer it, and settle the reservation.

        Shared by the buffered and streaming ask routes so metering and the
        error contract cannot drift apart between them.
        """
        await rerank_ready()
        reservation = await get_services().access.reserve_question(session_id, repo_id)
        provider = (
            await get_services().access.provider_for(session_id)
            if reservation.source == "user"
            else None
        )
        try:
            answer = await get_services().qa.ask(
                repo_id,
                request.question,
                intent_profile=request.intent_profile,
                provider=provider,
                on_token=on_token,
            )
        except RepoNotReadyError as exc:
            await get_services().access.release(reservation)
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "REPO_NOT_READY",
                    "message": "repo must finish indexing before it can answer questions",
                    "repo_id": exc.repo_id,
                    "status": exc.status,
                },
            ) from exc
        except KeyError as exc:
            await get_services().access.release(reservation)
            raise HTTPException(status_code=404, detail="repo not found") from exc
        except Exception as exc:
            await get_services().access.release(reservation)
            log.exception("repo.ask_failed", repo_id=repo_id)
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "QA_FAILED",
                    "message": (
                        "RepoPilot could not answer that question right now. "
                        "Try again, or ask about a concrete symbol or file."
                    ),
                },
            ) from exc
        await get_services().access.complete(reservation)
        return answer

    @app.post("/repos/{repo_id:path}/ask", response_model=QAAnswerResponse)
    async def ask_repo(
        repo_id: str,
        request: AskRequest,
        session_id: str = Depends(resolve_session),
    ) -> QAAnswerResponse:
        return await answer_metered(repo_id, request, session_id)

    @app.post("/repos/{repo_id:path}/ask/stream")
    async def ask_repo_stream(
        repo_id: str,
        request: AskRequest,
        session_id: str = Depends(resolve_session),
    ) -> StreamingResponse:
        """The same answer as ``/ask``, delivered as it is generated.

        Errors ride the stream as an ``error`` event rather than a status code:
        the response headers are long gone by the time the model fails.
        """

        async def event_source() -> AsyncIterator[BaseTourEvent]:
            queue: asyncio.Queue[BaseTourEvent | None] = asyncio.Queue()

            async def on_token(text: str) -> None:
                await queue.put(AnswerTokenEvent(text=text))

            async def run() -> None:
                try:
                    answer = await answer_metered(repo_id, request, session_id, on_token=on_token)
                    await queue.put(AnswerDoneEvent(answer=answer))
                except HTTPException as exc:
                    # The buffered route's structured detail ({code, message})
                    # carried over verbatim, so both routes fail the same way.
                    detail: object = exc.detail
                    if isinstance(detail, dict):
                        code = str(detail.get("code", "ASK_FAILED"))
                        message = str(detail.get("message", detail))
                    else:
                        code, message = "ASK_FAILED", str(detail)
                    await queue.put(TourErrorEvent(code=code, message=message))
                except Exception:
                    log.exception("repo.ask_stream_failed", repo_id=repo_id)
                    await queue.put(
                        TourErrorEvent(
                            code="QA_FAILED",
                            message="RepoPilot could not answer that question right now.",
                        )
                    )
                finally:
                    await queue.put(None)

            task = asyncio.create_task(run())
            try:
                while (event := await queue.get()) is not None:
                    yield event
            finally:
                # The reader closed the tab: stop paying for the answer.
                task.cancel()

        return StreamingResponse(
            with_heartbeats(event_source()),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    @app.get("/me", response_model=IdentityResponse)
    async def read_identity(session_id: str = Depends(resolve_session)) -> IdentityResponse:
        identity = await get_services().tours.identity(session_id)
        return IdentityResponse(
            session_id=identity.session_id,
            authenticated=identity.provider is not None,
            provider=identity.provider,
            provider_account_id=identity.provider_account_id,
            display_name=identity.display_name,
            email=identity.email,
            avatar_url=identity.avatar_url,
        )

    @app.put("/me", response_model=IdentityResponse)
    async def write_identity(
        request: IdentityRequest,
        session_id: str = Depends(resolve_session),
    ) -> IdentityResponse:
        """Record who this session belongs to after the web app signs them in.

        The claim is only as trustworthy as the signed cookie that carries it,
        which is exactly the trust level the rest of the product already runs
        on: the cookie *is* the identity, and this just labels it for display.
        """
        identity = await get_services().tours.set_identity(
            session_id,
            Identity(
                session_id=session_id,
                provider=request.provider,
                provider_account_id=request.provider_account_id,
                display_name=request.display_name,
                email=request.email,
                avatar_url=request.avatar_url,
            ),
        )
        return IdentityResponse(
            session_id=identity.session_id,
            authenticated=True,
            provider=identity.provider,
            provider_account_id=identity.provider_account_id,
            display_name=identity.display_name,
            email=identity.email,
            avatar_url=identity.avatar_url,
        )

    @app.post("/tours", response_model=CreateTourResponse, status_code=201)
    async def create_tour(
        request: CreateTourRequest,
        session_id: str = Depends(resolve_session),
    ) -> CreateTourResponse:
        snapshot_repo_id: str | None = None
        try:
            snapshot_repo_id = (await get_services().repos.get(request.repo_id)).indexed_repo_id
        except KeyError:
            # A tour may be started before indexing finishes; the snapshot id is
            # a convenience, not the identity of the tour.
            snapshot_repo_id = None
        tour_id = await get_services().tours.create_tour(
            session_id,
            repo_id=request.repo_id,
            snapshot_repo_id=snapshot_repo_id,
            intent_profile=(
                None if request.intent_profile is None else request.intent_profile.model_dump()
            ),
            title=request.title,
        )
        return CreateTourResponse(tour_id=tour_id)

    @app.get("/tours", response_model=list[TourSummaryResponse])
    async def list_tours(
        session_id: str = Depends(resolve_session),
    ) -> list[TourSummaryResponse]:
        return [
            TourSummaryResponse(
                tour_id=tour.tour_id,
                repo_id=tour.repo_id,
                title=tour.title,
                created_at=tour.created_at,
                updated_at=tour.updated_at,
                message_count=tour.message_count,
            )
            for tour in await get_services().tours.list_tours(session_id)
        ]

    @app.get("/tours/{tour_id}", response_model=TourDetailResponse)
    async def get_tour(
        tour_id: str,
        session_id: str = Depends(resolve_session),
    ) -> TourDetailResponse:
        tour = await get_services().tours.get_tour(session_id, tour_id)
        if tour is None:
            raise HTTPException(status_code=404, detail="tour not found")
        return TourDetailResponse(
            tour_id=tour.tour_id,
            repo_id=tour.repo_id,
            snapshot_repo_id=tour.snapshot_repo_id,
            title=tour.title,
            intent_profile=(
                IntentProfile.model_validate(tour.intent_profile) if tour.intent_profile else None
            ),
            created_at=tour.created_at,
            updated_at=tour.updated_at,
            message_count=len(tour.messages),
            messages=[
                TourMessagePayload(
                    ordinal=message.ordinal,
                    question=message.question,
                    answer=message.answer,
                    claims=[ClaimPayload.model_validate(claim) for claim in message.claims],
                    persona_label=message.persona_label,
                )
                for message in tour.messages
            ],
        )

    @app.get(
        "/repos/{repo_id:path}/graph/neighbours",
        response_model=GraphNeighboursResponse,
    )
    async def repo_graph_neighbours(
        repo_id: str,
        symbol: str = Query(min_length=1, max_length=500),
        limit: int = Query(default=60, ge=1, le=MAX_NEIGHBOURS),
        session_id: str = Depends(resolve_session),
    ) -> GraphNeighboursResponse:
        """Symbols adjacent to ``symbol`` in the snapshot's code graph.

        Not metered: this reads data the AST already produced and runs no
        model, so charging for it would make people avoid the one surface that
        shows where a claim's code sits.
        """
        graph = get_services().graph
        if graph is None:
            raise HTTPException(status_code=404, detail="graph view is not configured")
        try:
            return await graph.neighbours(repo_id, symbol, limit=limit)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="repo not found") from exc

    @app.get(
        "/repos/{repo_id:path}/graph/modules",
        response_model=GraphModulesResponse,
    )
    async def repo_graph_modules(
        repo_id: str,
        limit: int = Query(default=60, ge=1, le=MAX_MODULES),
        session_id: str = Depends(resolve_session),
    ) -> GraphModulesResponse:
        """The snapshot's intra-repo module dependency map.

        Not metered, for the same reason as the neighbourhood read: it runs no
        model over data the AST already produced.
        """
        graph = get_services().graph
        if graph is None:
            raise HTTPException(status_code=404, detail="graph view is not configured")
        try:
            return await graph.modules(repo_id, limit=limit)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="repo not found") from exc

    @app.post(
        "/tours/{tour_id}/messages",
        response_model=AppendTourMessageResponse,
        status_code=201,
    )
    async def append_tour_message(
        tour_id: str,
        request: AppendTourMessageRequest,
        session_id: str = Depends(resolve_session),
    ) -> AppendTourMessageResponse:
        ordinal = await get_services().tours.append_message(
            session_id,
            tour_id,
            question=request.question,
            answer=request.answer,
            claims=[claim.model_dump() for claim in request.claims],
            persona_label=request.persona_label,
        )
        if ordinal is None:
            raise HTTPException(status_code=404, detail="tour not found")
        return AppendTourMessageResponse(ordinal=ordinal)

    @app.delete("/tours/{tour_id}", status_code=204)
    async def delete_tour(
        tour_id: str,
        session_id: str = Depends(resolve_session),
    ) -> Response:
        if not await get_services().tours.delete_tour(session_id, tour_id):
            raise HTTPException(status_code=404, detail="tour not found")
        return Response(status_code=204)

    @app.get("/chunks/{chunk_id:path}", response_model=ChunkPayload)
    async def get_chunk(chunk_id: str) -> ChunkPayload:
        try:
            return await get_services().chunks.get(chunk_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="chunk not found") from exc

    if settings.repopilot_env != "production":

        @app.get("/__dev/sse-idle")
        async def dev_sse_idle() -> StreamingResponse:
            async def idle_source() -> AsyncIterator[BaseTourEvent]:
                event: BaseTourEvent = await asyncio.Future()
                yield event

            return StreamingResponse(
                with_heartbeats(idle_source(), interval_seconds=5.0),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
            )

    return app


app = create_app()
