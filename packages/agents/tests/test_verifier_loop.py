"""Verifier-loop tests: actionability rubric + retry budget + flagging.

The grounding pass itself is exercised in ``test_verifier_grounding.py``;
here we test the *loop* — actionability JSON parsing, section-level
aggregation, retry semantics, and the "flagged, not dropped" rule.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import pytest

from repopilot_agents.state import (
    Claim,
    CodeRef,
    IntentProfile,
    TourSection,
    VerifierObjection,
)
from repopilot_agents.verifier import grounding as grounding_mod
from repopilot_agents.verifier import loop as loop_mod
from repopilot_agents.verifier.loop import (
    MAX_SOURCE_RETRIES,
    ActionabilityVerdict,
    _parse_actionability,
    verify_section,
    verify_section_with_retries,
)
from repopilot_core.llm.provider import LLMProvider

# ─── Fixtures: chunk reader + provider doubles ──────────────────────────


def _ref(start: int = 10, end: int = 20, sym: str = "pkg.foo") -> CodeRef:
    return CodeRef(file_path="pkg/foo.py", start_line=start, end_line=end, symbol=sym)


def _claim(text: str, ref: CodeRef | None = None) -> Claim:
    return Claim(text=text, refs=[ref or _ref()])


def _section(claims: list[Claim], order: int = 0) -> TourSection:
    return TourSection(title="Section", order=order, claims=claims)


@dataclass(slots=True)
class _StubResponse:
    text: str

    @property
    def total_tokens(self) -> int:
        return 0


class _ScriptedProvider:
    """Queues responses keyed on which prompt is being graded.

    The verifier loop issues two prompts per claim: one grounding, one
    actionability. We deliver them by inspecting the system message —
    grounding starts with "You are a strict grounding verifier",
    actionability starts with "You are the actionability rubric".
    """

    def __init__(
        self,
        *,
        grounding_results: list[str],
        actionability_results: list[str],
    ) -> None:
        self._grounding = list(grounding_results)
        self._actionability = list(actionability_results)
        self.calls: list[dict[str, Any]] = []

    async def generate(self, model: Any, messages: Any, **kwargs: Any) -> _StubResponse:
        system = next(m for m in messages if m.role == "system")
        if "grounding verifier" in system.content:
            payload = self._grounding.pop(0)
        else:
            payload = self._actionability.pop(0)
        self.calls.append({"system": system.content[:50]})
        return _StubResponse(text=payload)


@pytest.fixture(autouse=True)
def _patch_read_chunks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bypass DB-backed ``read_chunks`` — grounding loops over them but
    the bodies don't matter once we mock the verdict."""
    from repopilot_agents.types import ChunkContent

    async def fake_read_chunks(
        refs: list[CodeRef], *, engine: Any, repo_id: str
    ) -> list[ChunkContent]:
        return [ChunkContent(ref=r, content=f"# code for {r.symbol}") for r in refs]

    monkeypatch.setattr(grounding_mod, "read_chunks", fake_read_chunks)


@pytest.fixture
def engine() -> Any:
    class _E:
        async def dispose(self) -> None:
            return None

    return _E()


# ─── Actionability JSON parsing ─────────────────────────────────────────


def test_parse_actionability_accepts_clean_json() -> None:
    v = _parse_actionability(
        '{"verdict":"actionable","reason":"flags a tradeoff matching the goal"}'
    )
    assert v is not None
    assert v.verdict == "actionable"


def test_parse_actionability_returns_none_on_garbage() -> None:
    assert _parse_actionability("¯\\_(ツ)_/¯") is None


def test_parse_actionability_returns_none_on_invalid_verdict() -> None:
    assert _parse_actionability('{"verdict":"yes","reason":"x"}') is None


def test_parse_actionability_extracts_json_from_prose() -> None:
    v = _parse_actionability('Here you go: {"verdict":"not_actionable","reason":"off-goal"} done')
    assert v is not None
    assert v.verdict == "not_actionable"


# ─── Section verification: happy paths ──────────────────────────────────


@pytest.mark.asyncio
async def test_verify_section_passes_when_grounded_and_actionable(engine: Any) -> None:
    grounding_mod.reset_cache()
    section = _section([_claim("foo() does the bar dance")])
    provider = _ScriptedProvider(
        grounding_results=['{"decision":"supported","reason":"line 12"}'],
        actionability_results=['{"verdict":"actionable","reason":"matches goal"}'],
    )
    result = await verify_section(
        section,
        IntentProfile(raw_text="understand foo"),
        provider=cast(LLMProvider, provider),
        engine=engine,
        repo_id="r1",
    )
    assert result.passed
    assert result.claims[0].status == "verified"


@pytest.mark.asyncio
async def test_verify_section_rejects_ungrounded_and_skips_actionability(
    engine: Any,
) -> None:
    grounding_mod.reset_cache()
    section = _section([_claim("foo() does the bar dance")])
    provider = _ScriptedProvider(
        grounding_results=['{"decision":"rejected","reason":"not in chunks"}'],
        actionability_results=[],  # must never be called
    )
    result = await verify_section(
        section,
        IntentProfile(raw_text="understand foo"),
        provider=cast(LLMProvider, provider),
        engine=engine,
        repo_id="r1",
    )
    assert not result.passed
    assert result.claims[0].status == "rejected"
    assert "ungrounded" in result.objections[0].reason


@pytest.mark.asyncio
async def test_verify_section_rejects_off_goal_claim(engine: Any) -> None:
    grounding_mod.reset_cache()
    section = _section([_claim("the LICENSE file is MIT")])
    provider = _ScriptedProvider(
        grounding_results=['{"decision":"supported","reason":"line 1"}'],
        actionability_results=[
            '{"verdict":"not_actionable","reason":"off-goal for understand request"}'
        ],
    )
    result = await verify_section(
        section,
        IntentProfile(raw_text="understand request lifecycle"),
        provider=cast(LLMProvider, provider),
        engine=engine,
        repo_id="r1",
    )
    assert not result.passed
    assert result.claims[0].status == "rejected"
    assert "not_actionable" in result.objections[0].reason


@pytest.mark.asyncio
async def test_verify_section_handles_empty_section(engine: Any) -> None:
    grounding_mod.reset_cache()
    provider = _ScriptedProvider(grounding_results=[], actionability_results=[])
    result = await verify_section(
        _section([]),
        IntentProfile(raw_text="anything"),
        provider=cast(LLMProvider, provider),
        engine=engine,
        repo_id="r1",
    )
    assert result.passed
    assert result.claims == []
    assert result.objections == []


# ─── Retry budget + flagging ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_retries_then_flags_when_source_cannot_recover(engine: Any) -> None:
    grounding_mod.reset_cache()
    bad_section = _section([_claim("off-goal claim")])
    profile = IntentProfile(raw_text="understand request lifecycle")

    # Provider scripted to fail actionability on every attempt.
    provider = _ScriptedProvider(
        grounding_results=[
            '{"decision":"supported","reason":"line 1"}',
            '{"decision":"supported","reason":"line 1"}',
            '{"decision":"supported","reason":"line 1"}',
        ],
        actionability_results=[
            '{"verdict":"not_actionable","reason":"off-goal"}',
            '{"verdict":"not_actionable","reason":"off-goal"}',
            '{"verdict":"not_actionable","reason":"off-goal"}',
        ],
    )

    attempts: list[int] = []

    async def retry(section: TourSection, objections: list[VerifierObjection]) -> TourSection:
        attempts.append(len(objections))
        # Source returns the same (broken) section — simulates a source
        # node that cannot recover.
        return section

    result = await verify_section_with_retries(
        bad_section,
        profile,
        provider=cast(LLMProvider, provider),
        engine=engine,
        repo_id="r1",
        retry=retry,
    )

    assert len(attempts) == MAX_SOURCE_RETRIES
    assert not result.passed
    # The defining behavior: flagged, not silently dropped.
    assert result.claims[0].status == "flagged"
    assert result.claims[0].verifier_note == "off-goal"


@pytest.mark.asyncio
async def test_retry_recovers_when_source_fixes_section(engine: Any) -> None:
    grounding_mod.reset_cache()
    bad_section = _section([_claim("off-goal claim")])
    profile = IntentProfile(raw_text="understand request lifecycle")

    provider = _ScriptedProvider(
        grounding_results=[
            '{"decision":"supported","reason":"line 1"}',
            '{"decision":"supported","reason":"line 2"}',
        ],
        actionability_results=[
            '{"verdict":"not_actionable","reason":"off-goal"}',
            '{"verdict":"actionable","reason":"now on-goal"}',
        ],
    )

    async def retry(section: TourSection, objections: list[VerifierObjection]) -> TourSection:
        fixed = section.model_copy(deep=True)
        fixed.claims[0].text = "request lifecycle ends in transport.send()"
        return fixed

    result = await verify_section_with_retries(
        bad_section,
        profile,
        provider=cast(LLMProvider, provider),
        engine=engine,
        repo_id="r1",
        retry=retry,
    )
    assert result.passed
    assert result.claims[0].status == "verified"


@pytest.mark.asyncio
async def test_no_retry_callback_flags_immediately(engine: Any) -> None:
    grounding_mod.reset_cache()
    section = _section([_claim("off-goal")])
    provider = _ScriptedProvider(
        grounding_results=['{"decision":"supported","reason":"line 1"}'],
        actionability_results=['{"verdict":"not_actionable","reason":"off-goal"}'],
    )

    result = await verify_section_with_retries(
        section,
        IntentProfile(raw_text="anything"),
        provider=cast(LLMProvider, provider),
        engine=engine,
        repo_id="r1",
        retry=None,
    )
    assert not result.passed
    # With retry=None the loop bails out without consuming the budget,
    # so the result is "rejected" — the caller decides what to do with
    # it. Flagging requires the budget to actually have been spent.
    assert result.claims[0].status == "rejected"


# ─── Parse-fail safety net ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_actionability_parse_fail_marks_not_actionable(engine: Any) -> None:
    grounding_mod.reset_cache()
    section = _section([_claim("claim that grounds fine")])
    provider = _ScriptedProvider(
        grounding_results=['{"decision":"supported","reason":"line 1"}'],
        actionability_results=["I cannot grade that."],  # unparseable
    )
    result = await verify_section(
        section,
        IntentProfile(raw_text="anything"),
        provider=cast(LLMProvider, provider),
        engine=engine,
        repo_id="r1",
    )
    assert not result.passed
    assert "actionability_parse_error" in result.objections[0].reason


def test_actionability_verdict_model_round_trip() -> None:
    v = ActionabilityVerdict(verdict="actionable", reason="ok")
    assert v.verdict == "actionable"


def test_loop_module_re_exports_retries_constant() -> None:
    assert loop_mod.MAX_SOURCE_RETRIES == 2
