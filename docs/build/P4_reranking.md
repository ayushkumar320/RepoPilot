# Build Prompt — RAG Phase 4: Reranking (Cross-Encoder + MMR)

> **Must-ship.** Spec: [`docs/rag/04_RERANKING.md`](../rag/04_RERANKING.md). The one phase with a new pip dep (`fastembed`). This is where "tests/docs outrank source" should visibly die — check rare-symbol and the flask routing questions specifically.

---

You are implementing **RAG Phase 4 (Reranking)** for RepoPilot. Read `CLAUDE.md`, `docs/CURRENT_PHASE.md`, and `docs/rag/04_RERANKING.md` first. Prerequisite: hybrid search returns a stable ranked pool of ~50; `evals/results/rag_phase3/_after.json` committed.

## Objective

Lift **NDCG@5 by ≥ 0.05 over Phase 3** with a `fastembed` cross-encoder (`BAAI/bge-reranker-base`, CPU/onnx) over the candidate pool, plus MMR diversity in the final top-8. NDCG, not recall, is the metric — reranking changes order, not pool membership.

## Before writing any code

1. Copy `evals/results/rag_phase3/_after.json` → `evals/results/rag_phase4/_before.json`.
2. Create the reranker self-test set: 20 labeled `(query, positive_chunk, negative_chunk)` triples.

## Implementation steps (in order)

1. Add `fastembed >= 0.4, < 0.5` to `packages/agents/pyproject.toml`. Smoke-test: model loads, scores 10 pairs in < 1 s (first run downloads ~250 MB weights, cached).
2. New `rerank/cross_encoder.py`: `CrossEncoderReranker`. Feed it `chunk.symbol + "\n" + chunk.content` (the known fix for code mismatch). Cache scores by `sha256(query + chunk_content)` in SQLite alongside the embedding cache.
3. New `rerank/mmr.py`: pure-function MMR over `(chunk, dense_embedding, score)`; formula and `lambda_` rationale in spec §3.
4. New `rerank/pipeline.py`: `rerank_and_diversify(query, pool, k=8, lambda_=0.7)`. Settings in `repopilot_core/settings.py`: `rerank_model`, `rerank_cache_path`, `rerank_max_pool` (default 30 — truncate the pool before reranking to hold latency).
5. Wire into `qa/graph.py` between `hybrid_search` and the sufficiency judge, **behind `rerank_enabled`**. Run the reranker concurrent with the sufficiency judge's first call where possible.
6. Tests: `test_cross_encoder.py` (monotone on self-test set), `test_mmr.py` (hand-crafted near-duplicates).
7. Bench sweep: `lambda_` ∈ {0.5, 0.7, 0.9} × `rerank_max_pool` ∈ {20, 30, 50}. Pick by NDCG@5; commit winners as defaults. `lambda_` is the most impactful knob — bench it, don't intuit it.

## Gate (all must hold)

- NDCG@5 lift ≥ 0.05 on `httpx_qa_v1` **and** ≥ 1 of flask/fastapi.
- MRR lift ≥ 0.05 on `multi_hop_v1` (skip this line if Phase 2 was deferred and the dataset doesn't exist — note it).
- `diversity_score` (distinct file paths in top-5) does not decrease on any dataset.
- Reranker self-test ≥ 90% pairwise accuracy.
- Grounding regression ≤ 1 pp anywhere; `latency_p95_ms` ≤ 2× Phase 0 baseline.
- `evals/results/rag_phase4/{_before,_after,delta}.json` committed.

## Stop conditions → revert

- Lifts on httpx only (overfit to distribution) — try `bge-reranker-large` once, else ship dense+sparse-only.
- Obviously-wrong chunks at top → confirm the symbol-prefix input fix is in place.
- Latency p95 > 3 s despite caching, pool truncation, and parallelism → ship without reranking; note "revisit with distilled reranker" in the phase doc.

## Landing protocol

Flip `docs/CURRENT_PHASE.md` (4 🟢) in the same commit. `graphify update .`, stage graph files, emit GRAPH STATUS. Don't push unasked.
