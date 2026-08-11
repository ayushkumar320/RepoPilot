# Audit Plan — RepoPilot, 2026-08-11

The project is feature-complete. This plan defines a full audit of it: what
gets examined, in what order, with what evidence, and what "a finding" means.
Results land in [`AUDIT_REPORT.md`](AUDIT_REPORT.md) — this file is the method,
that file is the outcome.

**Baseline:** `main` at `e40dc02`, clean working tree, 254 commits.
**Scope:** everything tracked in the repository — `packages/` (core,
ingestion, agents, evals), `apps/api`, `apps/web`, `docs/`, CI, and packaging.
Out of scope: the showcase video under `videos/` (media, not product), and any
runtime data in the Neon database.

---

## Severity scale

| Level | Meaning | Response |
|---|---|---|
| **P0** | Broken in production, data loss, or a live security hole | Fix before anything else |
| **P1** | Broken on `main`, or a defect a user hits on a normal path | Fix this cycle |
| **P2** | Correctness/abuse/cost risk that needs a decision, not a panic | Schedule with an owner |
| **P3** | Dead code, drift, hygiene, missing coverage | Batch and sweep |

A finding needs three things: **where** (`file:line`), **what breaks**
(a concrete failure, not a smell), and **evidence** (a command's output, a
reachable code path, or a diff). Anything without all three is a note, not a
finding, and is recorded as such.

---

## Passes

The audit runs in eight passes. Each names its method so it can be re-run
later and produce a comparable result.

### Pass 1 — Build and gate health

Does the repository pass its own gates, today, from a clean tree?

Run `ruff check`, `ruff format --check`, `mypy --strict`, `pytest` with the
80% coverage gate, `npm run typecheck`, `npm run test:store`, and the
Playwright suite. Compare against what `.github/workflows/ci.yml` actually
runs — a gate that exists locally but not in CI is a finding of its own.

**Also install and run the pre-commit hooks** (`uv run pre-commit install`,
then `run --all-files`). The 2026-08-11 run checked that the gates existed and
that CI ran them, and missed that the mypy hook could not pass on any commit —
which turned out to be the cause of the one P1 the audit did find. Verifying a
gate exists is not verifying a developer can satisfy it.

### Pass 2 — Security and abuse surface

Trust boundaries first: session cookie signing, BYOK credential storage and
encryption, CORS, what an unauthenticated caller can reach, and whether the
free-tier allowance can be walked around. Then injection surfaces: the clone
path (SSRF, argument injection), path parameters, and SQL construction.
Finally, dependency CVEs on both sides (`npm audit`, Python advisories) and
secret handling (`gitleaks`, tracked files).

### Pass 3 — Correctness of the request paths

Trace each API route end to end: metering reserve/settle on every exit,
streaming error contracts, generator cleanup on client disconnect, and the
ingestion job's failure handling. Look specifically for paths where an
exception leaves usage reserved or a task orphaned.

### Pass 4 — CLAUDE.md conformance

The project rules in §3 of `CLAUDE.md` are testable. Check each: `file:line`
grounding on claims, `Insight` shape enforcement, state-mutation discipline,
the six-tool ceiling, `recursion_limit=15`, the ≤2000-token prompt budget,
and the Lane C language constraints. Record which are enforced by a test and
which are enforced only by prose.

### Pass 5 — Dead code and drift

Find code with no consumer: endpoints no UI calls, exports nothing imports,
settings nothing reads, tests for deleted features. Then check whether
`docs/` still describes the code that exists — particularly `STATUS.md`,
which is the file people read first.

### Pass 6 — Test integrity

Coverage is 85%, but coverage is not confidence. Identify the modules with
the weakest coverage that sit on a user-facing path, tests that mock the
thing they claim to verify, and behaviours that only a slow/integration test
covers (and so nothing in CI covers at all).

### Pass 7 — Data, cost, and operations

The LLM spend path, retry and backoff budgets, the index recipe versioning
mechanism, migration reversibility, and what happens on a cold start with no
provider quota. This is where the project's known operational pain lives.

### Pass 8 — Frontend

Accessibility basics, error and empty states, the SSE client contract, state
handling in `repopilot-app.tsx` (1,338 lines in one component), and whether
the e2e specs still exercise the app as it is now built.

---

## Method notes

- **Evidence over inference.** Where a claim can be checked by running
  something, it is run, and the output is quoted in the report.
- **`main` is the subject.** Findings describe committed code, not local
  edits. The working tree stays clean for the duration.
- **No fixes during the audit.** Findings are recorded, not repaired — fixing
  as you go destroys the ability to say what state the project was in.
- **Known bugs are inputs, not findings.** Anything already recorded in
  `STATUS.md` under "Known-broken" is cross-referenced rather than re-reported,
  unless the audit finds it is worse than documented.

---

## Deliverable

`AUDIT_REPORT.md`, containing: a verdict per pass, a severity-ranked findings
table with `file:line` and evidence, and a shortlist of what to do first.
