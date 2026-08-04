"""API contracts and SSE event models.

The tour entity is gone: a repository plus an ``IntentProfile`` (the reader's
persona) is everything a question needs, and the persona travels with each
``/repos/{repo_id}/ask`` call rather than being frozen into a server-side
record. What remains here is the repo lifecycle, the ask contract, and the
first-impression stream.
"""

from __future__ import annotations

import json
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, SecretStr, TypeAdapter

from repopilot_agents.state import ClaimStatus, IntentProfile
from repopilot_agents.types import CodeRef

RepoStatus = Literal["queued", "indexing", "ready", "error", "stale"]


class CreateRepoRequest(BaseModel):
    repo_url: str = Field(min_length=1)


class CreateRepoResponse(BaseModel):
    repo_id: str = Field(min_length=1)
    status: RepoStatus


class RepoStatusResponse(BaseModel):
    status: RepoStatus
    progress: int | None = Field(default=None, ge=0, le=100)
    error: str | None = None
    indexed_sha: str | None = None
    remote_sha: str | None = None
    commits_behind_estimate: int | None = Field(default=None, ge=0)


class AskRequest(BaseModel):
    """A question plus the persona it should be answered for.

    ``intent_profile`` is optional so the endpoint still works for a caller
    that has no persona (scripts, evals); omitting it yields the neutral,
    pre-persona answer prompt.
    """

    question: str = Field(min_length=1)
    intent_profile: IntentProfile | None = None


class IntentDraftRequest(BaseModel):
    """Free-text persona description to be structured by the intent profiler."""

    raw_text: str = Field(min_length=1, max_length=1000)


class ProviderCredentialsRequest(BaseModel):
    groq_api_key: SecretStr
    huggingface_api_key: SecretStr | None = None


class AccountUsageResponse(BaseModel):
    free_repositories_remaining: int = Field(ge=0)
    free_questions_remaining: int = Field(ge=0)
    provider_connected: bool
    groq_connected: bool
    huggingface_connected: bool
    credential_storage: Literal["session_only"] = "session_only"


class ClaimPayload(BaseModel):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    refs: list[CodeRef] = Field(min_length=1)
    status: ClaimStatus
    verifier_note: str | None = None
    retrieval_path: list[str] = Field(default_factory=list)


class QAAnswerResponse(BaseModel):
    answer: str = Field(min_length=1)
    claims: list[ClaimPayload] = Field(default_factory=list)
    retrieval_path: list[str] = Field(default_factory=list)


class ChunkPayload(BaseModel):
    chunk_id: str = Field(min_length=1)
    repo_id: str = Field(min_length=1)
    ref: CodeRef
    content: str
    summary: str | None = None


class BaseTourEvent(BaseModel):
    v: Literal[1] = 1
    event: str


class TourFirstImpressionEvent(BaseTourEvent):
    event: Literal["first_impression"] = "first_impression"
    text: str = Field(min_length=1)


class TourDoneEvent(BaseTourEvent):
    event: Literal["done"] = "done"


class TourErrorEvent(BaseTourEvent):
    event: Literal["error"] = "error"
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)


TourEventType = Annotated[
    TourFirstImpressionEvent | TourDoneEvent | TourErrorEvent,
    Field(discriminator="event"),
]


class TourEvent:
    _adapter: TypeAdapter[TourEventType] = TypeAdapter(TourEventType)

    @staticmethod
    def parse_sse_frame(frame: str) -> TourEventType:
        event_name: str | None = None
        data_lines: list[str] = []
        for line in frame.strip().splitlines():
            if line.startswith("event:"):
                event_name = line.removeprefix("event:").strip()
            elif line.startswith("data:"):
                data_lines.append(line.removeprefix("data:").strip())
        if event_name is None:
            raise ValueError("SSE frame missing event name")
        payload = json.loads("\n".join(data_lines) or "{}")
        payload["event"] = event_name
        return TourEvent._adapter.validate_python(payload)


def event_payload(event: BaseTourEvent) -> dict[str, Any]:
    return event.model_dump()


__all__ = [
    "AccountUsageResponse",
    "AskRequest",
    "BaseTourEvent",
    "ChunkPayload",
    "ClaimPayload",
    "CreateRepoRequest",
    "CreateRepoResponse",
    "IntentDraftRequest",
    "ProviderCredentialsRequest",
    "QAAnswerResponse",
    "RepoStatus",
    "RepoStatusResponse",
    "TourDoneEvent",
    "TourErrorEvent",
    "TourEvent",
    "TourEventType",
    "TourFirstImpressionEvent",
    "event_payload",
]
