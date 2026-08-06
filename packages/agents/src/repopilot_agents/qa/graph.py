"""Q&A LangGraph mini-graph — the Phase 2 spine.

```
vector_search → graph_traverse → judge_sufficiency
                                       │
                       insufficient ←──┴──→ sufficient
                          │                     │
                     (expand: ≤3 hops)     answer → verifier
                          │                     │
                          ▼                     ▼
                     graph_traverse        QAResult
```

* Hop budget: hard counter at 3 outer iterations.
* The sufficiency judge is the SAME Q&A primary model (decision **D3**).
* The verifier runs at the end via ``verifier.grounding.verify_claims``;
  rejected claims are tagged ``flagged`` (never silently dropped).

Phase 2 ships this as a callable ``answer_question()`` rather than a full
LangGraph ``StateGraph`` — the state schema lives in Phase 3 and pulling it
forward would duplicate work. The control flow here is exactly what Phase 3
will wrap, so swapping in ``StateGraph`` later is a refactor, not a rewrite.
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field

import structlog
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncEngine

from repopilot_agents.qa.compress import compress_chunks
from repopilot_agents.qa.prompts import (
    SUFFICIENCY_SYSTEM,
    answer_system,
    answer_user_prompt,
    sufficiency_user_prompt,
)
from repopilot_agents.qa.query_spec import QuerySpec, build_query_spec, fallback_query_spec
from repopilot_agents.qa.types import SufficiencyVerdict
from repopilot_agents.qa.union import reciprocal_rank_fusion
from repopilot_agents.rerank.pipeline import rerank_and_diversify
from repopilot_agents.state import IntentProfile
from repopilot_agents.tools.graph_traverse import graph_traverse
from repopilot_agents.tools.hybrid_search import hybrid_search
from repopilot_agents.tools.read_chunks import read_chunks
from repopilot_agents.tools.vector_search import NON_SOURCE_PATH_PREFIXES, vector_search
from repopilot_agents.types import ChunkContent, ChunkHit, CodeRef
from repopilot_agents.verifier.grounding import (
    VERIFIER_PROVIDER_ERROR_REASON,
    Claim,
    VerifierObjection,
    verify_claims,
)
from repopilot_core.llm.models import ModelId
from repopilot_core.llm.provider import LLMProvider, Message
from repopilot_core.settings import get_settings

log = structlog.get_logger(__name__)


MAX_HOPS = 3
# RAG Phase 1: pool width fetched from pgvector. The prompt slice stays at
# ``k`` — Phase 5's compression will consume the full pool; until then the
# graph trims the top-k itself.
RECALL_K = 50
NOT_FOUND_SENTINEL = "I couldn't find that in the repo."
# The answer prompt requires a [N] citation on every claim line (see
# ``answer_user_prompt``). When the model drops one anyway, we used to pin
# the claim to ``pool[0]`` and run it through the verifier — which then
# rejected it for not matching a chunk it was never about, mislabeling a
# possibly-true claim as "flagged". Skip verification for these instead.
UNCITED_CLAIM_REASON = "no_citation_in_answer"


class QAResult(BaseModel):
    """The end-to-end output of one Q&A run."""

    question: str
    answer: str
    claims: list[Claim] = Field(default_factory=list)
    objections: list[VerifierObjection] = Field(default_factory=list)
    hops: int = 0
    retrieval_path: list[str] = Field(default_factory=list)
    answer_input_tokens: int = 0
    # Wall-clock ms per pipeline stage (see STAGES). Loop stages accumulate
    # across hops. The latency eval aggregates these into per-stage p50/p95;
    # without them a p95 regression tells you only *that* the budget slipped,
    # never *which* stage ate it.
    stage_timings_ms: dict[str, float] = Field(default_factory=dict)


# Stage keys recorded in ``QAResult.stage_timings_ms``. Ordered as the
# pipeline runs them so reports read top-to-bottom.
STAGES = (
    "retrieval",
    "rerank",
    "read_chunks",
    "compress",
    "sufficiency",
    "expand",
    "answer",
    "verify",
)


@dataclass(slots=True)
class _Context:
    seen_refs: set[tuple[str, int, int]]
    chunks: list[ChunkContent]
    retrieval_path: list[str]
    stage_ms: dict[str, float] = field(default_factory=dict)


@contextmanager
def _timed(ctx: _Context, stage: str) -> Iterator[None]:
    """Accumulate wall-clock ms for ``stage`` onto ``ctx``.

    Accumulates rather than overwrites: ``sufficiency`` and ``expand`` run
    once per hop, and the interesting number is their total contribution.
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = (time.perf_counter() - start) * 1000
        ctx.stage_ms[stage] = ctx.stage_ms.get(stage, 0.0) + elapsed


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


async def answer_question(
    question: str,
    *,
    engine: AsyncEngine,
    provider: LLMProvider,
    repo_id: str,
    k: int = 8,
    max_hops: int = MAX_HOPS,
    recall_k: int | None = RECALL_K,
    exclude_path_prefixes: Sequence[str] = NON_SOURCE_PATH_PREFIXES,
    use_hybrid: bool = True,
    use_query_understanding: bool | None = None,
    use_rerank: bool = True,
    use_compress: bool = True,
    retry_429_attempts: int | None = None,
    intent_profile: IntentProfile | None = None,
) -> QAResult:
    """Run the hybrid-retrieval Q&A loop for ``question``.

    ``recall_k`` / ``exclude_path_prefixes`` default to the Phase 1 policy
    (wide source-only pool). Passing ``recall_k=None`` and
    ``exclude_path_prefixes=()`` reproduces the pre-Phase-1 ``k``-only
    retrieval — used by the eval to baseline both arms under one verifier.

    ``use_hybrid`` (Phase 3) fuses a BM25 sparse lane with the dense lane via
    RRF. Requires ``recall_k`` (BM25 needs a pool); with ``recall_k=None`` it
    falls back to pure dense, so the pre-Phase-1 baseline arm stays dense-only.
    Set ``use_hybrid=False`` for the Phase 1/2 dense-only ``_before`` arm.

    ``use_query_understanding`` (Phase 2) asks a cheap model for retrieval
    rewrites and path hints, fans retrieval out over the rewrites, then fuses
    the pools with RRF. ``None`` follows settings; explicit ``True``/``False``
    lets evals A/B the path. Parse/provider failures fall back to raw.

    ``use_rerank`` (Phase 4) cross-encoder-reranks + MMR-diversifies the top
    of the pool before the prompt slice. Requires ``recall_k`` (needs a pool
    to reorder); disabled automatically on the pre-Phase-1 baseline arm.

    ``intent_profile`` carries the reader's persona (who they are, what they
    are optimizing for). It tilts the answer's emphasis and ordering only —
    retrieval, citation, and verification are identical with or without it, so
    two personas asking the same question get the same facts, prioritized
    differently. ``None`` reproduces the pre-persona prompt byte-for-byte.

    ``use_compress`` (Phase 5) narrows the answerer's view of each chunk to
    load-bearing lines only. ``ChunkContent.content`` remains full text so the
    verifier still checks claims against the whole source chunk.
    """
    settings = get_settings()
    ctx = _Context(seen_refs=set(), chunks=[], retrieval_path=[])

    with _timed(ctx, "retrieval"):
        hits = await _initial_retrieval(
            question,
            engine=engine,
            provider=provider,
            repo_id=repo_id,
            k=k,
            recall_k=recall_k,
            exclude_path_prefixes=exclude_path_prefixes,
            use_hybrid=use_hybrid,
            use_query_understanding=(
                settings.query_understanding_enabled
                if use_query_understanding is None
                else use_query_understanding
            ),
            max_rewrites=settings.query_understanding_max_rewrites,
            retrieval_path=ctx.retrieval_path,
        )

    if use_rerank and recall_k is not None and len(hits) > k:
        # Phase 4: fetch the top of the pool, cross-encoder rerank + MMR
        # diversify, and let the reranked order decide the prompt slice.
        with _timed(ctx, "rerank"):
            # Pool size and lambda come from settings, not the module constants:
            # until 2026-08-04 this read rerank.pipeline's DEFAULT_MAX_POOL and
            # ``Settings.rerank_max_pool`` was dead config that silently did
            # nothing. Pool size is the single biggest latency lever here --
            # it costs a read_chunks over the pool *and* a cross-encoder pass.
            max_pool = settings.rerank_max_pool
            pool_hits = hits[:max_pool]
            pool_chunks = await read_chunks(
                [h.ref for h in pool_hits], engine=engine, repo_id=repo_id
            )
            if len(pool_chunks) == len(pool_hits):
                # to_thread, not a direct call: the cross-encoder is sync CPU
                # work and its first invocation downloads the ONNX model. On
                # the event loop that stalls every other request on the worker
                # until it finishes, which the web proxy sees as a socket hang
                # up (ECONNRESET).
                ranked = await asyncio.to_thread(
                    rerank_and_diversify,
                    question,
                    pool_hits,
                    pool_chunks,
                    k=k,
                    lambda_=settings.rerank_lambda,
                    max_pool=max_pool,
                )
                ctx.retrieval_path.append(f"rerank:pool={len(pool_hits)}:k={len(ranked)}")
                initial_chunks = [content for _, content in ranked]
            else:
                # read_chunks dropped refs (stale index?) — fall back untranked.
                initial_chunks = pool_chunks[:k]
    else:
        with _timed(ctx, "read_chunks"):
            initial_chunks = await read_chunks(
                [h.ref for h in hits[:k]], engine=engine, repo_id=repo_id
            )
    if use_compress and settings.compress_enabled and initial_chunks:
        with _timed(ctx, "compress"):
            initial_chunks = await compress_chunks(
                question,
                initial_chunks,
                provider=provider,
                min_lines=settings.compress_min_chunk_lines,
                retry_429_attempts=retry_429_attempts,
            )
        ctx.retrieval_path.append(f"compress:k={len(initial_chunks)}")
    _extend_context(ctx, initial_chunks)

    # Outer loop: sufficiency judge → optional traverse expansion.
    hops = 0
    while hops < max_hops:
        with _timed(ctx, "sufficiency"):
            verdict = await _judge_sufficiency(
                provider,
                question,
                ctx.chunks,
                retry_429_attempts=retry_429_attempts,
            )
        if verdict.decision == "sufficient" or verdict.next_symbol is None:
            break

        with _timed(ctx, "expand"):
            ctx.retrieval_path.append(f"graph_traverse:{verdict.next_symbol}")
            paths = await graph_traverse(
                verdict.next_symbol,
                engine=engine,
                repo_id=repo_id,
                edge_types=("calls", "imports", "inherits"),
                max_depth=2,
            )
            if not paths:
                ctx.retrieval_path.append("graph_traverse:empty")
                break
            new_refs: list[CodeRef] = []
            for path in paths:
                for ref in path.steps:
                    key = (ref.file_path, ref.start_line, ref.end_line)
                    if key not in ctx.seen_refs and ref.file_path != "<unresolved>":
                        new_refs.append(ref)
            new_chunks = await read_chunks(new_refs, engine=engine, repo_id=repo_id)
            _extend_context(ctx, new_chunks)
        hops += 1

    answer_prompt_tokens = _estimate_tokens(answer_user_prompt(question, ctx.chunks))
    with _timed(ctx, "answer"):
        answer_text = await _generate_answer(
            provider,
            question,
            ctx.chunks,
            retry_429_attempts=retry_429_attempts,
            intent_profile=intent_profile,
        )

    if _is_not_found(answer_text):
        return QAResult(
            question=question,
            answer=NOT_FOUND_SENTINEL,
            claims=[],
            objections=[],
            hops=hops,
            retrieval_path=ctx.retrieval_path,
            answer_input_tokens=answer_prompt_tokens,
            stage_timings_ms=ctx.stage_ms,
        )

    claims = _parse_claims(answer_text, ctx.chunks)
    if not claims:
        return QAResult(
            question=question,
            answer=answer_text,
            claims=[],
            objections=[],
            hops=hops,
            retrieval_path=ctx.retrieval_path,
            answer_input_tokens=answer_prompt_tokens,
            stage_timings_ms=ctx.stage_ms,
        )

    # Uncited claims were already marked "unverified" in _parse_claims and
    # skip the verifier entirely — there's no chunk to check them against.
    to_verify = [c for c in claims if c.verifier_note != UNCITED_CLAIM_REASON]
    with _timed(ctx, "verify"):
        verify_results = await verify_claims(
            to_verify,
            provider=provider,
            engine=engine,
            repo_id=repo_id,
            retry_429_attempts=retry_429_attempts,
        )
    objections = [r.objection for r in verify_results if r.objection is not None]

    # Flag the rejected ones (still shipped, but visually marked). A claim whose
    # verification could not run because every provider was exhausted is a
    # transient infra failure, not a grounding rejection — surface it as
    # "unverified" (retry) rather than "flagged" (checked and found wanting).
    for verified in verify_results:
        if verified.claim.status == "rejected":
            verified.claim.status = (
                "unverified"
                if verified.claim.verifier_note == VERIFIER_PROVIDER_ERROR_REASON
                else "flagged"
            )

    return QAResult(
        question=question,
        answer=answer_text,
        # ``claims`` (not verify_results) — verify_claim mutates in place, and
        # this preserves original line order including the uncited claims
        # that were filtered out of to_verify.
        claims=claims,
        objections=objections,
        hops=hops,
        retrieval_path=ctx.retrieval_path,
        answer_input_tokens=answer_prompt_tokens,
        stage_timings_ms=ctx.stage_ms,
    )


# ── internals ───────────────────────────────────────────────────────────────


def _extend_context(ctx: _Context, chunks: list[ChunkContent]) -> None:
    for chunk in chunks:
        key = (chunk.ref.file_path, chunk.ref.start_line, chunk.ref.end_line)
        if key in ctx.seen_refs:
            continue
        ctx.seen_refs.add(key)
        ctx.chunks.append(chunk)


def _estimate_tokens(text: str) -> int:
    """Cheap, stable token estimate for relative Phase 5 prompt-size gating."""
    return max(1, (len(text) + 3) // 4) if text else 0


async def _initial_retrieval(
    question: str,
    *,
    engine: AsyncEngine,
    provider: LLMProvider,
    repo_id: str,
    k: int,
    recall_k: int | None,
    exclude_path_prefixes: Sequence[str],
    use_hybrid: bool,
    use_query_understanding: bool,
    max_rewrites: int,
    retrieval_path: list[str],
) -> list[ChunkHit]:
    pool = recall_k if recall_k is not None else k
    if use_query_understanding:
        spec = await build_query_spec(question, provider=provider)
    else:
        spec = fallback_query_spec(question)

    queries = spec.retrieval_queries(max_rewrites=max_rewrites if use_query_understanding else 0)
    path_prefix = _single_path_prefix(spec)

    if len(queries) == 1:
        hits = await _retrieve_one(
            queries[0],
            engine=engine,
            provider=provider,
            repo_id=repo_id,
            k=k,
            recall_k=recall_k,
            exclude_path_prefixes=exclude_path_prefixes,
            use_hybrid=use_hybrid,
            path_prefix=path_prefix,
        )
    else:
        pools = await asyncio.gather(
            *(
                _retrieve_one(
                    query,
                    engine=engine,
                    provider=provider,
                    repo_id=repo_id,
                    k=k,
                    recall_k=recall_k,
                    exclude_path_prefixes=exclude_path_prefixes,
                    use_hybrid=use_hybrid,
                    path_prefix=path_prefix,
                )
                for query in queries
            )
        )
        hits = reciprocal_rank_fusion(pools, weights=_query_lane_weights(len(pools)))[:pool]

    mode = "hybrid_search" if use_hybrid and recall_k is not None else "vector_search"
    if use_query_understanding:
        retrieval_path.append(
            "query_spec:"
            f"queries={len(queries)}:paths={len(spec.extracted_paths)}:"
            f"intent={spec.intent_class}:multi_hop={spec.needs_multi_hop}"
        )
    retrieval_path.append(f"{mode}:recall_k={pool}:k={k}:hits={len(hits)}")
    return hits


async def _retrieve_one(
    query: str,
    *,
    engine: AsyncEngine,
    provider: LLMProvider,
    repo_id: str,
    k: int,
    recall_k: int | None,
    exclude_path_prefixes: Sequence[str],
    use_hybrid: bool,
    path_prefix: str | None,
) -> list[ChunkHit]:
    if use_hybrid and recall_k is not None:
        return await hybrid_search(
            query,
            engine=engine,
            provider=provider,
            repo_id=repo_id,
            recall_k=recall_k,
            path_prefix=path_prefix,
            exclude_path_prefixes=exclude_path_prefixes,
        )
    return await vector_search(
        query,
        engine=engine,
        provider=provider,
        repo_id=repo_id,
        k=k,
        recall_k=recall_k,
        path_prefix=path_prefix,
        exclude_path_prefixes=exclude_path_prefixes,
    )


def _single_path_prefix(spec: QuerySpec) -> str | None:
    if spec.needs_multi_hop or spec.intent_class != "where_is":
        return None
    if len(spec.extracted_paths) != 1:
        return None
    path = spec.extracted_paths[0]
    if path.endswith(".py"):
        return path
    return path.rstrip("/") + "/"


def _query_lane_weights(count: int) -> list[float]:
    if count <= 0:
        return []
    return [3.0, *([1.0] * (count - 1))]


async def _judge_sufficiency(
    provider: LLMProvider,
    question: str,
    chunks: list[ChunkContent],
    *,
    retry_429_attempts: int | None,
) -> SufficiencyVerdict:
    response = await provider.generate(
        ModelId.QA_PRIMARY,
        [
            Message("system", SUFFICIENCY_SYSTEM),
            Message("user", sufficiency_user_prompt(question, chunks)),
        ],
        temperature=0.0,
        max_tokens=1024,
        retry_429_attempts=retry_429_attempts,
    )
    match = _JSON_RE.search(response.text)
    if match is None:
        return SufficiencyVerdict(decision="sufficient", reason="parse_error")
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return SufficiencyVerdict(decision="sufficient", reason="parse_error")
    try:
        return SufficiencyVerdict(**data)
    except Exception:
        return SufficiencyVerdict(decision="sufficient", reason="schema_error")


async def _generate_answer(
    provider: LLMProvider,
    question: str,
    chunks: list[ChunkContent],
    *,
    retry_429_attempts: int | None,
    intent_profile: IntentProfile | None = None,
) -> str:
    user_prompt = answer_user_prompt(question, chunks)
    response = await provider.generate(
        ModelId.QA_PRIMARY,
        [
            Message("system", answer_system(intent_profile)),
            Message("user", user_prompt),
        ],
        temperature=0.0,
        # Reasoning-model headroom: Cerebras gpt-oss-120b spends its budget in
        # a separate `reasoning` field before emitting content — a hard
        # multi-step question was observed burning 1021 reasoning tokens and
        # dying at 1024 with no content at all. 4096 gives real room.
        max_tokens=4096,
        retry_429_attempts=retry_429_attempts,
    )
    return response.text.strip()


def _is_not_found(answer: str) -> bool:
    """True only when the whole answer IS the not-found sentinel.

    A detailed answer is allowed to say "I couldn't find a test for this" in
    one of its lines; substring-matching the whole body threw away the other
    twelve grounded claims with it. Only a short, sentinel-shaped reply counts.
    """
    lines = [line for line in answer.strip().splitlines() if line.strip()]
    if len(lines) != 1:
        return False
    norm = lines[0].strip().lower()
    return "couldn't find" in norm or "could not find" in norm or "not in the repo" in norm


def _parse_claims(answer: str, chunks: list[ChunkContent]) -> list[Claim]:
    """One sentence per line → one Claim per line.

    Extracts explicit [X] citations from the LLM output to map claims
    directly to the chunks they came from.
    """
    out: list[Claim] = []
    pool = list(chunks)
    for line in answer.splitlines():
        raw = line.strip()
        # '## Section' lines organize the answer; they assert nothing, so they
        # are not claims and must never reach the verifier.
        if raw.startswith("#"):
            continue
        text = line.strip(" -•").strip()
        if not text:
            continue

        refs: list[CodeRef] = []
        citations = re.findall(r"\[(\d+)\]", text)
        for c in citations:
            idx = int(c)
            if 0 <= idx < len(pool):
                refs.append(pool[idx].ref)

        clean_text = re.sub(r"\s*\[\d+\]\s*", "", text).strip()

        cited = bool(refs)
        if not refs and pool:
            # The model dropped its required citation. Still attach a ref —
            # Claim.refs must be non-empty — but pool[0] is an arbitrary
            # attribution, not a real source, so this claim must not be run
            # through the verifier against it (see UNCITED_CLAIM_REASON).
            refs = [pool[0].ref]

        if refs:
            seen = set()
            unique_refs = []
            for r in refs:
                key = (r.file_path, r.start_line, r.end_line)
                if key not in seen:
                    seen.add(key)
                    unique_refs.append(r)
            claim = Claim(text=clean_text or text, refs=unique_refs)
            if not cited:
                claim.status = "unverified"
                claim.verifier_note = UNCITED_CLAIM_REASON
            out.append(claim)
    return out


__all__ = [
    "MAX_HOPS",
    "NON_SOURCE_PATH_PREFIXES",
    "NOT_FOUND_SENTINEL",
    "RECALL_K",
    "QAResult",
    "answer_question",
]
