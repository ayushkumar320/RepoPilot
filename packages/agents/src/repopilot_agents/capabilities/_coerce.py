"""Shared LLM-output coercion helpers for capability nodes.

Every node asks the LLM for a strict JSON list. Both Groq and HF
occasionally emit code-fenced or trailing-prose output, so we extract
the first ``[...]`` payload and drop entries that don't validate. The
verifier loop catches anything semantically wrong; this layer just
keeps the pipeline from crashing on schema drift.
"""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import ValidationError

from repopilot_agents.state import Claim, CodeRef, Insight

_JSON_LIST_RE = re.compile(r"\[.*\]", re.DOTALL)


def extract_json_list(raw: str) -> list[dict[str, Any]]:
    """Pull the first JSON array out of ``raw`` and return it as a list of
    dicts. Returns an empty list on parse failure — never raises."""
    match = _JSON_LIST_RE.search(raw)
    if match is None:
        return []
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, dict)]


def _coerce_ref(value: Any, allowed_refs: dict[str, CodeRef]) -> CodeRef | None:
    """Validate a ref. If the LLM names a symbol, prefer the known CodeRef
    for that symbol over the model's possibly-hallucinated line numbers."""
    if isinstance(value, str) and value in allowed_refs:
        return allowed_refs[value]
    if not isinstance(value, dict):
        return None
    symbol = value.get("symbol")
    if isinstance(symbol, str) and symbol in allowed_refs:
        # Trust the structural ref over the LLM's numbers.
        return allowed_refs[symbol]
    try:
        return CodeRef(
            file_path=value["file_path"],
            start_line=int(value["start_line"]),
            end_line=int(value["end_line"]),
            symbol=value.get("symbol"),
        )
    except (KeyError, TypeError, ValueError, ValidationError):
        return None


def coerce_refs(value: Any, allowed_refs: dict[str, CodeRef]) -> list[CodeRef]:
    if not isinstance(value, list):
        return []
    out: list[CodeRef] = []
    for item in value:
        ref = _coerce_ref(item, allowed_refs)
        if ref is not None:
            out.append(ref)
    return out


def coerce_insight(payload: dict[str, Any], allowed_refs: dict[str, CodeRef]) -> Insight | None:
    """Validate a single ``Insight`` payload. Returns ``None`` if any
    required field is missing or empty — empty so_what/goal_link is a
    hard fail per the state-schema rules."""
    refs = coerce_refs(payload.get("refs"), allowed_refs)
    if not refs:
        return None
    try:
        return Insight(
            finding=str(payload.get("finding", "")).strip(),
            because=str(payload.get("because", "")).strip(),
            so_what=str(payload.get("so_what", "")).strip(),
            refs=refs,
            goal_link=str(payload.get("goal_link", "")).strip(),
        )
    except ValidationError:
        return None


def coerce_claim(payload: dict[str, Any], allowed_refs: dict[str, CodeRef]) -> Claim | None:
    refs = coerce_refs(payload.get("refs"), allowed_refs)
    if not refs:
        return None
    try:
        return Claim(text=str(payload.get("text", "")).strip(), refs=refs)
    except ValidationError:
        return None


__all__ = [
    "coerce_claim",
    "coerce_insight",
    "coerce_refs",
    "extract_json_list",
]
