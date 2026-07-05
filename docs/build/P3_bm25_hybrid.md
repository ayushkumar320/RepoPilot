# Build Prompt — RAG Phase 3: BM25 Hybrid Retrieval

> **Must-ship.** Spec: [`docs/rag/03_HYBRID_RETRIEVAL_BM25.md`](../rag/03_HYBRID_RETRIEVAL_BM25.md). If Phase 2 was deferred, `_before.json` is Phase 1's `_after.json`, and RRF (`qa/union.py`) must be built here instead — budget +30 min. The migration triggers a backfill/re-index; kick it off early, the arq worker runs it unattended.

---

You are implementing **RAG Phase 3 (BM25 Hybrid)** for RepoPilot. Read `CLAUDE.md`, `docs/CURRENT_PHASE.md`, and `docs/rag/03_HYBRID_RETRIEVAL_BM25.md` first.

## Objective

Lift **recall@10 on rare-symbol queries by ≥ 5 pp** over the last landed phase by adding a sparse Postgres-FTS lane fused with the dense lane via RRF. **Zero new deps** — tsvector + GIN is built-in.

## Before writing any code

1. Copy the last landed phase's `_after.json` → `evals/results/rag_phase3/_before.json`.
2. Create `evals/datasets/rare_symbol_v1.jsonl` (12 rows) via propose→review. Every question contains ≥ 1 rare exact symbol (< 5 chunks in the repo). **Include both snake_case identifiers and CamelCase class names** — this is what decides the `english` vs `simple` analyzer question honestly.

## Implementation steps (in order)

1. Alembic migration `000X_chunks_tsvector`: `content_tsv` as `GENERATED ALWAYS AS (to_tsvector('english', coalesce(content,'') || ' ' || coalesce(symbol,''))) STORED` + GIN index (spec §3). Run it; confirm backfill is seconds, not minutes, and the slow-lane httpx index gate still passes (≤ 90 s + 10 s).
2. New `tools/bm25_search.py` (~100 LOC): `ts_rank_cd` + `plainto_tsquery`, params `k`, `kind`, `path_prefix`; return `ChunkHit` with `distance = 1 - normalized_score` so it composes with `vector_search`. Smoke-test against the live httpx index.
3. New `tools/hybrid_search.py` (~80 LOC): dense lanes (multi-query if Phase 2 landed, else single) + one sparse lane, fused with `reciprocal_rank_fusion(k_constant=60)[:recall_k]`. **Feature-flagged.** Re-export both in `tools/__init__.py`.
4. Swap the `qa/graph.py` call to `hybrid_search` (same return shape).
5. Tests: `test_bm25_search.py` (synthetic corpus), `test_hybrid_search.py` (RRF ordering).
6. Bench with **per-lane attribution** — `bench --phase 3` must report `recall@10_dense`, `recall@10_sparse`, `recall@10_hybrid` separately.
7. A/B sweeps (cheap, cached): `k_constant` ∈ {40, 60, 80}; `english` vs `simple` analyzer; score normalization on/off. Flip the default to hybrid only after the winner is clear.

## Gate (all must hold)

- `recall@10_hybrid − recall@10_dense ≥ 0.05` on `rare_symbol_v1`.
- `recall@10_hybrid` ≥ last-landed `_after` + 0.03 on `httpx_qa_v1`.
- All 9 not-in-repo traps still return `NOT_FOUND_SENTINEL` — BM25 must return zero candidates for nonsense tokens.
- `latency_p95_ms` ≤ 1.2× previous phase; migration applies cleanly on fresh httpx.
- `evals/results/rag_phase3/{_before,_after,delta}.json` committed.

## Stop conditions → revert

- Hybrid worse than dense-alone on `httpx_qa_v1` (RRF weight imbalance — try `k_constant` 40/80 first).
- Backfill > 5 min on a 50 kLOC repo.
- `recall@10_sparse < 0.1` on rare-symbol → `english` config is stripping identifiers; switch to `to_tsvector('simple', ...)` before giving up.
- If multi-query + BM25 underperforms but single-query + BM25 passes, the problem is Phase 2's rewrites — report it, don't paper over it.

## Landing protocol

Flip `docs/CURRENT_PHASE.md` (3 🟢, 4 🟡) in the same commit. `graphify update .`, stage graph files, emit GRAPH STATUS. Don't push unasked.
