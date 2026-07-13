# RAG Phase Ladder — README

One file per RAG phase. Each is the **spec + executable prompt** in one; hand it to a coding agent to run that phase end-to-end (implement → measure → gate → land or revert).

The plan they collectively implement is [`../RAG_PLAN.md`](../RAG_PLAN.md). The always-correct pointer at the active phase is [`../CURRENT_PHASE.md`](../CURRENT_PHASE.md).

## Order of execution

| Spec | Phase | Priority | Timebox |
|---|---|---|---|
| [`00_BASELINE_AND_MEASUREMENT.md`](00_BASELINE_AND_MEASUREMENT.md) | 0 — Baseline & Measurement | **shipped** | — |
| [`00_TODAY_PLAN.md`](00_TODAY_PLAN.md) | Cross-phase 2-day ship plan | reference | — |
| [`01_RECALL_LIFT.md`](01_RECALL_LIFT.md) | 1 — Recall Lift | **must-ship** | ~3 h |
| [`02_QUERY_UNDERSTANDING.md`](02_QUERY_UNDERSTANDING.md) | 2 — Query Understanding | polish (may defer) | 2 h hard |
| [`03_HYBRID_RETRIEVAL_BM25.md`](03_HYBRID_RETRIEVAL_BM25.md) | 3 — BM25 Hybrid | **must-ship** | ~3 h + re-index |
| [`04_RERANKING.md`](04_RERANKING.md) | 4 — Reranking | **must-ship** | ~3 h |
| [`05_CONTEXT_COMPRESSION.md`](05_CONTEXT_COMPRESSION.md) | 5 — Context Compression | polish (may defer) | 90 min hard |
| [`06_INGESTION_ENRICHMENT.md`](06_INGESTION_ENRICHMENT.md) | 6 — Ingestion Enrichment | **active polish** | 90 min hard incl. re-index |
| [`07_SHIP_CLOSEOUT.md`](07_SHIP_CLOSEOUT.md) | Ship / Definition of Done | **must-ship** | ~1 h |
| [`RISKS.md`](RISKS.md) | Cross-phase risk register | reference | — |

**One phase in flight at a time.** Never start N+1 while N is unlanded. If Phase 2 is deferred, run Phase 3 against Phase 1's `_after.json` — the specs spell this out.

## Iron rules (baked into every spec)

1. **Before/after or it didn't happen.** Copy the previous landed phase's `_after.json` to `evals/results/rag_phaseN/_before.json` before touching code. Rerun the bench after. If `_after ≤ _before`, **revert the phase**.
2. **Datasets are frozen.** Never edit a gold label mid-phase; note it and version `_v2` after the phase.
3. **Significance required.** Use the bootstrap CI runner (`repopilot_evals.runners.significance`); a lift inside the noise floor doesn't ship.
4. **Guardrail metrics never regress silently:** `grounding_accuracy` (≤ 1 pp), `hallucination_rate` (0 regressions on the 9 not-in-repo traps), `latency_p95_ms` (per-phase budget in each spec).
5. **Phase advance = same-commit `docs/CURRENT_PHASE.md` flip** + `graphify update .` + staged graph files.
6. **Project conventions apply** (CLAUDE.md §6): `mypy --strict`, `ruff` + `ruff format`, pytest ≥ 80% coverage, prompt budget ≤ 2000 input tokens per node, no new tools without justification.

## Bench commands (referee, unchanged since Phase 0)

```bash
python -m repopilot_evals.bench --phase N --repo httpx    # per repo
python -m repopilot_evals.bench --phase N --aggregate     # writes _after.json
```

The LLM cache makes reruns after 429s cheap. Known landmines: Neon drops idle SSL connections (`pool_pre_ping` is set; if SSL errors return, restart api+worker); HF router may return 402 (out of credits) — the verifier chain must succeed on Groq/Cerebras; Groq 429s → wait 60 s and rerun, the cache resumes.
