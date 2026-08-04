# RAG Ship Report

Generated: 2026-07-17

## Executive Status

RepoPilot ships the measured retrieval stack through Phase 4: widened source retrieval, BM25 hybrid retrieval, and cross-encoder reranking with MMR. Phase 5's context-compression plumbing exists but is switched off (see the post-ship note below). Phase 2 and Phase 6 have completed eval artifacts, but both miss their gates and stay deferred/disabled for runtime. Phase 7's permanent CI forcing function is now in place: PRs touching retrieval paths must include a fresh `evals/results/rag_phaseN/_after.json`.

## Phase Scorecard

| Phase | Status | Headline metric | Significance / gate note |
|---|---|---|---|
| 0 - Baseline | Landed | Baseline artifacts committed in `evals/results/rag_phase0/` | Measurement spine established. |
| 1 - Recall Lift | Landed | httpx recall@10 `0.385 -> 0.949` (+56 pp) | Landed. Verifier recheck later confirmed `verifier_quality_v1 = 1.00`. |
| 2 - Query Understanding | Deferred | multi-hop/httpx recall@10 `0.949 -> 0.817` vs Phase 1 artifact; documented raw dense comparison was `0.850 -> 0.817` | Gate missed. Runtime remains disabled by `query_understanding_enabled=False`. |
| 3 - BM25 Hybrid | Landed | fastapi rare-symbol recall@10 `0.417 -> 0.583` (+17 pp) | Landed on primary rare-symbol gate; httpx general cost documented. |
| 4 - Reranking | Landed | fastapi rare-symbol NDCG@5 `0.491 -> 0.917`; recall@10 `0.583 -> 0.917` | Landed. Also repaired httpx general recall to `0.974`. |
| 5 - Compression | **Disabled 2026-08-04** (was: landed by override) | input tokens did not reach the -40% gate; Phase 5 after records httpx `2591`, flask `3439`, fastapi `14455` tokens/question | Gate failed, was overridden, now switched off — see the Phase 5 note below. |
| 6 - Ingestion Enrichment | Deferred | recall@10 unchanged: httpx `0.974 -> 0.974`, flask `0.868 -> 0.868`, fastapi `0.833 -> 0.833`; httpx NDCG@5 regressed `0.818 -> 0.800` | Gate missed. Keep raw dense embeddings; `enriched_text` remains available for BM25/FTS experiments. |
| 7 - Ship Closeout | Landed | CI artifact gate added for retrieval-path PRs | Permanent regression guard installed. |

## Cumulative Picture

| Repo / set | Current landed recall@10 | Current landed NDCG@5 | Grounding accuracy | Latency p95 |
|---|---:|---:|---:|---:|
| httpx QA | `0.974` | `0.818` | Phase 6 measured `0.813`; Phase 5 landed `0.563` | Phase 5 landed `1381 ms`; Phase 6 deferred `3765 ms` |
| flask QA | `0.868` | `0.708` | Phase 6 measured `0.550`; Phase 5 landed `0.650` | Phase 5 landed `2441 ms`; Phase 6 deferred `4027 ms` |
| fastapi QA | `0.833` | `0.588` | Phase 6 measured `0.800`; Phase 5 landed `0.800` | Phase 5 landed `2149 ms`; Phase 6 deferred `12065 ms` |

Grounding DoD status: the final measured values do not meet the stated product bars (`httpx >= 90%`, `flask/fastapi >= 85%`). The more stable claim-level guardrail is stronger (`httpx 0.938`, `flask 0.875`, `fastapi 0.950` in Phase 6), which keeps pointing at the known all-or-nothing claim attribution weakness rather than hallucination.

Verifier DoD status: `verifier_quality_v1 = 1.00` on 30/30 after the parse fix.

Trap-question DoD status: **met as of 2026-08-04.** The committed QA datasets contain 9 `not_in_repo` trap rows: 3 httpx, 3 flask, 3 fastapi. The 9th (fastapi, "built-in database migration system") was added after this report's original run and verified to abstain individually; the last full-bench figure remains the Phase 6 run, which passed all 8 then-committed traps with `hallucination_rate = 0.0` for every repo. The 9-trap set has not yet been through a full bench.

Latency DoD status: the cumulative `1.5x` target is not met consistently. The clean Phase 5 landed run is acceptable for httpx and near-bound for flask/fastapi, but the Phase 6 run regressed latency heavily, especially fastapi (`12065 ms` p95). Phase 6 is deferred partly for this reason.

## Post-Ship Notes

These amend the report above; the phase artifacts themselves are unchanged.

**Phase 5 compression — switched off 2026-08-04.** Re-measured on fastapi (3 answerable
questions, A/B over identical retrieval): `+5.6%` input-token reduction against the `-40%`
gate, at multiple seconds per question. Two claims in the original report do not survive
re-measurement:

- The `413 Payload Too Large` fallback story did not reproduce — **zero** payload errors
  observed. Compression is not failing loudly on oversized chunks; it succeeds and barely
  helps. Only 1 of 3 questions changed at all (`5942 -> 5309` tokens); the rest returned
  identical because `compress_chunk` hands back the original whenever the model emits no
  usable keep-ranges.
- `Settings.compress_enabled` now defaults to `False` and is the single authority:
  `use_compress=True` alone no longer enables compression for any caller. The code and the
  `use_compress` kwarg are retained so the phase can be re-measured after prompt or
  chunk-splitting work.

**Latency attribution — instrumented 2026-08-04.** `QAResult.stage_timings_ms` now records
wall-clock per pipeline stage, and a latency breach names the worst stages. First
measurement on fastapi contradicts this report's diagnosis at "Latency DoD status" below:
rerank is `~2.1 s`/query (53% of wall-clock), not verifier concurrency, which measured
15.8%. That diagnosis predates `llm_verifier_max_concurrency` going `3 -> 10`. Within
rerank, reading the 50-chunk pool costs `~990 ms`/query and cross-encoder scoring
`~1265 ms`/query — the latter against a documented `~460 pairs/s` (`~110 ms`) budget, i.e.
roughly `11x` slower than assumed. A pool sweep (50/35/25/15) found pool `25` holds
recall@10 flat on httpx (`0.974`) and flask (`0.868`) while saving `~933 ms`/query; **not
yet landed.**

## Deferred Entry States

Phase 2 deferred entry state: implementation exists, eval artifacts exist, runtime default remains disabled. Latest measured artifact: `evals/results/rag_phase2/_after.json` on `multi_hop_v1` reports recall@10 `0.8167`, NDCG@5 `0.7231`, MRR `0.9000`, grounding accuracy `0.5000`, hallucination rate `0.0000`, latency p95 `2025 ms`.

Phase 6 deferred entry state: enrichment fields are implemented and the dense regression fix keeps dense embeddings on raw `content` by default. Latest measured artifact: `evals/results/rag_phase6/_after.json` reports no recall@10 lift, httpx NDCG@5 regression of `-0.018`, flask grounding regression of `-0.10`, and large latency regressions.

## Permanent Regression Gate

`.github/workflows/ci.yml` now contains `retrieval-eval-artifact-gate`. On pull requests, it diffs against the PR base SHA and fails when files under `packages/agents/src/repopilot_agents/{tools,qa,rerank}/` or `packages/ingestion/` changed without a matching `evals/results/rag_phaseN/_after.json` artifact.
