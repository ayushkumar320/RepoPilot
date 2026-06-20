# Current Build Phase

> **Active implementation phase:** **RAG Phase 0 — Baseline & Measurement** (not started).
> **Last verified gate:** the product slice (clone → index → retrieve → answer → verify) runs end-to-end locally; no formal LLM-side gate has ever been measured.
> **Last updated:** 2026-06-19

This document is the **always-correct pointer** at where the build is. Anyone (human or agent) starting a session reads this first. The plan it points at is [`docs/RAG_PLAN.md`](RAG_PLAN.md). Per-phase as-built records live in [`docs/rag/`](rag/).

---

## What just happened

The original product-build plan (`docs/04_BUILD_PLAN.md`, `docs/05_PHASE_PROMPTS.md`) was the right driver while there was no product yet. The product slice now exists end-to-end (the previous `CURRENT_PHASE.md` had Phases 0–5 marked done or code-side done). What it does **not** have is measured quality under real LLM load — every prior gate carries an "awaits paid Groq" or "awaits labeled dataset" caveat.

The doc set has been reshaped to drive that closure. We have replaced the product-build phase ladder with a **retrieval-quality phase ladder** focused on measured improvements. The old build docs (`00_CLAUDE_BUILD_GUIDE`, `04_BUILD_PLAN`, `05_PHASE_PROMPTS`) are removed.

What we keep:

- [`01_PROBLEM_AND_SOLUTION.md`](01_PROBLEM_AND_SOLUTION.md) — the product thesis. Still true.
- [`02_TECH_STACK.md`](02_TECH_STACK.md) — the stack choices. Still true.
- [`03_ARCHITECTURE.md`](03_ARCHITECTURE.md) — the agent/state/tools blueprint. Still true.
- [`../CLAUDE.md`](../CLAUDE.md) — project rules + engineering conventions. Updated to point at the new plan.

What's new:

- [`RAG_PLAN.md`](RAG_PLAN.md) — the 7-phase plan, the measurement spine, the Definition of Done.
- [`rag/`](rag/) — one doc per phase, each with goal / changes / eval / gate / stop conditions.

---

## RAG phase ladder

| Phase | Status | Spec | Headline gate |
|---|---|---|---|
| **0 — Baseline & Measurement** | 🟡 **active** (next to start) | [rag/00](rag/00_BASELINE_AND_MEASUREMENT.md) | Baseline number exists for every metric on at least 2 repos |
| 1 — Recall Lift | ⚪ pending | [rag/01](rag/01_RECALL_LIFT.md) | recall@10 ≥ baseline + 5 pp |
| 2 — Query Understanding | ⚪ pending | [rag/02](rag/02_QUERY_UNDERSTANDING.md) | recall@10 lift ≥ 5 pp on multi-hop |
| 3 — BM25 Hybrid | ⚪ pending | [rag/03](rag/03_HYBRID_RETRIEVAL_BM25.md) | recall@10 lift ≥ 5 pp on rare-symbol |
| 4 — Reranking | ⚪ pending | [rag/04](rag/04_RERANKING.md) | NDCG@5 lift ≥ 0.05 |
| 5 — Context Compression | ⚪ pending | [rag/05](rag/05_CONTEXT_COMPRESSION.md) | ≥ 40% input-token reduction at equal grounding |
| 6 — Ingestion Enrichment | ⚪ pending | [rag/06](rag/06_INGESTION_ENRICHMENT.md) | recall@10 lift ≥ 3 pp from corpus changes alone |

Legend: 🟢 done · 🟡 active · ⚪ pending · 🔴 blocked.

---

## RAG Phase 0 — entry checklist

Phase 0 cannot start until these are confirmed. Restated from [`rag/00_BASELINE_AND_MEASUREMENT.md`](rag/00_BASELINE_AND_MEASUREMENT.md) for visibility:

- [ ] **Paid Groq quota** available, OR explicit decision to run baseline against Ollama-only with documented quality cost.
- [ ] **LangSmith API key** provisioned (otherwise we cannot inspect failures after the fact).
- [ ] **Human time budgeted** — 3–5 hours of focused labeling for `flask_qa_v1.jsonl` (20 rows) and `fastapi_qa_v1.jsonl` (15 rows). Or, alternatively, 1.5 hours of human time if the candidate-proposed labels are auto-generated and reviewed.
- [ ] **`docker-compose` is running**, the Phase 1 slow-lane `httpx` index gate passes locally at least once (so we know the pipeline actually works end-to-end before measuring it).

If any box is unchecked, do that first. Phase 0 work that starts before these are checked produces numbers we cannot trust.

---

## What's still load-bearing from the previous product build

Although the product-build phase docs are removed, the **code** they produced is intact and live on `main`. Treat this as the corpus the RAG plan operates on:

- ✅ `LLMProvider` (Groq → Cerebras → Ollama fallback, SQLite cache, 429 backoff).
- ✅ Ingestion pipeline (clone → tree-sitter chunk → NetworkX graph → embed → persist).
- ✅ Six deterministic tools (`vector_search`, `read_chunks`, `graph_traverse`, `graph_query`, `graph_metrics`, `github_issues` stub).
- ✅ Verifier (parse-fail = reject, async batched, hash cache, `<source>` prompt-injection wrapper).
- ✅ Q&A graph (hybrid retrieval ≤ 3 hops, hallucination short-circuit).
- ✅ `ArchaeologistState`, Intent Profiler, Capability Planner, goal-anchor helper, full LangGraph wiring with `recursion_limit=15`.
- ✅ Contribute lanes (A issue-triage, B quality, C suspicion) and deterministic ranker.
- ✅ FastAPI route surface (`POST /repos`, `GET /repos/{id}/status`, `POST /tours`, etc.).
- ✅ Next.js 15 frontend (URL input, intent-capture, tour panel, synchronized code viewer, ask-anything).
- ⚠️ **Phase 1 slow-lane `httpx` 90 s gate**: still unrun on every developer machine. Run it before RAG Phase 0 starts.

---

## How to advance the phase

1. Read [`RAG_PLAN.md`](RAG_PLAN.md), then the active phase's doc.
2. Implement; produce a measured `_after.json`.
3. If the gate passes: update **this file** in the same commit (flip status, update "Last verified gate"). Open a PR or commit to main per project policy.
4. If the gate fails: stop. Either iterate within the same phase, or document the stop condition met in the phase doc and consult before advancing.

> **The phase-transition forcing function from the old plan stays.** A phase advance without a `CURRENT_PHASE.md` update in the same commit is a documentation-layering bug. The old commit history shows three Phase 1 → 2 → 3 transitions that broke this rule; we will not break it again.
