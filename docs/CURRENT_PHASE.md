# Current Build Phase

> **Active implementation phase:** **RAG Phase 1 — Recall Lift** (next to start).
> **Last verified gate:** RAG Phase 0 complete — `evals/results/rag_phase0/baseline.json` committed (`8e7d0d6`) with per-repo baselines for httpx, flask, fastapi and reviewed QA datasets for all three.
> **Last updated:** 2026-07-05

This document is the **always-correct pointer** at where the build is. Anyone (human or agent) starting a session reads this first. The plan it points at is [`docs/RAG_PLAN.md`](RAG_PLAN.md); the execution schedule is the **2-day ship plan** in [`rag/00_TODAY_PLAN.md`](rag/00_TODAY_PLAN.md). Per-phase specs live in [`docs/rag/`](rag/).

---

## What just happened

**RAG Phase 0 (Baseline & Measurement) shipped.** All three repos are indexed (fastapi required a re-index after a Neon pooled-connection fix — `pool_pre_ping` now set in `make_engine`), the answer keys are reviewed, and the baseline is committed. Notable Phase 0 facts, recorded for later phases:

- `flask_qa_v1.jsonl`: 20 rows (17 gold + 3 not-in-repo traps). ~15 labels were AI-proposed from source-filtered candidates and spot-checked; 3 (`Config.from_object`, default-404 handling, cookie parsing) were hand-labeled directly from the chunks table because retrieval missed them **beyond rank 150** — a concrete Phase 1 target.
- The label-proposal tool (`evals/tools/propose_labels.py`) now over-fetches top-150 and filters `tests/`, `examples/`, `docs/`, `docs_src/`, `scripts/` — gold labels are source-only by construction.
- Known infra landmines: Neon drops idle SSL connections (fixed); HuggingFace router returns 402 (out of credits) — the verifier chain must succeed on Groq/Cerebras.

The doc set was consolidated on 2026-07-05: `rag/00_EXECUTION_RUNBOOK.md` removed (Phase 0 executed; git history retains it), `rag/00_TODAY_PLAN.md` rewritten as the 2-day ship plan for Phases 1–6.

---

## RAG phase ladder

| Phase | Status | Spec | Headline gate |
|---|---|---|---|
| **0 — Baseline & Measurement** | 🟢 **done** (2026-07-04) | [rag/00](rag/00_BASELINE_AND_MEASUREMENT.md) | Baseline committed for every metric on 3 repos ✅ |
| **1 — Recall Lift** | 🟡 **active** | [rag/01](rag/01_RECALL_LIFT.md) | recall@10 ≥ baseline + 5 pp |
| 2 — Query Understanding | ⚪ pending (timeboxed — may defer) | [rag/02](rag/02_QUERY_UNDERSTANDING.md) | recall@10 lift ≥ 5 pp on multi-hop |
| 3 — BM25 Hybrid | ⚪ pending (must-ship) | [rag/03](rag/03_HYBRID_RETRIEVAL_BM25.md) | recall@10 lift ≥ 5 pp on rare-symbol |
| 4 — Reranking | ⚪ pending (must-ship) | [rag/04](rag/04_RERANKING.md) | NDCG@5 lift ≥ 0.05 |
| 5 — Context Compression | ⚪ pending (timeboxed — may defer) | [rag/05](rag/05_CONTEXT_COMPRESSION.md) | ≥ 40% input-token reduction at equal grounding |
| 6 — Ingestion Enrichment | ⚪ pending (timeboxed — may defer) | [rag/06](rag/06_INGESTION_ENRICHMENT.md) | recall@10 lift ≥ 3 pp from corpus changes alone |

Legend: 🟢 done · 🟡 active · ⚪ pending · 🔴 blocked. "Must-ship / may defer" reflects the 2-day ship plan's priority calls (from RAG_PLAN §Sequencing: 1+3+4 are the quality minimum, 2+5+6 are polish).

---

## RAG Phase 1 — entry state

All Phase 0 exit criteria hold; Phase 1 can start immediately:

- ✅ Baseline numbers exist and are committed for httpx / flask / fastapi.
- ✅ Datasets frozen: `httpx_qa_v1` (16), `flask_qa_v1` (20), `fastapi_qa_v1` (15) — do **not** edit gold labels mid-phase; version `_v2` instead.
- ✅ Bench + cache + significance runner in place (`python -m repopilot_evals.bench`).
- Procedure: copy baseline → `evals/results/rag_phase1/_before.json`, implement per [rag/01](rag/01_RECALL_LIFT.md), rerun bench → `_after.json`. **If after ≤ before, revert the phase.**

---

## What's still load-bearing from the previous product build

Although the product-build phase docs are removed, the **code** they produced is intact and live on `main`. Treat this as the corpus the RAG plan operates on:

- ✅ `LLMProvider` (Groq → Cerebras → HF → Ollama fallback, SQLite cache, 429 backoff).
- ✅ Ingestion pipeline (clone → tree-sitter chunk → NetworkX graph → embed → persist).
- ✅ Six deterministic tools (`vector_search`, `read_chunks`, `graph_traverse`, `graph_query`, `graph_metrics`, `github_issues` stub).
- ✅ Verifier (parse-fail = reject, async batched, hash cache, `<source>` prompt-injection wrapper).
- ✅ Q&A graph (hybrid retrieval ≤ 3 hops, hallucination short-circuit).
- ✅ `ArchaeologistState`, Intent Profiler, Capability Planner, goal-anchor helper, full LangGraph wiring with `recursion_limit=15`.
- ✅ Contribute lanes (A issue-triage, B quality, C suspicion) and deterministic ranker.
- ✅ FastAPI route surface (`POST /repos`, `GET /repos/{id}/status`, `POST /tours`, etc.).
- ✅ Next.js 15 frontend (URL input, intent-capture, tour panel, synchronized code viewer, ask-anything).

---

## How to advance the phase

1. Read [`RAG_PLAN.md`](RAG_PLAN.md), then the active phase's doc, then the day schedule in [`rag/00_TODAY_PLAN.md`](rag/00_TODAY_PLAN.md). To hand the phase to a coding agent, use the ready-made build prompt in [`docs/build/`](build/README.md).
2. Implement; produce a measured `_after.json`.
3. If the gate passes: update **this file** in the same commit (flip status, update "Last verified gate"). Run `/graph-update`.
4. If the gate fails: stop. Either iterate within the same phase, or document the stop condition met in the phase doc and consult before advancing.
5. If a timeboxed phase (2, 5, 6) blows its box: mark it ⚪ **deferred** here with its entry state noted — deferred with a clean note is a good outcome; half-merged is the only bad one.

> **The phase-transition forcing function stays.** A phase advance without a `CURRENT_PHASE.md` update in the same commit is a documentation-layering bug.
