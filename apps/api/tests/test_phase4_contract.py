from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any, cast

import pytest
from httpx import ASGITransport, AsyncClient

from repopilot_agents.qa import QAResult
from repopilot_agents.state import Claim, IntentProfile
from repopilot_agents.types import CodeRef
from repopilot_agents.verifier.grounding import Claim as QAClaim
from repopilot_api import create_app
from repopilot_api.models import (
    BaseTourEvent,
    ChunkPayload,
    QAAnswerResponse,
    RepoStatus,
    RepoStatusResponse,
    TourClaimPayload,
    TourEvent,
    TourFirstImpressionEvent,
    TourSectionStartEvent,
)
from repopilot_api.services import (
    AppServices,
    LiveTourService,
    RepoNotReadyError,
    RepoRecord,
    Runtime,
    TourRecord,
    decode_chunk_id,
    encode_chunk_id,
)
from repopilot_api.sse import format_sse_comment, format_sse_event, with_heartbeats
from repopilot_core.settings import Settings


class FakeRepoService:
    def __init__(self) -> None:
        self.records: dict[str, RepoRecord] = {
            "repo-123": RepoRecord(
                repo_id="repo-123",
                repo_url="https://github.com/pallets/flask",
                status="ready",
                progress=100,
                indexed_sha="abc",
                remote_sha="abc",
                commits_behind_estimate=0,
            )
        }
        self.enqueued: list[str] = []

    async def enqueue(self, repo_url: str) -> RepoRecord:
        self.enqueued.append(repo_url)
        record = RepoRecord(repo_id="repo-new", repo_url=repo_url, status="queued")
        self.records[record.repo_id] = record
        return record

    async def get(self, repo_id: str) -> RepoRecord:
        return self.records[repo_id]

    async def first_impression_stream(self, repo_id: str) -> AsyncIterator[BaseTourEvent]:
        assert repo_id in self.records
        yield TourFirstImpressionEvent(text="Flask looks routing-heavy.")


class FakeTourService:
    def __init__(self, repo_service: FakeRepoService) -> None:
        self.repo_service = repo_service
        claim = Claim(
            text="Flask exposes a Flask app object.",
            refs=[
                CodeRef(
                    file_path="src/flask/app.py",
                    start_line=1,
                    end_line=20,
                    symbol="Flask",
                )
            ],
            status="verified",
            verifier_note="Grounded against the class definition.",
        )
        self.records: dict[str, TourRecord] = {
            "tour-123": TourRecord(
                tour_id="tour-123",
                repo_id="repo-123",
                created_at=datetime(2026, 6, 18, tzinfo=UTC),
                intent_profile=IntentProfile(
                    raw_text="Help me learn Flask",
                    modality_weights={"understand": 1.0},
                    focus_keywords=["routing"],
                ),
                snapshot_repo_id="repo-123@abc",
            )
        }
        self.ask_calls: list[tuple[str, str]] = []
        self.claim = claim

    async def create(self, repo_id: str, intent_profile: IntentProfile) -> TourRecord:
        if repo_id == "repo-indexing":
            raise RepoNotReadyError(repo_id, "indexing")
        if repo_id not in self.repo_service.records:
            raise KeyError(repo_id)
        record = TourRecord(
            tour_id="tour-new",
            repo_id=repo_id,
            created_at=datetime(2026, 6, 18, tzinfo=UTC),
            intent_profile=intent_profile,
            snapshot_repo_id="repo-123@abc",
        )
        self.records[record.tour_id] = record
        return record

    async def get(self, tour_id: str) -> TourRecord:
        return self.records[tour_id]

    async def stream(self, tour_id: str) -> AsyncIterator[BaseTourEvent]:
        assert tour_id in self.records
        yield TourSectionStartEvent(order=0, title="Entry points")

    async def ask(self, tour_id: str, question: str) -> QAAnswerResponse:
        self.ask_calls.append((tour_id, question))
        return QAAnswerResponse(
            answer="Start with the Flask class in `app.py`.",
            claims=[
                TourClaimPayload(
                    id="claim-1",
                    text=self.claim.text,
                    refs=self.claim.refs,
                    status=self.claim.status,
                    verifier_note=self.claim.verifier_note,
                    retrieval_path=["vector_search:k=8", "graph_traverse:Flask"],
                )
            ],
            retrieval_path=["vector_search:k=8", "graph_traverse:Flask"],
        )


class FakeChunkService:
    async def get(self, chunk_id: str) -> ChunkPayload:
        return ChunkPayload(
            chunk_id=chunk_id,
            repo_id="repo-123",
            ref=CodeRef(
                file_path="src/flask/app.py",
                start_line=1,
                end_line=20,
                symbol="Flask",
            ),
            content="class Flask:",
            summary="Flask application object.",
        )


@pytest.fixture
def app_services() -> AppServices:
    repos = FakeRepoService()
    return AppServices(
        repos=repos,
        tours=FakeTourService(repos),
        chunks=FakeChunkService(),
    )


@pytest.fixture
async def api_client(app_services: AppServices) -> AsyncIterator[AsyncClient]:
    app = create_app(services=app_services)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.mark.asyncio
async def test_post_repos_enqueues_indexing(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/repos",
        json={"repo_url": "https://github.com/pallets/flask"},
    )

    assert response.status_code == 202
    assert response.json() == {"repo_id": "repo-new", "status": "queued"}


@pytest.mark.asyncio
async def test_get_repo_status_returns_phase4_shape(api_client: AsyncClient) -> None:
    response = await api_client.get("/repos/repo-123/status")

    assert response.status_code == 200
    assert RepoStatusResponse.model_validate(response.json()) == RepoStatusResponse(
        status="ready",
        progress=100,
        indexed_sha="abc",
        remote_sha="abc",
        commits_behind_estimate=0,
        error=None,
    )


@pytest.mark.asyncio
async def test_post_tours_returns_stream_url(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/tours",
        json={
            "repo_id": "repo-123",
            "intent_profile": {
                "raw_text": "Help me learn Flask",
                "modality_weights": {"understand": 1.0},
            },
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "tour_id": "tour-new",
        "stream_url": "/tours/tour-new/stream",
    }


@pytest.mark.asyncio
async def test_post_tours_returns_404_for_unknown_repo(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/tours",
        json={
            "repo_id": "{{repoId}}",
            "intent_profile": {
                "raw_text": "Help me learn Flask",
                "modality_weights": {"understand": 1.0},
            },
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "repo not found"}


@pytest.mark.asyncio
async def test_post_tours_returns_409_when_repo_not_ready(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/tours",
        json={
            "repo_id": "repo-indexing",
            "intent_profile": {
                "raw_text": "Help me learn Flask",
                "modality_weights": {"understand": 1.0},
            },
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": {
            "code": "REPO_NOT_READY",
            "message": "repo must finish indexing before a tour can be created",
            "repo_id": "repo-indexing",
            "status": "indexing",
        }
    }


@pytest.mark.asyncio
async def test_stream_endpoint_emits_sse_events(api_client: AsyncClient) -> None:
    async with api_client.stream("GET", "/tours/tour-123/stream") as response:
        body = ""
        async for chunk in response.aiter_text():
            body += chunk
            if "section_start" in body:
                break

    assert response.status_code == 200
    assert "event: section_start" in body
    assert '"v":1' in body


@pytest.mark.asyncio
async def test_first_impression_endpoint_emits_sse_events(api_client: AsyncClient) -> None:
    async with api_client.stream("GET", "/repos/repo-123/first-impression") as response:
        body = ""
        async for chunk in response.aiter_text():
            body += chunk
            if "first_impression" in body:
                break

    assert response.status_code == 200
    assert "event: first_impression" in body


@pytest.mark.asyncio
async def test_post_tour_ask_returns_answer_and_claims(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/tours/tour-123/ask",
        json={"question": "Where should I start?"},
    )

    assert response.status_code == 200
    payload = QAAnswerResponse.model_validate(response.json())
    assert payload.claims[0].refs[0].file_path == "src/flask/app.py"
    assert payload.retrieval_path == ["vector_search:k=8", "graph_traverse:Flask"]


@pytest.mark.asyncio
async def test_get_chunk_returns_code_payload(api_client: AsyncClient) -> None:
    response = await api_client.get("/chunks/chunk-123")

    assert response.status_code == 200
    payload = ChunkPayload.model_validate(response.json())
    assert payload.ref.symbol == "Flask"
    assert payload.content == "class Flask:"


def test_sse_event_round_trips_through_parser() -> None:
    event = TourSectionStartEvent(order=1, title="Request flow")

    frame = format_sse_event(event)
    parsed = TourEvent.parse_sse_frame(frame)

    assert parsed == event
    assert parsed.event == "section_start"


def test_sse_comment_frame_is_valid_heartbeat() -> None:
    frame = format_sse_comment()

    assert frame == ": heartbeat\n\n"


def test_deterministic_qa_result_accepts_grounding_claims() -> None:
    ref = CodeRef(file_path="src/app.py", start_line=1, end_line=2, symbol="app")
    claim = QAClaim(text="`app` is relevant.", refs=[ref], status="verified")

    result = QAResult(
        question="Where do I start?",
        answer="Start with `app`.",
        claims=[claim],
        objections=[],
        retrieval_path=["deterministic_text_overlap"],
    )

    assert result.claims[0].refs[0].file_path == "src/app.py"


@pytest.mark.asyncio
async def test_live_tour_ask_uses_rag_answer_question(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, str]] = []

    async def fake_answer_question(
        question: str,
        *,
        engine: Any,
        provider: Any,
        repo_id: str,
        k: int = 8,
        max_hops: int = 3,
    ) -> QAResult:
        calls.append({"question": question, "repo_id": repo_id, "k": str(k)})
        ref = CodeRef(file_path="app.py", start_line=1, end_line=20, symbol="app")
        return QAResult(
            question=question,
            answer="RAG used vector search over indexed chunks.",
            claims=[QAClaim(text="The answer came from retrieved chunks.", refs=[ref])],
            objections=[],
            retrieval_path=["vector_search:k=8:hits=1"],
            hops=max_hops,
        )

    monkeypatch.setattr("repopilot_api.services.answer_question", fake_answer_question)
    repos = FakeRepoService()
    service = LiveTourService(
        runtime=Runtime(settings=Settings(), provider=cast(Any, object())),
        repos=repos,
    )
    service.records["tour-rag"] = TourRecord(
        tour_id="tour-rag",
        repo_id="repo-123",
        created_at=datetime(2026, 6, 18, tzinfo=UTC),
        intent_profile=IntentProfile(raw_text="Am I using RAG?"),
        snapshot_repo_id="repo-123@abc",
    )

    response = await service.ask("tour-rag", "is rag getting used here?")

    assert calls == [
        {
            "question": "is rag getting used here?",
            "repo_id": "repo-123@abc",
            "k": "8",
        }
    ]
    assert response.retrieval_path == ["vector_search:k=8:hits=1"]


def test_chunk_id_codec_accepts_browser_base64url_without_padding() -> None:
    ref = CodeRef(file_path="src/app.py", start_line=1, end_line=2, symbol="app")
    chunk_id = encode_chunk_id("owner/repo@abc", ref).rstrip("=")

    repo_id, decoded = decode_chunk_id(chunk_id)

    assert repo_id == "owner/repo@abc"
    assert decoded == ref


def test_chunk_id_decode_rejects_placeholder() -> None:
    with pytest.raises(ValueError, match="invalid chunk id"):
        decode_chunk_id("chunk-123")


@pytest.mark.asyncio
async def test_with_heartbeats_keeps_idle_stream_alive_until_event_arrives() -> None:
    async def delayed_event() -> AsyncIterator[BaseTourEvent]:
        await asyncio.sleep(0.05)
        yield TourSectionStartEvent(order=0, title="Delayed section")

    stream = with_heartbeats(delayed_event(), interval_seconds=0.01)

    frames: list[str] = []
    for _ in range(8):
        frame = await anext(stream)
        frames.append(frame)
        if "event: section_start" in frame:
            break

    assert frames[:2] == [": heartbeat\n\n", ": heartbeat\n\n"]
    assert any("event: section_start" in frame for frame in frames)


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("queued", True),
        ("indexing", True),
        ("ready", True),
        ("error", True),
        ("stale", True),
    ],
)
def test_repo_status_enum_covers_phase4_contract(status: RepoStatus, expected: bool) -> None:
    payload = RepoStatusResponse(status=status)
    assert isinstance(payload, RepoStatusResponse) is expected
