# RAG Phase 5 — Context Compression

## 1. Goal

Reduce **input tokens reaching the answerer model by ≥ 40%** at **equal or better grounding accuracy**.

Mechanism: after Phase 4 produces the top-N reranked chunks, ask the cheap 8B model *"which lines of this chunk are relevant to: \<question\>?"* and keep only those lines. The kept lines preserve `file_path` + line spans so verifier refs still work.

## 2. Why now

After Phases 1–4 the top-N pool is high-quality but **fat**. A typical class chunk is 40–80 lines of which 3–8 are load-bearing for the question. Sending the whole chunk:

- Burns Groq quota faster.
- Increases per-claim verifier cost (each claim's chunks are bigger).
- Slows latency p95 (longer prompts ↔ slower decode).
- Plausibly **hurts** answer quality — the answerer has more irrelevant context to filter through.

Compression is the polish step: same chunks, smaller prompt, same answer or better.

Phase 4 prerequisite-checks:

- Reranker yields a stable top-N pool (the input to compression).
- `evals/results/rag_phase4/_after.json` committed.
- `grounding_accuracy` measured under real LLM on at least `httpx_qa_v1`.

## 3. What changes in the code

| Path | Type | LOC est. | Purpose |
|---|---|---|---|
| `packages/agents/src/repopilot_agents/qa/compress.py` | new | ~120 | `compress_chunks(question, chunks)` — 8B LLM call per chunk |
| `packages/agents/src/repopilot_agents/qa/prompts.py` | edit | ~+40 | `COMPRESS_SYSTEM` prompt + 2 few-shot examples |
| `packages/agents/src/repopilot_agents/qa/graph.py` | edit | ~+15 | Insert compression between rerank and answer-generation |
| `packages/agents/src/repopilot_agents/types.py` | edit | ~+15 | `ChunkContent` gains optional `kept_line_spans: list[tuple[int, int]]` |
| `packages/agents/src/repopilot_agents/verifier/grounding.py` | edit | ~+10 | When verifying, expand `kept_line_spans` back to the full chunk before grounding check — verifier must see the full source, not the compressed view |
| `packages/agents/tests/test_compress.py` | new | ~80 | LLM-stubbed tests for line-span extraction |
| `packages/agents/tests/test_compress_integration.py` | new | ~60 | Verifier accuracy unchanged when refs come from compressed chunks |
| `evals/results/rag_phase5/` | new artifact dir | — | `_before`/`_after`/`delta` |

**Zero new pip deps.** Reuses `ModelId.CODE_HEALTH` (8B Groq).

### The compression prompt shape

```
SYSTEM:
You see one Python chunk and a user question. Return ONLY the line numbers
needed to answer the question (as JSON: {"keep": [[start, end], ...]}).
If unsure, keep the line. If totally irrelevant, return {"keep": []}.
You are NOT generating an answer — only selecting line ranges.

USER:
QUESTION: {question}

CHUNK ({file_path}:{start_line}-{end_line}):
{numbered_content}
```

Each chunk gets ~50–200 input tokens, output ~10–30. Cost is low.

### Critical safety rule

**Verifier checks against full chunks, not compressed views.** Otherwise a compressed view could selectively drop the contradicting line and "ground" a wrong claim. Implementation:

- `ChunkContent` carries both `content` (full) and optional `kept_line_spans` (the view).
- Answer prompt is built from the compressed view.
- Verifier reads `content` (full) via `read_chunks` as before. The `kept_line_spans` are surfaced to the verifier as an annotation ("the answerer was shown these lines"), but the verifier validates against the whole chunk.

This means **compression can never make a wrong answer pass verification** — only the answerer's view shrinks. That preserves the principle 1 (truthful over fluent) guarantee.

### Skip conditions

Don't compress when:

- Chunk is < 15 lines (overhead > savings).
- Chunk kind is `module` (it's already just imports + top-level — compression hurts).
- The compressor LLM call fails or returns empty `keep` (skip, send the full chunk; never silent-drop).

## 4. What changes in the eval

- **New metric**: `input_tokens_per_question` (sum of answerer-side prompt tokens; emit from `bench.py`).
- **Reused**: all Phase 0–4 datasets.
- **Compression-specific check**: run `verifier_quality_v1` *with* compression active. Verifier accuracy must not regress. If it does, the verifier is accidentally seeing the compressed view somewhere — bug.

## 5. Gate

The phase ships when all hold:

- [ ] `input_tokens_per_question after ≤ 0.6 × input_tokens_per_question before` on `httpx_qa_v1`. (40% reduction = ≤ 0.6× the previous count.)
- [ ] `grounding_accuracy after ≥ grounding_accuracy before − 1 pp` on every dataset. (Equality is the target; the 1 pp cushion is the noise floor.)
- [ ] `verifier_accuracy after = verifier_accuracy before ± 0.5 pp` on `verifier_quality_v1`. Verifier sees full chunks; this number must be invariant.
- [ ] `hallucination_rate` does not regress — compressed views must not cause the answerer to forget the "couldn't find that" sentinel.
- [ ] `latency_p50_ms` does NOT regress despite the extra LLM calls (parallel compression across chunks + smaller answerer prompt should net out). `latency_p95_ms` may increase ≤ 1.2× Phase 4.
- [ ] `evals/results/rag_phase5/{_before,_after,delta}.json` committed.

## 6. Stop conditions

Phase 5 is rolled back if:

- `grounding_accuracy` regresses by > 1 pp — the compressor is dropping load-bearing lines and the answerer is hallucinating to fill the gap.
- `verifier_accuracy` regresses at all — there's a bug routing the compressed view to the verifier (the principle 1 guarantee is broken).
- Token savings come in at < 30% — compression overhead (an LLM call per chunk) isn't justified by the saving. Cut the phase; revisit with a smaller / faster compressor (e.g. distilled scoring model).

## 7. Implementation order

1. Add `kept_line_spans` to `ChunkContent`; default `None`. Confirm no fast-lane regression.
2. Build `compress.py` against a stub; unit-test prompt construction + JSON parse.
3. Wire into the Q&A graph behind a `compress_enabled` setting flag.
4. Run `bench --phase 5` twice: once with compress disabled (must match Phase 4 numbers exactly), once enabled.
5. Tune `min_chunk_lines_to_compress` (default 15) — too low and we waste compressor calls, too high and we miss the savings.
6. Verify with `verifier_quality_v1` that verifier accuracy is unchanged.
7. Flip default to enabled; commit results.

---

## Honest notes

- **The 40% reduction target is conservative.** Anthropic's published RAG benchmarks suggest 60–70% is achievable on code chunks where most lines are imports/boilerplate around a tight load-bearing block. 40% is set so we ship even with conservative line-keeping.
- **Compression LLM cost vs. savings tradeoff:** each compressor call is small (~200 input + ~20 output tokens on 8B). For a 50-chunk pool that's ~10 K extra input tokens to save ~40 K on the answerer (70B). Net savings, but the 8B and 70B quotas are separate, so this is also load-balancing across the Groq tiers.
- **The most subtle bug** in this phase is the verifier-sees-full-chunks invariant. The test `test_compress_integration.py` is critical: it must specifically assert that the verifier got the *full* `content`, not the compressed view.
- **MMR (Phase 4) and compression (Phase 5) interact**: MMR keeps diverse chunks; compression keeps relevant lines within them. If they fight (MMR picks 3 diverse chunks of which compression keeps only 1 line each), the answerer ends up with very thin context. Worth watching during the bench.
