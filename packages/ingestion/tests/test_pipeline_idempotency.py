"""Idempotency + staleness — exercised against a stubbed DB and stubbed clone.

These are unit tests; the live-Postgres equivalent runs under the
``integration`` marker in CI.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from repopilot_ingestion import pipeline as pipeline_mod
from repopilot_ingestion.pipeline import PipelineResult, revisit_status


@dataclass
class _StubEngine:
    indexed: dict[str, str]  # repo_url -> head_sha

    async def dispose(self) -> None:
        return None


@pytest.mark.asyncio
async def test_revisit_with_advanced_remote_returns_stale_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the remote HEAD has moved past the indexed SHA → status=stale."""
    engine = _StubEngine(indexed={"https://github.com/encode/httpx": "old-sha"})
    monkeypatch.setattr(pipeline_mod, "make_engine", lambda settings: engine)
    monkeypatch.setattr(pipeline_mod, "remote_head_sha", lambda repo_url: "new-sha")

    async def fake_known(eng: Any, *, repo_url: str) -> str | None:
        return engine.indexed.get(repo_url)

    monkeypatch.setattr(pipeline_mod, "known_head_sha", fake_known)

    result: PipelineResult = await revisit_status(repo_url="https://github.com/encode/httpx")
    assert result.status == "stale"
    assert result.indexed_sha == "old-sha"
    assert result.remote_sha == "new-sha"


@pytest.mark.asyncio
async def test_revisit_with_matching_remote_returns_already_indexed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _StubEngine(indexed={"https://github.com/encode/httpx": "same-sha"})
    monkeypatch.setattr(pipeline_mod, "make_engine", lambda settings: engine)
    monkeypatch.setattr(pipeline_mod, "remote_head_sha", lambda repo_url: "same-sha")

    async def fake_known(eng: Any, *, repo_url: str) -> str | None:
        return engine.indexed.get(repo_url)

    monkeypatch.setattr(pipeline_mod, "known_head_sha", fake_known)

    result = await revisit_status(repo_url="https://github.com/encode/httpx")
    assert result.status == "already_indexed"
    assert result.head_sha == "same-sha"


@pytest.mark.asyncio
async def test_revisit_unknown_repo_returns_stale(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _StubEngine(indexed={})
    monkeypatch.setattr(pipeline_mod, "make_engine", lambda settings: engine)
    monkeypatch.setattr(pipeline_mod, "remote_head_sha", lambda repo_url: "fresh-sha")

    async def fake_known(eng: Any, *, repo_url: str) -> str | None:
        return None

    monkeypatch.setattr(pipeline_mod, "known_head_sha", fake_known)
    result = await revisit_status(repo_url="https://github.com/encode/httpx")
    assert result.status == "stale"
    assert result.indexed_sha is None
    assert result.remote_sha == "fresh-sha"
