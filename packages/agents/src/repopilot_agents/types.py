"""Shared Pydantic types used across tools, verifier, and Q&A.

These are the typed inputs and outputs the LLM never inspects directly —
agents receive them as structured objects so prompts stay shaped, predictable,
and verifiable.

A subset of these (``CodeRef``) appears verbatim in
``docs/03_ARCHITECTURE.md`` State schema. Phase 3 will move ``CodeRef`` and
``Claim`` into ``packages/agents/state.py`` and re-import them here; for
Phase 2 they live here to keep the tool layer self-contained.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class CodeRef(BaseModel):
    """Pointer into the repo. Every factual claim must carry at least one."""

    file_path: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    symbol: str | None = None

    @field_validator("end_line")
    @classmethod
    def _end_after_start(cls, v: int, info: object) -> int:
        # info.data is a dict[str, Any] in pydantic v2; cast-free access keeps
        # mypy --strict quiet while preserving the validator contract.
        data: dict[str, int] = getattr(info, "data", {})
        if "start_line" in data and v < data["start_line"]:
            raise ValueError("end_line must be >= start_line")
        return v


class ChunkContent(BaseModel):
    """Result of ``read_chunks``: a CodeRef paired with the source text it points at."""

    ref: CodeRef
    content: str
    summary: str | None = None
    kind: str = "function"
    kept_line_spans: list[tuple[int, int]] | None = None
    signature: str | None = None
    decorators: list[str] = Field(default_factory=list)
    neighbor_symbols: list[str] = Field(default_factory=list)


class ChunkHit(BaseModel):
    """Result of ``vector_search``: a chunk with retrieval metadata."""

    ref: CodeRef
    distance: float = Field(ge=0.0)
    summary: str | None = None
    kind: str = "function"


class Path(BaseModel):
    """Result of ``graph_traverse``: an ordered chain of CodeRefs."""

    steps: list[CodeRef] = Field(min_length=1)
    edge_types: list[str] = Field(default_factory=list)

    @property
    def depth(self) -> int:
        return len(self.steps) - 1


class SymbolMetrics(BaseModel):
    """Result of ``graph_metrics``: per-symbol metric pack."""

    symbol: str
    fan_in: int = Field(ge=0)
    fan_out: int = Field(ge=0)
    cyclomatic: int = Field(ge=0)
    churn: int = Field(ge=0)
    has_tests: bool = False


class GraphQueryResult(BaseModel):
    """Result of ``graph_query``: one row of an entry-points / hubs / layers query."""

    symbol: str
    kind: str = "function"
    score: float = 0.0  # in-degree for hubs, community id for layers, etc.
    metadata: dict[str, str] = Field(default_factory=dict)


__all__ = [
    "ChunkContent",
    "ChunkHit",
    "CodeRef",
    "GraphQueryResult",
    "Path",
    "SymbolMetrics",
]
