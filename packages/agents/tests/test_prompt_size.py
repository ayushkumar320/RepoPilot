"""The answer prompt stays under a size a provider will actually accept.

A chunk is one AST node, so a single chunk can be a 1500-line class. Eight of
those went out as one request and Groq answered 413 Payload Too Large, which
the API turns into a keyword-only answer.
"""

from __future__ import annotations

from repopilot_agents.qa.prompts import (
    MAX_CHUNK_CHARS,
    MAX_CHUNKS_CHARS,
    answer_user_prompt,
)
from repopilot_agents.types import ChunkContent, CodeRef


def _huge_chunk(index: int) -> ChunkContent:
    lines = [f"    self.attribute_{i} = {i}" for i in range(4000)]
    return ChunkContent(
        ref=CodeRef(
            file_path=f"pkg/mod_{index}.py",
            start_line=1,
            end_line=len(lines),
            symbol=f"pkg.mod_{index}.Huge",
        ),
        content="\n".join(lines),
        kind="class",
    )


def test_oversized_chunks_are_capped() -> None:
    chunks = [_huge_chunk(index) for index in range(8)]
    raw = sum(len(chunk.content) for chunk in chunks)
    prompt = answer_user_prompt("what does this class do?", chunks)

    assert raw > MAX_CHUNKS_CHARS * 4, "fixture is not big enough to prove the cap"
    # Chunk bodies are capped; the wrapper text around them is small and fixed.
    assert len(prompt) < MAX_CHUNKS_CHARS + 4000
    assert "chunk truncated for prompt size" in prompt
    # Truncated, not dropped: the first chunks still reach the model.
    assert "pkg/mod_0.py" in prompt


def test_small_chunks_are_untouched() -> None:
    chunk = ChunkContent(
        ref=CodeRef(file_path="pkg/mod.py", start_line=1, end_line=2, symbol="pkg.mod.fn"),
        content="def fn():\n    return 1",
        kind="function",
    )
    prompt = answer_user_prompt("what does fn return?", [chunk])

    assert "def fn():\n    return 1" in prompt
    assert "truncated" not in prompt
    assert len(chunk.content) < MAX_CHUNK_CHARS
