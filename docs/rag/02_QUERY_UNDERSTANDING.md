# RAG Phase 2 — Query Understanding (Rewriting + Multi-Query + Metadata Extraction)

> **Status 2026-07-15:** Implemented, but not landed. Retrieval-only measurement on `multi_hop_v1`/httpx found raw dense recall@10 **0.8500** vs query-understanding recall@10 **0.8167**. Ranking improved (`ndcg@10` 0.7343 → 0.7435; MRR 0.8667 → 0.9000), but the recall gate requires +5 pp, so this phase remains unlanded until rewrite acceptance improves or the phase is explicitly deferred.

## 1. Goal

Lift recall@10 on **multi-hop questions** by **≥ 5 percentage points** over the Phase 1 number, by transforming the raw user question into a structured `QuerySpec` before retrieval.

A `QuerySpec` carries:

- **Rewrites** — 2–3 reformulations of the question to query for in parallel and union (`HyDE`-style + lexical paraphrase).
- **Extracted metadata** — any symbol/file/module hints in the question, fed to Phase 1's metadata filters.
- **Intent class** — `factual` / `procedural` / `architectural` / `where-is` / `compare`, controls retrieval policy.

## 2. Why now

Phase 1 grew the candidate pool. That helps when the question is well-stated. It doesn't help when the user asks *"how does flask handle redirects?"* and the actual code uses the symbol `_redirect_method` — the embedding distance between "redirect" and `_redirect_method` is fine but the lexical mismatch loses to a 10-token question. Multi-query union with reformulations and extracted symbol mentions closes that gap.

Phase 1 prerequisite-checks:

- `evals/results/rag_phase1/_after.json` committed.
- `recall_k` parameter on `vector_search` is wired (Phase 2 issues N parallel `vector_search` calls and unions; without `recall_k`, the union pool is too small).

## 3. What changes in the code

| Path | Type | LOC est. | Purpose |
|---|---|---|---|
| `packages/agents/src/repopilot_agents/qa/query_spec.py` | new | ~120 | `QuerySpec` Pydantic model + `build_query_spec(question)` LLM call |
| `packages/agents/src/repopilot_agents/qa/prompts.py` | edit | ~+60 | `QUERY_SPEC_SYSTEM` prompt + few-shot examples |
| `packages/agents/src/repopilot_agents/qa/graph.py` | edit | ~+30 | Replace the single `vector_search` call with N parallel calls + RRF union |
| `packages/agents/src/repopilot_agents/qa/union.py` | new | ~50 | Reciprocal Rank Fusion (RRF) helper — reused by Phase 3 |
| `packages/agents/tests/test_query_spec.py` | new | ~80 | LLM-stubbed unit tests for the QuerySpec builder |
| `packages/agents/tests/test_qa_multi_query.py` | new | ~60 | End-to-end test that multi-query unions correctly |
| `evals/datasets/multi_hop_v1.jsonl` | new (labeled) | 10 rows | The bench Phase 2 must lift on |
| `evals/results/rag_phase2/` | new artifact dir | — | `_before` (copy Phase 1 `_after`), `_after`, `delta` |

**Zero new pip deps.** `QuerySpec` uses `ModelId.CODE_HEALTH` (the cheap 8B Groq slot) — same model already wired for chunk summaries.

### What `build_query_spec` does

```python
class QuerySpec(BaseModel):
    raw_text: str                    # original question, preserved
    rewrites: list[str]              # 2-3 reformulations
    extracted_symbols: list[str]     # dotted paths if any
    extracted_paths: list[str]       # file path globs if any
    intent_class: Literal["factual", "procedural", "architectural", "where_is", "compare"]
    needs_multi_hop: bool             # hint to the sufficiency judge
```

One LLM call to the 8B model, JSON output, **parse-fail-falls-back-to-raw** (the raw question becomes the only "rewrite", so the pipeline never breaks if the LLM stumbles).

### Multi-query union

```python
all_rewrites = [spec.raw_text, *spec.rewrites]
pools = await asyncio.gather(*(
    vector_search(q, recall_k=50, ...) for q in all_rewrites
))
unioned = reciprocal_rank_fusion(pools, k_constant=60)
top_pool = unioned[:50]    # back to a single pool of 50 for downstream
```

RRF (Reciprocal Rank Fusion) is the standard fusion technique — combines ranked lists without needing to compare distance scores across queries. The `k_constant=60` is the literature default.

Implemented note: the raw user query lane is weighted 3× above rewrite lanes. This protects the original dense ranking from noisy rewrites, matching the Phase 3 dense-over-sparse precedent.

### Metadata filter wiring

If `spec.extracted_paths` is non-empty and the intent is a focused `where_is` query, the calls become `vector_search(q, path_prefix=...)` — Phase 1 already exposed this surface. Path filters are intentionally disabled for multi-hop/architectural questions because an early run showed broad flow questions could collapse to zero-hit lanes when the small model extracted phrase-like "paths."

## 4. What changes in the eval

- **New dataset**: `multi_hop_v1.jsonl` (10 rows). Each question requires ≥ 2 graph traversals or ≥ 2 distinct file regions to answer correctly. Labeled with `expected_refs` spanning multiple files.
- **Reused datasets**: all from Phase 0/1.
- **New runner step**: `bench --phase 2` runs the suite including `multi_hop_v1`.
- **New metric**: `query_spec_extraction_accuracy` — on a hand-labeled subset, does the extractor get symbols/paths right? Threshold: ≥ 85%.

## 5. Gate

The phase ships when all hold:

- [ ] `recall@10 after − recall@10 before ≥ 0.05` on `multi_hop_v1`.
- [ ] `recall@10` does not regress on `httpx_qa_v1`, `flask_qa_v1`, or `fastapi_qa_v1` (multi-query shouldn't hurt single-hop).
- [ ] `query_spec_extraction_accuracy ≥ 0.85` on the labeled extraction subset.
- [ ] `grounding_accuracy` does not regress > 1 pp on any dataset.
- [ ] `latency_p95_ms` ≤ 1.3× the Phase 1 number. Multi-query parallelism keeps wall-clock reasonable but does pay 3× the embedding cost.
- [ ] `evals/results/rag_phase2/{_before,_after,delta}.json` committed.

## 6. Stop conditions

Phase 2 is rolled back if:

- Rewrites cause `grounding_accuracy` regression > 1 pp on `httpx_qa_v1`. Common failure mode: rewrites add noise to a question the dense model would have answered fine alone.
- The LLM extraction step costs > 500 ms p50 on the 8B model. The "cheap query rewrite" should not become the latency bottleneck.
- The intent classifier is wrong > 30% of the time on a labeled spot-check. We can keep multi-query and drop intent-class routing if that happens, and revisit later.

## 7. Implementation order

1. `QuerySpec` model + `build_query_spec` stub that returns `rewrites=[raw_text]`. Wire it through the Q&A graph. Confirm no regression — this is the "do nothing" check.
2. Add real rewrites (LLM call); confirm parallel fan-out works under the existing `asyncio.gather` patterns.
3. Add metadata extraction; gate it behind a feature flag so we can A/B in `bench`.
4. Add intent-class routing; for now this only affects the sufficiency judge's `max_hops` (multi-hop questions get `max_hops=3`, others `max_hops=1`).
5. Run `bench --phase 2`; commit results.

---

## Honest notes

- **Multi-query is a known win in code RAG**; recall lifts of 5–10 pp are typical. Whether *this codebase* gets it depends on how lexically-mismatched the test questions are. The `multi_hop_v1.jsonl` dataset must be constructed to *include* lexical mismatches deliberately — if every test question already uses the right symbol name, multi-query won't help and we'll wrongly conclude it didn't work.
- **Intent classification is the riskiest part**: small models classify intent poorly on terse questions. If the dataset has many "what is X?" questions, classification may default to `factual` so consistently that the routing does nothing. That's fine — the routing then has zero impact rather than negative impact.
- **`HyDE` (Hypothetical Document Embeddings) is the obvious next step** after this — generate a hypothetical answer and embed *that* — but it's a 6th rewrite at best and the cost grows. Defer to Phase 6 polish if Phase 2's lift is below the gate.
