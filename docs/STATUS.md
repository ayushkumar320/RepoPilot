# Status — what is in flight, what is next, what is known-broken

The one page to read before picking work up. `README.md` says what RepoPilot
*is*; this says where it currently stands.

**Last updated:** 2026-08-08 · `main` at `93f1de4`

---

## Shipped recently

In dependency order. The graph view was estimated at 4.5–6.5 days
and took a fraction of that — but only because the three ingestion fixes above it
landed first. Built in the other order it would have shipped a view where two
thirds of neighbours had no source and no cross-module edges existed at all.

| Commit | What it did |
|---|---|
| `b9b39bc` | Parser sliced source by tree-sitter's **byte** offsets instead of indexing the decoded `str` with them. 71% of symbol names were corrupt; graph nodes resolving to a `file:line` went 34% → 91%. |
| `93e77fe` | Modules named from the package root rather than the repo-relative path, and relative imports resolved instead of dropped. Cross-module edges went 0 → 342 on this repo. |
| `764a111` | Re-indexing deleted and recreated the `repos` row, and `ON DELETE SET NULL` silently unpinned every saved tour. Now upserts. |
| `2368035` | `GET /repos/{repo_id}/graph/neighbours` — the read API behind the graph view. |
| `2715599` | The "Related code" panel: expand a claim into what it calls, what calls it, what it inherits, what imports it. |
| `adb2332` | This file. |
| `248b86b` | The e2e suite runs again — Playwright starts its own server with the sign-in gate cleared. |
| `4890ab5` | The showcase video's composition and plan layer versioned; its ~75 MB of renders and media ignored. |
| `6524263` | The `web` CI job runs `node --test` and Playwright, not just typecheck and build. 15 store tests + 9 e2e specs, all green; traces upload on failure. |
| `b3f43f5` | The graph resolver types instance attributes and locals from **declared** types, so `self._transport.handle_request(...)` and `t = self._pick(); t.handle(...)` are edges instead of drops. `INDEX_RECIPE_VERSION` → 5. |
| `12c8428` | "Related code" follows the claim you click instead of always anchoring on the exchange's first claim. |
| `b3661ac` | `defines` edges — a class or module links to the symbols nested inside it. Panel-only; the agent-facing loader whitelists the other kinds. `INDEX_RECIPE_VERSION` → 6. |
| `b3661ac` | Multi-hop: a neighbour expands into its own neighbours, three panels deep, one request per step. |
| _pending_ | The module dependency map. `GET /repos/{id}/graph/modules` rolls the symbol graph up to one node per module; the UI draws it with React Flow + dagre. |

## Measured state of the graph data

> **Stale as of `INDEX_RECIPE_VERSION = 5`.** The table below was measured at
> version 4. Version 5 adds call edges (see "Shipped recently") without renaming
> any symbol, so *Graph nodes*, *Symbols* and *In graph* still hold — but
> *With ≥1 neighbour* can only rise, and has not been re-measured against the
> database. Re-index and re-run the queries before quoting that column.

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

### 1. The quota-blocked batch — do these together when a provider answers

Three separate items, one blocker. Groq and Cerebras returned 429 throughout
2026-08-08, so none of them could be finished; all three want a working
provider and two of them want a re-index, so batch them.

- **Re-run summaries.** Every chunk indexed on 2026-08-08 carries a placeholder
  summary. Symbols, spans, embeddings and graph edges are all correct; only
  summaries are affected, and they feed retrieval quality. No re-index needed,
  just the summary pass.
- **Bench the resolver change.** `b3f43f5` adds call edges, which change
  `chunks.neighbor_symbols`, which the retrieval path reads. It plausibly moves
  ranking and has never been measured — it landed by direct push while the
  artifact gate still existed, and `d84e98d` has since removed that gate
  entirely. Nothing will catch this now, so it is a deliberate `make
  test-eval-sampled` run rather than something CI will remind anyone about.
- **Re-measure the graph table, and the map's own numbers.** STATUS previously
  claimed 379 cross-package edges on fastapi and 213 on flask. Rolling the graph
  up per module measures 81 unique module→module pairs on flask, so those two
  figures describe something else and should not be quoted until re-derived.
- **Re-measure the neighbour column.** Recipe version 5 means snapshots rebuild on
  next visit; the "With ≥1 neighbour" column above was measured at version 4 and
  can only have risen.

---

## Known-broken

| What | Detail |
|---|---|
| `test_httpx_indexing.py` | Both tests pass now — the resolver was fixed and the call-chain test retargeted. Still `slow`/`integration` and still deselected by CI, and both clone over the network, so a failure here is as likely to be a rate limit or a provider 429 as a regression. Run it by hand after any resolver change. |
| Placeholder summaries | See "next work" #2. |
| `b3f43f5` never benched | It changes `chunks.neighbor_symbols` and was never measured: it landed by direct push past the then-`pull_request`-only gate, which `d84e98d` has since removed. Not a defect — an unmeasured change on the retrieval path, and now nothing automated will notice. See "next work" #2. |

## Open product questions

**Should claim-to-code come back?** A claim states a `file:line`; nothing in the
app renders that file's source. The synchronized code panel that did was deleted
in `cf18b1b`, and "Related code" is not a replacement — it shows a claim's graph
*neighbours*, so reaching the claim's own source means finding it in a
neighbour list that may not contain it. `persona-ask.spec.ts` asserted the old
panel's output until this was resolved; it now asserts the reference text, which
is what actually ships. Nothing in the test suite is holding the question open
any more, so it lives here.

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
  on next visit.
