# Audit Report — RepoPilot

**Baseline:** `main` at `e40dc02`, clean working tree · **Run:** 2026-08-11
**Method:** [`AUDIT_PLAN.md`](AUDIT_PLAN.md) · **Status:** complete — all eight
passes run. Of 21 findings: **14 fixed**, 4 accepted with a written expiry
condition, 1 open, 1 revised, 1 withdrawn. See [Fixed](#fixed).

---

## Verdict

*Written at audit time, 2026-08-11, and left as written — the per-finding
status column above is what is current.*

The backend is in better shape than most projects of this size. `mypy --strict`
is clean across 152 files, 408 tests pass in under three seconds at 85%
coverage, the 12 Playwright specs pass against the current UI, and the
security-sensitive paths — clone URL fencing, credential encryption, cookie
signing, production boot guards — were designed rather than stumbled into.

What is wrong falls into four groups:

1. **`main` cannot pass its own CI.** One committed file fails
   `ruff format --check`. Every pull request from this baseline is red before
   it changes anything.
2. **Nothing bounds what the platform pays for.** The free-repository
   allowance is keyed on a cookie the caller controls, questions are unmetered
   by design, `/intent` is an unauthenticated model call, and a repository is
   cloned in full before any size limit is checked.
3. **The two newest capabilities have no tests.** Provider-level token
   streaming and the verifier's recheck path — the one path that can upgrade a
   rejected claim to supported — are both uncovered.
4. **A feature was deleted from the frontend and left everywhere else.** The
   module map's UI is gone; its endpoint, service, models, client method and
   tests still ship, and `STATUS.md` still describes the UI as present.

---

## Findings

| # | Sev | Status | Where | What breaks |
|---|---|---|---|---|
| 1 | **P1** | ✅ fixed | `packages/core/tests/test_llm_provider.py:513` | CI format gate fails on `main` |
| 2 | **P2** | 🔒 accepted | `apps/api/src/repopilot_api/app.py:140` | Free-repo allowance resets by clearing a cookie |
| 3 | **P2** | 🔒 accepted | `apps/api/src/repopilot_api/access.py:353` | Questions unmetered — unbounded platform-key spend |
| 4 | **P2** | 🔒 accepted | `apps/api/src/repopilot_api/app.py:270` | `/intent` runs an unmetered LLM call for anonymous callers |
| 5 | **P2** | 🔒 accepted | `packages/ingestion/src/repopilot_ingestion/pipeline.py:132` | Repo cloned in full before any size limit applies |
| 6 | **P2** | ✅ fixed | `apps/api/src/repopilot_api/services.py:213,298` | Raw exception text served to clients; no traceback logged |
| 7 | **P2** | open | `apps/web/package.json` (transitive `sharp`) | 4 high-severity CVEs in the web dependency tree |
| 8 | **P2** | ✅ fixed | `packages/agents/src/repopilot_agents/verifier/grounding.py:360-415` | The claim-upgrade path has no test |
| 9 | **P2** | ✅ fixed | `packages/core/src/repopilot_core/llm/provider.py:730-789` | Token streaming has no unit test |
| 10 | **P3** | ✅ fixed | `apps/api/src/repopilot_api/app.py:545` | Dead feature: `/graph/modules` has no consumer |
| 11 | **P3** | ✅ fixed | `docs/STATUS.md:9` | Documents a UI file that no longer exists |
| 12 | **P3** | ✅ fixed | `apps/api/src/repopilot_api/app.py:261` | `HTTPException` raised inside a started SSE stream |
| 13 | **P3** | ✅ fixed | `CLAUDE.md` §3 | "Prompt budget ≤2000 tokens, enforced in CI" is not enforced |
| 14 | **P3** | ✅ fixed | `verifier/grounding.py:96` | Verdict cache is an unbounded process-global dict |
| 15 | **P3** | ✅ fixed | `llm/provider.py:149` | LLM SQLite cache records `created_at` and never expires anything |
| 16 | **P3** | ✅ fixed | `package.json` (repo root) | A dev tool as the root dependency creates a second lockfile |
| 17 | **P3** | ✏️ revised | `apps/api/src/repopilot_api/services.py:187` | BYOK users index inside the API process — the obvious fix is wrong |
| 18 | **P3** | ✅ fixed | `packages/ingestion/src/repopilot_ingestion/pipeline.py:201` | `gather` leaves the sibling task running when one side raises |
| 19 | **P3** | ✏️ withdrawn | `apps/web/tests/e2e/` | The deleted spec covered deleted code |
| 20 | **P3** | ✅ fixed | `scratch_index.py`, `httpx_index_time.txt`, `test-results/.last-run.json` | Scratch files tracked in the repository |
| 21 | **P2** | ✅ fixed | `.pre-commit-config.yaml:23` | The mypy hook could never pass — the root cause of finding 1 |

---

## Pass 1 — Build and gate health

### 1 — `main` fails its own format gate · **P1**

`ci.yml` runs `ruff format --check .`. From a clean checkout:

```
Would reformat: packages/core/tests/test_llm_provider.py
1 file would be reformatted, 154 files already formatted
```

The committed code hand-wraps a 96-character line that ruff 0.15.17 — the
pinned version, matching `.pre-commit-config.yaml` — wants on one line under
the configured `line-length = 100`. `ruff check` and `mypy --strict` both pass,
so this is the only thing between `main` and a green build.

`make fmt` fixes it. The interesting question is how it got committed: the
pre-commit hook would have caught it, which suggests it was pushed with hooks
skipped or not installed.

Everything else in this pass is green — see [What passed](#what-passed).

---

## Pass 2 — Security and abuse surface

> **Findings 2–5 are accepted, not fixed** (decided 2026-08-11). The deployment
> is private: everyone who can reach the API is someone who pays for it, so a
> spend ceiling would cost more to build than it protects. The decision, the
> cost of closing each one, and the conditions that revoke it are recorded in
> [`STATUS.md`](STATUS.md) — the short version is that **findings 3 and 4 must
> close before the API is reachable by anyone who is not paying for it**, since
> neither needs an account or a repository to exploit. Finding 5 also fires by
> accident rather than only by abuse, so it is the one to close first if disk
> pressure ever appears. The descriptions below stand as written; only their
> status changed.

### 2 — The free-repository allowance is cookie-scoped · **P2**

`resolve_session` (`app.py:140`) mints a fresh signed session whenever the
cookie is absent or fails its HMAC check, and `reserve_repository`
(`access.py:348`) counts free repositories per `session_id`. Deleting the
cookie therefore issues a new identity with a fresh allowance — no sign-in, no
rate limit, no fingerprint.

This is business logic, not a break-in: nothing else is protected by the
session, and the signing is correctly implemented (HMAC-SHA256,
`compare_digest`, `httponly`, `secure` + `samesite=none` in production). But
"one free repository" currently costs an attacker one cookie clear, and each
one is a full clone, parse, embed and summarise pass on the platform key.

The decision is a product one: accept it as the price of anonymous access, or
bind the allowance to something with a cost — the signed-in account, which the
schema already supports.

### 3 — Questions are unmetered · **P2**

```python
async def reserve_question(self, session_id: str, repo_id: str) -> UsageReservation:
    # Questions are unmetered; the row is still written for usage history.
    return await self._reserve(..., free_limit=None)
```

`access.py:353`. The row is written but no limit is checked, so a session with
no BYOK key asks unlimited questions against the platform Groq key. Each
question is a retrieval pass, a cross-encoder rerank, an answer generation and
up to three concurrent verifier calls. Combined with finding 2, there is no
ceiling of any kind on platform LLM spend.

This is deliberate — the comment says so — and reasonable for a demo. It is not
reasonable for anything publicly exposed, and nothing in the codebase marks the
difference between those two situations.

### 4 — `/intent` is an unauthenticated LLM call · **P2**

`app.py:270`. The docstring reasons honestly that metering it would push users
toward presets for the wrong reason, and the call is small. But it takes free
text from any caller, sends it to the platform provider when the session has no
key, and has no rate limit. It is the cheapest way to spend someone else's
quota in the whole API. Same decision as finding 3, same fix shape — a
per-session rate limit rather than metering — and it should be decided at the
same time.

### 5 — The size limit applies after the clone · **P2**

`index_repo` (`pipeline.py:132`) clones, scans every file, and only then checks
`loc_total > settings.ingestion_max_repo_loc`. The cap bounds what gets
*indexed*; it bounds nothing about what gets *downloaded*. A caller who pastes
a multi-gigabyte public repository gets it cloned in full, to disk, before
anything rejects it.

The clone is shallow and single-branch, which helps, but `--depth 1` of a large
monorepo is still large. Two cheap bounds exist and neither is used: GitHub's
API reports repository size before any clone, and `git clone --filter=blob:none`
defers blob download. Either one turns this from "unbounded" into "bounded".

### 7 — Four high-severity CVEs in the web tree · **P2**

`npm audit --omit=dev` in `apps/web`:

```
sharp  <0.35.0
Severity: high
sharp inherited vulnerabilities in libvips: CVE-2026-33327, CVE-2026-33328,
CVE-2026-35590, CVE-2026-35591
```

`sharp` arrives transitively through `next@15.5.20` (image optimisation). The
clean fix is `next@16.3.0`, which npm flags as breaking. Practical exposure
depends on whether the deployment serves user-supplied images through Next's
optimiser — RepoPilot does not, which lowers the risk considerably without
making the advisory go away. Nothing in CI runs `npm audit`, so this would not
have surfaced on its own.

---

## Pass 3 — Correctness of the request paths

### 6 — Internal exception text is served to clients · **P2**

```python
except Exception as exc:
    record.status = "error"
    record.progress = None
    record.error = str(exc)
```

`services.py:294-298`, and identically at `:210-213`. `record.error` is
returned by `GET /repos/{repo_id}/status` as the `error` field and rendered in
the UI. Whatever a failure inside clone, parse, embed, summarise or persist
stringifies to goes straight to the browser — SQLAlchemy and redis errors carry
connection targets, and provider errors carry request detail.

The second half is worse than the first: neither handler logs the exception.
There is no `log.exception` on either path, so a failed index leaves a
one-line string in an in-memory record and **no traceback anywhere**. When a
user reports "indexing failed", there is nothing to read.

Both handlers want the same two lines: log the exception with its traceback,
and hand the user a fixed message. The two branches that already do this —
`too_large` and `unsupported` — show the shape.

### 12 — `HTTPException` raised inside a live SSE stream · **P3**

```python
async def event_source() -> AsyncIterator[BaseTourEvent]:
    try:
        async for event in get_services().repos.first_impression_stream(repo_id):
            yield event
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="repo not found") from exc
```

`app.py:255-262`. By the time the generator runs, `StreamingResponse` has
already sent `200 OK` and the SSE headers — the 404 can never reach the client.
The reader sees a stream that stops with no explanation. The `/ask/stream`
route next door gets this right: it converts failures into a `TourErrorEvent`
on the wire, and says why in a comment. This route should do the same.

Related and smaller: `with_heartbeats` (`sse.py:31`) leaves the shielded
`__anext__()` future dangling if the consumer closes mid-wait, so a
disconnecting client orphans the pending task rather than cancelling it.

### 18 — `gather` leaves a sibling running on failure · **P3**

`pipeline.py:201` runs `summarise_chunks` and `embed_chunks` under a bare
`asyncio.gather`. If summarising raises, the exception propagates immediately
but the embedding task is not cancelled — it keeps running against the
provider, on a pipeline that has already failed, holding the model and its
quota. `return_exceptions=True` with an explicit check, or a `TaskGroup`, ends
it properly.

### 17 — BYOK users index inside the API process · **P3, revised**

`services.py:186-192` routes to the arq worker only when
`repopilot_env == "production"` **and** no BYOK provider was supplied.
Everything else — all of development, and every production request from a user
with their own key — runs the whole pipeline as an asyncio task inside the API
process. The heavy stages are threaded (`asyncio.to_thread` for the scan,
`embed_many` under an encode lock), so the event loop is not hard-blocked, but
a single API process is doing minutes of CPU-bound embedding while serving
requests.

**The obvious fix is wrong, and this was found by trying to apply it.** The
arq job is `index_repo(ctx, repo_url)` (`jobs/index_repo.py:47`); it builds its
provider from `ctx["llm"]`, which is the *platform* key. Routing a BYOK request
to the worker would silently bill the platform for work the user is paying for
— worse than the condition it replaced.

Doing this properly means getting the user's key to the worker, which means
either putting a Groq key in a Redis job payload or storing a reference the
worker resolves from `product_credentials`. That is a trust-model decision, not
a P3 sweep item. Left as-is deliberately; the condition is correct for the
reason it exists, even though it reads like a development shortcut.

A related structural note, not a finding: `self.records` is per-process memory,
so any deployment running more than one uvicorn worker will show different
indexing state depending on which worker answers the poll.

---

## Pass 4 — CLAUDE.md conformance

Every rule in §3 holds up except one.

| Rule | Enforced? | Evidence |
|---|---|---|
| Truthful over fluent; `file:line` on every claim | Yes | `Claim.refs` min_length=1, `verifier/grounding.py:56` |
| No stat dumps; `Insight` shape | Yes | `state.py:63-68`, `capabilities/_coerce.py:71`, `test_capabilities.py:124` |
| State discipline, `recursion_limit=15` | Yes | `test_graph_wiring.py:98` pins it |
| Six deterministic tools | Yes | `tools/__init__.py:1` documents the eight modules and why the palette is still six |
| Lane C guarded language | Yes | Prompted and post-checked by the Verifier |
| **Prompt budget ≤2000 input tokens, "enforced in CI"** | **No** | Nothing measures tokens |
| Quality gates (ruff, mypy, pytest 80%, gitleaks) | Yes, and they run | See pass 1 |

### 13 — An unenforced rule presented as enforced · **P3**

`CLAUDE.md` §3 states the prompt budget is "Enforced in CI". Nothing enforces
it. `test_prompt_size.py` asserts character caps on chunk bodies
(`MAX_CHUNK_CHARS` / `MAX_CHUNKS_CHARS`) — a different and much looser
property. The 2000-token figure appears only in docstrings (`qa/prompts.py:3`,
`capabilities/cartographer.py:10`, `prompts/goal_anchor.py:68`).

It is the one rule in the file whose claim of enforcement is false, which makes
it the one worth either enforcing or rewording. A rule that says it is enforced
and is not is worse than a rule that admits it is a convention.

---

## Pass 5 — Dead code and drift

### 10 — The module map is dead code below the UI · **P3**

Commit `74b396e` ("token streaming", 2026-08-10) deleted
`apps/web/src/components/module-map.tsx` (212 lines) and
`apps/web/tests/e2e/module-map.spec.ts` (183 lines), and dropped the React Flow
and dagre dependencies. What it did not delete:

- `GET /repos/{repo_id}/graph/modules` (`app.py:545`)
- the `modules` service behind it and `MAX_MODULES` (`services.py`)
- `GraphModulesResponse` / `GraphModule` (`models.py`)
- `getGraphModules` and both response interfaces (`generated.ts:126,389`)
- `apps/api/tests/test_graph_modules.py`

The endpoint is live, tested and reachable, and nothing calls it. Not harmful —
but it is a feature's worth of surface being maintained for no consumer, and
the audit found it by listing files, which is exactly how dead code survives.

It also collides with the scope decision in `STATUS.md`, which froze the
feature as "still ships, no further investment". Half of it has since been
removed. The freeze needs re-deciding now that the decision has partly been
made by accident.

**Fixed** — removed end to end on 2026-08-11: the route, `LiveGraphService.modules`
and `_module_owners`, `_rollup_modules` and `_owning_module`, `MAX_MODULES`, the
three response models, the client method and its interfaces, and
`test_graph_modules.py`. No re-index: the map read the same `imports` edges the
"Related code" panel and retrieval read, and stored nothing of its own. The
panel is untouched. `STATUS.md` records the decision.

### 11 — `STATUS.md` describes a file that does not exist · **P3**

`docs/STATUS.md:9` names `apps/web/src/components/module-map.tsx` as code that
"remains in the codebase and still ships". It was deleted the same day the file
was last updated. Two smaller drifts alongside it: the doc claims "15 store
tests and 15 e2e specs" — there are 16 store tests and 12 e2e cases across
three spec files.

`STATUS.md` is the file the project tells everyone to read first. It is the one
document where drift costs the most.

**Fixed** — the scope decision now records the removal, the stale test counts
are corrected in place with a note saying why they moved, and the per-module
measurement table carries a line saying the feature it measured is gone.

### 16 — A dev tool is the repository's root dependency · **P3**

The root `package.json` contains exactly one dependency,
`@anthropic-ai/claude-code`, and brings a root `package-lock.json` with it.
Next then has two lockfiles to choose between and picks the wrong one:

```
⚠ Warning: Next.js inferred your workspace root, but it may not be correct.
We detected multiple lockfiles and selected the directory of
/Users/.../RepoPilot/package-lock.json as the root directory.
```

The web app is a self-contained npm project under `apps/web`. A personal tool
does not belong in the repository's dependency graph, and removing it also
removes the warning.

### 20 — Scratch files are tracked · **P3**

`scratch_index.py`, `httpx_index_time.txt` and `test-results/.last-run.json`
are committed at the repository root. Harmless, but they are the first thing
anyone cloning the project sees.

---

## Pass 6 — Test integrity

Coverage is 85.23% and the suite is fast and honest — the mocks mock providers
and the database, not the logic under test. Two gaps matter, and both sit on
paths where being wrong is expensive.

### 8 — The claim-upgrade path has no test · **P2**

`verifier/grounding.py:360-415` is `_recheck`: when a claim is rejected, it is
re-verified against the answerer's wider context, and a flip to `supported`
replaces the verdict. Coverage reports lines 369-415 as never executed.

This is the only code in the system that turns a rejected claim into a
displayed one. Principle 1 of `CLAUDE.md` — truthful over fluent — rests on the
verifier, and the branch that can overturn the verifier is the branch nothing
tests. Its guards read correctly (a second rejection changes nothing, a
`ProviderError` leaves the original verdict standing, an empty widening
returns early), which is precisely why a regression here would be silent.

**Fixed** — four tests in `test_verifier_grounding.py`, one per guard, driving
the real `verify_claim` rather than the private helper so the wiring is covered
too. Module coverage 75% → 94%.

### 9 — Token streaming has no test · **P2**

`LLMProvider.generate_stream` (`provider.py:730-789`) is uncovered. (The
original entry named the method `stream`; that is the client-level method it
calls.) It carries real logic: cache-hit replay, first-streamable-binding
selection, mid-stream failure that must *not* be retried because the reader has
already seen text, a before-first-token failure that falls back to the full
`generate` chain, and a cache write with deliberately zeroed token counts.

It is also the newest user-facing feature — commit `74b396e` is named "token
streaming" — and it is the newest feature that nothing verifies. `provider.py`
is 73% covered overall across 409 statements; this block is the part of the gap
that a user would notice.

**Fixed** — five tests in `test_llm_provider.py`, one per branch, with a
`FakeStreamingClient` that can fail at a chosen point in the stream. Module
coverage 73% → 79%.

Lower priority, same category: `clone.py` at 57% and `resummarise.py` at 28%
are the weakest modules overall, but both are operator-facing rather than
request-path, and `resummarise` is a maintenance script.

### 19 — Frontend test coverage shrank · **withdrawn**

Recorded as a finding on the count (15 cases → 12) and withdrawn on inspection.
The 183-line spec `74b396e` deleted tested the module map, which the same
commit deleted — removing it lost no coverage of code that still exists.

The streaming concern behind the finding is also unfounded: `tests/e2e/sse.ts`
splits an answer into `answer_token` frames precisely so the mock does not
serve JSON to both routes, and its header says why — "a route mock that serves
JSON to both leaves the streaming path untested". `persona-ask.spec.ts` uses
it. The frontend streaming path is covered.

What remains true, as a note rather than a finding: `repopilot-app.tsx` is
1,338 lines holding all streaming, session and tour state, and its only
`useReducer` is a poll counter — there is no reducer to unit-test, so the 12
e2e cases are the whole safety net for that component. Splitting it would give
the state something testable to live in. That is a refactor, not a defect.

---

## Pass 7 — Data, cost, and operations

Migrations are in good order: nine revisions, every one with a real
`downgrade` — including `0005_drop_product_tours`, which rebuilds the table it
drops rather than leaving a `pass`. The `INDEX_RECIPE_VERSION` mechanism is
correctly wired: all three queries that decide whether a snapshot counts filter
on it (`persist.py:91`, `:112`, `:163`, plus `services.py:384`), which is the
thing `653235c` fixed and the thing most likely to silently regress.

Two unbounded caches, both P3, both the same shape of problem — something
grows for the life of the process and nothing ever removes anything.

### 14 — The verifier verdict cache never evicts · **P3**

`grounding.py:96-113`. `_Cache` is a module-global `dict[str, VerifierVerdict]`
with `get` and `put` and no eviction; the only thing that clears it is
`reset_cache()`, a test helper. Every claim verified over the process lifetime
stays resident, keyed by sha256 of claim text plus chunk content. A long-lived
API process grows monotonically. An `OrderedDict` with a size cap, or
`functools.lru_cache` over a keyed helper, is the whole fix.

### 15 — The LLM SQLite cache never expires · **P3**

`provider.py:149`. Both tables store `created_at`, and no code reads it. There
is no TTL, no size bound, and no pruning — `.cache/llm.sqlite` grows for as
long as the deployment lives. Recording a timestamp and never using it suggests
expiry was intended and not finished.

Neither cache is a correctness problem: keys include the full request content,
so a stale hit is a hit on identical input. One consequence worth stating
plainly, since it is invisible from the code: the LLM cache key
(`_cache_key`, `provider.py:265`) covers model, messages and kwargs but not the
provider or the caller, so a BYOK user's paid completion is served to a
platform-key user on an identical question, and vice versa. That is a spend
question, not a leak — the cached content is derived from public repository
data either way.

---

## Pass 8 — Frontend

Better than the file sizes suggest. `repopilot-app.tsx` is 1,338 lines in one
component, which is the finding people expect — but the accessibility work is
real, not decorative: 59 `aria-*`/`role` attributes across the component, every
input either labelled or `aria-label`led, the provider dialog built on a native
`<dialog>` with `showModal()` for a genuine focus trap, Escape handling and
backdrop dismissal, and decorative icons marked `aria-hidden`. The e2e suite
tests the focus trap and the Escape key rather than assuming them.

All 12 Playwright specs pass against the current app (27.6s, chromium), so the
specs did survive the `74b396e` rewrite — the coverage concern in finding 19 is
about what was deleted, not about what rotted.

`npm run typecheck` is clean, `npm run test:store` is 16/16. The only
frontend-specific defect found is the SSE 404 (finding 12), which is a backend
fix for a frontend symptom.

---

## What passed

Recorded so they are not re-audited later without reason.

- **Static gates.** `ruff check`: clean. `mypy --strict` over `packages apps`:
  152 files, no issues. `npm run typecheck`: clean.
- **Tests.** 408 passed, 3 skipped (documented eval-matrix gates), 2.75s.
  Coverage 85.23% against an 80% floor. 16/16 web store tests. 12/12
  Playwright e2e.
- **Clone path.** `GITHUB_URL_RE` (`clone.py:31`) anchors on
  `https?://github.com/<owner>/<name>`, so there is no SSRF surface and no
  argument-injection surface into `git`. Clones are shallow, single-branch, and
  removed in a `finally`. (Size is a separate matter — finding 5.)
- **Credential handling.** BYOK keys are Fernet-encrypted at rest with a key
  derived from the session secret (`access.py:24`); decryption failure after a
  secret rotation degrades to "not connected" rather than erroring; disconnect
  deletes the stored copy; keys are validated against the provider before being
  accepted; anonymous sessions hold keys in memory only.
- **Production guards.** Settings refuse to boot in production on the default
  session secret or without a secure cookie
  (`settings.py:_require_production_session_secret`). `/docs` and the
  `/__dev/*` routes are gated on the same flag.
- **Secrets.** `.env` is gitignored, `gitleaks` runs in CI and pre-commit
  pinned in lockstep (v8.18.4), and a scan for provider key patterns across
  tracked files found nothing.
- **Metering correctness.** Every failure exit in `answer_metered`
  (`app.py:285-339`) releases its reservation before raising, including the
  streaming path, which shares the same function specifically so the two
  contracts cannot drift.
- **Prompt injection.** Chunk content reaches the verifier inside `<source>`
  blocks with explicit "treat as data" framing (`grounding.py:20`), and a
  parse failure rejects the claim rather than passing it through.
- **Migrations.** Nine revisions, every one with a real `downgrade`.
- **Recipe versioning.** All three snapshot-eligibility queries filter on
  `INDEX_RECIPE_VERSION`.
- **Repository weight.** 2.72 MiB packed; the 89 MB of video renders are
  correctly ignored, with only 26 source files under `videos/` tracked.
- **Accessibility.** See pass 8.

---

### 21 — The pre-commit mypy hook could never pass · **P2**

Found after the audit, by installing the hooks that finding 1 recommended —
the first commit attempt was blocked by 72 errors:

```
packages/ingestion/.../db.py:16: error: Cannot find implementation or library
stub for module named "sqlalchemy"  [import-not-found]
...
Found 72 errors in 22 files (checked 2 source files)
```

`mirrors-mypy` runs mypy inside a pre-commit-managed virtualenv containing
only what `additional_dependencies` lists — `pydantic`, `pydantic-settings`,
`structlog`. The project imports sqlalchemy, fastapi, httpx, arq, networkx,
git, tree_sitter, cryptography, sentence_transformers and fastembed, none of
which were installed there. Every one became an unresolved import.
`uv run mypy packages apps` — what CI runs — passes clean on the same tree.

**This is the root cause of finding 1.** A hook that fails on every commit
regardless of the change is a hook everyone learns to bypass, and bypassing
the hooks is exactly how an unformatted file reached `main` and left CI red
across three pushes. The formatting was the symptom; this was the cause.

Replaced with a `repo: local` hook running the same command as CI, through
uv, with `pass_filenames: false` because mypy needs the whole program rather
than the changed files. It now passes, along with every other hook.

Worth noting how this was found: not by reading the config, but by taking the
audit's own advice and installing the hooks. The audit checked that the gates
*existed* and that CI *ran* them; it did not check that a developer could
satisfy them locally. That is a gap in the method, and pass 1 of
[`AUDIT_PLAN.md`](AUDIT_PLAN.md) should say so next time.

---

## Fixed

Applied 2026-08-11, after the audit run. Full suite green afterwards: ruff
clean, `ruff format --check` clean, `mypy --strict` clean, 409 passed at 85.29%
coverage, 16/16 store tests, 12/12 Playwright.

| # | What changed |
|---|---|
| 1 | `make fmt` — `main` passes `ruff format --check` again |
| 6 | Both handlers in `services.py` log the traceback and return `INDEX_FAILED_MESSAGE`; internal exception text no longer reaches the browser |
| 12 | `/first-impression` yields `TourErrorEvent` instead of raising into a started stream, with a catch-all that logs |
| 13 | `CLAUDE.md`, `AGENTS.md` and `.agents/rules/project.md` now say the token budget is a convention, and name what CI does enforce |
| 14 | `_Cache` is an LRU capped at 2,048 verdicts; one test covers eviction order |
| 15 | `_SQLiteCache` prunes entries older than 30 days on open — `created_at` was written and never read |
| 16 | Root `package.json` / `package-lock.json` removed; Next no longer infers the wrong workspace root |
| 18 | `asyncio.TaskGroup` replaces the bare `gather`, so a failed summarise cancels the embedding pass |
| 20 | Scratch files untracked; `test-results/`, `scratch_*.py`, `*_index_time.txt` gitignored |
| 8, 9 | Nine tests over `_recheck_against_answer_context` and `generate_stream`, each guard mutation-checked — the guard was inverted and the matching test confirmed to fail. Suite 409 → 418, coverage 85% → 87% |
| 21 | The pre-commit mypy hook runs CI's command through uv instead of in a three-dependency venv; it passes for the first time |
| 10, 11 | Module map removed end to end — route, service, rollup helpers, models, client method, tests. `STATUS.md` records the decision and its corrected test counts |

Two findings did not survive the attempt to fix them — 17 (the obvious fix
misroutes BYOK billing) and 19 (withdrawn). Both sections above are rewritten
to say why.

Note: `@anthropic-ai/claude-code` was the root `package.json`'s only
dependency. Install it globally (`npm i -g @anthropic-ai/claude-code`) rather
than through the repository.

---

## Do first

What is left, now that the sweep has landed.

1. ~~**Decide the spend question**~~ — decided 2026-08-11: the deployment is
   private, findings 2–5 accepted, conditions for revisiting written into
   `STATUS.md`. No code was written for it, which was the point.
2. ~~**Test the two untested paths**~~ — done: nine tests, each guard
   mutation-checked. (8, 9)
3. ~~**Decide the module map**~~ — decided: removed end to end. (10, 11)
4. **Track the CVEs** — add `npm audit --audit-level=high` to the `web` CI job,
   and schedule the Next 16 upgrade separately rather than inside a fix pass.
   (7)
5. **Reconsider 17** when the BYOK worker path is worth building — it needs a
   decision about where a user's key lives, not a code change.
