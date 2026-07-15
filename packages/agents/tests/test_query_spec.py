"""Tests for Phase 2 query understanding."""

from __future__ import annotations

from typing import Any

import pytest

from repopilot_agents.qa.query_spec import build_query_spec, fallback_query_spec


class _Provider:
    def __init__(self, text: str | BaseException) -> None:
        self.text = text
        self.calls = 0

    async def generate(self, *args: Any, **kwargs: Any) -> Any:
        self.calls += 1
        if isinstance(self.text, BaseException):
            raise self.text

        class _R:
            pass

        response = _R()
        response.text = self.text  # type: ignore[attr-defined]
        return response


@pytest.mark.asyncio
async def test_build_query_spec_parses_json_and_preserves_raw_question() -> None:
    provider = _Provider(
        """
        {"raw_text":"wrong","rewrites":["redirect method", "response location header"],
         "extracted_symbols":["_redirect_method"], "extracted_paths":["./src/httpx/_client.py"],
         "intent_class":"procedural", "needs_multi_hop":true}
        """
    )

    spec = await build_query_spec("How do redirects flow?", provider=provider)  # type: ignore[arg-type]

    assert spec.raw_text == "How do redirects flow?"
    assert spec.rewrites == ["redirect method", "response location header"]
    assert spec.extracted_symbols == ["_redirect_method"]
    assert spec.extracted_paths == ["src/httpx/_client.py"]
    assert spec.intent_class == "procedural"
    assert spec.needs_multi_hop is True


@pytest.mark.asyncio
async def test_build_query_spec_falls_back_on_parse_error() -> None:
    spec = await build_query_spec(
        "Where is `src/httpx/_client.py` used?",
        provider=_Provider("not json"),  # type: ignore[arg-type]
    )

    assert spec.raw_text == "Where is `src/httpx/_client.py` used?"
    assert spec.rewrites == []
    assert spec.extracted_paths == ["src/httpx/_client.py"]
    assert spec.intent_class == "where_is"


@pytest.mark.asyncio
async def test_build_query_spec_falls_back_on_provider_error() -> None:
    spec = await build_query_spec(
        "How does `Client.send` call transports?",
        provider=_Provider(RuntimeError("quota")),  # type: ignore[arg-type]
    )

    assert spec.raw_text == "How does `Client.send` call transports?"
    assert spec.extracted_symbols == ["Client.send"]
    assert spec.needs_multi_hop is True


def test_retrieval_queries_dedupes_and_caps_rewrites() -> None:
    spec = fallback_query_spec("How does redirect handling work?").model_copy(
        update={
            "rewrites": [
                "redirect handling",
                "REDIRECT HANDLING",
                "response redirect method",
                "location header redirect",
            ]
        }
    )

    assert spec.retrieval_queries(max_rewrites=2) == [
        "How does redirect handling work?",
        "redirect handling",
    ]
