# RAG Phase 0 — Baseline & Measurement

> **How to run this:** [`00_EXECUTION_RUNBOOK.md`](00_EXECUTION_RUNBOOK.md) is the step-by-step.

> Without this phase, every later phase ships on vibes.

## 1. Goal

Establish a **fixed, committed, reproducible** measurement of the current retrieval pipeline on a labeled eval set, plus the runners + significance-test scaffolding that every later phase will use.

Single number that defines done: **a `baseline.json` file is committed under `evals/results/rag_phase0/` covering all 8 metrics in the plan, on at least 2 repos (httpx + flask).**

## 2. Why now

The product-build Phases 0–5 deliberately deferred the "real-LLM gate" — every previous phase doc carries an "awaits paid Groq" or "awaits labeled dataset" caveat. Without paying that debt now, every retrieval upgrade we make is unfalsifiable. We cannot say "BM25 lifted recall by 6 points" because we never knew what recall was.

This phase prerequisite-checks:

- A **provisioned Groq key with paid-tier quota** for the labeled-eval runs (or an explicit decision to use Cerebras / Ollama-only with the documented quality tradeoff).
- A **provisioned LangSmith key** so the runs are inspectable after the fact.
- **A human** to spend 3–5 hours labeling the new datasets.

If any of those three are missing, Phase 0 stalls. There is no way around it.

## 3. What changes in the code

| Path | Type | LOC est. | Purpose |
|---|---|---|---|
| `packages/evals/src/repopilot_evals/runners/retrieval.py` | new | ~120 | `recall_at_k`, `ndcg_at_k`, `mrr` over a JSONL dataset |
| `packages/evals/src/repopilot_evals/runners/grounding.py` | edit | ~+40 | Add hallucination-rate + verifier-accuracy paths reusing existing scaffolding |
| `packages/evals/src/repopilot_evals/runners/significance.py` | new | ~80 | Bootstrap CI + paired t-test on metric arrays; the Definition-of-Done check |
| `packages/evals/src/repopilot_evals/runners/latency.py` | new | ~60 | p50/p95 timings around `answer_question`; emits histogram |
| `packages/evals/src/repopilot_evals/bench.py` | new | ~100 | Top-level `python -m repopilot_evals.bench --phase 0` runner; writes results to `evals/results/rag_phase0/baseline.json` |
| `evals/results/rag_phase0/baseline.json` | new artifact | — | The committed baseline — every later phase compares against this |
| `evals/results/rag_phase0/baseline.csv` | new artifact | — | Same data flat, for human review |
| `evals/datasets/flask_qa_v1.jsonl` | new (labeled) | 20 rows | Cross-repo recall + grounding bench |
| `evals/datasets/fastapi_qa_v1.jsonl` | new (labeled) | 15 rows | Cross-repo recall + grounding bench |

No production code changes in this phase. **The pipeline is not touched** — we are measuring what we have.

## 4. What changes in the eval

**New datasets** (Phase 0 owns labeling):

- `flask_qa_v1.jsonl`: 20 rows. Schema matches the existing `httpx_qa_v1.jsonl`. Mix: 12 single-hop + 5 multi-hop + 3 not-in-repo.
- `fastapi_qa_v1.jsonl`: 15 rows. Same schema. Mix: 9 single-hop + 4 multi-hop + 2 not-in-repo.

**Labeling protocol** (locks quality so later phases can trust the gate):

1. Each question must be answerable from the repo (or explicitly not, for the hallucination tests).
2. `expected_refs` are the **minimal** set of chunks the answer truly depends on — not "everything that mentions the topic."
3. `expected_answer_keywords` are 2–4 tokens that any correct answer must contain. Symbol names count; commentary does not.
4. Every row is **double-checked** by re-reading the cited file in GitHub at the indexed SHA.

**New runners:**

- `retrieval.py` — pure-retrieval metrics. Runs against the current `vector_search` and reports recall/NDCG/MRR by computing the chunk overlap between the top-k hits and `expected_refs`.
- `grounding.py` — extended to also emit `verifier_accuracy` (using `verifier_quality_v1`) and `hallucination_rate` (using the 3 not-in-repo rows per dataset).
- `significance.py` — given two `*_metrics.json` files, returns whether the delta is statistically significant. Used by every later phase's gate.
- `latency.py` — wraps `answer_question` with `time.perf_counter()`; emits the p50/p95 over N runs per question.

**The new top-level runner:**

```bash
python -m repopilot_evals.bench --phase 0 --repo httpx
# writes evals/results/rag_phase0/httpx_baseline.json
python -m repopilot_evals.bench --phase 0 --repo flask
# writes evals/results/rag_phase0/flask_baseline.json
python -m repopilot_evals.bench --phase 0 --aggregate
# writes evals/results/rag_phase0/baseline.json (the index)
```

## 5. Gate

The phase ships when **all of the following hold**:

- [ ] `evals/datasets/flask_qa_v1.jsonl` has exactly 20 labeled rows, double-checked.
- [ ] `evals/datasets/fastapi_qa_v1.jsonl` has exactly 15 labeled rows, double-checked.
- [ ] `python -m repopilot_evals.bench --phase 0 --repo httpx` runs to completion without quota exhaustion. Outputs:
  - `recall@5`, `recall@10`, `recall@20`
  - `ndcg@5`, `ndcg@10`
  - `mrr`
  - `grounding_accuracy`
  - `hallucination_rate`
  - `verifier_accuracy`
  - `latency_p50_ms`, `latency_p95_ms`
- [ ] Same command on `flask` and `fastapi` repos completes.
- [ ] `evals/results/rag_phase0/baseline.json` is committed (the source of truth all later phases compare against).
- [ ] The baseline `verifier_accuracy` is **≥ 88%**. If it isn't, every later "grounding accuracy" number is meaningless — we'd be measuring two error rates at once. In that case Phase 0 includes a verifier-prompt tightening pass until `verifier_accuracy ≥ 88%` is hit.
- [ ] `significance.py` is exercised by a self-test: running it on `baseline.json` vs. `baseline.json` reports `not significant` (sanity check).

## 6. Stop conditions

Phase 0 is **abandoned** and the plan does not advance if any of:

- Labeling cannot reach quality on at least one repo. (If `flask_qa_v1` ships with fuzzy `expected_refs`, every Phase 1+ recall number is a lie.)
- The baseline `grounding_accuracy` is **above 90% already**. In that case the product's truth claim is already met and the whole RAG plan needs re-justification — the bottleneck is elsewhere.
- Latency p95 is **already > 30 s**. Then Phase 0 forks to add a latency-optimization sub-phase before any of Phases 1–6 can land, because they all add latency.

Phase 0 is **complete** when `baseline.json` is committed and `CURRENT_PHASE.md` is flipped to Phase 1.

---

## Honest notes for future-me

- **The 20 + 15 row datasets are small.** They are diagnostic, not statistically dispositive. The bootstrap CI in `significance.py` will frequently say `inconclusive` for small lifts — that's the right answer.
- **The baseline number will be embarrassing.** Phase 2 of the product build never measured it; what we find may be well below the "≥ 90% grounding" gate that doc claimed. That's the point of measuring.
- **Do not skip the verifier-accuracy step.** This is `docs/06` S5 in the original plan, never landed. If the verifier itself is wrong 15% of the time, "grounding accuracy" is two error rates multiplied, and no later phase can untangle them.

---

## Open questions to resolve before starting

- **Paid-Groq quota or Ollama-only baseline?** Ollama-only doubles latency but stays free. Recommendation: paid Groq for the baseline (so later phases can A/B against the *real* production model), Ollama for development.
- **Who labels?** If the user labels: 3–5 hrs of focused work. If Claude proposes + user reviews: ~1.5 hrs of user time (with the bias caveat from the earlier eval-labeling discussion).
- **Significance test threshold.** Default proposal: `alpha = 0.05`, paired bootstrap, n_resamples = 10_000. Tunable in Phase 0 config.
