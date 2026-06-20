# RepoPilot — Documentation Set Overview

The product slice (clone → index → retrieve → answer → verify) ships end-to-end on `main`. The doc set has been reshaped around the next chapter: **measured retrieval quality**, driven by [`RAG_PLAN.md`](RAG_PLAN.md).

> Prefer the [Graphify knowledge graph](../graphify-out/) over reading these raw — `graphify query "<question>"`. See [`CLAUDE.md`](../CLAUDE.md) for the project rules. This overview is the human-readable map; `CLAUDE.md` is the authoritative rule set.

## Where the build is right now

Read these in order if you're picking up cold:

1. [`CURRENT_PHASE.md`](CURRENT_PHASE.md) — which phase is active, what's blocking it.
2. [`RAG_PLAN.md`](RAG_PLAN.md) — the 7-phase plan, measurement spine, Definition of Done.
3. The active phase's doc in [`rag/`](rag/).

## Doc layout

```
docs/
├── README.md                       this file — doc index
├── CURRENT_PHASE.md                always-correct pointer at the active phase
├── RAG_PLAN.md                     the 7-phase retrieval-quality plan
├── 01_PROBLEM_AND_SOLUTION.md      product thesis (still true)
├── 02_TECH_STACK.md                tech choices + rationale (still true)
├── 03_ARCHITECTURE.md              agents, state, tools, verifier (still true)
└── rag/
    ├── 00_BASELINE_AND_MEASUREMENT.md     measurement spine; must run first
    ├── 01_RECALL_LIFT.md                  bigger pool + metadata filters
    ├── 02_QUERY_UNDERSTANDING.md          rewriting + multi-query + extraction
    ├── 03_HYBRID_RETRIEVAL_BM25.md        sparse + dense fusion
    ├── 04_RERANKING.md                    cross-encoder + MMR diversity
    ├── 05_CONTEXT_COMPRESSION.md          per-chunk line-level pruning
    └── 06_INGESTION_ENRICHMENT.md         richer chunk metadata for embedding
```

## What was removed

The original product-build planning docs (`00_CLAUDE_BUILD_GUIDE.md`, `04_BUILD_PLAN.md`, `05_PHASE_PROMPTS.md`) are gone. They drove the build through Phases 0–5 of the product; that work shipped and they're no longer load-bearing. Git history retains them.

## Per-doc summaries

### 01 — Problem and Solution

The product thesis. Establishes the user (juniors/OSS contributors on Python repos), the gap (no current tool gives a *purpose-driven* guided tour grounded in the actual source), and the bet (capture intent in free text → adapt every agent to it). Still true; the RAG plan operates on this premise.

### 02 — Tech Stack

Every layer choice with rationale and rejected alternatives. Hard constraint: free-tier survivable on a laptop. Still the controlling constraint for the RAG plan — Phase 4's new `fastembed` dep is the only deviation, and the doc justifies why local CPU inference fits the constraint.

### 03 — Architecture

Agent topology, state schema, six deterministic tools, verifier loop, hybrid-retrieval pattern. The blueprint the code implements. RAG phases edit this blueprint at specific points (Phase 3 adds a BM25 lane, Phase 4 adds a reranker block, Phase 5 adds compression); when they land, the blueprint diagram updates.

### RAG_PLAN

The 7-phase plan. Read this before any individual phase doc — it has the sequencing rationale, the measurement methodology, and the cross-phase Definition of Done.

### rag/00–06

One doc per phase. Each follows the same template: **Goal · Why now · What changes in the code · What changes in the eval · Gate · Stop conditions**. The gates are specific numbers, not vibes.

## One-paragraph takeaway

RepoPilot's product slice is built. The next stretch of work is making it *measurably good* under real LLM load: bigger recall pools, query understanding, hybrid sparse+dense, cross-encoder reranking, context compression, and ingestion-side enrichment — each phase with a baseline number it must beat, each shipped only if the bench says it actually helped.
