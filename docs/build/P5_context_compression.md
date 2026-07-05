# Build Prompt — RAG Phase 5: Context Compression

> **Timebox: 90 minutes hard.** Polish phase — if grounding drops even 1 pp inside the box, cut it and defer. Spec: [`docs/rag/05_CONTEXT_COMPRESSION.md`](../rag/05_CONTEXT_COMPRESSION.md).

---

You are implementing **RAG Phase 5 (Context Compression)** for RepoPilot. Read `CLAUDE.md`, `docs/CURRENT_PHASE.md`, and `docs/rag/05_CONTEXT_COMPRESSION.md` first. Prerequisite: `evals/results/rag_phase4/_after.json` committed; grounding measured under real LLM on `httpx_qa_v1`.

## Objective

Cut **input tokens to the answerer by ≥ 40% at equal grounding accuracy**: after reranking, ask the 8B model which line spans of each chunk are relevant, and build the answer prompt from only those lines. **Zero new deps.**

## The invariant that must never break

**The verifier always validates against full `chunks.content`, never the compressed view.** The compressed view only shrinks what the *answerer* sees. `kept_line_spans` may be surfaced to the verifier as an annotation, but grounding checks run on the whole chunk. This is the "truthful over fluent" guarantee — a compressed view must never be able to hide the line that contradicts a claim. `test_compress_integration.py` must assert this explicitly.

## Before writing any code

Copy `evals/results/rag_phase4/_after.json` → `evals/results/rag_phase5/_before.json`.

## Implementation steps (in order)

1. `types.py`: `ChunkContent` gains optional `kept_line_spans: list[tuple[int, int]]` (default `None`). Confirm fast lane green.
2. New `qa/compress.py`: `compress_chunks(question, chunks)` — one parallel 8B call per chunk, JSON `{"keep": [[start,end],...]}`; prompt shape in spec §3 (stay under the 2000-token budget). **Skip conditions:** chunk < 15 lines, `kind == "module"`, or LLM failure/empty keep → send the full chunk, never silent-drop.
3. `verifier/grounding.py`: expand spans back to the full chunk before grounding (the invariant above).
4. Wire into `qa/graph.py` between rerank and answer generation, **behind `compress_enabled`**.
5. Add `input_tokens_per_question` metric to `bench.py`.
6. Tests: `test_compress.py` (stubbed span extraction), `test_compress_integration.py` (verifier sees full content).
7. Bench twice: disabled (must match Phase 4 exactly) and enabled. Tune `min_chunk_lines_to_compress` (default 15). Run `verifier_quality_v1` with compression on.

## Gate (all must hold)

- `input_tokens_per_question` ≤ 0.6× before on `httpx_qa_v1`.
- Grounding regression ≤ 1 pp on every dataset.
- `verifier_accuracy` within ± 0.5 pp on `verifier_quality_v1` (must be invariant — a change means the verifier saw the compressed view: bug).
- `hallucination_rate` unchanged (all traps still return the not-found sentinel).
- `latency_p50_ms` does not regress; `latency_p95_ms` ≤ 1.2× Phase 4.
- `evals/results/rag_phase5/{_before,_after,delta}.json` committed.

## Stop conditions → revert

- Grounding drops > 1 pp (compressor dropping load-bearing lines).
- Verifier accuracy moves at all (invariant broken).
- Token savings < 30% (overhead not justified).
- Timebox blown → defer cleanly in `CURRENT_PHASE.md`.

Watch the MMR interaction: if diverse chunks compress to one line each, the answerer's context gets too thin — report it if the bench shows it.

## Landing protocol

Flip `docs/CURRENT_PHASE.md` (5 🟢 or ⚪ deferred) in the same commit. `graphify update .`, stage graph files, emit GRAPH STATUS. Don't push unasked.
