"""Types specific to the Q&A subgraph (sufficiency judge + final answer)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SufficiencyDecision = Literal["sufficient", "insufficient"]


class SufficiencyVerdict(BaseModel):
    """The structured response we require from the sufficiency judge."""

    decision: SufficiencyDecision
    reason: str = ""
    next_symbol: str | None = None  # if insufficient: which symbol to traverse next


class QAClaim(BaseModel):
    """A single grounded claim in the Q&A answer."""

    text: str
    refs: list[str] = Field(default_factory=list)  # CodeRef.symbol strings for prompt-side debug


__all__ = ["QAClaim", "SufficiencyDecision", "SufficiencyVerdict"]
