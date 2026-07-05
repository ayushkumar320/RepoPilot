# Build Prompt — Ship Closeout (Definition of Done)

> **Non-negotiable, ~1 hour — steal time from Phases 5/6 if needed.** This is the RAG_PLAN Definition of Done run as a checklist, plus the regression-gate forcing function.

---

You are running the **ship closeout** for RepoPilot's RAG plan. Read `CLAUDE.md`, `docs/RAG_PLAN.md` §Definition of Done, and `docs/CURRENT_PHASE.md` first.

## Verify (report each with the actual number, no hedging)

- [ ] Every **landed** phase has `_before.json` < `_after.json` with bootstrap-CI significance (`evals/results/rag_phase*/`).
- [ ] `httpx_qa_v1` grounding accuracy ≥ 90% under real LLM.
- [ ] `flask_qa_v1` and `fastapi_qa_v1` grounding accuracy each ≥ 85%.
- [ ] `verifier_quality_v1` verifier accuracy ≥ 92%.
- [ ] All 9 not-in-repo trap questions return `NOT_FOUND_SENTINEL`.
- [ ] Latency p95 ≤ 1.5× the Phase 0 baseline (per-phase budgets were looser; the *cumulative* budget is 1.5×).
- [ ] Every deferred phase is marked ⚪ deferred in `CURRENT_PHASE.md` with its entry state written down. Deferred ≠ failed; half-merged is the only bad outcome.

## Build the regression gate

Add a CI job that fails any future PR touching retrieval paths (`packages/agents/src/repopilot_agents/{tools,qa,rerank}/`, `packages/ingestion/`) unless it includes a fresh `_after.json`. This turns the eval harness into a permanent regression gate — the last bullet of RAG_PLAN's Definition of Done.

## Write the ship report

`evals/results/SHIP_REPORT.md`: per-phase table (landed/deferred, headline metric before → after, significance), the cumulative recall@10 / NDCG@5 / grounding / latency picture vs. Phase 0 baseline, and the deferred phases' entry states.

## Final protocol

Update `docs/CURRENT_PHASE.md` to show exactly what shipped and what was deferred. Final commit: results + report + phase flip together. `graphify update .`, stage graph files, emit GRAPH STATUS, and give the user the push command — do not push unasked.
