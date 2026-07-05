# Build Prompt — RAG Phase 1: Recall Lift

> Paste everything below the line into the coding agent. Spec: [`docs/rag/01_RECALL_LIFT.md`](../rag/01_RECALL_LIFT.md).

---

You are implementing **RAG Phase 1 (Recall Lift)** for RepoPilot. Read `CLAUDE.md`, `docs/CURRENT_PHASE.md`, and `docs/rag/01_RECALL_LIFT.md` first. Follow all conventions in CLAUDE.md §6 (mypy --strict, ruff, ≥80% coverage, Pydantic v2, no new deps).

## Objective

Lift **recall@10 by ≥ 5 pp over the Phase 0 baseline** on `httpx_qa_v1`, with the same lift on at least one of `flask_qa_v1`/`fastapi_qa_v1`, by widening the dense-search candidate pool from k=8 to a `recall_k` of 50 (sweep 30–80 if needed) and exposing metadata filters the schema already supports. **Zero new pip dependencies.**

## Before writing any code

1. Copy `evals/results/rag_phase0/baseline.json` → `evals/results/rag_phase1/_before.json`.
2. Confirm the three datasets exist and are untouched: `httpx_qa_v1` (16), `flask_qa_v1` (20, incl. 3 traps), `fastapi_qa_v1` (15). **Do not edit gold labels.**

## Implementation steps (in order)

1. `packages/agents/src/repopilot_agents/tools/vector_search.py`: add optional `kind`, `path_prefix`, `path_glob` params and a `recall_k` param (default 50). Keep `k=8` default for back-compat. SQL shape is in the spec §3. Re-export in `tools/__init__.py`.
2. New tests `packages/agents/tests/test_vector_search_filters.py` (~80 LOC) against stubbed Postgres. Run the fast lane — must stay green with defaults unchanged.
3. `packages/agents/src/repopilot_agents/qa/graph.py`: call `vector_search` with `recall_k=50`; the Q&A prompt slice stays `[:8]` (compression comes in Phase 5).
4. Add a latency guardrail assertion in `bench.py`: fail if `latency_p95_ms` > 1.5× baseline.
5. Run `python -m repopilot_evals.bench --phase 1 --repo <each>` then `--aggregate` → `evals/results/rag_phase1/_after.json` + `delta.json`. Run the significance runner.

Known target from Phase 0: three flask questions (`Config.from_object`, default-404 handling, cookie parsing) missed **beyond rank 150** — check whether they now land in the top pool; report either way.

## Gate (all must hold)

- recall@10 lift ≥ 0.05 on `httpx_qa_v1`, and on ≥ 1 of flask/fastapi.
- Statistically significant on ≥ 1 dataset (bootstrap CI).
- `grounding_accuracy` regression ≤ 1 pp on every dataset.
- `latency_p95_ms` ≤ 1.5× baseline.
- `evals/results/rag_phase1/{_before,_after,delta}.json` committed.

## Stop conditions → revert, don't land

- Significant on httpx but ≤ 0.02 on both other datasets (eval overfit).
- Grounding regression > 1 pp anywhere (pool noise hurting the answerer).
- Latency p95 doubles.
- Gate misses by < 5 pp: spend max 1 extra hour sweeping `recall_k` in {30, 50, 80}; still short → stop and report, don't torture the gate.

## Landing protocol

Update `docs/rag/01_RECALL_LIFT.md` honest-notes with the `recall_k` value that actually won. Flip `docs/CURRENT_PHASE.md` (1 🟢, 2 🟡) **in the same commit** as the results. Run `graphify update .`, stage `graphify-out/graph.json` + `manifest.json`, emit the GRAPH STATUS block. Do not push without being asked.
