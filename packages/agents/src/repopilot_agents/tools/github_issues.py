"""``github_issues`` — Phase 5 dependency, stubbed in Phase 2.

The signature is locked here so the Q&A subgraph and the Lane A scanner
import from a stable place. Implementation lands in Phase 5 (PyGithub +
response caching).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class Issue(BaseModel):
    """Subset of the GitHub issue shape Lane A scores on."""

    number: int
    title: str
    body: str
    state: str
    labels: list[str]
    referenced_files: list[str] = []


async def github_issues(
    repo_url: str, *, state: Literal["open", "closed", "all"] = "open"
) -> list[Issue]:
    """Phase 5 will implement; raises until then so Lane A fails loudly."""
    raise NotImplementedError(
        "github_issues lands in Phase 5 (Contribute mode). "
        f"called with repo_url={repo_url!r}, state={state!r}"
    )


__all__ = ["Issue", "github_issues"]
