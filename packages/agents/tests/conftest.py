"""Shared fixtures: stubbed engine + LLMProvider for the unit-testable layer.

We can't use a real Postgres in the fast lane, so the tools that touch DB
(``read_chunks``, ``vector_search``, ``graph_traverse``, ``graph_query``,
``graph_metrics``) are exercised against a small in-memory model that mimics
the relevant slice of the schema. Postgres-/pgvector-specific paths
(``vector_search`` SQL, ``persist_index``) belong in the slow + integration
lane and are not unit-tested here.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

import pytest

from repopilot_agents.tools import _adjacency
from repopilot_agents.types import ChunkContent, CodeRef
from repopilot_agents.verifier import grounding as grounding_mod


@dataclass(slots=True)
class FakeChunk:
    file_path: str
    start_line: int
    end_line: int
    symbol: str
    kind: str
    content: str
    summary: str | None = None


@dataclass
class FakeEngine:
    """Minimal in-memory stand-in matching the surface the tools call."""

    chunks: list[FakeChunk] = field(default_factory=list)
    adjacency: dict[str, dict[str, list[str]]] = field(default_factory=dict)

    async def dispose(self) -> None:  # pragma: no cover
        return None


@pytest.fixture(autouse=True)
def _reset_caches() -> Iterator[None]:
    _adjacency.reset_cache()
    grounding_mod.reset_cache()
    yield
    _adjacency.reset_cache()
    grounding_mod.reset_cache()


@pytest.fixture
def sample_chunks() -> list[FakeChunk]:
    return [
        FakeChunk(
            file_path="pkg/mod.py",
            start_line=10,
            end_line=20,
            symbol="pkg.mod.foo",
            kind="function",
            content="def foo():\n    return bar()\n",
        ),
        FakeChunk(
            file_path="pkg/mod.py",
            start_line=30,
            end_line=45,
            symbol="pkg.mod.bar",
            kind="function",
            content="def bar():\n    if True:\n        return 1\n    else:\n        return 2\n",
        ),
        FakeChunk(
            file_path="tests/test_mod.py",
            start_line=1,
            end_line=5,
            symbol="tests.test_mod.test_bar",
            kind="function",
            content="def test_bar():\n    assert bar() == 1\n",
        ),
    ]


@pytest.fixture
def sample_adjacency() -> dict[str, dict[str, list[str]]]:
    return {
        "pkg.mod.foo": {
            "calls": ["pkg.mod.bar"],
            "called_by": [],
            "imports": [],
            "imported_by": [],
            "inherits": [],
            "inherited_by": [],
        },
        "pkg.mod.bar": {
            "calls": [],
            "called_by": ["pkg.mod.foo"],
            "imports": [],
            "imported_by": [],
            "inherits": [],
            "inherited_by": [],
        },
    }


def make_ref(file_path: str, start_line: int, end_line: int, symbol: str | None = None) -> CodeRef:
    return CodeRef(
        file_path=file_path,
        start_line=start_line,
        end_line=end_line,
        symbol=symbol,
    )


def make_content(ref: CodeRef, content: str = "stub") -> ChunkContent:
    return ChunkContent(ref=ref, content=content)


class FakeProvider:
    """LLM provider double — queues canned responses, records calls."""

    def __init__(self, responses: list[Any]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    async def generate(self, model: Any, messages: Any, **kwargs: Any) -> Any:
        self.calls.append({"model": model, "messages": list(messages), "kwargs": dict(kwargs)})
        if not self._responses:
            raise AssertionError("FakeProvider exhausted")
        head = self._responses.pop(0)
        return head

    async def embed(self, text: str, *, model: Any = None) -> Any:
        self.calls.append({"embed": True, "text": text})
        if not self._responses:
            raise AssertionError("FakeProvider embed exhausted")
        return self._responses.pop(0)

    async def aclose(self) -> None:  # pragma: no cover
        return None


@dataclass
class StubResponse:
    text: str

    @property
    def total_tokens(self) -> int:
        return 0
