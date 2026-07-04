# Finish Phase 0 Today — The Simple Plan

> Plain-language version of [`00_EXECUTION_RUNBOOK.md`](00_EXECUTION_RUNBOOK.md). Same steps, no jargon. Total: **~4 hours**, of which only ~1.5 hours needs your full attention.

**The goal in one sentence:** by tonight, we have a committed file (`baseline.json`) that says exactly how good our retrieval is *right now* — so every future improvement can prove itself with numbers instead of vibes.

---

## The day at a glance

| # | Step | What it is | Your effort | Clock time |
|---|------|-----------|-------------|-----------|
| 1 | Start the machines | Get the app + worker + databases running | copy-paste commands | 10 min |
| 2 | Feed it 3 repos | Have RepoPilot index httpx, flask, fastapi | paste 3 URLs, wait | 15 min (mostly waiting) |
| 3 | Generate answer-key drafts | Script guesses which code files answer each question | run 2 commands | 2 min |
| 4 | **Grade the answer keys** | You review each guess: right or wrong? | **focused work** | **~75 min** |
| 5 | Run the exam | Script measures the system against your answer keys | run 4 commands, wait | 30 min (mostly waiting) |
| 6 | Save the report card | Commit the results, flip the phase to done | 2 commands | 10 min |

Step 4 is the only part that truly needs *you*. Everything else is copy-paste-wait.

---

## Step 1 — Start the machines (10 min)

Three things must be running, each in its own terminal:

```bash
# terminal 1 — the API
uv run uvicorn repopilot_api.app:app --reload

# terminal 2 — the background worker (does the indexing)
uv run arq repopilot_api.jobs.index_repo.WorkerSettings

# terminal 3 — check Ollama has its models
ollama list   # need: qwen2.5-coder:7b and nomic-embed-text
```

Also confirm `.env` has `GROQ_API_KEY` and `LANGCHAIN_API_KEY`, and Postgres + Redis are reachable.

**Done when:** all three run without errors.

---

## Step 2 — Feed it the 3 repos (15 min)

Ask RepoPilot to index each repo (like you did in Postman):

```bash
curl -X POST http://localhost:8000/repos -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/encode/httpx"}'
curl -X POST http://localhost:8000/repos -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/pallets/flask"}'
curl -X POST http://localhost:8000/repos -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/fastapi/fastapi"}'
```

Poll `GET /repos/{id}/status` until each says **ready**. Grab a coffee.

**Done when:** all three repos show status `ready`.

---

## Step 3 — Generate the answer-key drafts (2 min)

We already wrote 35 exam questions (20 for flask, 15 for fastapi — see `evals/tools/questions/`). This script makes the system *guess* which code files answer each one:

```bash
uv run python evals/tools/propose_labels.py --repo flask \
  --questions evals/tools/questions/flask.txt \
  --out evals/tools/candidates/flask_qa_v1.candidates.jsonl

uv run python evals/tools/propose_labels.py --repo fastapi \
  --questions evals/tools/questions/fastapi.txt \
  --out evals/tools/candidates/fastapi_qa_v1.candidates.jsonl
```

**Done when:** both `.candidates.jsonl` files exist.

---

## Step 4 — Grade the answer keys (~75 min, the real work)

This is the part only a human can do honestly. For each question, the script shows its guessed code locations; you say which are truly correct.

```bash
uv run python evals/tools/review_tui.py \
  --candidates evals/tools/candidates/flask_qa_v1.candidates.jsonl \
  --out packages/evals/src/repopilot_evals/datasets/flask_qa_v1.jsonl
# then the same for fastapi
```

For each question you press one key:

- **a** = accept — pick which of the guessed locations are genuinely the answer, then type 2–4 keywords a correct answer must contain (e.g. function names)
- **r** = reject — bad question, drop it
- **k** = keep as a trick question (the "not in this repo" ones — the `!` rows)
- **s** = skip for now · **q** = quit (progress is saved, resume any time)

**Two rules that keep the exam honest:**
1. Before accepting a location, **open that file on GitHub and check** it really answers the question. ~2 min per question. This is the whole point of human review.
2. Only keep the *minimal* locations the answer truly depends on — not everything vaguely related.

Pace: ~35 questions × ~2 min ≈ 75 min. Do flask, take a break, do fastapi.

**Done when:** `flask_qa_v1.jsonl` (20 rows) and `fastapi_qa_v1.jsonl` (15 rows) exist in the datasets folder.

---

## Step 5 — Run the exam (30 min, mostly waiting)

Now measure the system against your graded answer keys:

```bash
uv run python -m repopilot_evals.bench --phase 0 --repo httpx
uv run python -m repopilot_evals.bench --phase 0 --repo flask
uv run python -m repopilot_evals.bench --phase 0 --repo fastapi
uv run python -m repopilot_evals.bench --phase 0 --aggregate
```

Each run prints its scores. The last command merges everything into
`evals/results/rag_phase0/baseline.json` + a CSV, and runs a sanity self-test.

If Groq rate-limits you (429), just wait a minute and rerun — the cache means it won't repay for finished questions.

**Sanity check the numbers.** Rough expectations: recall@10 somewhere in 0.4–0.8, grounding accuracy 0.5–0.85. **Red flags:** anything at exactly 0.0 or 1.0 across the board (usually a wiring bug, not reality), or verifier accuracy below 88% (then the verifier needs tightening before we trust anything else).

**Done when:** `baseline.json` exists and the numbers look plausible.

---

## Step 6 — Save the report card (10 min)

```bash
git add evals/results/rag_phase0/ packages/evals/src/repopilot_evals/datasets/*.jsonl
git commit -m "rag(phase0): committed baseline across httpx/flask/fastapi"
```

Then update [`CURRENT_PHASE.md`](../CURRENT_PHASE.md) **in the same commit habit**: mark Phase 0 🟢 done, Phase 1 🟡 active. Run `/graph-update`. Push.

**Done when:** baseline committed, phase flipped, pushed.

---

## If something goes wrong

| Problem | Fix |
|---|---|
| Repo stuck on "queued" | The arq worker (terminal 2) isn't running |
| `no indexed repo found for slug` | Step 2 didn't finish for that repo — check its status |
| Groq 429 errors | Wait 60 s, rerun the same bench command |
| Numbers all 0.0 or 1.0 | Something's miswired — stop and investigate, don't commit |
| Review taking forever | Quit with `q`, resume later — progress is saved per keystroke |

---

## What "done today" buys us

Tomorrow, when we build Phase 1 (bigger recall pool), we run the same bench and the significance test tells us — with statistics, not feelings — whether it actually helped. That's the entire value of today: **every future improvement becomes provable.**
