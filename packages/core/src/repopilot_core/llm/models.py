"""Logical model identifiers and their physical-model resolution per provider.

Agents NEVER reference a physical model name. They ask for a `ModelId`; the
provider resolves it to the concrete model on Groq / Cerebras / Hugging Face.
This indirection is what makes the failover chain transparent — see
`docs/02_TECH_STACK.md` and `docs/03_ARCHITECTURE.md` (Agent table).

Provider fallback chain in v1:
    Groq → Cerebras → Hugging Face (Inference Providers)
Embeddings: sentence-transformers in-process (no HTTP, no daemon).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ProviderName(StrEnum):
    GROQ = "groq"
    CEREBRAS = "cerebras"
    HUGGINGFACE = "huggingface"


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
# Hugging Face's Inference Providers gateway (https://router.huggingface.co/v1)
# is OpenAI-compatible and routes to underlying providers (Together, Replicate,
# Cerebras, etc.). It is the universal final fallback for chat models.
#
# EMBEDDINGS uses sentence-transformers in-process; the binding's physical
# model is the HF model id passed to `SentenceTransformer(...)`. No HTTP.
RESOLUTION: dict[ModelId, tuple[ModelBinding, ...]] = {
    ModelId.INTENT_PROFILER: (
        ModelBinding(ProviderName.GROQ, "llama-3.3-70b-versatile"),
        ModelBinding(ProviderName.HUGGINGFACE, "meta-llama/Llama-3.3-70B-Instruct"),
    ),
    ModelId.CAPABILITY_PLANNER: (
        ModelBinding(ProviderName.GROQ, "llama-3.3-70b-versatile"),
        ModelBinding(ProviderName.HUGGINGFACE, "meta-llama/Llama-3.3-70B-Instruct"),
    ),
    ModelId.CARTOGRAPHER: (
        ModelBinding(ProviderName.GROQ, "llama-3.3-70b-versatile"),
        ModelBinding(ProviderName.HUGGINGFACE, "meta-llama/Llama-3.3-70B-Instruct"),
    ),
    ModelId.FLOW_TRACER: (
        ModelBinding(ProviderName.GROQ, "qwen/qwen3-32b"),
        ModelBinding(ProviderName.HUGGINGFACE, "Qwen/Qwen2.5-Coder-32B-Instruct"),
    ),
    ModelId.TEACHER: (
        ModelBinding(ProviderName.GROQ, "llama-3.3-70b-versatile"),
        ModelBinding(ProviderName.HUGGINGFACE, "meta-llama/Llama-3.3-70B-Instruct"),
    ),
    ModelId.QA_PRIMARY: (
        ModelBinding(ProviderName.GROQ, "llama-3.3-70b-versatile"),
        ModelBinding(ProviderName.CEREBRAS, "gpt-oss-120b"),
        ModelBinding(ProviderName.HUGGINGFACE, "meta-llama/Llama-3.3-70B-Instruct"),
    ),
    ModelId.QA_FALLBACK: (
        ModelBinding(ProviderName.GROQ, "qwen/qwen3-32b"),
        ModelBinding(ProviderName.HUGGINGFACE, "Qwen/Qwen2.5-Coder-32B-Instruct"),
    ),
    ModelId.CODE_HEALTH: (
        ModelBinding(ProviderName.GROQ, "llama-3.1-8b-instant"),
        ModelBinding(ProviderName.HUGGINGFACE, "meta-llama/Llama-3.1-8B-Instruct"),
    ),
    # Verifier is the highest call-volume agent. We use Groq's qwen-coder for
    # cost (fast) with HF as the durable fallback. No Ollama daemon required.
    # Cerebras sits between them: the verifier chain must survive Groq 429
    # bursts without reaching HF (which may be out of credits — 402).
    # gemma-4-31b over gpt-oss-120b here: no thinking tokens, so the
    # verifier's strict JSON parse (parse-fail = reject) stays reliable.
    ModelId.VERIFIER: (
        ModelBinding(ProviderName.GROQ, "qwen/qwen3-32b"),
        ModelBinding(ProviderName.CEREBRAS, "gemma-4-31b"),
        ModelBinding(ProviderName.HUGGINGFACE, "Qwen/Qwen2.5-Coder-7B-Instruct"),
    ),
    # Embeddings run in-process via sentence-transformers (HF model weights).
    # physical_model is the HF model id passed to SentenceTransformer().
    # nomic-embed-text-v1.5 is 768-dim, matches the existing pgvector schema.
    ModelId.EMBEDDINGS: (ModelBinding(ProviderName.HUGGINGFACE, "nomic-ai/nomic-embed-text-v1.5"),),
}
