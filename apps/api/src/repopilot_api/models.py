"""Phase 4 API contracts and SSE event models."""

from __future__ import annotations

import json
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, TypeAdapter

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


class CreateTourRequest(BaseModel):
    repo_id: str = Field(min_length=1)
    intent_profile: IntentProfile


class CreateTourResponse(BaseModel):
    tour_id: str = Field(min_length=1)
    stream_url: str = Field(min_length=1)


class AskTourRequest(BaseModel):
    question: str = Field(min_length=1)


class TourClaimPayload(BaseModel):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    refs: list[CodeRef] = Field(min_length=1)
    status: ClaimStatus
    verifier_note: str | None = None
    retrieval_path: list[str] = Field(default_factory=list)


class QAAnswerResponse(BaseModel):
    answer: str = Field(min_length=1)
    claims: list[TourClaimPayload] = Field(default_factory=list)
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


class TourSectionStartEvent(BaseTourEvent):
    event: Literal["section_start"] = "section_start"
    order: int = Field(ge=0)
    title: str = Field(min_length=1)


class TourTokenEvent(BaseTourEvent):
    event: Literal["token"] = "token"
    text: str


class TourClaimEvent(BaseTourEvent):
    event: Literal["claim"] = "claim"
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    refs: list[CodeRef] = Field(min_length=1)
    status: ClaimStatus
    verifier_note: str | None = None
    retrieval_path: list[str] = Field(default_factory=list)

class TourDiagramEvent(BaseTourEvent):
    event: Literal["diagram"] = "diagram"
    mermaid: str = Field(min_length=1)


class TourSectionEndEvent(BaseTourEvent):
    event: Literal["section_end"] = "section_end"
    order: int = Field(ge=0)


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
    TourSectionStartEvent
    | TourTokenEvent
    | TourClaimEvent
    | TourDiagramEvent
    | TourSectionEndEvent
    | TourFirstImpressionEvent
    | TourDoneEvent
    | TourErrorEvent,
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
    "AskTourRequest",
    "BaseTourEvent",
    "ChunkPayload",
    "CreateRepoRequest",
    "CreateRepoResponse",
    "CreateTourRequest",
    "CreateTourResponse",
    "QAAnswerResponse",
    "RepoStatus",
    "RepoStatusResponse",
    "TourClaimEvent",
    "TourClaimPayload",
    "TourDiagramEvent",
    "TourDoneEvent",
    "TourErrorEvent",
    "TourEvent",
    "TourEventType",
    "TourFirstImpressionEvent",
    "TourSectionEndEvent",
    "TourSectionStartEvent",
    "TourTokenEvent",
    "event_payload",
]
