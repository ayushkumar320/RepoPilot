"""API contracts and SSE event models.

The tour entity is gone: a repository plus an ``IntentProfile`` (the reader's
persona) is everything a question needs, and the persona travels with each
``/repos/{repo_id}/ask`` call rather than being frozen into a server-side
record. What remains here is the repo lifecycle, the ask contract, and the
first-impression stream.
"""

from __future__ import annotations

import json
from datetime import datetime
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
    provider_connected: bool
    groq_connected: bool
    huggingface_connected: bool
    credential_storage: Literal["account_bound"] = "account_bound"


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


class CreateTourRequest(BaseModel):
    """Start a history entry for one repo read through one persona."""

    repo_id: str = Field(min_length=1)
    intent_profile: IntentProfile | None = None
    title: str | None = Field(default=None, max_length=200)


class CreateTourResponse(BaseModel):
    tour_id: str = Field(min_length=1)


class TourMessagePayload(BaseModel):
    ordinal: int = Field(ge=0)
    question: str
    answer: str
    claims: list[ClaimPayload] = Field(default_factory=list)
    persona_label: str


class AppendTourMessageRequest(BaseModel):
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    claims: list[ClaimPayload] = Field(default_factory=list)
    persona_label: str = Field(min_length=1)


class AppendTourMessageResponse(BaseModel):
    ordinal: int = Field(ge=0)


class TourSummaryResponse(BaseModel):
    tour_id: str
    repo_id: str
    title: str | None = None
    created_at: datetime
    updated_at: datetime
    message_count: int = Field(ge=0)


class TourDetailResponse(TourSummaryResponse):
    snapshot_repo_id: str | None = None
    intent_profile: IntentProfile | None = None
    messages: list[TourMessagePayload] = Field(default_factory=list)


class IdentityRequest(BaseModel):
    """Identity claimed by the web app after a completed OAuth sign-in."""

    provider: str = Field(min_length=1, max_length=32)
    provider_account_id: str = Field(min_length=1, max_length=128)
    display_name: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=320)
    avatar_url: str | None = Field(default=None, max_length=2000)


class IdentityResponse(BaseModel):
    session_id: str
    authenticated: bool
    provider: str | None = None
    provider_account_id: str | None = None
    display_name: str | None = None
    email: str | None = None
    avatar_url: str | None = None


class ChunkPayload(BaseModel):
    chunk_id: str = Field(min_length=1)
    repo_id: str = Field(min_length=1)
    ref: CodeRef
    content: str
    summary: str | None = None


GraphEdgeKind = Literal[
    "defined_by",
    "calls",
    "called_by",
    "inherits",
    "inherited_by",
    "defines",
    "imports",
    "imported_by",
]


class GraphNeighbour(BaseModel):
    """One symbol adjacent to the queried one, and how to reach its source.

    ``resolved`` and ``external`` are deliberately separate. ``external`` says
    the symbol sits outside this repo's own top-level packages — stdlib or a
    third-party name pulled in by an import edge. ``resolved`` says we found a
    ``file:line`` for it. A node can be internal yet unresolved (a nested def
    the chunker never chunked), and claiming otherwise would be inventing a
    source we do not have.
    """

    symbol: str = Field(min_length=1)
    label: str = Field(min_length=1)
    edge: GraphEdgeKind
    kind: str | None = None
    external: bool = False
    resolved: bool = False
    chunk_id: str | None = None
    ref: CodeRef | None = None


class GraphNeighboursResponse(BaseModel):
    """Neighbourhood of one symbol in the indexed snapshot's code graph.

    ``available`` is false when the snapshot has no graph at all, which is the
    normal case for a repo with no Python: the AST graph is Python-only, and an
    empty diagram would read as broken rather than as not-applicable.
    """

    symbol: str
    available: bool
    found: bool
    neighbours: list[GraphNeighbour] = Field(default_factory=list)
    total: int = Field(default=0, ge=0)
    truncated: bool = False


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
    "AppendTourMessageRequest",
    "AppendTourMessageResponse",
    "AskRequest",
    "BaseTourEvent",
    "ChunkPayload",
    "ClaimPayload",
    "CreateRepoRequest",
    "CreateRepoResponse",
    "CreateTourRequest",
    "CreateTourResponse",
    "GraphEdgeKind",
    "GraphNeighbour",
    "GraphNeighboursResponse",
    "IdentityRequest",
    "IdentityResponse",
    "IntentDraftRequest",
    "ProviderCredentialsRequest",
    "QAAnswerResponse",
    "RepoStatus",
    "RepoStatusResponse",
    "TourDetailResponse",
    "TourDoneEvent",
    "TourErrorEvent",
    "TourEvent",
    "TourEventType",
    "TourFirstImpressionEvent",
    "TourMessagePayload",
    "TourSummaryResponse",
    "event_payload",
]
