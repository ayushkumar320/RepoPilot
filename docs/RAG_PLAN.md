# RAG Quality Plan — RepoPilot Retrieval Upgrade

> **Status:** Active. This is the doc that replaces the original product-build plan now that the product slice ships end-to-end. The work below is about **retrieval quality**, not new product surface.
>
> **Owner of progress tracking:** [`CURRENT_PHASE.md`](CURRENT_PHASE.md).
> **Owner of conventions / rules:** [`CLAUDE.md`](../CLAUDE.md).
> **What we built before this plan:** see [`01_PROBLEM_AND_SOLUTION.md`](01_PROBLEM_AND_SOLUTION.md), [`02_TECH_STACK.md`](02_TECH_STACK.md), [`03_ARCHITECTURE.md`](03_ARCHITECTURE.md).

---

## Why this plan exists

The product Phases 0–5 shipped the end-to-end pipeline (clone → parse → chunk → embed → persist → vector search → graph traverse → answer → verify). It works. **It is also unmeasured under real LLM load.** Phase 2's grounding gate (≥ 90%), Phase 3's intent-profiler accuracy (≥ 90% per field), Phase 5's opportunity-quality numbers — all of them have "datasets ready, harness wired, awaits real-LLM run" stamped on them.

That isn't an accident — it's the cost of moving fast in the first half of the build. Now we close it.

In parallel, the retrieval shape we shipped in Phase 2 is **minimum-viable hybrid retrieval**: pure cosine k-NN with `k=8`, then graph traversal on the same set, then answer. The target shape (from the user-supplied diagram) is the full pipeline:

```
User Query → Query Understanding → Hybrid Retrieval → Candidate Pool (50–200)
            → Reranking → Context Compression → Answer Generation
            → Grounding & Verification → Final Response
```

We are missing **roughly 8 stages worth of quality lift** between where we are and that target. This plan ships them, **one phase at a time, each with a measured gate.** No phase ships without a number that says it's better than the phase before it.

---

## The 7 phases at a glance

Each phase is independently shippable; each unlocks the next. The diagram on the right of every phase number shows where in the target pipeline it lands.

| # | Phase | Stage in target pipeline | Headline gate | New deps |
|---|---|---|---|---|
| **0** | [Baseline & Measurement](rag/00_BASELINE_AND_MEASUREMENT.md) | (measurement spine) | A baseline number exists for every metric we will improve later | `ragas` or hand-rolled (TBD in phase) |
| **1** | [Recall lift](rag/01_RECALL_LIFT.md) | Hybrid Retrieval (dense side) + Candidate Pool | recall@10 ≥ baseline + 5 pp | none |
| **2** | [Query Understanding](rag/02_QUERY_UNDERSTANDING.md) | Query Understanding | recall@10 lift ≥ 5 pp over Phase 1 on multi-hop questions | none (uses existing 8B model) |
| **3** | [BM25 Hybrid](rag/03_HYBRID_RETRIEVAL_BM25.md) | Hybrid Retrieval (sparse side) | recall@10 lift ≥ 5 pp on rare-symbol / proper-noun queries | none (Postgres FTS built-in) |
| **4** | [Reranking](rag/04_RERANKING.md) | Reranking | NDCG@5 lift ≥ 0.05 over Phase 3 | `fastembed` (~80 MB) |
| **5** | [Context Compression](rag/05_CONTEXT_COMPRESSION.md) | Context Compression | ≥ 40% input-token reduction at equal grounding-accuracy | none |
| **6** | [Ingestion Enrichment](rag/06_INGESTION_ENRICHMENT.md) | Embeddings + Vector DB (offline side) | recall@10 lift ≥ 3 pp from corpus-side change alone | none (radon optional) |

After Phase 6, the pipeline implements the full user-supplied diagram with every stage measured.

---

## The measurement spine (read this before any phase)

Every phase must answer **the same three questions** before it ships:

1. **What was the number before this phase?** (recorded in `docs/rag/<phase>.md` and in `evals/results/<phase>_before.json`)
2. **What is the number after this phase?** (same files, `_after.json`)
3. **Is the delta meaningful?** (statistical significance with at least the bootstrap CI in `evals/runners/significance.py`, which Phase 0 builds)

If a phase ships with `_after.json` ≤ `_before.json`, **the phase is reverted, not landed.** This is non-negotiable; otherwise we are guessing whether the pipeline improved.

### Eval datasets we will use

| Dataset | Existing? | Used by which phases |
|---|---|---|
| `httpx_qa_v1.jsonl` (16 rows) | ✅ in repo | All phases (primary recall + grounding bench) |
| `verifier_quality_v1.jsonl` (30 rows) | ✅ in repo | Phase 0 (calibrate verifier), Phase 5 (compression should not change verifier verdicts) |
| `flask_qa_v1.jsonl` (target 20 rows) | ❌ Phase 0 creates | Phase 1 onward (cross-repo generalization check) |
| `fastapi_qa_v1.jsonl` (target 15 rows) | ❌ Phase 0 creates | Phase 1 onward (cross-repo generalization check) |
| `rare_symbol_v1.jsonl` (target 12 rows) | ❌ Phase 3 creates | Phase 3, 4 (BM25 + reranker validation) |
| `multi_hop_v1.jsonl` (target 10 rows) | ❌ Phase 2 creates | Phase 2 onward (query-understanding lift) |

The datasets are small on purpose. Hand-labeling 15–20 rows per repo is **3–5 hours of focused work**, and labels are higher quality than auto-generated. Phase 0 owns the labeling protocol.

### Metrics, in priority order

| Metric | Why we track it | Phase that targets it most |
|---|---|---|
| **recall@k** (k = 5, 10, 20) | Did the right chunk make it into the candidate pool? | 1, 2, 3, 6 |
| **NDCG@k** (k = 5, 10) | Are the *good* chunks at the top of the pool? | 4 |
| **MRR** (mean reciprocal rank) | How close to position 1 was the first relevant chunk? | 4 |
| **grounding accuracy** | Did the answerer get the right claims, and are they all grounded? | All (this is the product's truth claim) |
| **hallucination rate** | On not-in-repo questions, do we honestly say so? | All (must not regress) |
| **input tokens per question** | Cost / latency proxy | 5 |
| **wall-clock latency p50 / p95** | UX quality | All (must not regress beyond 1.5×) |
| **verifier accuracy** | Without this, grounding accuracy is a function of two unknown error rates | 0 |

---

## Per-phase doc template (what every `docs/rag/<n>_*.md` looks like)

Each phase doc has the same six sections so progress is comparable:

1. **Goal** — one sentence, one number.
2. **Why now** — what the previous phase unlocked and what this phase prerequisite-checks.
3. **What changes in the code** — files touched, new modules, new schemas, with line-count estimates.
4. **What changes in the eval** — new datasets, new metric runners, new fixtures.
5. **Gate** — the explicit pass/fail number on the eval set, including significance test.
6. **Stop conditions** — what would make us *not* land this phase.

This is the same shape `docs/05_PHASE_PROMPTS.md` used to have, just for retrieval quality instead of product surface.

---

## Sequencing rationale (why this order)

The order is **lowest-risk-highest-leverage first**:

- **Phase 0 must be first** because every later number is meaningless without a baseline. If Phase 0 takes 2 days that's correct; if it takes 4 hours that's because we cut a corner we will pay for.
- **Phase 1 before Phase 4** because a reranker reranking 8 candidates is useless — the right chunk has to be *in the pool* before reranking can pull it to the top.
- **Phase 2 before Phase 3** because query rewriting lifts recall on the dense side too, so BM25's measured contribution in Phase 3 reflects what BM25 *actually* adds, not what we missed in Phase 2.
- **Phase 4 before Phase 5** because compression operates on whatever the reranker chose — if reranking is wrong, compression amplifies the wrong context.
- **Phase 6 last** because ingestion enrichment requires re-indexing every test repo — running it earlier wastes hours every time we re-index.

If you must skip phases for time pressure: Phase 0 is non-skippable; Phases 1 + 3 + 4 are the meaningful-quality minimum; Phases 2 + 5 + 6 are the polish.

---

## What this plan deliberately does NOT do

To keep scope honest:

- **No swap to an external vector DB.** pgvector + Postgres FTS + the existing JSONB graph stay. Adding Pinecone/Weaviate/Qdrant doesn't help any gate.
- **No swap of the embedding model.** Ollama `nomic-embed-text` (768 d) stays. Benchmarks on code retrieval don't justify the migration cost.
- **No new graph DB.** The Phase 1 JSONB sidecar + in-memory NetworkX rebuild is fast enough.
- **No paid reranker APIs** (Cohere Rerank, Voyage). Phase 4 uses local `fastembed`. If we eventually need Cohere-level quality, that's a separate decision after measurement, not before.
- **No agentic retrieval rewrite** (e.g. ReAct-style multi-tool loops). The Q&A graph already does hop-budgeted retrieval expansion. Adding a tool-call loop on top is bloat until the simpler pipeline plateaus.

If a future contributor wants to add any of the above, they own a measured A/B showing the existing pipeline isn't enough, on at least 3 repos.

---

## Definition of Done (for the whole plan)

The plan is done when **all of the following hold simultaneously**:

- [ ] Every phase's `_after.json` improves over its `_before.json` with statistical significance.
- [ ] `httpx_qa_v1` grounding accuracy ≥ 90% under real LLM (the Phase 2 product gate, never previously measured).
- [ ] `verifier_quality_v1` verifier accuracy ≥ 92% under real LLM.
- [ ] Forced-hallucination test: 3 not-in-repo questions across each labeled dataset return `NOT_FOUND_SENTINEL`.
- [ ] Cross-repo generalization: `flask_qa_v1` and `fastapi_qa_v1` grounding accuracy each ≥ 85% (lower bar; different repos to stress generalization).
- [ ] Latency p95 ≤ 1.5× the baseline measured in Phase 0 (so we don't trade quality for unusable demos).
- [ ] All 7 phase docs have committed `_before.json` and `_after.json` artifacts; CI fails if a future PR changes retrieval without producing a fresh `_after.json`.

The last bullet is the forcing function: **once this plan ships, the eval harness becomes a regression gate.**

---

## For contributors

Read in this order: this file → [`docs/CURRENT_PHASE.md`](CURRENT_PHASE.md) (which phase is active) → the active phase's doc in [`docs/rag/`](rag/). The active phase doc tells you exactly what to build, what to measure, and what number must improve.

When you finish a phase: update `CURRENT_PHASE.md` in the same commit. The "documentation-layering bug" rule from `CLAUDE.md` applies here too — a phase advance without a `CURRENT_PHASE.md` update is a process bug.
