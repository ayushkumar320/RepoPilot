# RAG Phase 1 — Recall Lift (Candidate Pool + Metadata Filtering)

## 1. Goal

Lift recall@10 by **≥ 5 percentage points** over the Phase 0 baseline without changing the embedding model, the LLM, or adding any new dependency.

Mechanism: grow the dense-search candidate pool from `k=8` to `k=50–200`, and let the Q&A flow take advantage of metadata filters (`kind`, `file_path` glob) that the schema already supports but `vector_search` doesn't expose.

## 2. Why now

Phase 0 measured the existing pipeline at `k=8`. That's a tiny pool — the bug-fix lift you can get for free by just *retrieving more candidates* is the cheapest quality lift in the entire plan. Until the pool is big, every later phase (rerank, MMR, compression) operates on a starved input and underperforms.

Phase 0 prerequisite-checks:

- `baseline.json` is committed (so the lift is comparable).
- Latency p95 baseline is recorded (so we can confirm `k=50` doesn't blow it up).

## 3. What changes in the code

| Path | Type | LOC est. | Purpose |
|---|---|---|---|
| `packages/agents/src/repopilot_agents/tools/vector_search.py` | edit | ~+30 | Add optional `kind`, `path_prefix`, `path_glob` params; default `k` stays 8 for back-compat; new `recall_k` param defaults to 50 |
| `packages/agents/src/repopilot_agents/qa/graph.py` | edit | ~+10 | Call `vector_search` with `recall_k=50` upstream of the existing flow; sufficiency judge sees the larger pool |
| `packages/agents/src/repopilot_agents/tools/__init__.py` | edit | ~+2 | Re-export the new param surface |
| `packages/agents/tests/test_vector_search_filters.py` | new | ~80 | Unit tests for the new filters against a stubbed Postgres |
| `evals/results/rag_phase1/` | new artifact dir | — | `_before.json` (copy of Phase 0 baseline), `_after.json`, `delta.json` |

**Zero new pip deps.** The schema already has `chunks.kind` and `chunks.file_path` from Phase 1 of the product build; we are exposing what was already there.

### The shape of the new SQL

```sql
SELECT c.file_path, c.start_line, c.end_line, c.symbol, c.kind, c.summary,
       (ce.embedding <=> CAST(:vec AS vector)) AS distance
FROM chunks c
JOIN chunk_embeddings ce ON ce.chunk_id = c.id
WHERE c.repo_id = :repo_id
  AND (:kind IS NULL OR c.kind = :kind)
  AND (:path_prefix IS NULL OR c.file_path LIKE :path_prefix || '%')
  AND (:path_glob IS NULL OR c.file_path SIMILAR TO :path_glob)
ORDER BY ce.embedding <=> CAST(:vec AS vector)
LIMIT :recall_k
```

`recall_k` is **separate from** the `k` used by the Q&A flow's final prompt. Phase 1 widens the pool that *reaches the sufficiency judge*; the judge still gets ~8 chunks at a time because of Phase 5's compression (which will operate on the larger pool).

Until Phase 5 lands, the Q&A graph will trim the top-`k` from the larger pool itself.

## 4. What changes in the eval

- **Reuse**: `httpx_qa_v1`, `flask_qa_v1`, `fastapi_qa_v1` from Phase 0.
- **New runner step**: `python -m repopilot_evals.bench --phase 1` runs the same metric suite as Phase 0 but with the new `vector_search` defaults, writes `evals/results/rag_phase1/_after.json`, and prints the delta vs. `_before.json`.
- **Latency guardrail**: a new assertion in `bench.py` fails the phase if `latency_p95_ms` regresses by > 1.5×.

## 5. Gate

The phase ships when all hold:

- [ ] `recall@10 after − recall@10 before ≥ 0.05` on `httpx_qa_v1`.
- [ ] Same lift on **at least one** of `flask_qa_v1` and `fastapi_qa_v1` (so it's not an httpx artifact).
- [ ] `significance.py` reports the lift as **statistically significant** on at least one of the three datasets.
- [ ] `grounding_accuracy` does not regress by more than 1 pp on any dataset. (A bigger pool that contains more noise can hurt the answerer even with better recall — this guardrail catches that.)
- [ ] `latency_p95_ms` does not regress by more than 1.5× the Phase 0 baseline.
- [ ] `evals/results/rag_phase1/{_before,_after,delta}.json` committed.

## 6. Stop conditions

Phase 1 is **not landed** and the work is rolled back if:

- The lift is significant on `httpx_qa_v1` but ≤ 0.02 pp on both other datasets — that's overfitting the eval set, not a real lift.
- `grounding_accuracy` regresses by > 1 pp anywhere. Bigger pool feeding more noise to the answerer is the failure mode here.
- `latency_p95` doubles. The reranker phase (4) will reclaim some latency, but Phase 1 alone can't be allowed to make the demo unusable.

## 7. Implementation order

1. Add the new `vector_search` params + tests with the existing `k=8` default — confirm fast lane still green.
2. Bump the call in `qa/graph.py` to `recall_k=50`, leaving Q&A's prompt slice at `[:8]`.
3. Run `bench --phase 1` against each repo; commit results.
4. Read the numbers honestly. If they pass, advance `CURRENT_PHASE.md` to Phase 2.

---

## Honest notes

- The `recall_k=50` default is a guess. The phase doc should be updated with what *actually* lifts recall most without hurting latency or grounding. Plausible answer is somewhere in 30–80; choose by data.
- The `path_glob` / `path_prefix` params are not used in the Q&A loop yet. They are exposed because Phase 2's query-understanding step will use them ("the question mentions `_transports/`" → filter to that prefix). That work is in Phase 2; Phase 1 just makes the surface available.
- This phase is **not the same** as just bumping `k`. The metadata filters are the cheap lift that compounds with Phase 2's query understanding.
