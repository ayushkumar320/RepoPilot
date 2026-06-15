"""Logical model identifiers and their physical-model resolution per provider.

Agents NEVER reference a physical model name. They ask for a `ModelId`; the
provider resolves it to the concrete model on Groq / Cerebras / Ollama. This
indirection is what makes the failover chain transparent — see
`docs/02_TECH_STACK.md` and `docs/03_ARCHITECTURE.md` (Agent table).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ProviderName(StrEnum):
    GROQ = "groq"
    CEREBRAS = "cerebras"
    OLLAMA = "ollama"


class ModelId(StrEnum):
    """Logical, agent-facing model identifiers."""

    INTENT_PROFILER = "intent_profiler"
    CAPABILITY_PLANNER = "capability_planner"
    CARTOGRAPHER = "cartographer"
    FLOW_TRACER = "flow_tracer"
    TEACHER = "teacher"
    QA_PRIMARY = "qa_primary"
    QA_FALLBACK = "qa_fallback"
    CODE_HEALTH = "code_health"
    VERIFIER = "verifier"
    EMBEDDINGS = "embeddings"


@dataclass(frozen=True, slots=True)
class ModelBinding:
    """The concrete model name to send to a given provider for one `ModelId`."""

    provider: ProviderName
    physical_model: str


# Per-model resolution chain. The first entry is the preferred provider; the
# remaining entries are tried in order on RateLimitError / connection failure.
#
# Cerebras has only two free-tier models in v1 (llama-3.3-70b, llama-3.1-8b);
# missing Cerebras entries fall straight through to Ollama. For VERIFIER and
# EMBEDDINGS the chain is Ollama-only — Groq doesn't host them.
RESOLUTION: dict[ModelId, tuple[ModelBinding, ...]] = {
    ModelId.INTENT_PROFILER: (
        ModelBinding(ProviderName.GROQ, "llama-3.3-70b-versatile"),
        ModelBinding(ProviderName.CEREBRAS, "llama-3.3-70b"),
        ModelBinding(ProviderName.OLLAMA, "qwen2.5-coder:7b"),
    ),
    ModelId.CAPABILITY_PLANNER: (
        ModelBinding(ProviderName.GROQ, "llama-3.3-70b-versatile"),
        ModelBinding(ProviderName.CEREBRAS, "llama-3.3-70b"),
        ModelBinding(ProviderName.OLLAMA, "qwen2.5-coder:7b"),
    ),
    ModelId.CARTOGRAPHER: (
        ModelBinding(ProviderName.GROQ, "llama-3.3-70b-versatile"),
        ModelBinding(ProviderName.CEREBRAS, "llama-3.3-70b"),
        ModelBinding(ProviderName.OLLAMA, "qwen2.5-coder:7b"),
    ),
    ModelId.FLOW_TRACER: (
        ModelBinding(ProviderName.GROQ, "qwen/qwen3-32b"),
        ModelBinding(ProviderName.OLLAMA, "qwen2.5-coder:7b"),
    ),
    ModelId.TEACHER: (
        ModelBinding(ProviderName.GROQ, "llama-3.3-70b-versatile"),
        ModelBinding(ProviderName.CEREBRAS, "llama-3.3-70b"),
        ModelBinding(ProviderName.OLLAMA, "qwen2.5-coder:7b"),
    ),
    ModelId.QA_PRIMARY: (
        ModelBinding(ProviderName.GROQ, "llama-3.3-70b-versatile"),
        ModelBinding(ProviderName.CEREBRAS, "llama-3.3-70b"),
        ModelBinding(ProviderName.OLLAMA, "qwen2.5-coder:7b"),
    ),
    ModelId.QA_FALLBACK: (
        ModelBinding(ProviderName.GROQ, "qwen/qwen3-32b"),
        ModelBinding(ProviderName.OLLAMA, "qwen2.5-coder:7b"),
    ),
    ModelId.CODE_HEALTH: (
        ModelBinding(ProviderName.GROQ, "llama-3.1-8b-instant"),
        ModelBinding(ProviderName.CEREBRAS, "llama-3.1-8b"),
        ModelBinding(ProviderName.OLLAMA, "qwen2.5-coder:7b"),
    ),
    ModelId.VERIFIER: (ModelBinding(ProviderName.OLLAMA, "qwen2.5-coder:7b"),),
    ModelId.EMBEDDINGS: (ModelBinding(ProviderName.OLLAMA, "nomic-embed-text"),),
}
