# RAG Phase 6 — Ingestion Enrichment

> **Status:** Active as of 2026-07-13. Baseline seeded from `evals/results/rag_phase5/_after.json` to `evals/results/rag_phase6/_before.json`.

## 1. Goal

Lift recall@10 by **≥ 3 percentage points** from **corpus-side changes alone** — same retrieval, same reranker, but the chunks themselves carry richer metadata and better-shaped content.

## 2. Why now

Last because it's the most expensive change to validate: every adjustment requires **re-indexing every test repo**. Iteration cost is hours, not minutes. Running this earlier means we'd re-pay that cost every time Phases 1–5 also changed.

By landing now, the upstream retrieval (dense + BM25 + rerank + compress) is fixed, so the lift we measure is unambiguously **corpus quality, not pipeline luck**.

Phase 5 prerequisite-checks:

- All Phases 0–5 results committed.
- Indexing time on `httpx` is still ≤ 90 s + (Phase 3 backfill cost ≤ 10 s). Phase 6 must not push it past that.

## 3. What changes in the code

| Path | Type | LOC est. | Purpose |
|---|---|---|---|
| `packages/ingestion/src/repopilot_ingestion/parse.py` | edit | ~+80 | Extract decorators, signature, return-type annotation, base classes, docstring tokens — per chunk |
| `packages/ingestion/src/repopilot_ingestion/chunk.py` | edit | ~+60 | New `enriched_text` field built from `signature + decorators + docstring + neighbor_symbols + body` — this is what gets embedded and stored as `content_tsv` |
| `packages/ingestion/src/repopilot_ingestion/migrations/versions/000Y_chunks_enrichment.py` | new | ~70 | Add `chunks.signature`, `chunks.decorators` (JSONB), `chunks.neighbor_symbols` (JSONB) columns |
| `packages/ingestion/src/repopilot_ingestion/persist.py` | edit | ~+15 | Write the new columns |
| `packages/ingestion/src/repopilot_ingestion/embed.py` | edit | ~+5 | Embed `enriched_text`, not raw `content` |
| `packages/agents/src/repopilot_agents/tools/read_chunks.py` | edit | ~+5 | Return enriched fields if present (verifier still uses raw `content`) |
| `packages/ingestion/tests/test_enrichment.py` | new | ~100 | Decorator extraction, signature parsing, neighbor-symbol selection |
| `evals/results/rag_phase6/` | new artifact dir | — | `_before`/`_after`/`delta` |

**No new pip deps required.** If we want cyclomatic complexity numbers on chunks (Phase 5 contribute already has its own AST walker), we can reuse that, no `radon`.

### What `enriched_text` looks like

For a function chunk:

```
# decorators: @app.route("/login", methods=["POST"]), @csrf_protect
# signature: def login(request: Request, *, redirect_url: str | None = None) -> Response
# neighbors: flask.app.Flask.handle_request, flask.helpers.flash, flask.session.SecureCookieSession
# docstring keywords: login, session, csrf, redirect, validate
def login(request, *, redirect_url=None):
    ...
```

The `# ...` lines are **synthetic** — added at ingestion time before embedding. They are not in the source. They are not what the answerer sees (the answerer reads `content`, not `enriched_text`). They exist *only to be embedded* — so the dense vector captures "this function is about login, csrf, session, redirect" even if those tokens never appear in the raw body.

### Critical safety rule (same shape as Phase 5's)

The verifier reads `chunks.content` — the raw, true source. It never sees `enriched_text`. This guarantees:

- A function whose docstring lies about what it does cannot trick the verifier (the verifier reads the body, not the docstring).
- A maliciously crafted decorator string cannot influence the verifier (the verifier never sees the synthetic line).

`content` stays the source of truth. `enriched_text` is a retrieval-side optimization.

### Neighbor symbols

For each chunk:

- For a **function/method**: the symbols it calls (top 5 by importance from the existing call graph).
- For a **class**: the symbols of its methods + base classes.
- For a **module**: the top 5 symbols imported.

This data already exists in `graph_adjacency` from product Phase 1. Phase 6 just denormalizes it onto the chunk row at index time so embeddings can incorporate it.

## 4. What changes in the eval

- **All Phase 0–5 datasets reused.**
- **New metric**: `index_time_seconds` per repo (already measured by Phase 1 slow lane). Phase 6 must keep `httpx` ≤ 100 s wall clock.
- **The `--phase 6` bench requires a full re-index of httpx, flask, fastapi.** This is the most expensive bench run in the plan; budget ~10 minutes wall clock for the full sweep.

## 5. Gate

The phase ships when all hold:

- [ ] `recall@10 after − recall@10 before ≥ 0.03` on `httpx_qa_v1` **and at least one** of `flask_qa_v1`/`fastapi_qa_v1`.
- [ ] `NDCG@5` does not regress on any dataset. Enrichment is a recall-focused change; if it hurts NDCG, the reranker is being confused by synthetic lines (a known failure mode — the reranker may see "# decorators:" and rank that chunk higher despite irrelevance).
- [ ] `grounding_accuracy` does not regress > 1 pp on any dataset. Verifier sees raw `content`, so this should be invariant — if it isn't, there's a leak.
- [ ] `index_time_seconds` ≤ 100 s on httpx (was ≤ 90 s in Phase 1 + ≤ 10 s for the BM25 backfill in Phase 3 + ≤ 10 s headroom for enrichment).
- [ ] `evals/results/rag_phase6/{_before,_after,delta}.json` committed.

## 6. Stop conditions

Phase 6 is rolled back if:

- The recall lift is < 1 pp anywhere. The cost of re-indexing is real; this lift must justify itself.
- Index time blows past 120 s on httpx. Possible causes: a too-expensive decorator extractor, neighbor-symbol JOINs in the indexer hot path. The fix is to denormalize neighbors during graph build, not at chunk-write time.
- The reranker (Phase 4) starts ranking enriched chunks higher *because* of the synthetic prefix lines rather than the actual content. Detect with `diversity_score` regression. Fix: strip the `# ...` lines before sending chunks to the reranker — they were only meant to influence embeddings.

## 7. Implementation order

1. Migration: add the new columns. Backfill is the expensive part — do it for `httpx` first, measure index time.
2. Update `parse.py` to extract signatures + decorators; unit-test on a fixture file.
3. Update `chunk.py` to build `enriched_text`; unit-test the shape.
4. Update `embed.py` to embed `enriched_text` instead of `content`. **This is the cache-invalidating step** — every existing embedding becomes stale. Bump the embedding cache version.
5. Run `bench --phase 6` on freshly re-indexed httpx, flask, fastapi.
6. Strip the `# ...` prefix lines from inputs to the reranker (Phase 4 path) and the answerer (Phase 5 compression path). They are *embedding-only* content.
7. Commit results.

---

## Honest notes

- **This is the highest-effort phase by indexing cost.** Plan for ~1 hour of wall-clock indexing across the three test repos before any `bench --phase 6` numbers exist.
- **The synthetic-prefix approach is borrowed from BM25 + dense hybrid literature** ("contextualized chunks", "Anthropic's contextual retrieval"). The theoretical lift on out-of-domain code is unmeasured; the 3 pp gate is conservative because of that uncertainty.
- **An obvious extension** is to use the 8B model to *generate* a one-sentence summary per chunk and embed that — Anthropic's contextual retrieval does exactly this. We declined it for Phase 6 because it adds an LLM call per chunk at index time, blowing the 90 s gate. If Phase 6 lifts recall and we want more, that's the obvious Phase 7.
- **Semantic re-chunking** (using LLM to decide boundaries instead of AST) was considered for this phase and rejected. AST boundaries are higher-precision; the lift from LLM boundaries on code is < 1 pp in published benchmarks. Not worth the indexing cost.

---

## After Phase 6

If all 7 phases land successfully, **the full target pipeline is implemented and measured.** The "Definition of Done" checklist in `docs/RAG_PLAN.md` is the closeout.

Subsequent work would be:

- Replace the embedding model (cost-benefit analysis required).
- Add an explicit confidence-calibration step (per-claim Brier score).
- A/B against Cohere Rerank (paid, needs justification).
- Anthropic-style contextual chunk summaries (extension of this phase).
