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
recall@10 flat on httpx (`0.974`) and flask (`0.868`) while saving `~933 ms`/query.
**Landed 2026-08-04**: `Settings.rerank_max_pool` now defaults to `25` and — for the first
time — is actually read by the QA path, which previously used
`rerank.pipeline.DEFAULT_MAX_POOL` and ignored the setting entirely. No end-to-end p95
re-bench has been run against the new default yet.

## Deferred Entry States

Phase 2 deferred entry state: implementation exists, eval artifacts exist, runtime default remains disabled. Latest measured artifact: `evals/results/rag_phase2/_after.json` on `multi_hop_v1` reports recall@10 `0.8167`, NDCG@5 `0.7231`, MRR `0.9000`, grounding accuracy `0.5000`, hallucination rate `0.0000`, latency p95 `2025 ms`.

Phase 6 deferred entry state: enrichment fields are implemented and the dense regression fix keeps dense embeddings on raw `content` by default. Latest measured artifact: `evals/results/rag_phase6/_after.json` reports no recall@10 lift, httpx NDCG@5 regression of `-0.018`, flask grounding regression of `-0.10`, and large latency regressions.

## Phase 8 — accuracy pass (landed in code, **NOT MEASURED**)

Committed 2026-08-06. Every item below is a code change with unit tests and no
eval artifact: Docker was unavailable in the session that wrote them, so no
Postgres, no re-index, and no A/B. **Treat the numbers in this report as the
last measured state until `_after.json` exists for these.** Ordered by expected
effect on the numbers.

| # | Change | Where | Needs |
|---|---|---|---|
| 1 | nomic `search_document:`/`search_query:` prefixes. The model is asymmetric and was being run bare on both sides. | `llm/provider.py`, `ingestion/embed.py`, `tools/vector_search.py` | **Full re-index** |
| 2 | A claim rejected against its own `[N]` is rechecked once against the rest of the answer's chunks. Targets the documented all-or-nothing attribution weakness (`claim_grounding_rate` 0.94/0.88/0.95 vs `grounding_accuracy` 0.81/0.55/0.80). | `verifier/grounding.py`, `qa/graph.py` | — |
| 3 | Datasets still 16/20/6 rows. **Not done — see below.** | — | — |
| 4 | `content_tsv` gains a band-B split form of the symbol, so prose reaches `HTTPTransport.handle_request`. | migration `0009` | `alembic upgrade` (table rewrite, no re-embed) |
| 5 | Query-adaptive lane weights: identifier-shaped query routes to the sparse lane, prose keeps dense at 3:1. | `tools/hybrid_search.py` | — |
| 6 | Query understanding no longer fans dense retrieval over paraphrases (the Phase 2 recall regression); its identifiers feed the BM25 query and the path filter instead. Applies with the flag off too, via the regex fallback spec. | `qa/graph.py`, `qa/query_spec.py`, eval runner | — |
| 7 | Embedding input carries a two-line `# file:`/`# symbol:` locator; functions over `MAX_CHUNK_LINES = 150` split into contiguous parts under one symbol. | `ingestion/embed.py`, `ingestion/chunk.py`, `tools/graph_traverse.py` | **Full re-index** |
| 8 | Embedding failure no longer stores a hash-derived vector; the chunk is skipped and the gap is logged. `repos.index_version` (migration `0008`) invalidates snapshots built by an older recipe. | `ingestion/embed.py`, `ingestion/persist.py`, migration `0008` | `alembic upgrade` |

Not done: **item 3, the datasets.** fastapi carries 3 answerable questions, so
every fastapi figure in this report is 2.5 questions and cannot support a
decision. Gold labels have to be authored against an indexed corpus — inventing
them would corrupt the one instrument that says whether any of the above
worked. Do this first; the rest is unmeasurable until it lands.

Also unchanged by design: `vector_search` still wraps its scan in `MATERIALIZED`
and gets exact kNN, leaving the `ivfflat` index unused. Correct for accuracy,
won't scale. Dropping the materialization is a recall regression by
construction — measure it, and set `ivfflat.probes` if you do.

Validation order once Postgres is up:

```bash
docker compose up -d db && make db-migrate && make test-eval-sampled
```

Expect item 1 and item 7 to move every number: both change what is embedded, so
the corpus must be rebuilt before the comparison means anything.

## Permanent Regression Gate

`.github/workflows/ci.yml` now contains `retrieval-eval-artifact-gate`. On pull requests, it diffs against the PR base SHA and fails when files under `packages/agents/src/repopilot_agents/{tools,qa,rerank}/` or `packages/ingestion/` changed without a matching `evals/results/rag_phaseN/_after.json` artifact.
