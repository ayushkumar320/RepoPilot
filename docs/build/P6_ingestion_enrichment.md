# Build Prompt — RAG Phase 6: Ingestion Enrichment

> **Timebox: 90 minutes hard, including re-index wait.** Polish phase. Start the re-index and write the ship report while waiting. Spec: [`docs/rag/06_INGESTION_ENRICHMENT.md`](../rag/06_INGESTION_ENRICHMENT.md).

---

You are implementing **RAG Phase 6 (Ingestion Enrichment)** for RepoPilot. Read `CLAUDE.md`, `docs/CURRENT_PHASE.md`, and `docs/rag/06_INGESTION_ENRICHMENT.md` first. Prerequisite: all landed phases' results committed; httpx index time still ≤ 100 s.

## Objective

Lift **recall@10 by ≥ 3 pp from corpus-side changes alone**: embed an `enriched_text` (synthetic prefix of decorators + signature + neighbor symbols + docstring keywords, then body) instead of raw content. **No new deps.**

## Two invariants

1. **Verifier and answerer read raw `chunks.content`, never `enriched_text`.** The synthetic `# ...` lines exist only to be embedded. A lying docstring or crafted decorator must not be able to influence verification.
2. **Strip the synthetic prefix lines before the reranker and the compression path too** — they were only meant to influence embeddings (spec §7 step 6).

## Before writing any code

Copy the last landed `_after.json` → `evals/results/rag_phase6/_before.json`. Note: this phase requires **a full re-index of httpx, flask, fastapi** (~25 min wall clock) before any bench numbers exist.

## Implementation steps (in order)

1. Migration `000Y_chunks_enrichment`: add `chunks.signature`, `chunks.decorators` (JSONB), `chunks.neighbor_symbols` (JSONB). Backfill httpx first; measure index time.
2. `parse.py` (+~80): extract decorators, signature, return annotation, base classes, docstring tokens per chunk. Unit-test on a fixture file.
3. `chunk.py` (+~60): build `enriched_text` (shape in spec §3). Neighbor symbols come from the existing `graph_adjacency` — denormalize during graph build, **not** at chunk-write time (hot-path warning in spec §6).
4. `persist.py`: write the new columns. `embed.py`: embed `enriched_text` — **this invalidates the embedding cache; bump the cache version.** `read_chunks.py`: return enriched fields; verifier still uses raw `content`.
5. Strip synthetic prefixes from reranker/answerer inputs (invariant 2).
6. Tests: `test_enrichment.py` (~100 LOC) — decorator extraction, signature parsing, neighbor selection.
7. Re-index all three repos, then `bench --phase 6` (budget ~10 min for the sweep).

## Gate (all must hold)

- recall@10 lift ≥ 0.03 on `httpx_qa_v1` **and** ≥ 1 of flask/fastapi.
- NDCG@5 does not regress anywhere (regression = reranker confused by synthetic lines → check invariant 2).
- Grounding regression ≤ 1 pp (should be invariant; a change means a leak).
- `index_time_seconds` ≤ 100 s on httpx.
- `evals/results/rag_phase6/{_before,_after,delta}.json` committed.

## Stop conditions → revert

- Recall lift < 1 pp anywhere — re-indexing cost isn't justified.
- Index time > 120 s on httpx (expensive extractor or JOIN in hot path).
- `diversity_score` regression (reranker keying on synthetic prefixes) — verify the strip, then revert if it persists.
- Timebox blown → defer cleanly.

## Landing protocol

Flip `docs/CURRENT_PHASE.md` (6 🟢 or ⚪ deferred) in the same commit. `graphify update .`, stage graph files, emit GRAPH STATUS. Don't push unasked. Then run the ship closeout ([`P7_ship_closeout.md`](P7_ship_closeout.md)).
