"""Unit tests for the Intent Profiler.

The end-to-end accuracy gate (≥ 90% per field on ``intent_profiling_v1.jsonl``)
lives in the eval-runner lane. These tests pin the *coercion contract*:
what the profiler does with malformed, partial, or hostile LLM output. The
gate measures quality on real LLM output; these tests make sure the
plumbing around it can't silently produce a bad ``IntentProfile``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import pytest

from repopilot_agents.intent.profiler import profile_intent
from repopilot_agents.state import IntentProfile
from repopilot_core.llm.provider import LLMProvider


@dataclass(slots=True)
class StubResponse:
    text: str

    @property
    def total_tokens(self) -> int:
        return 0


class FakeProvider:
    """Minimal LLMProvider double — queues canned responses."""

    def __init__(self, responses: list[StubResponse]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    async def generate(self, model: Any, messages: Any, **kwargs: Any) -> StubResponse:
        self.calls.append({"model": model, "messages": list(messages), "kwargs": dict(kwargs)})
        if not self._responses:
            raise AssertionError("FakeProvider exhausted")
        return self._responses.pop(0)


@pytest.mark.asyncio
async def test_profiler_parses_a_clean_response() -> None:
    payload = (
        '{"modality_weights": {"understand": 0.8, "locate": 0.4}, '
        '"focus_keywords": ["connection pool", "leak"], '
        '"audience_framing": "for a PR review", '
        '"output_shape_preference": "narrative", '
        '"success_criterion": "user can trace the pool path"}'
    )
    provider = FakeProvider([StubResponse(text=payload)])

    profile = await profile_intent(
        "I want to understand how httpx handles connection pooling.",
        provider=cast(LLMProvider, provider),
    )

    assert isinstance(profile, IntentProfile)
    assert profile.modality_weights == {"understand": 0.8, "locate": 0.4}
    assert profile.focus_keywords == ["connection pool", "leak"]
    assert profile.audience_framing == "for a PR review"
    assert profile.output_shape_preference == "narrative"
    assert profile.success_criterion == "user can trace the pool path"


@pytest.mark.asyncio
async def test_profiler_drops_unknown_modality_keys() -> None:
    # 8B models hallucinate keys outside the Modality literal. Drop them
    # silently so the planner doesn't see garbage.
    payload = (
        '{"modality_weights": {"understand": 0.9, "vibes": 0.5, "compare": 1.2}, '
        '"focus_keywords": [], "audience_framing": null, '
        '"output_shape_preference": "narrative", "success_criterion": null}'
    )
    provider = FakeProvider([StubResponse(text=payload)])

    profile = await profile_intent("anything", provider=cast(LLMProvider, provider))

    assert "vibes" not in profile.modality_weights
    assert profile.modality_weights["understand"] == 0.9
    # 1.2 should be clipped, not dropped — preserves intent, satisfies validator.
    assert profile.modality_weights["compare"] == 1.0


@pytest.mark.asyncio
async def test_profiler_coerces_unknown_output_shape_to_unspecified() -> None:
    payload = (
        '{"modality_weights": {}, "focus_keywords": [], '
        '"audience_framing": null, '
        '"output_shape_preference": "diagram_first", '
        '"success_criterion": null}'
    )
    provider = FakeProvider([StubResponse(text=payload)])

    profile = await profile_intent("anything", provider=cast(LLMProvider, provider))
    assert profile.output_shape_preference == "unspecified"


@pytest.mark.asyncio
async def test_profiler_falls_back_on_unparseable_response() -> None:
    provider = FakeProvider([StubResponse(text="I cannot help with that.")])

    profile = await profile_intent("understand foo", provider=cast(LLMProvider, provider))

    assert profile == IntentProfile(raw_text="understand foo")


@pytest.mark.asyncio
async def test_profiler_extracts_json_embedded_in_prose() -> None:
    # Some models wrap JSON in a code fence or trailing apology — the
    # regex pulls the first {...} block.
    payload = (
        "Here is the profile: ```json\n"
        '{"modality_weights": {"locate": 0.6}, '
        '"focus_keywords": ["auth"], "audience_framing": null, '
        '"output_shape_preference": "ranked_list", "success_criterion": null}'
        "\n```"
    )
    provider = FakeProvider([StubResponse(text=payload)])

    profile = await profile_intent("find the auth code", provider=cast(LLMProvider, provider))
    assert profile.modality_weights == {"locate": 0.6}
    assert profile.focus_keywords == ["auth"]
    assert profile.output_shape_preference == "ranked_list"


@pytest.mark.asyncio
async def test_profiler_lowercases_and_trims_keywords() -> None:
    payload = (
        '{"modality_weights": {}, "focus_keywords": ["  Connection Pool  ", "", "LEAK"], '
        '"audience_framing": null, "output_shape_preference": "unspecified", '
        '"success_criterion": null}'
    )
    provider = FakeProvider([StubResponse(text=payload)])

    profile = await profile_intent("anything", provider=cast(LLMProvider, provider))
    assert profile.focus_keywords == ["connection pool", "leak"]


@pytest.mark.asyncio
async def test_profiler_caps_keywords_at_six() -> None:
    payload = (
        '{"modality_weights": {}, "focus_keywords": '
        '["a", "b", "c", "d", "e", "f", "g", "h"], '
        '"audience_framing": null, "output_shape_preference": "unspecified", '
        '"success_criterion": null}'
    )
    provider = FakeProvider([StubResponse(text=payload)])

    profile = await profile_intent("anything", provider=cast(LLMProvider, provider))
    assert profile.focus_keywords == ["a", "b", "c", "d", "e", "f"]


@pytest.mark.asyncio
async def test_profiler_rejects_empty_input() -> None:
    provider = FakeProvider([])
    with pytest.raises(ValueError):
        await profile_intent("   ", provider=cast(LLMProvider, provider))


@pytest.mark.asyncio
async def test_profiler_preserves_raw_text_verbatim() -> None:
    payload = (
        '{"modality_weights": {}, "focus_keywords": [], '
        '"audience_framing": null, "output_shape_preference": "unspecified", '
        '"success_criterion": null}'
    )
    provider = FakeProvider([StubResponse(text=payload)])

    raw = "I want to ship a fix for the auth bug by Friday."
    profile = await profile_intent(raw, provider=cast(LLMProvider, provider))
    assert profile.raw_text == raw
