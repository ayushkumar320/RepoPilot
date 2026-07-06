# Current Build Phase

> **Next build purpose:** **RAG Phase 1 — Recall Lift.** Grow the dense-search candidate pool from `k=8` to `recall_k≈50` and expose the metadata filters (`kind`, path prefix/glob) the schema already supports. Gate: **recall@10 ≥ baseline + 5 pp** on `httpx_qa_v1`, replicated on at least one other repo, statistically significant. Spec + executable prompt: [`rag/01_RECALL_LIFT.md`](rag/01_RECALL_LIFT.md).
> **Last verified gate:** RAG Phase 0 complete — `evals/results/rag_phase0/baseline.json` committed (`8e7d0d6`) with per-repo baselines for httpx, flask, fastapi and reviewed QA datasets for all three.
> **Last updated:** 2026-07-06

This document is the **always-correct pointer** at where the build is. Anyone (human or agent) starting a session reads this first. The plan it points at is [`RAG_PLAN.md`](RAG_PLAN.md); the execution schedule is the **2-day ship plan** in [`rag/00_TODAY_PLAN.md`](rag/00_TODAY_PLAN.md); per-phase specs (each is also the build prompt to hand a coding agent) live in [`rag/`](rag/).

---

## Why Phase 1 is the next build

Every question RepoPilot answers rides on one retrieval call. Today that call returns **8 candidates** — and Phase 0 proved that's the bottleneck: three flask gold answers sat **beyond rank 150**, invisible to a k=8 pool no matter how good the downstream answerer is. Phase 1 is the cheapest lift in the whole plan (zero new deps, ~40 LOC) and every later phase is starved without it:

- **Phase 2 (Query Understanding)** issues parallel rewritten queries and unions them — pointless against a k=8 pool; it also consumes the metadata filters Phase 1 exposes.
- **Phase 3 (BM25)** fuses a sparse lane into the pool — a wider pool is what it fuses into.
- **Phase 4 (Reranking)** reorders the pool — "a reranker reranking 8 candidates is useless."
- **Phase 5 (Compression)** trims the reranked pool back down to a lean prompt — it exists *because* Phase 1 made the pool big.

So the build order isn't arbitrary: **Phase 1 widens what we retrieve; 2 and 3 widen what we *catch*; 4 fixes the order; 5 shrinks the cost; 6 improves the raw material.** One number gates each step.

---

## The improvement chain (what each phase fixes, and what it hands the next)

Target pipeline (from [`RAG_PLAN.md`](RAG_PLAN.md)):

```
User Query → Query Understanding → Hybrid Retrieval → Candidate Pool (50–200)
            → Reranking → Context Compression → Answer Generation
            → Grounding & Verification → Final Response
```

| Phase | The failure it fixes | What it hands the next phase | Gate |
|---|---|---|---|
| **0 — Baseline** 🟢 | "Unmeasured under real LLM load" | Frozen datasets, baseline numbers, bench + significance runner | done ✅ |
| **1 — Recall Lift** 🟡 **← next** | Right chunk exists but never enters the k=8 pool (flask misses beyond rank 150) | A 50-wide pool + metadata-filter params for Phase 2 to drive | recall@10 +5 pp |
| 2 — Query Understanding *(may defer)* | User says "redirects", code says `_redirect_method` — one literal query misses | `QuerySpec` rewrites + the RRF union helper Phase 3 reuses | +5 pp on multi-hop |
| 3 — BM25 Hybrid **(must-ship)** | Embeddings can't rank rare tokens (exact symbols, error strings) | Sparse lane fused via RRF → a stable ~50-chunk hybrid pool | +5 pp on rare-symbol |
| 4 — Reranking **(must-ship)** | Best chunk is *in* the pool at rank 27; answerer reads only top ~8 | Cross-encoder + MMR ordered top-8 — the input compression trims | NDCG@5 +0.05 |
| 5 — Compression *(may defer)* | Top chunks are 40–80 lines; 3–8 lines are load-bearing | Lean prompts (verifier still sees full source) | −40% input tokens, grounding equal |
| 6 — Ingestion Enrichment *(may defer)* | Raw chunk text embeds worse than signature+decorators+docstring | Richer corpus; last because it re-pays a full re-index per iteration | +3 pp from corpus alone |
| [7 — Ship Closeout](rag/07_SHIP_CLOSEOUT.md) **(must-ship)** | A one-time win regresses silently | CI regression gate: retrieval PRs must ship a fresh `_after.json` | RAG_PLAN Definition of Done |

Priority (from the 2-day ship plan): **1 + 3 + 4 are the meaningful-quality minimum; 2, 5, 6 are timeboxed polish** — a blown timebox means cut and defer with a clean entry note, never stretch.

Legend: 🟢 done · 🟡 active · ⚪ pending · 🔴 blocked.

---

## Phase 1 — entry state (all Phase 0 exit criteria hold)

- ✅ Baseline numbers committed for httpx / flask / fastapi (`evals/results/rag_phase0/`).
- ✅ Datasets frozen: `httpx_qa_v1` (16), `flask_qa_v1` (20: 17 gold + 3 traps), `fastapi_qa_v1` (15) — never edit gold labels mid-phase; version `_v2` after.
- ✅ Bench + LLM cache + significance runner in place (`python -m repopilot_evals.bench`).
- Procedure: copy baseline → `evals/results/rag_phase1/_before.json`, implement per [rag/01](rag/01_RECALL_LIFT.md), rerun bench → `_after.json`. **If after ≤ before, revert the phase.**

### Phase 0 facts that feed later phases

- 3 flask answers (`Config.from_object`, default-404 handling, cookie parsing) were retrieved **beyond rank 150** — the concrete Phase 1 target, and the sanity check for Phase 4 ("tests/docs outrank source" should visibly die there).
- `evals/tools/propose_labels.py` over-fetches top-150 and filters `tests/`, `examples/`, `docs/`, `docs_src/`, `scripts/` — reuse this propose→review flow for `multi_hop_v1` (Phase 2) and `rare_symbol_v1` (Phase 3).
- Infra landmines: Neon drops idle SSL connections (fixed — `pool_pre_ping` in `make_engine`); HF router returns 402 (out of credits) — the verifier chain must succeed on Groq/Cerebras; Groq 429s → wait 60 s, the cache resumes.

---

## What the RAG plan operates on (live on `main`)

The product slice is intact — treat it as the corpus and pipeline the phases above modify:

- ✅ `LLMProvider` (Groq → Cerebras → HF → Ollama fallback, SQLite cache, 429 backoff).
- ✅ Ingestion pipeline (clone → tree-sitter chunk → NetworkX graph → embed → persist) — **Phase 6's target**.
- ✅ Six deterministic tools (`vector_search`, `read_chunks`, `graph_traverse`, `graph_query`, `graph_metrics`, `github_issues` stub) — **`vector_search` is Phase 1's target**; Phase 3 adds `bm25_search`/`hybrid_search` alongside.
- ✅ Verifier (parse-fail = reject, async batched, hash cache, `<source>` prompt-injection wrapper) — the referee for every grounding guardrail.
- ✅ Q&A graph (hybrid retrieval ≤ 3 hops, hallucination short-circuit) — where Phases 1–5 splice in.
- ✅ `ArchaeologistState`, Intent Profiler, Capability Planner, goal-anchor helper, LangGraph wiring (`recursion_limit=15`).
- ✅ Contribute lanes (A issue-triage, B quality, C suspicion) + deterministic ranker.
- ✅ FastAPI route surface + Next.js 15 frontend (URL input, intent capture, tour panel, synced code viewer, ask-anything).

---

## How to advance the phase

1. Read [`RAG_PLAN.md`](RAG_PLAN.md) → the active phase's spec in [`rag/`](rag/) (it doubles as the build prompt for a coding agent) → the day schedule in [`rag/00_TODAY_PLAN.md`](rag/00_TODAY_PLAN.md).
2. Implement; produce a measured `_after.json`.
3. Gate passes → update **this file** in the same commit (flip status, update "Last verified gate", rewrite the "Next build purpose" banner for the new phase). Run `/graph-update`.
4. Gate fails → stop. Iterate within the phase, or document the stop condition met in the phase spec and consult before advancing.
5. Timeboxed phase (2, 5, 6) blows its box → mark it ⚪ **deferred** here with its entry state noted. The next phase measures against the last **landed** `_after.json`, so nothing downstream breaks. Deferred with a clean note is a good outcome; half-merged is the only bad one.

> **The phase-transition forcing function stays.** A phase advance without a `CURRENT_PHASE.md` update in the same commit is a documentation-layering bug.
