"""RAG Phase 2 query understanding.

The query-spec step turns a terse user question into a small set of retrieval
queries plus optional metadata hints. It is deliberately fail-open: if the
small model returns invalid JSON or the provider is unavailable, retrieval uses
the raw question exactly as before.
"""

from __future__ import annotations

import json
import re
from typing import Literal

from pydantic import BaseModel, Field, ValidationError, field_validator

from repopilot_agents.qa.prompts import QUERY_SPEC_SYSTEM, query_spec_user_prompt
from repopilot_core.llm.models import ModelId
from repopilot_core.llm.provider import LLMProvider, Message

IntentClass = Literal["factual", "procedural", "architectural", "where_is", "compare"]

_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)
_BACKTICK_RE = re.compile(r"`([^`]+)`")
_PATH_HINT_RE = re.compile(r"[\w./-]+\.py\b")


class QuerySpec(BaseModel):
    """Structured retrieval plan for one user question."""

    raw_text: str
    rewrites: list[str] = Field(default_factory=list)
    extracted_symbols: list[str] = Field(default_factory=list)
    extracted_paths: list[str] = Field(default_factory=list)
    intent_class: IntentClass = "factual"
    needs_multi_hop: bool = False

    @field_validator("raw_text")
    @classmethod
    def _raw_not_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("raw_text must not be empty")
        return cleaned

    @field_validator("rewrites", "extracted_symbols", "extracted_paths")
    @classmethod
    def _clean_unique_strings(cls, values: list[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for value in values:
            cleaned = value.strip()
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            out.append(cleaned)
        return out

    def retrieval_queries(self, *, max_rewrites: int = 3) -> list[str]:
        """Return raw question + deduped rewrites, capped for latency."""
        queries: list[str] = []
        seen: set[str] = set()
        for query in [self.raw_text, *self.rewrites[:max_rewrites]]:
            cleaned = query.strip()
            key = cleaned.lower()
            if cleaned and key not in seen:
                queries.append(cleaned)
                seen.add(key)
        return queries or [self.raw_text]


def fallback_query_spec(question: str) -> QuerySpec:
    """Build a no-LLM spec from the raw question and obvious inline hints."""
    symbols: list[str] = []
    paths: list[str] = []
    for hint in _BACKTICK_RE.findall(question):
        if "/" in hint or hint.endswith(".py"):
            paths.append(hint)
        elif "." in hint or "_" in hint:
            symbols.append(hint)
    paths.extend(_PATH_HINT_RE.findall(question))
    return QuerySpec(
        raw_text=question,
        rewrites=[],
        extracted_symbols=symbols,
        extracted_paths=paths,
        intent_class=_infer_intent(question),
        needs_multi_hop=_looks_multi_hop(question),
    )


async def build_query_spec(question: str, *, provider: LLMProvider) -> QuerySpec:
    """Ask the cheap model for a query spec, falling back to raw retrieval."""
    fallback = fallback_query_spec(question)
    try:
        response = await provider.generate(
            ModelId.CODE_HEALTH,
            [
                Message("system", QUERY_SPEC_SYSTEM),
                Message("user", query_spec_user_prompt(question)),
            ],
            temperature=0.0,
            max_tokens=512,
        )
    except Exception:
        return fallback

    parsed = _parse_query_spec(response.text, raw_text=question)
    if parsed is None:
        return fallback
    if parsed.raw_text != question:
        parsed = parsed.model_copy(update={"raw_text": question})
    return _merge_fallback_hints(parsed, fallback)


def _parse_query_spec(raw: str, *, raw_text: str) -> QuerySpec | None:
    match = _JSON_RE.search(raw)
    if match is None:
        return None
    try:
        data = json.loads(match.group(0))
        data["raw_text"] = raw_text
        return QuerySpec.model_validate(data)
    except (json.JSONDecodeError, TypeError, ValidationError):
        return None


def _merge_fallback_hints(spec: QuerySpec, fallback: QuerySpec) -> QuerySpec:
    symbols = [*spec.extracted_symbols, *fallback.extracted_symbols]
    paths = [*_normalize_paths(spec.extracted_paths), *_normalize_paths(fallback.extracted_paths)]
    return spec.model_copy(
        update={
            "extracted_symbols": QuerySpec(
                raw_text=spec.raw_text, extracted_symbols=symbols
            ).extracted_symbols,
            "extracted_paths": QuerySpec(raw_text=spec.raw_text, extracted_paths=paths).extracted_paths,
            "needs_multi_hop": spec.needs_multi_hop or fallback.needs_multi_hop,
        }
    )


def _normalize_paths(paths: list[str]) -> list[str]:
    return [path.removeprefix("./") for path in paths]


def _infer_intent(question: str) -> IntentClass:
    lowered = question.lower()
    if any(word in lowered for word in ("compare", "difference", "versus", " vs ")):
        return "compare"
    if any(word in lowered for word in ("where", "located", "defined")):
        return "where_is"
    if any(word in lowered for word in ("flow", "trace", "call", "through", "lifecycle")):
        return "architectural"
    if any(word in lowered for word in ("how", "steps", "process")):
        return "procedural"
    return "factual"


def _looks_multi_hop(question: str) -> bool:
    lowered = question.lower()
    return any(
        phrase in lowered
        for phrase in (
            "how does",
            "flow",
            "trace",
            "from ",
            "through",
            "interact",
            "between",
            "end to end",
        )
    )


__all__ = ["IntentClass", "QuerySpec", "build_query_spec", "fallback_query_spec"]
