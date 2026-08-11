from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from repopilot_core.llm.provider import ProviderError
from repopilot_core.settings import Settings
from repopilot_ingestion.chunk import Chunk
from repopilot_ingestion.summary import CIRCUIT_TRIP_FAILURES, summarise_chunks


class FailingProvider:
    def __init__(self) -> None:
        self.calls = 0
        self.retry_attempts: list[int | None] = []

    async def generate(self, *args: Any, **kwargs: Any) -> Any:
        self.calls += 1
        self.retry_attempts.append(kwargs.get("retry_429_attempts"))
        raise ProviderError("all providers failed")


def _chunk(symbol: str) -> Chunk:
    return Chunk(
        file_path="app.py",
        symbol=symbol,
        kind="function",
        start_line=1,
        end_line=2,
        content=f"def {symbol}():\n    pass\n",
    )


@pytest.mark.asyncio
async def test_summarise_chunks_opens_circuit_after_provider_failure(tmp_path: Path) -> None:
    provider = FailingProvider()
    settings = Settings(
        repopilot_env="test",
        llm_cache_path=tmp_path / "llm.sqlite",
        ingestion_summary_concurrency=1,
    )

    chunks = [_chunk(f"sym{i}") for i in range(CIRCUIT_TRIP_FAILURES + 3)]
    summaries = await summarise_chunks(
        chunks,
        provider=provider,  # type: ignore[arg-type]
        settings=settings,
    )

    # On provider exhaustion each chunk degrades to a deterministic AST-derived
    # stand-in (not the opaque literal "unknown").
    assert all(summary.summary.endswith("(summary unavailable)") for summary in summaries)
    # The circuit tolerates a burst before giving up, so one 429 at high
    # concurrency no longer costs every remaining summary.
    assert provider.calls == CIRCUIT_TRIP_FAILURES
    assert provider.retry_attempts == [1] * CIRCUIT_TRIP_FAILURES


@pytest.mark.asyncio
async def test_summarise_chunks_recovers_from_an_isolated_provider_failure(
    tmp_path: Path,
) -> None:
    """A single blip must not downgrade the rest of the repo's summaries."""

    class FlakyProvider:
        def __init__(self) -> None:
            self.calls = 0

        async def generate(self, *args: Any, **kwargs: Any) -> Any:
            self.calls += 1
            if self.calls == 1:
                raise ProviderError("rate limited")

            class _R:
                text = "Does a thing."

            return _R()

    provider = FlakyProvider()
    settings = Settings(
        repopilot_env="test",
        llm_cache_path=tmp_path / "llm.sqlite",
        ingestion_summary_concurrency=1,
    )

    summaries = await summarise_chunks(
        [_chunk("first"), _chunk("second"), _chunk("third")],
        provider=provider,  # type: ignore[arg-type]
        settings=settings,
    )

    assert [s.summary for s in summaries[1:]] == ["Does a thing.", "Does a thing."]
