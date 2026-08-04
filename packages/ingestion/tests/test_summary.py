from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from repopilot_core.llm.provider import ProviderError
from repopilot_core.settings import Settings
from repopilot_ingestion.chunk import Chunk
from repopilot_ingestion.summary import summarise_chunks


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

    summaries = await summarise_chunks(
        [_chunk("first"), _chunk("second"), _chunk("third")],
        provider=provider,  # type: ignore[arg-type]
        settings=settings,
    )

    # On provider exhaustion each chunk degrades to a deterministic AST-derived
    # stand-in (not the opaque literal "unknown").
    assert all(summary.summary.endswith("(summary unavailable)") for summary in summaries)
    assert provider.calls == 1
    assert provider.retry_attempts == [1]
