# RAG Phase 4 — Reranking (Cross-Encoder + MMR Diversity)

## 1. Goal

Lift **NDCG@5 by ≥ 0.05** over Phase 3 by adding a cross-encoder rerank stage on the candidate pool, plus MMR diversity to suppress near-duplicate chunks.

NDCG (not recall) is the right metric for this phase because reranking does not change *what's in the pool* — it changes the **order**. A good reranker puts the most relevant chunks at positions 1–3 where the answerer's context window prioritizes them.

## 2. Why now

After Phases 1+2+3 the candidate pool is ~50 high-recall chunks. The answerer can only read the top 8–10 of them (token budget). If the *most* relevant chunk is at position 27, recall@10 says we hit it; the answerer never reads it. Cross-encoder reranking is the standard fix: score every `(query, chunk)` pair with a small dedicated model that's far more accurate than cosine distance, then take the top 8.

MMR (Maximal Marginal Relevance) addresses a related failure: when 5 of the top-8 chunks are different methods of the same class, the answerer wastes context on duplication. MMR penalizes the score of a chunk by its embedding similarity to chunks already chosen, ensuring **diversity in the final 8**.

Phase 3 prerequisite-checks:

- Hybrid search returns a stable, ranked pool of ~50.
- `evals/results/rag_phase3/_after.json` committed.

## 3. What changes in the code

| Path | Type | LOC est. | Purpose |
|---|---|---|---|
| `packages/agents/src/repopilot_agents/rerank/__init__.py` | new | ~10 | Package exports |
| `packages/agents/src/repopilot_agents/rerank/cross_encoder.py` | new | ~120 | `CrossEncoderReranker` wrapping `fastembed.TextCrossEncoder` |
| `packages/agents/src/repopilot_agents/rerank/mmr.py` | new | ~60 | Pure-function MMR over a list of (chunk, dense_embedding, score) tuples |
| `packages/agents/src/repopilot_agents/rerank/pipeline.py` | new | ~80 | `rerank_and_diversify(query, pool, k=8, lambda_=0.7)` — the composer |
| `packages/agents/src/repopilot_agents/qa/graph.py` | edit | ~+10 | Call `rerank_and_diversify` between `hybrid_search` and the sufficiency judge |
| `packages/agents/pyproject.toml` | edit | +1 line | Add `fastembed >= 0.4, < 0.5` |
| `packages/core/src/repopilot_core/settings.py` | edit | ~+10 | Add `rerank_model`, `rerank_cache_path`, `rerank_max_pool` settings |
| `packages/agents/tests/test_cross_encoder.py` | new | ~70 | Reranker scores monotone with relevance on a synthetic corpus |
| `packages/agents/tests/test_mmr.py` | new | ~60 | MMR diversity tests with hand-crafted near-duplicates |
| `evals/results/rag_phase4/` | new artifact dir | — | `_before`/`_after`/`delta` |

**One new pip dep: `fastembed`.** Justification:

- No `torch` runtime dep (it bundles `onnxruntime`, ~80 MB total).
- CPU-only inference; works on the laptop demo machine.
- Default model: `BAAI/bge-reranker-base` (~250 MB weights downloaded on first run, cached locally).
- Alternative considered (Cohere Rerank API) violates "free-tier survivable" from `docs/02_TECH_STACK.md`.

### Why `lambda_ = 0.7`?

MMR's formula:

```
MMR(c) = lambda * relevance_score(c) - (1 - lambda) * max(sim(c, c') for c' already chosen)
```

`lambda = 1.0` → pure relevance, no diversity. `lambda = 0.0` → pure diversity (random-ish). The literature default 0.5 is too aggressive for code retrieval (we *want* multiple methods of the same class sometimes). `0.7` favors relevance but doesn't ignore diversity.

We'll A/B `[0.5, 0.7, 0.9]` in the bench and pick the best.

### Latency budget

`fastembed`'s BGE reranker on CPU does **~30 (query, chunk) pairs per second** on an M-series Mac. Pool of 50 = ~1.7 s. That's the worst single addition to the pipeline. We mitigate:

- **Truncate pool to 30 before reranking** if `rerank_max_pool=30`. Recall holds because Phase 3 puts the best stuff at the top.
- **Cache reranker scores** by `sha256(query + chunk_content)` in SQLite alongside the embedding cache.
- **Run reranker concurrent with the sufficiency judge**'s first call — the reranker output is needed only for the *answer* prompt, not the sufficiency check.

## 4. What changes in the eval

- **All Phase 0–3 datasets reused.** Reranking should help universally; if it only helps one dataset, the model isn't generalizing.
- **NDCG@5 becomes the primary metric** for this phase (recall@10 is already saturated by hybrid search).
- **New metric**: `diversity_score` = average distinct file paths in top-5. Phase 4 should not reduce this; MMR is supposed to *increase* it.
- **Reranker self-test**: a labeled subset of 20 `(query, positive_chunk, negative_chunk)` triples checks that `reranker(positive) > reranker(negative)` ≥ 90% of the time.

## 5. Gate

The phase ships when all hold:

- [ ] `NDCG@5 after − NDCG@5 before ≥ 0.05` on `httpx_qa_v1`.
- [ ] Same lift on **at least one** of `flask_qa_v1` / `fastapi_qa_v1`.
- [ ] `MRR after ≥ MRR before + 0.05` on `multi_hop_v1` — multi-hop is where reranking matters most.
- [ ] `diversity_score after ≥ diversity_score before` on every dataset (MMR doing its job).
- [ ] Reranker self-test ≥ 90% pairwise accuracy.
- [ ] `grounding_accuracy` does not regress > 1 pp on any dataset.
- [ ] `latency_p95_ms` ≤ 2× Phase 0 baseline. Reranker is the most expensive single addition; this is the loosest latency budget in the plan.
- [ ] `evals/results/rag_phase4/{_before,_after,delta}.json` committed.

## 6. Stop conditions

Phase 4 is rolled back if:

- **NDCG lifts on httpx but not flask/fastapi.** Reranker may have been trained on a distribution that happens to match httpx — keeping it would be overfitting. Try `bge-reranker-large` next, or accept the dense+sparse-only stack.
- **Reranker overrides hybrid search by ranking obviously-wrong chunks at the top.** This happens when the reranker is mismatched to code — usually it's because we're feeding it `chunk.content` instead of `chunk.symbol + "\n" + chunk.content`. Adding the symbol prefix is a known fix.
- **Latency p95 > 3 s.** Even with caching and parallelism, BGE reranker is the slow step. If it can't be brought under 3 s, we ship without it and revisit with a smaller distilled reranker in Phase 6.

## 7. Implementation order

1. Add `fastembed` dep; smoke-test `bge-reranker-base` loads and scores 10 pairs in < 1 s.
2. Write `CrossEncoderReranker` + tests; confirm it scores monotone on the self-test set.
3. Write `mmr` as a pure function over `(score, embedding)` pairs; unit-test diversity.
4. Compose in `pipeline.py`; wire into `qa/graph.py` behind a `rerank_enabled` setting.
5. Run `bench --phase 4` with `lambda_ in {0.5, 0.7, 0.9}` and `rerank_max_pool in {20, 30, 50}`. Pick the best by NDCG@5.
6. Commit the chosen settings as defaults; commit bench results.

---

## Honest notes

- **The reranker is the heaviest single addition to the pipeline.** If Phases 1+2+3 already pushed NDCG@5 above 0.85 on the labeled bench, Phase 4 may be ungated improvement chasing — re-evaluate before landing.
- **`bge-reranker-base` is multilingual-trained.** It's not code-specialized. There's no good open-weight code-specialized reranker today. The bet here is that the cross-encoder architecture is the lift, not the specific weights; if that's wrong, Phase 4's gate will say so.
- **MMR's `lambda_` is the single most impactful knob in this phase.** Worth being careful with — bench it deliberately, don't pick by intuition.
- **Diversity can hurt grounding accuracy** when an answer genuinely needs 3 related chunks (e.g. "show me all three caching levels"). MMR will spread the top-5 across unrelated files. The grounding gate (≤ 1 pp regression) catches this.
