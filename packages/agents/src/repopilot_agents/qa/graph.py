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

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass

import structlog
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncEngine

from repopilot_agents.qa.prompts import (
    ANSWER_SYSTEM,
    SUFFICIENCY_SYSTEM,
    answer_user_prompt,
    sufficiency_user_prompt,
)
from repopilot_agents.qa.types import SufficiencyVerdict
from repopilot_agents.rerank.pipeline import DEFAULT_MAX_POOL as RERANK_MAX_POOL
from repopilot_agents.rerank.pipeline import rerank_and_diversify
from repopilot_agents.tools.graph_traverse import graph_traverse
from repopilot_agents.tools.hybrid_search import hybrid_search
from repopilot_agents.tools.read_chunks import read_chunks
from repopilot_agents.tools.vector_search import NON_SOURCE_PATH_PREFIXES, vector_search
from repopilot_agents.types import ChunkContent, ChunkHit, CodeRef
from repopilot_agents.verifier.grounding import (
    Claim,
    VerifierObjection,
    verify_claims,
)
from repopilot_core.llm.models import ModelId
from repopilot_core.llm.provider import LLMProvider, Message

log = structlog.get_logger(__name__)


MAX_HOPS = 3
# RAG Phase 1: pool width fetched from pgvector. The prompt slice stays at
# ``k`` — Phase 5's compression will consume the full pool; until then the
# graph trims the top-k itself.
RECALL_K = 50
NOT_FOUND_SENTINEL = "I couldn't find that in the repo."


class QAResult(BaseModel):
    """The end-to-end output of one Q&A run."""

    question: str
    answer: str
    claims: list[Claim] = Field(default_factory=list)
    objections: list[VerifierObjection] = Field(default_factory=list)
    hops: int = 0
    retrieval_path: list[str] = Field(default_factory=list)


@dataclass(slots=True)
class _Context:
    seen_refs: set[tuple[str, int, int]]
    chunks: list[ChunkContent]
    retrieval_path: list[str]


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
    use_rerank: bool = True,
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

    ``use_rerank`` (Phase 4) cross-encoder-reranks + MMR-diversifies the top
    of the pool before the prompt slice. Requires ``recall_k`` (needs a pool
    to reorder); disabled automatically on the pre-Phase-1 baseline arm.
    """
    ctx = _Context(seen_refs=set(), chunks=[], retrieval_path=[])

    # Initial retrieval: wide source-only pool (gold-label noise prefixes
    # excluded), then trim to the top-k for the prompt. Phase 3 fuses a BM25
    # sparse lane in; the pre-Phase-1 baseline (recall_k=None) stays dense.
    hits: list[ChunkHit]
    if use_hybrid and recall_k is not None:
        hits = await hybrid_search(
            question,
            engine=engine,
            provider=provider,
            repo_id=repo_id,
            recall_k=recall_k,
            exclude_path_prefixes=exclude_path_prefixes,
        )
        ctx.retrieval_path.append(f"hybrid_search:recall_k={recall_k}:k={k}:hits={len(hits)}")
    else:
        hits = await vector_search(
            question,
            engine=engine,
            provider=provider,
            repo_id=repo_id,
            k=k,
            recall_k=recall_k,
            exclude_path_prefixes=exclude_path_prefixes,
        )
        pool = recall_k if recall_k is not None else k
        ctx.retrieval_path.append(f"vector_search:recall_k={pool}:k={k}:hits={len(hits)}")

    if use_rerank and recall_k is not None and len(hits) > k:
        # Phase 4: fetch the top of the pool, cross-encoder rerank + MMR
        # diversify, and let the reranked order decide the prompt slice.
        pool_hits = hits[:RERANK_MAX_POOL]
        pool_chunks = await read_chunks([h.ref for h in pool_hits], engine=engine, repo_id=repo_id)
        if len(pool_chunks) == len(pool_hits):
            ranked = rerank_and_diversify(question, pool_hits, pool_chunks, k=k)
            ctx.retrieval_path.append(f"rerank:pool={len(pool_hits)}:k={len(ranked)}")
            initial_chunks = [content for _, content in ranked]
        else:
            # read_chunks dropped refs (stale index?) — fall back untranked.
            initial_chunks = pool_chunks[:k]
    else:
        initial_chunks = await read_chunks(
            [h.ref for h in hits[:k]], engine=engine, repo_id=repo_id
        )
    _extend_context(ctx, initial_chunks)

    # Outer loop: sufficiency judge → optional traverse expansion.
    hops = 0
    while hops < max_hops:
        verdict = await _judge_sufficiency(provider, question, ctx.chunks)
        if verdict.decision == "sufficient" or verdict.next_symbol is None:
            break

        ctx.retrieval_path.append(f"graph_traverse:{verdict.next_symbol}")
        paths = await graph_traverse(
            verdict.next_symbol,
            engine=engine,
            repo_id=repo_id,
            edge_types=("calls", "imports", "inherits"),
            max_depth=2,
        )
        new_refs: list[CodeRef] = []
        for path in paths:
            for ref in path.steps:
                key = (ref.file_path, ref.start_line, ref.end_line)
                if key not in ctx.seen_refs and ref.file_path != "<unresolved>":
                    new_refs.append(ref)
        new_chunks = await read_chunks(new_refs, engine=engine, repo_id=repo_id)
        _extend_context(ctx, new_chunks)
        hops += 1

    answer_text = await _generate_answer(provider, question, ctx.chunks)

    if _is_not_found(answer_text):
        return QAResult(
            question=question,
            answer=NOT_FOUND_SENTINEL,
            claims=[],
            objections=[],
            hops=hops,
            retrieval_path=ctx.retrieval_path,
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
        )

    verify_results = await verify_claims(claims, provider=provider, engine=engine, repo_id=repo_id)
    objections = [r.objection for r in verify_results if r.objection is not None]

    # Flag the rejected ones (still shipped, but visually marked).
    for verified in verify_results:
        if verified.claim.status == "rejected":
            verified.claim.status = "flagged"

    return QAResult(
        question=question,
        answer=answer_text,
        claims=[r.claim for r in verify_results],
        objections=objections,
        hops=hops,
        retrieval_path=ctx.retrieval_path,
    )


# ── internals ───────────────────────────────────────────────────────────────


def _extend_context(ctx: _Context, chunks: list[ChunkContent]) -> None:
    for chunk in chunks:
        key = (chunk.ref.file_path, chunk.ref.start_line, chunk.ref.end_line)
        if key in ctx.seen_refs:
            continue
        ctx.seen_refs.add(key)
        ctx.chunks.append(chunk)


async def _judge_sufficiency(
    provider: LLMProvider, question: str, chunks: list[ChunkContent]
) -> SufficiencyVerdict:
    response = await provider.generate(
        ModelId.QA_PRIMARY,
        [
            Message("system", SUFFICIENCY_SYSTEM),
            Message("user", sufficiency_user_prompt(question, chunks)),
        ],
        temperature=0.0,
        max_tokens=1024,
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


async def _generate_answer(provider: LLMProvider, question: str, chunks: list[ChunkContent]) -> str:
    response = await provider.generate(
        ModelId.QA_PRIMARY,
        [
            Message("system", ANSWER_SYSTEM),
            Message("user", answer_user_prompt(question, chunks)),
        ],
        temperature=0.0,
        # Reasoning-model headroom: Cerebras gpt-oss-120b spends its budget in
        # a separate `reasoning` field before emitting content — a hard
        # multi-step question was observed burning 1021 reasoning tokens and
        # dying at 1024 with no content at all. 4096 gives real room.
        max_tokens=4096,
    )
    return response.text.strip()


def _is_not_found(answer: str) -> bool:
    norm = answer.strip().lower()
    return "couldn't find" in norm or "could not find" in norm or "not in the repo" in norm


def _parse_claims(answer: str, chunks: list[ChunkContent]) -> list[Claim]:
    """One sentence per line → one Claim per line.

    Refs are attached by matching short symbol mentions against the
    available chunks. This is intentionally generous — false-positive ref
    attribution is harmless because the verifier checks each claim against
    its refs, not the other way around.
    """
    out: list[Claim] = []
    pool = list(chunks)
    for line in answer.splitlines():
        text = line.strip(" -•").strip()
        if not text:
            continue
        # Heuristic ref attribution: take the first two chunks that share any
        # token with the line. Cheap and good enough for Phase 2 — Phase 3
        # will move this into the typed state once Claim has a Pydantic home.
        tokens = {t.lower() for t in re.findall(r"[A-Za-z_][A-Za-z_0-9]+", text)}
        scored: list[tuple[int, ChunkContent]] = []
        for chunk in pool:
            sym_tokens = {
                t.lower() for t in re.findall(r"[A-Za-z_][A-Za-z_0-9]+", chunk.ref.symbol or "")
            }
            overlap = len(tokens & sym_tokens)
            if overlap > 0:
                scored.append((overlap, chunk))
        scored.sort(key=lambda t: -t[0])
        refs = [c.ref for _, c in scored[:2]]
        if not refs and pool:
            # Fall back to the top retrieved chunk so the claim has at least
            # one ref the verifier can check against.
            refs = [pool[0].ref]
        if refs:
            out.append(Claim(text=text, refs=refs))
    return out


__all__ = [
    "MAX_HOPS",
    "NON_SOURCE_PATH_PREFIXES",
    "NOT_FOUND_SENTINEL",
    "RECALL_K",
    "QAResult",
    "answer_question",
]
