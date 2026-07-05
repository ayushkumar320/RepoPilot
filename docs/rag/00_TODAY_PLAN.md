# Ship the RAG Upgrade in 2 Days — The Plan

> Plain-language driver for the whole [`RAG_PLAN.md`](../RAG_PLAN.md) ladder, replacing the old Phase-0-only day plan (Phase 0 is essentially done — `baseline.json` + all three per-repo baselines + all three QA datasets exist).
>
> **The deal in one sentence:** in 2 days we close Phase 0, ship the three phases that move quality the most (1 → 3 → 4), fit in the polish phases (2, 5, 6) only as time allows, and end with every landed change proven by a number over baseline.

**The honest scope call (from RAG_PLAN §Sequencing):** Phases **1 + 3 + 4 are the meaningful-quality minimum**; Phases **2 + 5 + 6 are polish**. Two days ships the minimum *well* rather than all six *badly*. Polish phases are strictly timeboxed — if one blows its box, it's cut, not stretched.

**The iron rule (unchanged):** every phase records `_before.json`, lands, records `_after.json`. If after ≤ before, **revert the phase, don't land it.** No exceptions for schedule pressure.

---

## Where we actually are (verified 2026-07-05)

| Artifact | Status |
|---|---|
| `httpx/flask/fastapi` indexed in Postgres | ✅ (fastapi re-indexed after the Neon SSL fix) |
| `flask_qa_v1.jsonl` (20 rows: 17 gold + 3 traps) | ✅ reviewed |
| `fastapi_qa_v1.jsonl`, `httpx_qa_v1.jsonl` | ✅ in datasets/ |
| `evals/results/rag_phase0/baseline.json` + per-repo files | ✅ exists |
| `CURRENT_PHASE.md` flipped to Phase 0 done | ❌ **Day 1, first task** |
| Baseline + datasets committed | ❌ **Day 1, first task** |

---

## Day 1 — Close the books, then recall

### D1.1 — Close Phase 0 (30 min)
1. Sanity-read `baseline.json`: no metric at exactly 0.0 or 1.0; verifier accuracy ≥ 88% (if below → **stop, fix verifier first**, steal time from Phase 2's box).
2. Note in `rag/00_BASELINE_AND_MEASUREMENT.md`: ~15 flask labels were AI-proposed + spot-checked; 3 were hand-labeled from chunks because retrieval missed them beyond rank 150 (that's a baseline finding — write it down).
3. Commit: `git add evals/results/rag_phase0/ packages/evals/src/repopilot_evals/datasets/*.jsonl` → commit → flip `CURRENT_PHASE.md` (0 🟢, 1 🟡) in the same commit → `/graph-update` → push.

### D1.2 — Phase 1: Recall Lift (~3 h) — **must ship**
Spec: [`01_RECALL_LIFT.md`](01_RECALL_LIFT.md). Gate: **recall@10 ≥ baseline + 5 pp** on `httpx_qa_v1`, no regression on flask/fastapi.
- Copy `baseline.json` → `evals/results/rag_phase1/_before.json`.
- Widen the candidate pool (k=8 → 50–200 pre-filter), fix any distance-threshold clipping.
- Rerun bench on all 3 repos → `_after.json`. Significance via bootstrap CI.
- Land or revert. Commit + `CURRENT_PHASE.md` flip + `/graph-update`.

### D1.3 — Phase 2: Query Understanding (timebox **2 h**, cut line 18:00) — polish
Gate: +5 pp recall@10 on multi-hop questions; needs `multi_hop_v1.jsonl` (10 rows — reuse the propose→review flow, source-filtered).
- **If the box blows** (dataset labeling drags or the 8B rewriter is flaky): cut it, mark ⚪ deferred in `CURRENT_PHASE.md`, move on. Phase 3's gate is measured against whatever shipped last, so nothing downstream breaks.

### D1.4 — Phase 3: BM25 Hybrid (start today, finish by D2 morning) — **must ship**
Gate: +5 pp recall@10 on rare-symbol queries. Postgres FTS, no new deps.
- Tonight: create `rare_symbol_v1.jsonl` (12 rows) via propose→review, add the FTS column + GIN index (needs a quick re-index — kick it off before stopping for the day; the arq worker does it unattended).

**End-of-Day-1 checkpoint:** Phase 0 closed & pushed, Phase 1 landed with numbers, Phase 3 prepped, Phase 2 landed *or* explicitly deferred. If Phase 1 didn't land, Day 2 starts there — do not start Phase 4 on top of an unlanded pool.

---

## Day 2 — Precision, then ship

### D2.1 — Phase 3 finish (~2 h) — **must ship**
Score fusion (RRF is fine), `_before`/`_after` on rare-symbol + all 3 QA sets, land or revert, commit + flip.

### D2.2 — Phase 4: Reranking (~3 h) — **must ship**
Gate: **NDCG@5 lift ≥ 0.05** over Phase 3. Local `fastembed` cross-encoder over the (now larger) candidate pool.
- This is where the "tests/docs outrank source" failure from labeling should visibly die — check rare-symbol and the flask routing question specifically.

### D2.3 — Phase 5: Context Compression (timebox **90 min**) — polish
Gate: ≥ 40% input-token cut at equal grounding accuracy, verifier verdicts unchanged on `verifier_quality_v1`. If grounding drops even 1 pp inside the box → cut it.

### D2.4 — Phase 6: Ingestion Enrichment (timebox **90 min**, incl. re-index wait) — polish
Gate: +3 pp recall@10 from corpus-side change alone. Requires re-indexing all 3 repos (~25 min wall clock — start the re-index, write the ship report while waiting). If the box blows, defer.

### D2.5 — Ship (~1 h, non-negotiable — steal from 5/6 if needed)
Run the whole Definition of Done from `RAG_PLAN.md`:
- [ ] Every landed phase has `_before.json` < `_after.json`, significant.
- [ ] `httpx_qa_v1` grounding ≥ 90%; flask/fastapi ≥ 85%.
- [ ] `verifier_quality_v1` ≥ 92%.
- [ ] All 9 not-in-repo traps return the honest "not found".
- [ ] Latency p95 ≤ 1.5× baseline.
- [ ] `CURRENT_PHASE.md` shows exactly what shipped and what was deferred, with the deferred phases' entry state written down.
- Final commit + push + `/graph-update`. Deferred ≠ failed: a deferred phase with a clean entry note is a good outcome; an unlanded phase silently left half-merged is the only bad one.

---

## Standing rules for both days

- **One phase in flight at a time.** Never start phase N+1 while N is unlanded.
- **The bench is the referee.** Same commands as Phase 0 (`python -m repopilot_evals.bench --phase N --repo …` + `--aggregate`); the cache means reruns after 429s are cheap.
- **Datasets are frozen.** Improving retrieval must never involve "fixing" a gold label mid-phase. Found a genuinely wrong label? Note it, finish the phase, version the dataset `_v2` after.
- **Known landmines from Phase 0:** Neon drops idle connections (fixed via pool_pre_ping — if SSL errors return, restart api+worker); HF router is out of credits (verifier falls through Groq→Cerebras→HF; if Groq 429s persist, wait 60 s, the cache resumes); uvicorn without `--reload` on purpose.

## If it all goes wrong

| Situation | Call |
|---|---|
| Phase 1 gate misses (+<5 pp) | Spend max 1 extra hour on pool-size sweep; still short → ship Phase 0 alone, re-plan. Don't torture the gate. |
| Verifier accuracy < 88% at D1.1 | Fix verifier before anything else — every other number depends on it. Phases 2/5/6 all get cut. |
| Day 2 noon and Phase 3 unlanded | Cut Phase 5+6, ship 1+3+4 by end of day. |
| Any `_after` ≤ `_before` | Revert that phase. The 2-day clock never overrides the iron rule. |
