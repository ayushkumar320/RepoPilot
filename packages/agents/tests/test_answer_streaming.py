"""The streamed answer must show the answer, never the model's thinking."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from typing import Any

import pytest

from repopilot_agents.qa.graph import NOT_FOUND_SENTINEL, _stream_answer
from repopilot_core.llm.models import ModelId
from repopilot_core.llm.provider import Message


class _ScriptedProvider:
    """Replays fixed deltas, the way a provider's SSE stream would."""

    def __init__(self, deltas: Sequence[str]) -> None:
        self.deltas = deltas

    def generate_stream(
        self,
        model: ModelId,
        messages: Sequence[Message],
        retry_429_attempts: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        async def iterator() -> AsyncIterator[str]:
            for delta in self.deltas:
                yield delta

        return iterator()


async def _run(deltas: Sequence[str]) -> tuple[str, list[str]]:
    published: list[str] = []

    async def sink(text: str) -> None:
        published.append(text)

    answer = await _stream_answer(
        _ScriptedProvider(deltas),  # type: ignore[arg-type]
        [Message("user", "q")],
        retry_429_attempts=None,
        on_token=sink,
    )
    return answer, published


@pytest.mark.asyncio
async def test_plain_answer_streams_through_unchanged() -> None:
    answer, published = await _run(["The router ", "resolves ", "the request."])

    assert "".join(published) == "The router resolves the request."
    assert answer == "The router resolves the request."


@pytest.mark.asyncio
async def test_reasoning_block_is_withheld_until_the_answer_starts() -> None:
    answer, published = await _run(
        ["<think>", "restating the ", "prompt", "</think>", "The router ", "resolves it."]
    )

    # Nothing leaks while the block is open, and the reader never sees any of it.
    assert "".join(published) == "The router resolves it."
    assert "think" not in answer
    assert answer == "The router resolves it."


@pytest.mark.asyncio
async def test_unclosed_reasoning_block_fails_clean() -> None:
    """Budget ran out mid-thought: no answer exists, so publish none of it."""
    answer, published = await _run(["<think>", "weighing the ", "chunks and then it cut"])

    assert published == []
    assert answer == NOT_FOUND_SENTINEL
