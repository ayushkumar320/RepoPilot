# RAG Phase 3 — Hybrid Retrieval (BM25 / Keyword Search)

## 1. Goal

Lift recall@10 on **rare-symbol and proper-noun queries** by **≥ 5 percentage points** over Phase 2, by adding a sparse (BM25) search lane and fusing it with the dense lane via Reciprocal Rank Fusion.

## 2. Why now

Dense embeddings + multi-query (Phases 1+2) handle paraphrase well. They fail on **rare tokens** — exact symbol names, error messages, decorator names, configuration keys. The embedding model has never seen `_redirect_method`, so it embeds near `redirect`, `method`, and a lot of unrelated noise. BM25 thinks of `_redirect_method` as a unique high-IDF token, ranks the chunk that contains it at the top, and the union (RRF) picks up what dense missed.

Phase 2 prerequisite-checks:

- `reciprocal_rank_fusion` from `qa/union.py` is already in place (Phase 2 built it for multi-query union).
- `evals/results/rag_phase2/_after.json` committed.

## 3. What changes in the code

| Path | Type | LOC est. | Purpose |
|---|---|---|---|
| `packages/ingestion/src/repopilot_ingestion/migrations/versions/000X_chunks_tsvector.py` | new alembic migration | ~50 | Add `chunks.content_tsv` `tsvector` column + GIN index; backfill |
| `packages/ingestion/src/repopilot_ingestion/persist.py` | edit | ~+5 | Set `content_tsv = to_tsvector('english', content || ' ' || symbol)` on insert |
| `packages/agents/src/repopilot_agents/tools/bm25_search.py` | new | ~100 | `bm25_search()` — Postgres FTS k-NN-style search |
| `packages/agents/src/repopilot_agents/tools/hybrid_search.py` | new | ~80 | Top-level fusion: runs dense + BM25 in parallel, fuses with RRF |
| `packages/agents/src/repopilot_agents/qa/graph.py` | edit | ~+5 | Replace `vector_search` call with `hybrid_search` call (same return shape) |
| `packages/agents/src/repopilot_agents/tools/__init__.py` | edit | ~+4 | Re-exports |
| `packages/agents/tests/test_bm25_search.py` | new | ~80 | Unit tests against synthetic corpus |
| `packages/agents/tests/test_hybrid_search.py` | new | ~80 | RRF fusion ordering tests |
| `evals/datasets/rare_symbol_v1.jsonl` | new (labeled) | 12 rows | The bench Phase 3 must lift on |
| `evals/results/rag_phase3/` | new artifact dir | — | `_before`/`_after`/`delta` |

**Zero new pip deps.** Postgres `tsvector` + GIN is built-in.

### The migration

```python
def upgrade() -> None:
    op.execute("""
        ALTER TABLE chunks ADD COLUMN content_tsv tsvector
        GENERATED ALWAYS AS (
            to_tsvector('english', coalesce(content, '') || ' ' || coalesce(symbol, ''))
        ) STORED
    """)
    op.execute("CREATE INDEX ix_chunks_content_tsv ON chunks USING gin(content_tsv)")
```

Generated column + GIN means **no ingestion changes for symbol-only indexed repos** — the column populates from `content` and `symbol` automatically. For repos indexed *after* this migration, Phase 1's `persist.py` doesn't need to change at all.

For already-indexed repos, the `GENERATED ALWAYS AS ... STORED` triggers a one-time backfill on the migration; alembic will handle it.

### What `bm25_search` does

```python
async def bm25_search(
    query: str,
    *,
    engine: AsyncEngine,
    repo_id: str,
    k: int = 50,
    kind: str | None = None,
    path_prefix: str | None = None,
) -> list[ChunkHit]:
    sql = text("""
        SELECT c.file_path, c.start_line, c.end_line, c.symbol, c.kind, c.summary,
               ts_rank_cd(c.content_tsv, plainto_tsquery('english', :q)) AS score
        FROM chunks c
        WHERE c.repo_id = :repo_id
          AND c.content_tsv @@ plainto_tsquery('english', :q)
          AND (:kind IS NULL OR c.kind = :kind)
          AND (:path_prefix IS NULL OR c.file_path LIKE :path_prefix || '%')
        ORDER BY score DESC
        LIMIT :k
    """)
```

Returns a `ChunkHit` with `distance = 1 - normalized_score` so it composes with `vector_search`'s shape.

### Hybrid fusion

```python
async def hybrid_search(
    spec: QuerySpec, *, engine, provider, repo_id, recall_k=50,
) -> list[ChunkHit]:
    # Dense lane (uses spec.rewrites from Phase 2)
    dense_pools = await asyncio.gather(*(
        vector_search(q, engine=engine, provider=provider,
                      repo_id=repo_id, k=recall_k,
                      path_prefix=spec.first_path_prefix())
        for q in [spec.raw_text, *spec.rewrites]
    ))
    # Sparse lane — fewer queries (BM25 doesn't need paraphrase variants)
    sparse = await bm25_search(spec.raw_text, engine=engine,
                               repo_id=repo_id, k=recall_k)
    return reciprocal_rank_fusion([*dense_pools, sparse], k_constant=60)[:recall_k]
```

## 4. What changes in the eval

- **New dataset**: `rare_symbol_v1.jsonl` (12 rows). Every question contains at least one **rare exact symbol** (a function/class/constant that appears in fewer than 5 chunks across the indexed repo).
- **Per-lane attribution metric**: `bench --phase 3` reports `recall@10_dense`, `recall@10_sparse`, `recall@10_hybrid` separately. We need to know the marginal contribution.
- **Indexing-time check**: after the migration runs, the existing slow-lane `httpx` index test must still complete within ≤ 90 s + 10 s (the tsvector backfill is cheap but non-zero).

## 5. Gate

The phase ships when all hold:

- [ ] `recall@10 hybrid − recall@10 dense ≥ 0.05` on `rare_symbol_v1`.
- [ ] `recall@10 hybrid − recall@10 phase2_after ≥ 0.03` on `httpx_qa_v1` (sanity check that BM25 helps the general bench, not only the rare-symbol bench).
- [ ] On `not_in_repo` questions (the hallucination subset across all datasets), the union returns **no spurious hits** — BM25 should also return zero candidates for nonsense tokens. Forced-hallucination still returns `NOT_FOUND_SENTINEL`.
- [ ] `latency_p95_ms` ≤ 1.2× Phase 2. BM25 in Postgres FTS is fast (< 50 ms typically); the dense lane is the bottleneck.
- [ ] Migration `0002_chunks_tsvector` applies cleanly on a freshly-indexed httpx, and the slow-lane index gate still passes.
- [ ] `evals/results/rag_phase3/{_before,_after,delta}.json` committed.

## 6. Stop conditions

Phase 3 is rolled back if:

- BM25 + dense fusion is **worse than dense alone** on `httpx_qa_v1`. That means BM25 is injecting noise that RRF doesn't suppress; usually a sign of weight imbalance. Try `k_constant=40` or `80` before giving up.
- The migration backfill takes > 5 minutes on a 50 kLOC repo. Should be seconds; if it isn't, the SQL needs work.
- Per-lane attribution shows `recall@10_sparse < 0.1` on `rare_symbol_v1` — meaning BM25 isn't actually finding the rare-symbol chunks. The most likely cause is `to_tsvector('english', ...)` stripping non-word tokens; the fix is the `simple` config (`to_tsvector('simple', ...)`) which preserves identifiers.

## 7. Implementation order

1. Migration first; backfill the column; index. Confirm `bm25_search` works on the existing `httpx` index.
2. Wire `hybrid_search` as a feature-flagged path. Run the `--phase 3` bench in both modes (dense-only vs. hybrid).
3. Tune `k_constant`, normalize-vs-not, `english` vs. `simple` analyzer — these are 2–4 quick A/B sweeps with the bench.
4. Flip the default to hybrid; commit results.

---

## Honest notes

- **Why `simple` analyzer is likely correct for code**: `english` stems "redirects" to "redirect", which is good. But it also folds case and strips punctuation that matters in code (`HTTPTransport` becomes `httptransport`). Worth A/Bing.
- **The dataset must include both kinds of rare tokens**: snake_case identifiers (where `english` works fine) and CamelCase class names (where `simple` is essential). Otherwise the gate is gamed.
- **RRF is order-independent in `k_constant`**, but extremely sensitive to how many lanes you fuse. Fusing the 3 dense lanes from Phase 2 + 1 sparse lane (total 4) is empirically better than 1 dense + 1 sparse — but it can also hide bad rewrites. If the bench underperforms with multi-query + BM25 combined but passes with single-query + BM25, the right answer is to look harder at Phase 2's rewrites.
