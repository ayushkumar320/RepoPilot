# Status — what is in flight, what is next, what is known-broken

The one page to read before picking work up. `README.md` says what RepoPilot
*is*; this says where it currently stands.

**Last updated:** 2026-08-11 · `main` at `588102e`

---

## Scope decision — 2026-08-11: RepoPilot is not publicly exposed

The audit ([`AUDIT_REPORT.md`](AUDIT_REPORT.md), findings 2–5) found four ways
the platform's provider key can be spent without limit. All four are **accepted
as they stand**, because this deployment is private — the people who can reach
the API are the people who pay for it, so a spend ceiling would cost more to
build than it protects.

What was accepted, and what each would cost to close:

| # | The gap | If it ever needs closing |
|---|---|---|
| 2 | The free-repository allowance is keyed on a cookie the caller controls, so clearing it grants another free repository | Bind the allowance to the signed-in account; `product_accounts` already carries the identity |
| 3 | `reserve_question` passes `free_limit=None` — questions are unmetered | Pass a limit from settings; the counting code already exists |
| 4 | `/intent` is an unauthenticated model call with no rate limit | A per-session sliding window in a FastAPI dependency, ~15 lines |
| 5 | A repository is cloned in full before `ingestion_max_repo_loc` applies | Check repository size via the GitHub API before cloning, or `git clone --filter=blob:none` |

**This decision expires the moment the API is reachable by anyone who is not
paying for it.** That includes a public demo, a shared staging URL, and a
deployment behind a link that is "unlisted" rather than authenticated. Before
any of those, close 3 and 4 at minimum — they are the two that need no account
and no repository to exploit.

One caveat worth separating from the rest: **finding 5 has an accident mode**,
not only an abuse mode. A trusted user who pastes a large monorepo by mistake
still downloads all of it before anything rejects the size. If disk pressure
ever shows up on the host, close 5 first regardless of exposure.

---

## Scope decision — 2026-08-10: no further graph or map work

The "Related code" panel, the module dependency map and both read endpoints
**remain in the codebase and still ship.** Nothing was removed. What stopped is
further investment: no symbol-level node-link view, no map iteration, no new
graph surfaces.

**Open question, and it needs an answer before anyone touches this area.** If
"not implementing" was meant as *remove*, that is real work, not a doc edit —
`apps/web/src/components/graph-neighbours.tsx` and `module-map.tsx`,
`GET /repos/{id}/graph/neighbours` and `/graph/modules`, their services, models
and specs, plus the `defines` edges added at `INDEX_RECIPE_VERSION = 6`. Until
that is decided, treat the feature as **frozen, not deprecated**, and leave it
working.

The 60s promo no longer depicts either surface (`4a92fac`, `27fe7c9`): frame 3
shows spans resolving out of source, frame 4 shows findings reordering per
persona. `BRIEF.md` records the constraint so a later pass does not reintroduce
it. One loose end — narration line 3 still *says* "call graph"; re-synthesizing
that single line needs HeyGen quota and takes about a minute.


---

## Shipped today

One session, in the order it happened. It began with "put the frontend tests in
CI" and ended with the graph feature having no known gaps — because turning the
checks on is what made the rest safe to do quickly.

| Commit | What it did |
|---|---|
| `6524263` | The `web` CI job runs `node --test` and Playwright, not just typecheck and build. Nothing had been checking the visual half of the app on any change. Traces upload on failure. |
| `b3f43f5` | The resolver types instance attributes and locals from **declared** types, so `self._transport.handle_request(...)` and `t = self._pick(); t.handle(...)` are edges rather than drops. +66 call edges on httpx, +14 on flask, zero invented symbols. `INDEX_RECIPE_VERSION` → 5. |
| `12c8428` | "Related code" follows the claim you click. It had only ever anchored on the exchange's first claim, so clicking any other row restyled it and showed the wrong neighbours. |
| `b3661ac` | `defines` edges — a class or module links to the symbols nested inside it, so a class can list its own methods. 1,564 new edges on flask. Panel-only: `tools/_adjacency.py` whitelists the other kinds, so fan-in, hubs and entry points are untouched. `INDEX_RECIPE_VERSION` → 6. Same commit adds multi-hop: a neighbour expands into its own neighbours, three panels deep, one request per step. |
| `05320a4` | The module dependency map. `GET /repos/{id}/graph/modules` rolls the symbol graph up to one node per module; the UI draws it with React Flow + dagre. No re-index and no recipe bump — `imports` edges already start at a module. |
| `4cab1c4` | Non-Python files kept off the module map. `README.md` and `requirements.txt` are stored with `kind = 'module'`, so they were drawn as boxes that can never have a dependency. Found by running the app, not by a test. |
| `653235c` | Snapshots built by an older recipe are no longer served. `_latest_repo_snapshot_id` had no `index_version` filter, so a repo indexed at recipe 3 stayed at recipe 3 through two bumps — meaning **no shipped ingestion work had reached any indexed repository**. Each existing repo now rebuilds once, on next visit. |
| `62b9e58` | Claim-to-code. A claim expands inline to the source it cites, with real file line numbers. Settles the product question carried since `cf18b1b`: the capability came back, the third column it used to live in did not. |

Two of these were found only by running the app against the real database.
Neither could have been caught by the specs, which mock the API: one needed a
repository containing a `README.md`, the other needed a snapshot older than the
current recipe. **Run it, at least once, after shipping ingestion work.**

Two things this session settled that are worth not relitigating:

- **The graph feature has no known gaps** as built. Every item from the audit —
  dropped `self.x.y()` calls, the panel ignoring the clicked claim, classes not
  linked to their methods, one-hop-only, no module map, no claim-to-code — is
  shipped. It is now frozen; see the scope decision above.
- **CI now covers the frontend**, so the newest work is no longer the part with
  no safety net. 15 store tests and 15 e2e specs run on every push to `main` and
  every pull request.

## Shipped earlier (the graph foundation)

In dependency order. The graph view was estimated at 4.5–6.5 days and took a
fraction of that — but only because the three ingestion fixes above it landed
first. Built in the other order it would have shipped a view where two thirds of
neighbours had no source and no cross-module edges existed at all.

| Commit | What it did |
|---|---|
| `b9b39bc` | Parser sliced source by tree-sitter's **byte** offsets instead of indexing the decoded `str` with them. 71% of symbol names were corrupt; graph nodes resolving to a `file:line` went 34% → 91%. |
| `93e77fe` | Modules named from the package root rather than the repo-relative path, and relative imports resolved instead of dropped. |
| `764a111` | Re-indexing deleted and recreated the `repos` row, and `ON DELETE SET NULL` silently unpinned every saved tour. Now upserts. |
| `2368035` | `GET /repos/{repo_id}/graph/neighbours` — the read API behind the graph view. |
| `2715599` | The "Related code" panel: expand a claim into what it calls, what calls it, what it inherits, what imports it. |
| `adb2332` | This file. |
| `248b86b` | The e2e suite runs again — Playwright starts its own server with the sign-in gate cleared. |
| `4890ab5` | The showcase video's composition and plan layer versioned; its ~75 MB of renders and media ignored. |

## Measured state of the graph data

> **Stale as of `INDEX_RECIPE_VERSION = 6`.** The table below was measured at
> version 4. Versions 5 and 6 both add edges without renaming any symbol, so
> *Graph nodes*, *Symbols* and *In graph* still hold — but *With ≥1 neighbour*
> can only have risen, and has not been re-measured against the database.
> Re-index and re-run the queries before quoting that column.

All eight indexed repos were on `INDEX_RECIPE_VERSION = 4` with **zero** symbol
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

Rolled up per module — the map's own scale, measured on clones rather than on
the database:

| Repo | Module nodes | Intra-repo module→module edges |
|---|---|---|
| pallets/flask | 83 | 81 |
| encode/httpx | 60 | 72 |

Two things the symbol table settles:

- **The graph view has content.** Every symbol a claim can cite is a graph node,
  and 67–100% have neighbours to display. The panel appears essentially always
  and is useful roughly three times in four.
- **A quarter of indexed repos produce no graph at all**, because the AST graph
  is Python-only. The panel already says so in words rather than showing an
  empty list, but if most real users paste non-Python repos this is a product
  question, not a UI one.

---

## Next work, in the order it should be done

### 1. The quota-blocked batch — do these together when a provider answers

Three items, one blocker. Groq and Cerebras returned 429 throughout 2026-08-08,
so none could be finished; all three want a working provider and two want a
re-index, so batch them.

- **Re-run summaries.** `make resummarise-check` reports what is outstanding;
  `make resummarise REPO=<id>` (or `REPO=--all`) repairs it. Measured
  2026-08-08: **9,395 placeholder summaries across all eight snapshots**, fastapi
  alone holding 6,288 — far more than "the chunks indexed that day". No
  re-index is needed and none is safe to skip lightly either: `embedding_text`
  reads `content`/`enriched_text` and never `summary`, so rewriting one changes
  what the answer prompt is told without moving the chunk in vector space.

  The pass is incremental and safe to repeat. `summarise_chunks` opens its
  circuit on the first provider error and falls back for everything after it,
  so a quota-limited run repairs a prefix and leaves the rest — a proven run
  went 28 -> 13 repaired, then a second attempt examined only the remaining 15.
  It exits non-zero when it repaired nothing, so a retry loop can tell a
  stalled sweep from a finished one.
- **Bench `b3f43f5`.** It adds call edges, which change
  `chunks.neighbor_symbols`, which the retrieval path reads. It plausibly moves
  ranking and has never been measured — it landed by direct push while the
  artifact gate still existed, and `d84e98d` has since removed that gate
  entirely. Nothing automated will catch this now, so it is a deliberate
  `make test-eval-sampled` run. **Only this one needs it**: recipe 6's `defines`
  edges never reach retrieval, because `neighbor_symbols` comes from the parser
  rather than from adjacency, and the agent-facing loader does not read them.
- **Re-measure, and drop two figures that do not survive checking.** Re-index at
  recipe 6, then re-run the queries for the *With ≥1 neighbour* column, which
  was measured at version 4 and can only have risen. While there: this file used
  to claim 379 cross-package edges on fastapi and 213 on flask. Rolled up per
  module the map measures 81 unique module→module pairs on flask, so those two
  numbers describe something else and should not be quoted until re-derived.

---

## Known-broken

| What | Detail |
|---|---|
| `test_httpx_indexing.py` | Both tests pass now — the resolver was fixed and the call-chain test retargeted. Still `slow`/`integration` and still deselected by CI, and both clone over the network, so a failure here is as likely to be a rate limit or a provider 429 as a regression. Run it by hand after any resolver change. |
| Placeholder summaries | See "next work" #1. |
| `b3f43f5` never benched | It changes `chunks.neighbor_symbols` and was never measured: it landed by direct push past the then-`pull_request`-only gate, which `d84e98d` has since removed. Not a defect — an unmeasured change on the retrieval path, and now nothing automated will notice. See "next work" #1. |

## Conventions worth not relearning

- **A graph read API is not a seventh agent tool.** `services.py` already calls
  `graph_query` directly with no model involved, and `tools/__init__.py` states
  that living in `tools/` does not make something an agent tool. Keep this code
  in `apps/api/`. (This also used to keep it clear of the
  `retrieval-eval-artifact-gate`, removed in `d84e98d` — the separation is still
  right on its own merits, but it no longer has a CI job enforcing it.)
- **The resolver types from declarations, never from guesses.** An attribute or
  local gets a type from an annotation, a constructor call, or a declared return
  — and the resulting `owner.member` is emitted *only* if some file defines it.
  Both guards exist because the obvious shortcuts each invent a symbol: an
  untyped `self.x = build()` invents a class, and a typed receiver whose method
  comes from a third-party base class invents a method. Related: a call through
  a base-class-typed variable resolves to the **base**, not to whichever subclass
  runs. `Client.send` reaches `BaseTransport.handle_request`, not
  `HTTPTransport.handle_request`; the concrete class is a runtime fact and the
  inherits edge is how the two connect. Do not "fix" that by following
  subclasses — it is the difference between a fact and a plausible story.
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
  on next visit — but that is only true because `653235c` made it true. Three
  separate queries decide whether a snapshot counts as usable
  (`repo_already_indexed`, `known_head_sha`, `_latest_repo_snapshot_id`), and
  they must all filter on the version. One of them not doing so silently
  disabled the whole mechanism for two releases.
