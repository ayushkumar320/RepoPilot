"""Intent Profiler — free-text intent → structured ``IntentProfile``.

The Profiler is the first node every user hits. It reads
``state.user_question`` (or, in the standard flow, the user's intent
statement captured at session start) and returns a draft ``IntentProfile``
the user will confirm via the chip strip.

Design notes:

- **Single LLM call.** Low temperature, capped tokens. JSON-only response —
  same shape as the verifier, so the failure mode is consistent: parse fail
  → fall back to the maximally-inclusive minimal profile (raw_text only)
  rather than guess.
- **Bounded to the state schema.** Modality keys MUST come from
  ``state.Modality``; output shapes from ``state.OutputShape``. Anything
  else gets dropped at validation time. That keeps the planner's
  deterministic rules sound.
- **No purpose enum.** The profiler never returns a "purpose". The
  planner consumes weights + keywords + framing.
"""

from __future__ import annotations

import json
import re
from typing import Any, get_args

from pydantic import ValidationError

from repopilot_agents.state import IntentProfile, Modality, OutputShape
from repopilot_core.llm.models import ModelId
from repopilot_core.llm.provider import LLMProvider, Message

_VALID_MODALITIES: frozenset[str] = frozenset(get_args(Modality))
_VALID_OUTPUT_SHAPES: frozenset[str] = frozenset(get_args(OutputShape))

_SYSTEM_PROMPT = (
    "You are the intent profiler for a guided code-onboarding system. "
    "The user has stated, in free text, what they want from a repository "
    "tour. Your job is to translate that statement into a STRICT JSON "
    "object with these fields and no others:\n"
    "  - modality_weights: object mapping a subset of "
    f"[{', '.join(sorted(_VALID_MODALITIES))}] to floats in [0, 1]. "
    "Weights need not sum to 1. Use only the keys listed. The dominant key "
    "decides how every answer is written, so pick it deliberately: "
    "change = they will edit this code; understand = they are building a "
    "mental model; evaluate = they are judging fitness, risk, or quality; "
    "locate = they want exact positions in the tree; compare = they are "
    "weighing this against something else.\n"
    "  - focus_keywords: array of 1–6 short noun phrases lifted from the "
    "user's statement (lowercase, no punctuation).\n"
    "  - audience_framing: short string naming WHO is reading, in their "
    "role (e.g. 'a first-time outside contributor', 'a security engineer "
    "doing a first pass'), or null.\n"
    "  - output_shape_preference: one of "
    f"[{', '.join(sorted(_VALID_OUTPUT_SHAPES))}].\n"
    "  - success_criterion: a short measurable goal you infer, or null.\n\n"
    "Do not invent any field not in this list. Do not include commentary. "
    "Respond with a single JSON object on one line."
)


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse_json(raw: str) -> dict[str, Any] | None:
    match = _JSON_RE.search(raw)
    if match is None:
        return None
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _coerce_modality_weights(value: Any) -> dict[str, float]:
    """Drop unknown modality keys; coerce values into the unit interval.

    Drift-tolerant on purpose: an 8B model that hallucinates a new key
    shouldn't poison the whole profile. We keep the valid pairs and
    silently discard the rest — the planner only reads what's left.
    """
    if not isinstance(value, dict):
        return {}
    out: dict[str, float] = {}
    for k, v in value.items():
        if k not in _VALID_MODALITIES:
            continue
        try:
            weight = float(v)
        except (TypeError, ValueError):
            continue
        out[k] = max(0.0, min(1.0, weight))
    return out


def _coerce_keywords(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    cleaned: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        stripped = item.strip().lower()
        if stripped:
            cleaned.append(stripped)
    return cleaned[:6]


def _coerce_output_shape(value: Any) -> OutputShape:
    if isinstance(value, str) and value in _VALID_OUTPUT_SHAPES:
        return value  # type: ignore[return-value]
    return "unspecified"


def _coerce_optional_str(value: Any) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None


def _fallback_profile(raw_text: str) -> IntentProfile:
    """The minimal-but-valid profile used when the LLM fails us.

    Matches the "intent edit-loop fallback" contract from
    ``docs/03_ARCHITECTURE.md``: ``raw_text`` populated, everything else
    empty — the Planner's fallthrough rule then activates the inclusive
    default plan downstream.
    """
    return IntentProfile(raw_text=raw_text)


async def profile_intent(
    raw_text: str,
    *,
    provider: LLMProvider,
) -> IntentProfile:
    """Run the Profiler once on ``raw_text``.

    Returns a draft ``IntentProfile``. The UI surfaces this as a chip
    strip for user confirmation before the planner consumes it.

    On any failure (empty input, LLM unavailable, parse error, validation
    failure) returns the minimal ``IntentProfile(raw_text=raw_text)``.
    Never raises.
    """
    raw_text = raw_text.strip()
    if not raw_text:
        # The caller is responsible for not running the profiler with no
        # input. If they do, fail loudly — the alternative is a
        # min_length=1 ValidationError from IntentProfile, which is what
        # we'd want anyway.
        raise ValueError("profile_intent requires a non-empty raw_text")

    response = await provider.generate(
        ModelId.INTENT_PROFILER,
        [
            Message("system", _SYSTEM_PROMPT),
            Message("user", raw_text),
        ],
        temperature=0.1,
        max_tokens=400,
    )

    payload = _parse_json(response.text)
    if payload is None:
        return _fallback_profile(raw_text)

    try:
        return IntentProfile(
            raw_text=raw_text,
            modality_weights=_coerce_modality_weights(payload.get("modality_weights")),
            focus_keywords=_coerce_keywords(payload.get("focus_keywords")),
            audience_framing=_coerce_optional_str(payload.get("audience_framing")),
            output_shape_preference=_coerce_output_shape(payload.get("output_shape_preference")),
            success_criterion=_coerce_optional_str(payload.get("success_criterion")),
        )
    except ValidationError:
        return _fallback_profile(raw_text)


__all__ = ["profile_intent"]
