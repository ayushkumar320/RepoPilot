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
# **HF is NOT in any chat chain in v1.** The HF Inference Providers gateway
# has a tiny free-tier credit budget (~$0.10/mo) that a single bench run can
# exhaust. Chat chains stop at Cerebras — if BOTH Groq and Cerebras are 429,
# raise `ProviderError` cleanly instead of silently draining HF credits.
# The user can re-add HF explicitly when they have credits.
#
# EMBEDDINGS keeps the HUGGINGFACE ProviderName because that path is served
# by the in-process sentence-transformers embedder (HF model weights, no HTTP,
# no credits burned). See LLMProvider.embed().
RESOLUTION: dict[ModelId, tuple[ModelBinding, ...]] = {
    ModelId.INTENT_PROFILER: (
        ModelBinding(ProviderName.GROQ, "llama-3.3-70b-versatile"),
        ModelBinding(ProviderName.CEREBRAS, "llama-3.3-70b"),
    ),
    ModelId.CAPABILITY_PLANNER: (
        ModelBinding(ProviderName.GROQ, "llama-3.3-70b-versatile"),
        ModelBinding(ProviderName.CEREBRAS, "llama-3.3-70b"),
    ),
    ModelId.CARTOGRAPHER: (
        ModelBinding(ProviderName.GROQ, "llama-3.3-70b-versatile"),
        ModelBinding(ProviderName.CEREBRAS, "llama-3.3-70b"),
        ModelBinding(ProviderName.CEREBRAS, "llama-4-scout-17b-16e-instruct"),
    ),
    ModelId.FLOW_TRACER: (
        ModelBinding(ProviderName.GROQ, "qwen/qwen3-32b"),
        ModelBinding(ProviderName.CEREBRAS, "qwen-3-32b"),
        ModelBinding(ProviderName.CEREBRAS, "gpt-oss-120b"),
    ),
    ModelId.TEACHER: (
        ModelBinding(ProviderName.GROQ, "llama-3.3-70b-versatile"),
        ModelBinding(ProviderName.CEREBRAS, "llama-3.3-70b"),
        ModelBinding(ProviderName.CEREBRAS, "llama-4-scout-17b-16e-instruct"),
    ),
    # QA_PRIMARY chain broadened for bench stability on fastapi (2026-07-11):
    # Groq llama-3.3-70b is aggressively rate-limited on free tier, and the
    # previous Cerebras fallback (`gemma-4-31b`) does not exist in the Cerebras
    # catalog — 429s therefore had nowhere to land. Chain now hops through two
    # Cerebras models (different rate buckets) before a Groq gpt-oss shim.
    ModelId.QA_PRIMARY: (
        ModelBinding(ProviderName.GROQ, "llama-3.3-70b-versatile"),
        ModelBinding(ProviderName.CEREBRAS, "llama-3.3-70b"),
        ModelBinding(ProviderName.CEREBRAS, "llama-4-scout-17b-16e-instruct"),
        ModelBinding(ProviderName.GROQ, "openai/gpt-oss-20b"),
    ),
    ModelId.QA_FALLBACK: (
        ModelBinding(ProviderName.GROQ, "qwen/qwen3-32b"),
        ModelBinding(ProviderName.CEREBRAS, "qwen-3-32b"),
        ModelBinding(ProviderName.CEREBRAS, "gpt-oss-120b"),
    ),
    ModelId.CODE_HEALTH: (
        ModelBinding(ProviderName.GROQ, "llama-3.1-8b-instant"),
        ModelBinding(ProviderName.CEREBRAS, "llama-4-scout-17b-16e-instruct"),
        ModelBinding(ProviderName.GROQ, "openai/gpt-oss-20b"),
    ),
    # Verifier is the highest call-volume agent. Groq qwen3-32b is the primary
    # for its strict-JSON discipline; Cerebras qwen-3-32b matches semantics for
    # the failover, and gpt-oss-120b is the last-resort shim.
    ModelId.VERIFIER: (
        ModelBinding(ProviderName.GROQ, "qwen/qwen3-32b"),
        ModelBinding(ProviderName.CEREBRAS, "qwen-3-32b"),
        ModelBinding(ProviderName.CEREBRAS, "gpt-oss-120b"),
    ),
    # Embeddings run in-process via sentence-transformers (HF model weights).
    # physical_model is the HF model id passed to SentenceTransformer().
    # nomic-embed-text-v1.5 is 768-dim, matches the existing pgvector schema.
    ModelId.EMBEDDINGS: (ModelBinding(ProviderName.HUGGINGFACE, "nomic-ai/nomic-embed-text-v1.5"),),
}


# Opt-in HF Inference Providers chat fallback, appended to a model's chain only
# when settings.llm_hf_chat_fallback is set (see LLMProvider._resolution_for).
# Kept OUT of RESOLUTION so default behavior is unchanged and HF credits are
# never touched unless the operator explicitly enables it. Physical ids are the
# HF router names mirroring each model's Groq primary (verified on the router):
#   llama-3.3-70b → Llama-3.3-70B-Instruct, qwen/qwen3-32b → Qwen3-32B,
#   llama-3.1-8b-instant → Llama-3.1-8B-Instruct.
HF_CHAT_FALLBACK: dict[ModelId, ModelBinding] = {
    ModelId.INTENT_PROFILER: ModelBinding(
        ProviderName.HUGGINGFACE, "meta-llama/Llama-3.3-70B-Instruct"
    ),
    ModelId.CAPABILITY_PLANNER: ModelBinding(
        ProviderName.HUGGINGFACE, "meta-llama/Llama-3.3-70B-Instruct"
    ),
    ModelId.CARTOGRAPHER: ModelBinding(
        ProviderName.HUGGINGFACE, "meta-llama/Llama-3.3-70B-Instruct"
    ),
    ModelId.FLOW_TRACER: ModelBinding(ProviderName.HUGGINGFACE, "Qwen/Qwen3-32B"),
    ModelId.TEACHER: ModelBinding(ProviderName.HUGGINGFACE, "meta-llama/Llama-3.3-70B-Instruct"),
    ModelId.QA_PRIMARY: ModelBinding(ProviderName.HUGGINGFACE, "meta-llama/Llama-3.3-70B-Instruct"),
    ModelId.QA_FALLBACK: ModelBinding(ProviderName.HUGGINGFACE, "Qwen/Qwen3-32B"),
    ModelId.CODE_HEALTH: ModelBinding(ProviderName.HUGGINGFACE, "meta-llama/Llama-3.1-8B-Instruct"),
    ModelId.VERIFIER: ModelBinding(ProviderName.HUGGINGFACE, "Qwen/Qwen3-32B"),
}
