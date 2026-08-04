from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
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
    ClaimPayload,
    QAAnswerResponse,
    RepoStatus,
    RepoStatusResponse,
    TourEvent,
    TourFirstImpressionEvent,
)
from repopilot_api.services import (
    AppServices,
    LiveQAService,
    RepoNotReadyError,
    RepoRecord,
    Runtime,
    decode_chunk_id,
    encode_chunk_id,
)
from repopilot_api.sse import format_sse_comment, format_sse_event, with_heartbeats
from repopilot_core.settings import Settings

CONTRIBUTOR_PROFILE = {
    "raw_text": "I want to contribute to this project",
    "audience_framing": "a first-time outside contributor",
    "modality_weights": {"change": 1.0},
    "focus_keywords": ["tests"],
    "output_shape_preference": "ranked_list",
}


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
                indexed_repo_id="repo-123@abc",
            ),
            "repo-indexing": RepoRecord(
                repo_id="repo-indexing",
                repo_url="https://github.com/pallets/click",
                status="indexing",
                progress=40,
            ),
        }
        self.enqueued: list[str] = []

    async def enqueue(self, repo_url: str, *, provider: Any = None) -> RepoRecord:
        del provider
        self.enqueued.append(repo_url)
        record = RepoRecord(repo_id="repo-new", repo_url=repo_url, status="queued")
        self.records[record.repo_id] = record
        return record

    async def get(self, repo_id: str) -> RepoRecord:
        return self.records[repo_id]

    async def first_impression_stream(self, repo_id: str) -> AsyncIterator[BaseTourEvent]:
        assert repo_id in self.records
        yield TourFirstImpressionEvent(text="Flask looks routing-heavy.")


class FakeQAService:
    """Records the persona each question was asked under."""

    def __init__(self, repo_service: FakeRepoService) -> None:
        self.repo_service = repo_service
        self.claim = Claim(
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
        self.ask_calls: list[tuple[str, str, str | None]] = []
        self.drafted: list[str] = []

    async def ask(
        self,
        repo_id: str,
        question: str,
        *,
        intent_profile: IntentProfile | None = None,
        provider: Any = None,
    ) -> QAAnswerResponse:
        del provider
        if repo_id not in self.repo_service.records:
            raise KeyError(repo_id)
        record = self.repo_service.records[repo_id]
        if record.indexed_repo_id is None:
            raise RepoNotReadyError(repo_id, record.status)
        framing = intent_profile.audience_framing if intent_profile else None
        self.ask_calls.append((repo_id, question, framing))
        if question == "explode":
            raise RuntimeError("qa exploded")
        return QAAnswerResponse(
            answer="Start with the Flask class in `app.py`.",
            claims=[
                ClaimPayload(
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

    async def draft_intent(self, raw_text: str, *, provider: Any = None) -> IntentProfile:
        del provider
        self.drafted.append(raw_text)
        return IntentProfile(raw_text=raw_text, audience_framing="a migration-guide author")


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
        qa=FakeQAService(repos),
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
async def test_get_repo_status_returns_expected_shape(api_client: AsyncClient) -> None:
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
async def test_no_tour_endpoints_remain(api_client: AsyncClient) -> None:
    """The create-then-start flow is gone; nothing should answer on /tours."""
    create = await api_client.post("/tours", json={"repo_id": "repo-123"})
    stream = await api_client.get("/tours/tour-123/stream")
    ask = await api_client.post("/tours/tour-123/ask", json={"question": "hi"})

    assert create.status_code == 404
    assert stream.status_code == 404
    assert ask.status_code == 404


@pytest.mark.asyncio
async def test_ask_forwards_the_persona_to_the_qa_service(
    api_client: AsyncClient, app_services: AppServices
) -> None:
    response = await api_client.post(
        "/repos/repo-123/ask",
        json={"question": "Where should I start?", "intent_profile": CONTRIBUTOR_PROFILE},
    )

    assert response.status_code == 200
    payload = QAAnswerResponse.model_validate(response.json())
    assert payload.claims[0].refs[0].file_path == "src/flask/app.py"
    assert payload.retrieval_path == ["vector_search:k=8", "graph_traverse:Flask"]

    qa = cast(FakeQAService, app_services.qa)
    assert qa.ask_calls == [
        ("repo-123", "Where should I start?", "a first-time outside contributor")
    ]


@pytest.mark.asyncio
async def test_ask_without_a_persona_is_allowed(
    api_client: AsyncClient, app_services: AppServices
) -> None:
    response = await api_client.post(
        "/repos/repo-123/ask",
        json={"question": "Where should I start?"},
    )

    assert response.status_code == 200
    qa = cast(FakeQAService, app_services.qa)
    assert qa.ask_calls == [("repo-123", "Where should I start?", None)]


@pytest.mark.asyncio
async def test_ask_returns_409_when_repo_is_still_indexing(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/repos/repo-indexing/ask",
        json={"question": "Where should I start?"},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "REPO_NOT_READY"


@pytest.mark.asyncio
async def test_ask_returns_404_for_unknown_repo(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/repos/nope/ask",
        json={"question": "Where should I start?"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_ask_failure_returns_structured_503(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/repos/repo-123/ask",
        json={"question": "explode"},
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "QA_FAILED"


@pytest.mark.asyncio
async def test_intent_endpoint_structures_free_text(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/intent",
        json={"raw_text": "I'm writing a migration guide and need the breaking changes"},
    )

    assert response.status_code == 200
    profile = IntentProfile.model_validate(response.json())
    assert profile.audience_framing == "a migration-guide author"


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
async def test_account_starts_with_one_repo_and_five_questions(api_client: AsyncClient) -> None:
    response = await api_client.get("/account/usage")

    assert response.status_code == 200
    assert response.json() == {
        "free_repositories_remaining": 1,
        "free_questions_remaining": 5,
        "provider_connected": False,
        "groq_connected": False,
        "huggingface_connected": False,
        "credential_storage": "session_only",
    }


@pytest.mark.asyncio
async def test_sixth_question_requires_user_provider(api_client: AsyncClient) -> None:
    for index in range(5):
        response = await api_client.post(
            "/repos/repo-123/ask",
            json={"question": f"Question {index}?"},
        )
        assert response.status_code == 200

    response = await api_client.post(
        "/repos/repo-123/ask",
        json={"question": "Question six?"},
    )

    assert response.status_code == 402
    assert response.json()["detail"]["code"] == "PROVIDER_KEY_REQUIRED"


@pytest.mark.asyncio
async def test_connected_provider_continues_after_free_questions(api_client: AsyncClient) -> None:
    for index in range(5):
        await api_client.post(
            "/repos/repo-123/ask",
            json={"question": f"Question {index}?"},
        )

    connected = await api_client.post(
        "/account/provider",
        json={
            "groq_api_key": "gsk_test_key_long_enough",
            "huggingface_api_key": "hf_test_key",
        },
    )
    response = await api_client.post(
        "/repos/repo-123/ask",
        json={"question": "Question six?"},
    )

    assert connected.status_code == 200
    assert connected.json()["provider_connected"] is True
    assert "gsk_test_key_long_enough" not in connected.text
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_chunk_returns_code_payload(api_client: AsyncClient) -> None:
    response = await api_client.get("/chunks/chunk-123")

    assert response.status_code == 200
    payload = ChunkPayload.model_validate(response.json())
    assert payload.ref.symbol == "Flask"
    assert payload.content == "class Flask:"


def test_sse_event_round_trips_through_parser() -> None:
    event = TourFirstImpressionEvent(text="Flask looks routing-heavy.")

    frame = format_sse_event(event)
    parsed = TourEvent.parse_sse_frame(frame)

    assert parsed == event
    assert parsed.event == "first_impression"


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
async def test_live_qa_ask_passes_persona_into_answer_question(
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
        use_compress: bool = True,
        retry_429_attempts: int | None = None,
        intent_profile: IntentProfile | None = None,
    ) -> QAResult:
        calls.append(
            {
                "question": question,
                "repo_id": repo_id,
                "k": str(k),
                "use_compress": str(use_compress),
                "retry_429_attempts": str(retry_429_attempts),
                "audience": str(intent_profile.audience_framing if intent_profile else None),
            }
        )
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
    service = LiveQAService(
        runtime=Runtime(settings=Settings(), provider=cast(Any, object())),
        repos=cast(Any, repos),
    )

    response = await service.ask(
        "repo-123",
        "is rag getting used here?",
        intent_profile=IntentProfile(
            raw_text="Am I using RAG?", audience_framing="a competing product strategist"
        ),
    )

    assert calls == [
        {
            "question": "is rag getting used here?",
            "repo_id": "repo-123@abc",
            "k": "8",
            "use_compress": "False",
            "retry_429_attempts": "2",
            "audience": "a competing product strategist",
        }
    ]
    assert response.retrieval_path == ["vector_search:k=8:hits=1"]


@pytest.mark.asyncio
async def test_live_qa_ask_rejects_unindexed_repo() -> None:
    repos = FakeRepoService()
    service = LiveQAService(
        runtime=Runtime(settings=Settings(), provider=cast(Any, object())),
        repos=cast(Any, repos),
    )

    with pytest.raises(RepoNotReadyError):
        await service.ask("repo-indexing", "anything?")


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
        yield TourFirstImpressionEvent(text="Delayed impression")

    stream = with_heartbeats(delayed_event(), interval_seconds=0.01)

    frames: list[str] = []
    for _ in range(8):
        frame = await anext(stream)
        frames.append(frame)
        if "event: first_impression" in frame:
            break

    assert frames[:2] == [": heartbeat\n\n", ": heartbeat\n\n"]
    assert any("event: first_impression" in frame for frame in frames)


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
def test_repo_status_enum_covers_contract(status: RepoStatus, expected: bool) -> None:
    payload = RepoStatusResponse(status=status)
    assert isinstance(payload, RepoStatusResponse) is expected
