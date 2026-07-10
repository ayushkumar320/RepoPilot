# The Eval System, Explained Twice

A companion to [`EVAL_SYSTEM.md`](EVAL_SYSTEM.md). Same ideas, two altitudes. Read the layman half if you want the intuition; read the technical half if you want the wiring.

---

## Part 1 — Layman Explanation

### The core problem, in one sentence

RepoPilot is a robot that reads code and answers questions about it. **How do we know it's actually getting better instead of just seeming better?**

### Why this is hard

Imagine you hire a new librarian. You ask them where a book is, they point at a shelf. Was that the right shelf? A confident wrong answer looks exactly like a confident right answer — until you go check.

Now imagine hiring a new librarian every week and asking "is this one better than last week's?" You need a **test they all take**, graded the same way, so you can actually compare.

That is the eval system. It is the standardized test we make every version of RepoPilot take, so "did it get better?" has a real answer instead of a gut feeling.

### The three things we measure

1. **Did the robot find the right page in the book?** (Retrieval — cheap to check.)
2. **Did the robot only say things the book actually says?** (Grounding — the truthfulness bar. Expensive to check because it needs a full LLM run.)
3. **Did the robot answer fast enough?** (Latency — pointless to be right if it takes 60 seconds.)

### Why we can't just eyeball it

Because language is slippery. Two sentences can say the same thing in different words. Two answers can *sound* right and only one actually be. A gut feeling can't tell you "recall went up 5%" — but that 5% is the difference between shipping a real improvement and shipping a story.

### The "before and after" trick

Every time we change something, we run the test **twice**: once with the old code (`_before`), once with the new code (`_after`). We compare. If the "after" is genuinely better on the numbers that matter and doesn't break anything else, the change ships. If not, we throw it out. No feelings, no marketing — just the delta.

### The paranoia — "grading your own homework"

The obvious shortcut is to let the AI grade its own answers. That's the exact trap. So the tests use **hand-labeled correct answers written by humans**, and a separate **judge program** that only knows "does this claim appear in the actual code?" — it doesn't know or care what the AI thinks the answer should be. That way the AI can't cheat.

### Why we don't just write unit tests

Regular tests say "given input X, expect output Y." But for a code-Q&A robot, there are *many* correct outputs. The robot could say "this function handles login" or "this is the login handler" — both correct, neither matches a hard-coded string. So we test **properties** ("every claim must cite real code") instead of **exact outputs**.

### One-paragraph summary

We built a robot. Robots lie. We built a way to catch it lying and to prove — with numbers, on paper, reproducibly — that each new version is actually better than the last, using tests that a human wrote and a program (not another AI) grades. That is the eval system, and it is why the version history in this repo means something.

---

## Part 2 — Technical Explanation

### The problem, restated in system terms

RAG pipelines have **many high-quality-looking failure modes** that neither type checkers, unit tests, nor manual QA catch:

- Recall miss + confident hallucination (silent).
- Metric confounding (grounding rate drops because answers got richer, not wronger).
- Cross-dataset regressions hidden by single-dataset scoring.
- Latency creep amortized across phases.
- Verifier drift (the referee itself becoming miscalibrated).

The eval system exists to make each of those a **numeric, comparable, gated signal** so a phase transition is a defensible engineering decision, not a vibe.

### Architecture

```
packages/evals/src/repopilot_evals/
├── bench.py              # Harness: --phase N --repo X
├── datasets.py           # JSONL row schemas + loaders
├── registry.py           # EvalSpec: which datasets belong to which phase
├── reports.py            # delta.json + markdown emitters
└── runners/
    ├── retrieval.py      # recall@k, NDCG@k, MRR, diversity  (embeddings only)
    ├── grounding.py      # full answer_question() path       (LLM-bound)
    ├── verifier.py       # verifier_quality_v1               (calibrate the judge)
    └── latency.py        # p50/p95 wall-clock                (ship-bar)
```

Every runner is independent and produces a `dict[str, object]` of metrics. `bench.py::bench_repo` composes them per phase, `--aggregate` fuses per-repo runs into `_after.json` + `delta.json`.

### Design invariants

1. **One retrieval policy drives all runners per phase.** Both `_before` and `_after` are measured under the same verifier, only the policy differs. This is what makes the guardrails honest — no confounding from a mid-run verifier change.
2. **Datasets are frozen.** A new labelling round produces `_v2`; `_v1` stays as a compatibility baseline. Metrics computed on different `_vN` files are not comparable and the harness enforces this via `EvalSpec` registry lookups.
3. **Hand-labeled gold.** `evals/tools/propose_labels.py` over-fetches top-150 candidates from a pre-Phase-1 retriever and filters `tests/ examples/ docs/ docs_src/ scripts/`. A human picks the correct chunk. LLM-labeled datasets are explicitly forbidden by the plan (see [`RAG_PLAN.md`](RAG_PLAN.md)).
4. **Verifier is independently calibrated.** `verifier_quality_v1` is a set of `(claim, ref, verdict)` triples. Verifier accuracy must sit above 0.88 before any grounding number is trusted. Phase 0 D1.1 caught a 0.60-accuracy verifier via this exact runner.
5. **Significance testing on every aggregate.** A bootstrap paired test over per-question scores. A change that looks like +2 pp inside the noise band is flagged non-significant — the gate requires both **direction** and **magnitude**.

### The four runners, in detail

**`retrieval.py`** — `run_retrieval_eval(dataset, repo_slug, *, recall_k, exclude_path_prefixes, search_mode, rerank, sample_limit)`.
Metrics: `recall@{5,10,20}`, `ndcg@{5,10}`, `mrr`, `diversity` (distinct file paths in top-5). Runs the same pipeline the product uses (`vector_search` / `hybrid_search` / `rerank_and_diversify`). Cost: embeddings only, ~0.5 s/question.

**`grounding.py`** — `run_grounding_eval(dataset, repo_slug, **policy_kwargs)`.
Drives the full `answer_question()` and pipes claims to `verify_claims`. Emits `grounding_accuracy` (all-or-nothing per answer), `claim_grounding_rate` (per-claim), `keyword_accuracy` (does the answer mention the gold keywords), `hallucination_rate` (did the answerer emit the "couldn't find that" sentinel when it should have), `input_tokens_per_question` (Phase 5's headline gate), `answer_input_tokens` per case for delta drill-down. Cost: 20 answers × (1 answer call + N claim-verifier calls) — the expensive one.

**`verifier.py`** — `run_verifier_eval(repo_slug)`.
Runs `verify_claim` on the frozen `verifier_quality_v1` triples. Emits `verifier_accuracy`. This is the **calibration of the ruler** — if it moves, every grounding number is suspect. Cost: ~40 LLM calls.

**`latency.py`** — `run_latency_eval(dataset, repo_slug, **policy_kwargs)`.
Same LLM path as `grounding`, but reports `latency_p50_ms` / `latency_p95_ms`. Split so a partial-quota run still gets one signal.

### The phase gate, mechanically

Every phase spec (`docs/rag/0N_*.md`) has a `§5 Gate` section: a list of predicates over metrics. Example (Phase 5):

```
- input_tokens_per_question after ≤ 0.6 × before   (on httpx_qa_v1)
- grounding_accuracy after ≥ before − 1 pp         (every dataset)
- verifier_accuracy after = before ± 0.5 pp        (verifier_quality_v1)
- hallucination_rate non-regressed
- latency_p50 non-regressed; latency_p95 ≤ 1.2 × before
```

`delta.json` lays these predicates out side-by-side. Human reads, decides `LAND` or `ITERATE` or `DEFER`. Phase 7 will move this predicate check into CI so a `retrieval/` PR without an updated `_after.json` and a passing delta cannot merge.

### The `_before`/`_after`/`delta` protocol

- `_before.json` — usually the previous phase's `_after.json`, copied on branch creation. This is the baseline the new work is judged against.
- `_after.json` — produced by `--aggregate` at the end of the phase; per-repo results fused with the significance self-test.
- `delta.json` — per-metric per-dataset diff between `_before` and `_after`, plus significance verdicts. **This file is the artifact a reviewer reads to say "yes, this shipped."**

Once landed, `_after.json` becomes the *next* phase's `_before.json`. The whole build history is a chain of `_after.json` files, each provably better than the last.

### Why the runners are independent

Because LLM quota is unreliable and phases ship on partial signal:

- Groq/Cerebras rate-limits can kill a run mid-dataset.
- The verifier lane and the answerer lane use *different* Groq tiers; one going down doesn't kill the other.
- Retrieval-only runs need no LLM quota at all — they're the always-runnable smoke test.

By splitting the runners, a phase can partially advance on the signals it *did* get, with the caveat noted in `CURRENT_PHASE.md` ("fastapi grounding pending: quota").

### Where the eval system has already paid for itself

| Phase | What the eval caught |
|---|---|
| 0 D1.1 | Broken verifier (0.60 accuracy). Fix: strip `<think>`, raise `max_tokens`. Grounding numbers post-fix are trustworthy. |
| 1 | `grounding_accuracy` drop was a **metric artifact** of richer answers. Added `claim_grounding_rate` (per-claim) as the real signal. |
| 3 | BM25 helped fastapi +17 pp on rare-symbol, cost httpx −5 pp on general. Multi-repo eval forced the `dense_weight=3.0` compromise. |
| 4 | MiniLM (~80 MB) matched BGE (~1 GB) at 0.90 verifier-self-test. Eval picked the smaller/faster model. |
| infra | Malformed `.env` (`GROQ_API_KEY=gsk_...#Yash ka key`) → 401 → cascading 429s. Grounding runner's structured error payload surfaced the actual 401. |

### Read next

- [`EVAL_SYSTEM.md`](EVAL_SYSTEM.md) — the fuller "why + benefit" writeup this doc distills.
- [`rag/00_BASELINE_AND_MEASUREMENT.md`](rag/00_BASELINE_AND_MEASUREMENT.md) — the actual D0/D1/D2 build-out of the eval system.
- [`rag/07_SHIP_CLOSEOUT.md`](rag/07_SHIP_CLOSEOUT.md) — how the gate becomes CI.

---

*Two altitudes, one system. The layman half is the intuition; the technical half is the wiring. If someone asks "why do you have an eval system?" — the layman half is the answer. If someone asks "how does your eval system work?" — the technical half is.*
