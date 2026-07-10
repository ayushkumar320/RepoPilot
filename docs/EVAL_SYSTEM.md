# The RepoPilot Eval System — Why It Exists and What It Buys Us

> **TL;DR** — RepoPilot answers questions about unfamiliar Python codebases using a multi-hop RAG pipeline (retrieve → rerank → compress → answer → verify). "Better" is not a vibe here: every phase change ships with a **frozen dataset, a fixed verifier, and a numeric gate** that says whether the change was actually an improvement, a regression, or noise. Without the eval system we would be shipping guesses; with it, every commit in `evals/results/rag_phase*/` is a durable, reproducible receipt of "this is real."

---

## 1. Why RAG projects *specifically* need an eval system

A conventional web app can be verified with unit tests: given input `X`, assert output `Y`. Retrieval + LLM systems can't be pinned that tightly — the same question can yield three phrasings of a correct answer, or one confidently wrong one. So the failure modes are qualitatively different:

| Failure mode | What it looks like | Why unit tests can't catch it |
|---|---|---|
| **Silent recall miss** | The right code chunk was never fetched; the answerer confabulates instead. | The pipeline "worked" — no error, no crash, just wrong. |
| **Confident hallucination** | LLM invents a function name that sounds right. | Assertion frameworks don't know what "right" means for prose. |
| **Regression under a "polish" PR** | New reranker adds +5 pp recall on one repo but drops −8 pp on another. | A single-repo test misses the cross-repo tradeoff. |
| **Metric artifact** | `grounding_accuracy` drops because answers got richer, not wronger. | Point-in-time thresholds are confounded by output shape. |
| **Prompt-injection compliance** | A docstring says "ignore instructions"; the answerer might obey. | You need adversarial datasets, not asserts. |
| **Latency creep** | Every phase adds 200 ms; four phases in, p95 is 2.7× baseline. | Unit tests don't measure the shipping bar. |

Every one of those has bitten this repo (see [`docs/CURRENT_PHASE.md`](CURRENT_PHASE.md) — the "Phase 1 grounding drop was a metric artifact" note is the concrete example). The eval system is how we notice them **before** the user does.

---

## 2. The design principle: *one number gates each step*

RepoPilot's improvement plan ([`docs/RAG_PLAN.md`](RAG_PLAN.md)) is seven phases. Each phase has:

1. **One primary gate metric** (e.g. Phase 1 → `recall@10 ≥ +5 pp`; Phase 5 → `input_tokens_per_question ≤ 0.6×`).
2. **A frozen dataset** the metric is computed on (e.g. `httpx_qa_v1`, `fastapi_rare_symbol_v1`).
3. **A fixed verifier** so both `_before` and `_after` arms are judged by the same rubric.
4. **Stop conditions** — the explicit list of guardrails that must not regress (grounding, hallucination, latency).

That structure buys the two properties that matter most:

- **Comparability across time.** The Phase 4 `_after.json` becomes the Phase 5 `_before.json` — you can trace a metric across the whole build history without re-running old code.
- **Comparability across repos.** The same run on `httpx`, `flask`, and `fastapi` exposes tradeoffs one repo alone would hide. (Phase 3's landing note: "BM25 helps fastapi +17 pp, costs httpx −5 pp on general Q&A" — impossible to see without a multi-repo bench.)

Without gates, "did the change help?" collapses into "does it feel snappier?" — the exact failure mode this system is engineered against.

---

## 3. Anatomy — what's actually in `packages/evals/`

```
packages/evals/src/repopilot_evals/
├── __main__.py           # CLI: `uv run python -m repopilot_evals ...`
├── bench.py              # The retrieval-phase harness (--phase N --repo X)
├── datasets.py           # Row schemas + JSONL loaders
├── registry.py           # EvalSpec — which datasets belong to which phase
├── reports.py            # Markdown / JSON write-out
└── runners/
    ├── retrieval.py      # recall@k, NDCG@k, MRR, diversity — no LLM cost
    ├── grounding.py      # answer + verifier full path — the real quality signal
    ├── verifier.py       # verifier_quality_v1 accuracy (is the referee itself calibrated?)
    └── latency.py        # p50/p95 wall-clock across the answer path
```

There are **four independent runners** because each measures a distinct thing:

- **`retrieval`** — asks "did the right chunks even reach the pool?" Runs without any LLM cost beyond embeddings, so it's cheap enough to rerun on every PR.
- **`grounding`** — asks "did the answerer only say things the code supports?" This is the truthful-over-fluent guarantee turned into a number. Uses the real Groq/Cerebras path, so it's LLM-quota-bound.
- **`verifier`** — asks "is our judge itself calibrated?" We caught a 0.60-accuracy broken verifier this way in Phase 0's D1.1 repair; without this runner we would have been measuring quality against a bad ruler.
- **`latency`** — asks "does the change ship?" A 3× p95 regression is a stop condition even if quality improves.

These are independent so a partial run (say, retrieval-only when quota is out) still produces a durable signal.

---

## 4. The datasets — the immovable ground truth

Datasets live under `evals/datasets/` as JSONL, each row hand-labelled. Composition today:

| Dataset | Rows | Purpose | Built in |
|---|---|---|---|
| `httpx_qa_v1` | 20 | General natural-language questions about httpx internals | Phase 0 |
| `flask_qa_v1` | 20 | Same, for flask — the "answer beyond rank 150" set | Phase 0 |
| `fastapi_qa_v1` | 20 | Same, for fastapi | Phase 0 |
| `rare_symbol_v1` (httpx) | 12 | Exact-symbol / error-string queries — the BM25 target | Phase 3 |
| `fastapi_rare_symbol_v1` | 12 | Same, for fastapi | Phase 3 |
| `verifier_quality_v1` | ~40 | (claim, ref, verdict) triples for calibrating the verifier itself | Phase 0 (D1.1) |
| `multi_hop_v1` | (deferred, would be 10) | Multi-hop questions for Phase 2 | Phase 2 (deferred) |

**Why hand-labelled matters:** the alternative is to have an LLM judge its own answers, which is the classic "grade my own homework" fallacy. Hand-labelled gold answers make the gate independent of the model being evaluated.

**How they're built:** the propose→review flow — `evals/tools/propose_labels.py` over-fetches top-150 candidates and filters `tests/ examples/ docs/ docs_src/ scripts/`, a human picks the real answer. That flow is the same for every new dataset (multi-hop, rare-symbol, etc.), so adding coverage is a well-worn path.

Datasets are frozen — once a `_v1` file is committed, its rows don't change. A new labelling round produces `_v2`, and the old `_v1` stays around as a compatibility baseline.

---

## 5. The workflow — how a phase actually ships

Concretely, for each phase the loop is:

```
1. Freeze the current landed pipeline's numbers as `_before.json`.
   (Usually: previous phase's `_after.json` copies to the new phase's `_before.json`.)
2. Implement the phase's code change on a branch.
3. Run the retrieval-only bench first — cheap, catches gross regressions.
   uv run python -m repopilot_evals.bench --phase N --repo httpx --skip-llm
4. Run the full LLM path — grounding, verifier, latency.
   uv run python -m repopilot_evals.bench --phase N --repo httpx
5. Repeat for flask, fastapi.
6. Aggregate.
   uv run python -m repopilot_evals.bench --phase N --aggregate
   → writes _after.json, delta.json, plus a significance self-test.
7. Read the gate lines in docs/rag/0N_*.md §5. Pass → commit + flip
   status in CURRENT_PHASE.md. Fail → iterate, or cut cleanly per
   the 2-day-ship-plan rule.
```

The `delta.json` is where the whole system pays off — it lays out the before/after numbers side by side per metric and per dataset. That's the artifact a reviewer reads to say "yes, this shipped."

**Significance self-test.** `bench_repo` runs a paired significance test (bootstrap over per-question scores). A change that looks like +2 pp but is inside the noise band gets flagged as *not significant* — the gate demands both direction and magnitude, so nobody ships noise as a win.

---

## 6. Concrete wins the eval system has already delivered

Every one of these is a defect we would have shipped without it:

- **Phase 0 D1.1 repair — broken verifier caught.** The initial verifier had 0.60 accuracy on `verifier_quality_v1` because Groq `qwen/qwen3-32b`'s `<think>` reasoning burned the 200-token budget before emitting JSON. `verifier.py` runner surfaced this; fix (strip `<think>`, raise `max_tokens` to 1024) → 1.00 accuracy. **Without the verifier runner every downstream grounding number would have been wrong.**
- **Phase 1 recall lift — measured, not claimed.** Widening the pool from `k=8` to `k=50` was intuitively good; the eval showed recall@10 0.385 → 0.949 (+56 pp) **and** exposed that `grounding_accuracy` dropped because richer answers have more claims to fail — a *metric artifact*. The per-claim rate stayed flat/up, so the phase landed. **Without the eval this would have been either "we shipped a regression" or "we killed the phase over a false alarm."**
- **Phase 3 BM25 — repo-dependent tradeoff exposed.** BM25 helped fastapi +17 pp on rare-symbol and *cost* httpx −5 pp on general Q&A. Single-repo eval would have shipped a "win" that regressed our primary bench. Multi-repo eval forced the conversation that led to `dense_weight=3.0` — the compromise that gets the fastapi win without breaking httpx.
- **Phase 4 reranker — chosen model backed by numbers, not marketing.** The spec defaulted to BAAI/bge-reranker-base (~1 GB); a MiniLM alternative (~80 MB) scored the same 0.90 on the verifier self-test. Eval closed the loop and picked the 12× smaller / much faster model.
- **The `.env` malformed-key incident (2026-07-10).** A week of 429s was root-caused only because the grounding runner's structured errors surfaced the actual 401 payload — not a "429 backoff" mirage.

Every one of these is a case where the eval system was the difference between shipping a real improvement and shipping a story.

---

## 7. The economics — cheap where it needs to be, expensive where it must be

The eval system is designed so the **cheap signals run often** and the **expensive signals run at phase boundaries**:

| Runner | Cost per bench | When to run |
|---|---|---|
| `retrieval` | Embeddings only (~0.5 s / question, no LLM) | Every branch, every commit |
| `verifier` | ~40 LLM calls (verifier only) | Every phase transition |
| `grounding` | 20 questions × (answer + N-verifier-per-claim) — the expensive one | Every phase transition, per repo |
| `latency` | Same LLM path, timing only | Every phase transition |

This split is why we can afford honesty. A cheap retrieval-only run on every PR keeps the recall bar honest without burning Groq quota; the grounding gate runs only when we're actually claiming a phase landed.

---

## 8. What it protects against going forward

The Phase 7 Ship Closeout ([`docs/rag/07_SHIP_CLOSEOUT.md`](rag/07_SHIP_CLOSEOUT.md)) turns the eval system from a **manual** discipline into a **CI-enforced** one: any PR that touches retrieval code must ship a fresh `_after.json`, and the delta must pass gate. That's the moment the eval system stops being a habit and starts being a contract — the point where a future contributor (human or AI) cannot silently regress the system, because the CI won't let the PR merge.

The whole system was built for that final property. Everything before Phase 7 was the *habit*; Phase 7 is what makes the habit **binding**.

---

## 9. Read next

- [`RAG_PLAN.md`](RAG_PLAN.md) — the seven-phase plan the eval system exists to gate.
- [`CURRENT_PHASE.md`](CURRENT_PHASE.md) — where the build is right now, and which `_after.json` is the current baseline.
- [`rag/00_BASELINE_AND_MEASUREMENT.md`](rag/00_BASELINE_AND_MEASUREMENT.md) — the D0 / D1 / D2 measurement build-out that created the eval system.
- [`rag/07_SHIP_CLOSEOUT.md`](rag/07_SHIP_CLOSEOUT.md) — how the eval system becomes CI.
- [`03_ARCHITECTURE.md`](03_ARCHITECTURE.md) §"Verifier" — the truthful-over-fluent principle the eval system operationalises.

---

*This document is the "why" companion to the "what" specs in `docs/rag/`. If a future phase spec conflicts with the principles here, this file wins — those principles are what make the phase gates trustworthy in the first place.*
