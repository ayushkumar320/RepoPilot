# Build Prompt — RAG Phase 2: Query Understanding

> **Timebox: 2 hours hard.** Polish phase — if the box blows (dataset labeling drags or the 8B rewriter is flaky), defer: mark ⚪ deferred in `docs/CURRENT_PHASE.md` with entry state noted, and move to Phase 3 (which then measures against Phase 1's `_after.json`). Spec: [`docs/rag/02_QUERY_UNDERSTANDING.md`](../rag/02_QUERY_UNDERSTANDING.md).

---

You are implementing **RAG Phase 2 (Query Understanding)** for RepoPilot. Read `CLAUDE.md`, `docs/CURRENT_PHASE.md`, and `docs/rag/02_QUERY_UNDERSTANDING.md` first. Prerequisite: `evals/results/rag_phase1/_after.json` committed and `recall_k` wired on `vector_search`.

## Objective

Lift **recall@10 on multi-hop questions by ≥ 5 pp over Phase 1** by building a `QuerySpec` (2–3 rewrites, extracted symbols/paths, intent class) before retrieval and unioning parallel dense searches with RRF. Uses the existing cheap 8B slot (`ModelId.CODE_HEALTH`); **zero new deps**.

## Before writing any code

1. Copy `evals/results/rag_phase1/_after.json` → `evals/results/rag_phase2/_before.json`.
2. **Create the dataset first** (this is the schedule risk): `evals/datasets/multi_hop_v1.jsonl`, 10 rows, each needing ≥ 2 graph hops or ≥ 2 distinct file regions, `expected_refs` spanning multiple files. Use the existing propose→review flow (`evals/tools/propose_labels.py` + `review_tui.py`) — it already over-fetches top-150 and filters tests/docs/examples. **Deliberately include lexical mismatches** (question wording ≠ symbol names), otherwise multi-query can't show its lift. Also hand-label a small extraction subset (symbols/paths per question) for the `query_spec_extraction_accuracy` metric.

## Implementation steps (in order — step 1 is the "do nothing" check)

1. New `qa/query_spec.py`: `QuerySpec` Pydantic model (see spec §3) + `build_query_spec` **stub** returning `rewrites=[raw_text]`. Wire through `qa/graph.py`. Bench must match Phase 1 exactly — confirm no regression before adding behavior.
2. Real rewrites: `QUERY_SPEC_SYSTEM` prompt + few-shot in `qa/prompts.py` (respect the ≤ 2000-token prompt budget); one 8B call, JSON output, **parse-fail falls back to raw question** — the pipeline must never break on a bad LLM response.
3. New `qa/union.py`: Reciprocal Rank Fusion helper (`k_constant=60`), reused by Phase 3. Fan out `vector_search` over `[raw, *rewrites]` with `asyncio.gather`, union with RRF, trim to 50.
4. Metadata extraction → Phase 1's `path_prefix`/`kind` filters, **behind a feature flag** for A/B in bench.
5. Intent-class routing: only affects sufficiency judge `max_hops` (multi-hop → 3, else 1).
6. Tests: `test_query_spec.py` (LLM-stubbed), `test_qa_multi_query.py` (union correctness).
7. `bench --phase 2` → `_after.json` + `delta.json` + significance.

## Gate (all must hold)

- recall@10 lift ≥ 0.05 on `multi_hop_v1`.
- No recall@10 regression on httpx/flask/fastapi QA sets.
- `query_spec_extraction_accuracy` ≥ 0.85 on the labeled subset.
- Grounding regression ≤ 1 pp anywhere; `latency_p95_ms` ≤ 1.3× Phase 1.
- `evals/results/rag_phase2/{_before,_after,delta}.json` committed.

## Stop conditions → revert (or trim scope)

- Rewrites cause > 1 pp grounding regression on `httpx_qa_v1` (rewrite noise).
- Extraction call > 500 ms p50 on the 8B model.
- Intent classifier wrong > 30% on spot-check → **drop intent routing, keep multi-query** (partial land is allowed here).
- Timebox blown → defer cleanly (see header).

## Landing protocol

Flip `docs/CURRENT_PHASE.md` in the same commit (2 🟢 or ⚪ deferred with entry state). `graphify update .`, stage graph files, emit GRAPH STATUS. Don't push unasked.
