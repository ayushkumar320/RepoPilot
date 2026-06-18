from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient

from repopilot_agents.state import Claim, IntentProfile
from repopilot_agents.types import CodeRef
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
from repopilot_api.services import AppServices, RepoRecord, TourRecord
from repopilot_api.sse import format_sse_comment, format_sse_event


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
    def __init__(self) -> None:
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
    return AppServices(
        repos=FakeRepoService(),
        tours=FakeTourService(),
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
