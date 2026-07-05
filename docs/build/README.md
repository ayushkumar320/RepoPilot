# Build Prompts — RAG Phase Ladder

This directory holds **copy-pasteable build prompts**, one per RAG phase. Each file is a self-contained prompt you hand to a coding agent (Codex, Claude Code, etc.) to execute that phase end-to-end: implement → measure → gate → land or revert.

The prompts are **derived from** the phase specs in [`docs/rag/`](../rag/) and the plan in [`docs/RAG_PLAN.md`](../RAG_PLAN.md). The spec is authoritative; the prompt is the executable form. If they ever disagree, fix the prompt.

## Order of execution

| Prompt | Phase | Priority | Timebox |
|---|---|---|---|
| [`P1_recall_lift.md`](P1_recall_lift.md) | 1 — Recall Lift | **must-ship** | ~3 h |
| [`P2_query_understanding.md`](P2_query_understanding.md) | 2 — Query Understanding | polish (may defer) | 2 h hard |
| [`P3_bm25_hybrid.md`](P3_bm25_hybrid.md) | 3 — BM25 Hybrid | **must-ship** | ~3 h + re-index |
| [`P4_reranking.md`](P4_reranking.md) | 4 — Reranking | **must-ship** | ~3 h |
| [`P5_context_compression.md`](P5_context_compression.md) | 5 — Context Compression | polish (may defer) | 90 min hard |
| [`P6_ingestion_enrichment.md`](P6_ingestion_enrichment.md) | 6 — Ingestion Enrichment | polish (may defer) | 90 min hard incl. re-index |
| [`P7_ship_closeout.md`](P7_ship_closeout.md) | Ship / Definition of Done | **must-ship** | ~1 h |

**One phase in flight at a time.** Never start N+1 while N is unlanded. If Phase 2 is deferred, run Phase 3 against Phase 1's `_after.json` — the prompts spell this out.

## The iron rules (baked into every prompt)

1. **Before/after or it didn't happen.** Copy the previous landed phase's `_after.json` to `evals/results/rag_phaseN/_before.json` before touching code. Rerun the bench after. If `_after ≤ _before`, **revert the phase**.
2. **Datasets are frozen.** Never edit a gold label mid-phase; note it and version `_v2` after the phase.
3. **Significance required.** Use the bootstrap CI runner (`repopilot_evals.runners.significance`); a lift inside the noise floor doesn't ship.
4. **Guardrail metrics never regress silently:** `grounding_accuracy` (≤ 1 pp), `hallucination_rate` (0 regressions on the 9 not-in-repo traps), `latency_p95_ms` (per-phase budget in each prompt).
5. **Phase advance = same-commit `docs/CURRENT_PHASE.md` flip** + `graphify update .` + staged graph files.
6. **Project conventions apply** (CLAUDE.md §6): `mypy --strict`, `ruff` + `ruff format`, pytest ≥ 80% coverage, prompt budget ≤ 2000 input tokens per node, no new tools without justification.

## Bench commands (referee, unchanged since Phase 0)

```bash
python -m repopilot_evals.bench --phase N --repo httpx    # per repo
python -m repopilot_evals.bench --phase N --aggregate     # writes _after.json
```

The LLM cache makes reruns after 429s cheap. Known landmines: Neon drops idle SSL connections (pool_pre_ping is set; if SSL errors return, restart api+worker); HF router is out of credits (verifier chain must succeed on Groq/Cerebras); Groq 429s → wait 60 s and rerun, the cache resumes.
