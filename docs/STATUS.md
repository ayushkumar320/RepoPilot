# Status — what is in flight, what is next, what is known-broken

The one page to read before picking work up. `README.md` says what RepoPilot
*is*; this says where it currently stands.

**Last updated:** 2026-08-08 · `main` at `2715599`

---

## Shipped recently

Five commits, listed in dependency order. The last two only work because of the
first three — the graph view was estimated at 4.5–6.5 days and took a fraction
of that, because by the time it was built the data underneath was correct.
Building the panel first would have produced a view where two thirds of
neighbours had no source and no cross-module edges existed at all.

| Commit | What it did |
|---|---|
| `b9b39bc` | Parser sliced source by tree-sitter's **byte** offsets instead of indexing the decoded `str` with them. 71% of symbol names were corrupt; graph nodes resolving to a `file:line` went 34% → 91%. |
| `93e77fe` | Modules named from the package root rather than the repo-relative path, and relative imports resolved instead of dropped. Cross-module edges went 0 → 342 on this repo. |
| `764a111` | Re-indexing deleted and recreated the `repos` row, and `ON DELETE SET NULL` silently unpinned every saved tour. Now upserts. |
| `2368035` | `GET /repos/{repo_id}/graph/neighbours` — the read API behind the graph view. |
| `2715599` | The "Related code" panel: expand a claim into what it calls, what calls it, what it inherits, what imports it. |

## Measured state of the graph data

All eight indexed repos are on `INDEX_RECIPE_VERSION = 4` with **zero** symbol
corruption. Re-measure with the queries in this section after any ingestion
change; every number here was measured, not estimated.

| Repo | Graph nodes | Symbols | In graph | With ≥1 neighbour |
|---|---|---|---|---|
| tiangolo/fastapi | 7,470 | 5,208 | 100% | 67% |
| pallets/flask | 2,106 | 889 | 100% | 70% |
| encode/httpx | 1,582 | 1,132 | 100% | 86% |
| psf/requests | 1,148 | 687 | 100% | 86% |
| encode/databases | 523 | 347 | 100% | 72% |
| iprashantraj/AI-Research-Assistant | 138 | 66 | 100% | 100% |
| iprashantraj/leetcode-tracker | **0** | — | — | — |
| iprashantraj/mcp-discord-bridge | **0** | — | — | — |

Two things this table settles:

- **The graph view has content.** Every symbol a claim can cite is a graph node,
  and 67–100% have neighbours to display. The panel appears essentially always
  and is useful roughly three times in four.
- **A quarter of indexed repos produce no graph at all**, because the AST graph
  is Python-only. The panel already says so in words rather than showing an
  empty list, but if most real users paste non-Python repos this is a product
  question, not a UI one.

---

## Next work, in the order it should be done

### 1. Make the frontend tests actually run — ~half a day

Nothing currently checks the visual half of the app. Playwright, the Lighthouse
audit and `node --test` are all **absent from CI** (`.github/workflows/ci.yml`
runs only typecheck and build for `web`), and the suite cannot run locally
either: `apps/web/.env.local` sets `AUTH_GOOGLE_ID` / `AUTH_GITHUB_ID`, so
`authEnabled` gates the app behind sign-in and every spec times out waiting for
"Public GitHub URL".

That is true of `persona-ask.spec.ts` today, not just the new specs. The graph
panel's three specs pass, but only against a dev server started with the auth
variables cleared — which is how they were verified.

Do this before more UI work: the newest feature sits in the one part of the
codebase with no safety net.

### 2. The module dependency map — 1–2 weeks

The drawn picture, extending the same endpoint the panel already uses. Nodes are
modules, edges are real intra-repo imports, server-scoped to a readable count
with an honest `truncated` flag, click a node to reach its source.

This was impossible before `93e77fe`: a module-level rollup produced **zero**
cross-module edges on any src-layout repo. It now yields 379 cross-package edges
on fastapi and 213 on flask.

Do not ship a whole-repo symbol-level node-link view. fastapi is 7,470 nodes with
a median degree of 1–2 — sparse dust rather than structure, and no renderer fixes
that.

### 3. Re-run summaries when provider quota returns — minutes of work

Every chunk indexed on 2026-08-08 carries a placeholder summary: Groq and
Cerebras returned 429 throughout. Symbols, spans, embeddings and graph edges are
all correct; only summaries are affected, and they feed retrieval quality. No
re-index needed, just the summary pass.

---

## Known-broken

| What | Detail |
|---|---|
| `test_httpx_indexing.py` | Both tests fail on `main`, before and after recent changes. The call-chain test wants `Client.send → HTTPTransport.handle_request`, but the resolver does no instance-attribute type inference so `self._transport.handle_request(...)` cannot resolve. CI deselects it, which is why it went unnoticed. Fix the resolver, retarget the test, or `xfail` it — a silently-failing deselected test is the worst of the three. |
| Frontend tests in CI | See "next work" #1. |
| e2e suite locally | Blocked by the auth gate. See "next work" #1. |
| Placeholder summaries | See "next work" #3. |

## Conventions worth not relearning

- **A graph read API is not a seventh agent tool.** `services.py` already calls
  `graph_query` directly with no model involved, and `tools/__init__.py` states
  that living in `tools/` does not make something an agent tool. Keep this code
  in `apps/api/`, which also keeps it clear of the `retrieval-eval-artifact-gate`
  in `ci.yml`, which fails any PR touching `packages/agents/src/repopilot_agents/(tools|qa|rerank)/`
  or `packages/ingestion/` without a fresh RAG bench artifact.
- **`resolved` and `external` are different things.** A symbol can be the repo's
  own and still have no chunk (a nested def the chunker skipped). Collapsing them
  means either hiding the user's own code or inventing a source for it, and
  `CLAUDE.md` forbids the latter outright.
- **`nx.DiGraph` is not subscriptable at runtime.** A module without
  `from __future__ import annotations` passes `mypy --strict` and 500s on the
  first request.
- **`apps/web/src/lib/api/generated.ts` is hand-written** despite the name. There
  is no OpenAPI codegen; a new endpoint means editing it by hand.
- **Changing what is stored at rest means bumping `INDEX_RECIPE_VERSION`**
  (`packages/ingestion/src/repopilot_ingestion/db.py`). Snapshots below it rebuild
  on next visit.
