# RAG Phase 0 — Execution Runbook

> Step-by-step instructions to produce committed baseline numbers for three codebases (httpx · flask · fastapi).
> Companion to [`00_BASELINE_AND_MEASUREMENT.md`](00_BASELINE_AND_MEASUREMENT.md) — that doc is the **spec**, this doc is the **how-to-run**.

**Total your time:** ~1.5 hours, one-time
**Money cost:** $0 (free-tier Groq + local Ollama)
**Decision policy:** Option A — pure-metric grading, no LLM judge

---

## Pre-flight (do this once, ~10 min)

| Check | Command | Expected |
|---|---|---|
| Docker services up | `make docker-up && sleep 30 && docker compose ps` | postgres + redis + ollama all `healthy` |
| Postgres schema present | `cd packages/ingestion && uv run alembic current` | shows `0001_ingestion_schema (head)` |
| Groq key in `.env` | `grep '^GROQ_API_KEY=' .env` | non-empty line |
| LangSmith key in `.env` | `grep '^LANGSMITH_API_KEY=' .env` | non-empty line |
| Ollama models pulled | `curl -s localhost:11434/api/tags \| jq -r '.models[].name'` | includes `qwen2.5-coder:7b` and `nomic-embed-text` |
| Phase 1 ingestion works end-to-end | `make test-slow` (~15 min, one-time) | green |

If `make test-slow` fails, **stop**. The retrieval pipeline itself isn't working — no point benchmarking a broken system. Fix that first.

---

## Stage 1 — Index the three repos (~15 min wall clock, mostly waiting)

Start the FastAPI server + the arq worker in two terminals:

```bash
# Terminal A
uv run uvicorn repopilot_api.app:app --port 8000

# Terminal B
uv run arq repopilot_api.jobs.index_repo.WorkerSettings
```

Then enqueue all three repos at once. Worker drains them sequentially.

```bash
for repo in encode/httpx pallets/flask tiangolo/fastapi; do
  curl -s -X POST localhost:8000/repos \
    -H "content-type: application/json" \
    -d "{\"repo_url\":\"https://github.com/$repo\"}"
  echo
done
```

Each repo takes ~60–90 s to index. Poll status:

```bash
watch -n 5 'for repo in encode%2Fhttpx pallets%2Fflask tiangolo%2Ffastapi; do
  curl -s "localhost:8000/repos/$repo/status" | jq -r ".repo_id + \": \" + .status"
done'
```

**Done when:** all three report `status=ready`. If any errors, see the worker terminal log.

**Sanity check before moving on:** verify the chunks landed.

```bash
uv run python -c "
from sqlalchemy import create_engine, text
from repopilot_core.settings import get_settings
e = create_engine(get_settings().postgres_dsn.replace('+psycopg', ''))
with e.connect() as c:
    rows = c.execute(text(
        'SELECT repo_id, COUNT(*) FROM chunks GROUP BY repo_id ORDER BY repo_id'
    )).fetchall()
    for r in rows: print(r)
"
```

Expected: three rows, each with ~2,000–5,000 chunks depending on repo size.

---

## Stage 2 — Propose candidate labels (~2 min, I generate, you wait)

I'll have shipped `evals/tools/propose_labels.py` by the time you read this. Run:

```bash
uv run python -m repopilot_evals.tools.propose_labels \
  --repo httpx   --out evals/datasets/httpx_qa_v2.candidates.jsonl --target 20
uv run python -m repopilot_evals.tools.propose_labels \
  --repo flask   --out evals/datasets/flask_qa_v1.candidates.jsonl --target 25
uv run python -m repopilot_evals.tools.propose_labels \
  --repo fastapi --out evals/datasets/fastapi_qa_v1.candidates.jsonl --target 20
```

The targets are **larger than the final dataset size** (20/25/20 candidates → 15/20/15 accepted) because you'll reject 20–25% during review. The script picks:

- 60% single-hop (chunks whose docstring is enough to answer)
- 25% multi-hop (chunks that call ≥2 other documented functions)
- 15% hallucination probes (synthesized "what is `<random>_module`?" rows with `expected_refs=[]`)

**Why a new `httpx_qa_v2`** rather than reusing the existing 16-row `httpx_qa_v1`: the v1 was hand-labeled in a previous session and never audited. We'll spot-check it separately in Stage 5; in the meantime v2 gives us a fresh httpx bench labeled with the same protocol as flask + fastapi (apples-to-apples).

---

## Stage 3 — Review labels in the TUI (~75 min — the focused-work part)

Open the review tool:

```bash
uv run python -m repopilot_evals.tools.review_tui \
  --candidates evals/datasets/flask_qa_v1.candidates.jsonl \
  --accepted   evals/datasets/flask_qa_v1.jsonl
```

You'll see one row at a time:

```
─── flask_qa_v1 · row 5 of 25 ──────────────────────────────────
question:   How does Flask resolve URL rules when a request comes in?
refs:       flask/app.py:1240-1278  (Flask.dispatch_request)
keywords:   ["url_map", "match", "dispatch_request"]
tag:        auto_docstring_v1

  [a] accept    [e] edit refs    [r] reject
  [k] edit keywords    [s] skip (defer)    [q] quit & save
```

### The decision rules

| Press | When | What happens |
|---|---|---|
| **`a` — accept** | Question is real, refs look right, keywords reasonable | Row moves to the accepted JSONL |
| **`e` — edit refs** | Question is good but refs are wrong/incomplete | Opens `$EDITOR` at the chunk; you paste corrected `(file_path, start_line, end_line)` triples |
| **`r` — reject** | Question is tautological, too easy, or nonsensical | Row → `rejected.jsonl` (kept for audit, not benched) |
| **`k` — edit keywords** | Refs fine but keywords are weak or echo the question | Inline edit the keyword list |
| **`s` — skip** | You're tired and don't want to decide now | Defers; come back to it |
| **`q` — quit** | You need a break | Saves progress; resume later by re-running |

### Pacing guide

- **First 5 rows:** ~30 s each. You're calibrating what "good" looks like.
- **Middle:** ~10–15 s each. Most are quick accepts.
- **The ~3 rows that need ref edits:** ~2 min each — you need to open the file and find the real answer.
- **Hallucination rows:** ~5 s each. Either the synthesized symbol name reads convincingly nonsense (accept) or it accidentally matches something real (reject).

After processing all 25 candidates, the TUI prompts:

```
You've accepted 18 candidate rows.
Target for this dataset: 20 rows.
Author 5 adversarial rows? [y/n]
```

### Adversarial rows (~15 min)

These are the rows you write **from scratch**. The TUI prompts for each field:

```
question:   _
expected_refs: (file_path, start_line, end_line)  — minimum 1
expected_keywords: comma-separated tokens
tag: adversarial_<your_label>
```

Aim for questions that probe known weaknesses:

| Type | Example for flask |
|---|---|
| **Lexical mismatch** | *"How does Flask decide whether to run `before_request` callbacks?"* (uses NL where code uses `preprocess_request`) |
| **Multi-hop chain** | *"What happens to a session cookie when the response is being assembled?"* (spans 3 files) |
| **Wrong-but-plausible** | *"How does Flask use Redis for session storage by default?"* (it doesn't — `expected_refs=[]`, tests honest "couldn't find") |
| **Ambiguous intent** | *"How does routing work?"* (three valid answers; tests whether system picks confidently or asks) |
| **Rare symbol** | *"What does `_split_blueprint_path` do?"* (a real but obscure helper) |

5 adversarial rows per dataset is enough.

### Repeat for the other two

```bash
uv run python -m repopilot_evals.tools.review_tui \
  --candidates evals/datasets/httpx_qa_v2.candidates.jsonl \
  --accepted   evals/datasets/httpx_qa_v2.jsonl

uv run python -m repopilot_evals.tools.review_tui \
  --candidates evals/datasets/fastapi_qa_v1.candidates.jsonl \
  --accepted   evals/datasets/fastapi_qa_v1.jsonl
```

**Time budget per dataset:** ~25 min (20 min review + 5 min adversarial × ratio).

**Done when:** all three `*_qa_*.jsonl` files exist with row counts matching the targets (15 / 20 / 15).

---

## Stage 4 — Run the bench (~30 min wall clock, mostly waiting)

The infrastructure is already in place; this is a single command per repo.

```bash
# Each call ~10 min wall clock. Sequence them to stay under daily Groq quota.

uv run python -m repopilot_evals.bench \
  --phase 0 --repo httpx \
  --dataset evals/datasets/httpx_qa_v2.jsonl \
  --out evals/results/rag_phase0/httpx_baseline.json

# Wait for it to print "complete · 0 errors · 0 quota-stalls"

uv run python -m repopilot_evals.bench \
  --phase 0 --repo flask \
  --dataset evals/datasets/flask_qa_v1.jsonl \
  --out evals/results/rag_phase0/flask_baseline.json

uv run python -m repopilot_evals.bench \
  --phase 0 --repo fastapi \
  --dataset evals/datasets/fastapi_qa_v1.jsonl \
  --out evals/results/rag_phase0/fastapi_baseline.json

# Aggregate into the canonical index file
uv run python -m repopilot_evals.bench --aggregate \
  --in evals/results/rag_phase0/ \
  --out evals/results/rag_phase0/baseline.json
```

### What `bench.py` does per row

For every question:

1. Calls `answer_question(repo_id, query)` from the existing Q&A graph
2. Captures: `top_k_chunks`, `generated_answer`, `verified_claims`, `latency_ms`
3. Scores against the labels:
   - **recall@5/10/20** — was the right chunk in the top-k?
   - **NDCG@5/10** — was it ranked high?
   - **MRR** — what position was the first relevant chunk?
   - **grounding_accuracy** — do the system's claim refs overlap with `expected_refs`?
   - **hallucination_rate** — on `expected_refs=[]` rows, did the system honestly say "not found"?
   - **keyword_presence** — did any `expected_keywords` appear in the answer?
   - **latency_p50 / latency_p95** — wall clock

4. Bootstrap CI (10,000 resamples) for every metric — so we know noise vs. signal

### Quota safety

- The bench inserts a **2-second cooldown between questions** (configurable via `--cooldown`).
- On Groq 429, it sleeps 60 s and retries automatically (your existing `LLMProvider` handles this).
- Each run is **resumable** — if you Ctrl-C and re-run, it picks up from the last completed question via a state file at `evals/results/.bench_state.json`.

### Quota estimate

- 50 questions across 3 repos × ~5 LLM calls each (1 embed + 1 sufficiency + 1 answer + ~2 verifier) = ~250 calls per full run.
- Free-tier daily limit on `llama-3.3-70b-versatile` is ~1,000 RPD.
- Comfortably within budget. **Should run cleanly in one sitting.**

---

## Stage 5 — Spot-check + audit (~30 min)

Before committing the baseline, sanity-check the numbers and audit the existing `httpx_qa_v1`.

### 5a. Read the baseline file

```bash
uv run python -m repopilot_evals.bench --show baseline.json
```

Outputs something like:

```
                       httpx    flask    fastapi
recall@5             0.812    0.703      0.745
recall@10            0.875    0.812      0.823
NDCG@5               0.741    0.638      0.682
MRR                  0.683    0.594      0.621
grounding_accuracy   0.563    0.412      0.487
hallucination_rate   1.000    0.667      1.000   ← higher is better (honest "not found")
verifier_accuracy    0.92     0.89       0.91
latency_p50 (ms)     2,140    2,890      2,510
latency_p95 (ms)     4,820    6,710      5,930
```

**What's normal at baseline:**
- `recall@10` in the 0.70–0.90 range
- `grounding_accuracy` will probably be **embarrassing** — 0.40–0.65 range. That's the gap the RAG plan exists to close.
- `hallucination_rate` should be ≥0.66 (system honestly says "not found" on ≥2 of 3 not-in-repo questions per dataset)
- `verifier_accuracy` ≥ 0.88 is required by the `docs/rag/00` Gate. If lower, see the Gate's verifier-tightening pass before declaring Phase 0 done.

**What's a red flag:**
- `recall@10 < 0.50` on any dataset → indexing is broken or the embedder is mismatched
- `hallucination_rate < 0.33` on any dataset → system is making things up; baseline number is unreliable
- `latency_p95 > 30,000ms` → quota throttling is masking the real numbers; re-run when quota resets

### 5b. Audit the existing 16-row `httpx_qa_v1.jsonl`

Open the file. For each row:

1. Open `expected_refs[0]` location in the actual httpx source at the **indexed commit SHA** (`uv run python -c "from sqlalchemy import ...; print(SELECT head_sha FROM repos WHERE url LIKE '%httpx%')"`).
2. Read the cited code. Does it really answer the question?
3. If yes, leave the row.
4. If no, edit the refs (or reject the row outright).

Time per row: ~1 minute. Total: ~16 minutes.

After the audit, re-run httpx through `bench.py` with the corrected `httpx_qa_v1.jsonl` (alongside the new `httpx_qa_v2`):

```bash
uv run python -m repopilot_evals.bench --phase 0 --repo httpx \
  --dataset evals/datasets/httpx_qa_v1.jsonl \
  --out evals/results/rag_phase0/httpx_v1_baseline.json
```

If `httpx_qa_v1` numbers materially differ from `httpx_qa_v2`, **flag the divergence in the baseline JSON** — it means dataset quality matters more than we thought, and Phase 1's lift number needs to be measured against both.

---

## Stage 6 — Commit the baseline (~5 min)

```bash
git add evals/datasets/ evals/results/rag_phase0/
git commit -m "RAG Phase 0: committed baseline for 3 repos (httpx, flask, fastapi)

Baselines:
- httpx_qa_v2: 15 rows (auto-proposed, human-reviewed)
- flask_qa_v1: 20 rows
- fastapi_qa_v1: 15 rows
- httpx_qa_v1: audited (originally 16 rows, now N after edits)

Numbers: see evals/results/rag_phase0/baseline.json
Gate: verifier_accuracy >= 0.88 on all repos
Method: Option A pure-metric grading, no LLM judge
"
```

Then update `docs/CURRENT_PHASE.md`:

- Flip Phase 0 status to **🟢 done**
- Add `evals/results/rag_phase0/baseline.json` to the "Last verified gate" line
- Flip Phase 1 status to **🟡 active**
- Add a short "Session 2026-MM-DD" note summarizing what landed

Commit + push.

**Phase 0 is now complete.** The numbers in `baseline.json` are the bar every future phase has to beat.

---

## Troubleshooting

### "Worker crashed mid-indexing"

Look at the arq terminal log. Most common: `relation 'repos' does not exist` → `make db-migrate` first.

### "Bench keeps stalling on Groq 429"

Either you've burned today's quota (wait until UTC midnight) or another process is sharing the key. The state file at `evals/results/.bench_state.json` means you can stop and resume tomorrow without losing progress.

### "TUI is too slow — I want to just edit JSONL by hand"

Pass `--no-tui` to `review_tui` and it dumps the candidates to a tempfile, opens `$EDITOR`, then reads the saved version. Same outcome, less ergonomics.

### "I want to skip flask + fastapi for now"

Run Stages 1, 4, 5, 6 with only `--repo httpx`. The `docs/rag/00` Gate technically requires ≥ 2 repos, but `docs/CURRENT_PHASE.md` can call this out explicitly as a known reduced-scope baseline. You can always add the others later — they just need to be present before Phase 4 ships.

### "What if my numbers are way worse than the docs suggested?"

That's the **point** of measuring. The docs/rag plan was written assuming the existing pipeline was approximately working but unmeasured. If it turns out to be measurably bad — say, `grounding_accuracy < 0.30` — that doesn't change the plan, just the size of the lift each phase is targeting. Don't fudge the numbers; commit them honestly. The whole RAG plan compares lifts, not absolutes.

---

## After Phase 0

Phase 1 is the easy first lift (`recall_k=50` + metadata filters, no new deps). It uses the same `bench.py` infrastructure you just built — just runs with new code and writes `_after.json`. The `significance.py` runner tells you whether the lift is statistically real.

Read [`docs/rag/01_RECALL_LIFT.md`](01_RECALL_LIFT.md) when ready to start.
