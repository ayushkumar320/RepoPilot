"""Claim→ref attribution via cross-encoder (stubbed — no model download)."""

from __future__ import annotations

import pytest

from repopilot_agents.rerank import attribution as attribution_mod
from repopilot_agents.rerank.attribution import attribute_refs
from repopilot_agents.types import ChunkContent, CodeRef


def _chunk(path: str, symbol: str, content: str) -> ChunkContent:
    return ChunkContent(
        ref=CodeRef(file_path=path, start_line=1, end_line=10, symbol=symbol),
        content=content,
    )


class _StubReranker:
    """Scores by trivial keyword containment so tests control the ranking."""

    def score(self, query: str, texts: list[str]) -> list[float]:
        return [float(sum(1 for w in query.lower().split() if w in t.lower())) for t in texts]


@pytest.fixture(autouse=True)
def _stub_reranker(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(attribution_mod, "shared_reranker", lambda model_name: _StubReranker())


def test_attributes_to_most_relevant_chunk() -> None:
    chunks = [
        _chunk("a.py", "pkg.a.unrelated", "def unrelated(): pass"),
        _chunk("b.py", "pkg.b.redirect", "def redirect(): follow the redirect limit"),
        _chunk("c.py", "pkg.c.timeout", "def timeout(): pass"),
    ]
    refs = attribute_refs("the redirect limit is enforced here", chunks, k=2)
    assert refs[0].file_path == "b.py"
    assert len(refs) == 2


def test_k_caps_ref_count() -> None:
    chunks = [_chunk(f"f{i}.py", f"s{i}", "text") for i in range(5)]
    assert len(attribute_refs("text", chunks, k=2)) == 2
    assert len(attribute_refs("text", chunks, k=1)) == 1


def test_empty_inputs() -> None:
    assert attribute_refs("", [_chunk("a.py", "s", "c")]) == []
    assert attribute_refs("claim", []) == []
