# RepoPilot — Project Guide (Single Source of Truth)

This file is the **primary, always-loaded set of project rules** for RepoPilot. Every Claude Code prompt and every contributor should treat it as authoritative. Keep it concise: deep design detail lives in [`docs/`](docs/) and is navigable through the Graphify knowledge graph — this file is the index and the rules, not the encyclopedia.

> If a rule here conflicts with anything else, **this file wins.** When you change a convention, change it here first.

---

## 1. What this project is

**RepoPilot** (internally "Codebase Archaeologist") is a web app where a developer pastes a public GitHub repo URL and gets a **purpose-driven, guided onboarding tour** of an unfamiliar codebase, powered by a multi-agent AI system. Beachhead: junior devs and first-time OSS contributors on **Python** repos.

The distinguishing bet: **before analyzing anything, the system captures pre-context (purpose + focus) and adapts every downstream agent to it.** Product thesis and tech-stack rationale are archived under [`docs/archive/`](docs/archive/) — still true, no longer load-bearing for current work.

| Want to understand… | Read |
|---|---|
| Where the build is right now | [`docs/CURRENT_PHASE.md`](docs/CURRENT_PHASE.md) |
| The 7-phase retrieval-quality plan | [`docs/RAG_PLAN.md`](docs/RAG_PLAN.md) |
| The active phase's spec, gate, stop conditions | [`docs/rag/`](docs/rag/) (start at [`docs/rag/README.md`](docs/rag/README.md)) |
| Agent topology, state schema, tools, verifier | [`docs/03_ARCHITECTURE.md`](docs/03_ARCHITECTURE.md) |
| Historical: product thesis, tech-stack rationale | [`docs/archive/`](docs/archive/) |

**Prefer the Graphify graph over reading these raw** — see §3.

---

## 2. How project knowledge is organized

RepoPilot uses four layers of project knowledge. Know which one to edit.

| Layer | Location | Committed? | Purpose |
|---|---|---|---|
| **Project rules** | `CLAUDE.md` (this file) | ✅ Yes | Single source of truth. Auto-loaded by Claude Code every session. |
| **Portable rules** | [`.agents/rules/`](.agents/rules/) | ✅ Yes | The same rules in a tool-neutral format so other AI assistants (Cursor, Gemini, etc.) and Graphify pick them up. Keep in sync with this file. |
| **Harness config** | [`.claude/`](.claude/) | ✅ Yes | Claude Code-specific wiring: hooks, subagents, slash commands. See §5. |
| **Knowledge graph** | [`graphify-out/`](graphify-out/) | ✅ graph.json + manifest.json | The indexed, queryable map of the whole repo (code + docs + these rules). See §3. |
| **Per-user memory** | `~/.claude/…/memory/` | ❌ No (local) | Your private notes across sessions. Never holds shared project rules — those belong here. |

**Interaction model:** `CLAUDE.md` defines the rules → `.agents/rules/` mirrors them for other tools → `.claude/` enforces them via hooks/subagents/commands → Graphify indexes *all* of the above so the rules are themselves queryable. Per-user memory is personal and additive; it must never contradict this file.

---

## 3. Knowledge Graph first (Graphify)

This repo ships a Graphify knowledge graph at [`graphify-out/`](graphify-out/) covering source, docs, **and these rule files**. Use it before raw file searching.

**For any codebase or architecture question, when `graphify-out/graph.json` exists:**

- `graphify query "<question>"` — scoped subgraph for a question (start here).
- `graphify explain "<concept>"` — focused explanation of a node and its neighbors.
- `graphify path "<A>" "<B>"` — relationship / dependency path between two nodes.
- `graphify-out/GRAPH_REPORT.md` — read only for broad architecture review, or when query/path/explain don't surface enough.

Only read raw source files **after** Graphify has oriented you, or to modify/debug specific lines. A `PreToolUse` hook in [`.claude/settings.json`](.claude/settings.json) enforces this for `Read`/`Glob`/`grep`. **This rule applies to subagents too** — include it in every subagent prompt that explores code (the [`codebase-explorer`](.claude/agents/codebase-explorer.md) subagent already does).

---

## 4. Graph maintenance (mandatory)

After any **major change**, run:

```bash
graphify update .          # AST re-extraction, no API cost
```

This keeps the shared graph honest. Use the [`/graph-update`](.claude/commands/graph-update.md) slash command to run it and emit the status block in one step.

**Major change** (graph update required): creating/deleting/moving files; multi-file refactors; new modules, services, components, agents, workflows, or tools; architecture, API, or schema changes; any task touching more than one source file.

**Minor change** (no update needed): formatting, comments, docs-only typo fixes, or a single trivial one-file edit.

If `graphify update .` fails, explain the failure and propose a fix before proceeding.

After updating, you **must**:
1. Confirm the command succeeded.
2. Check whether `graphify-out/graph.json` and `graphify-out/manifest.json` changed.
3. If either changed, **stage them automatically** (`git add graphify-out/graph.json graphify-out/manifest.json`) and tell the user — do **not** auto-commit or auto-push.
4. Emit the GRAPH STATUS block (§7).

The committed graph is a **shared artifact**: collaborators pull it to get the latest architectural map without re-indexing. A merge driver (`graphify merge-driver`) union-merges `graph.json` on conflicts.

---

## 5. Claude Code harness (`.claude/`)

| Path | Purpose |
|---|---|
| [`.claude/settings.json`](.claude/settings.json) | Hooks enforcing "graph before grep/read"; permission allow-list for `graphify` commands so they don't prompt. |
| [`.claude/agents/codebase-explorer.md`](.claude/agents/codebase-explorer.md) | Read-only explorer subagent. Always consults Graphify first; use it to answer architecture questions without polluting the main context. |
| [`.claude/commands/graph-update.md`](.claude/commands/graph-update.md) | `/graph-update` — runs `graphify update .`, verifies, stages graph files, emits GRAPH STATUS. |

The portable mirror lives in [`.agents/`](.agents/): [`rules/`](.agents/rules/) (always-on rules for any AI tool) and [`workflows/`](.agents/workflows/) (the Graphify pipeline definition).

---

## 6. Engineering conventions

Enforced in code review and CI — not optional. Full rationale in [`docs/03_ARCHITECTURE.md`](docs/03_ARCHITECTURE.md) (and, historically, in [`docs/archive/02_TECH_STACK.md`](docs/archive/02_TECH_STACK.md)).

- **Truthful over fluent.** Every factual claim from an agent carries a `file:line` ref. Unknown → say so; never invent. Verifier rejections render as "flagged", never silently dropped.
- **No stat dumps.** Agents emit `Insight` objects (`finding` / `because` / `so_what` / `goal_link`), not raw metrics. Empty `so_what`/`goal_link` fails Pydantic validation by design.
- **State discipline.** Pydantic v2. No agent writes another agent's field; mutate only via node return values (`return {"foo": [item]}`, never `state.foo.append`). Append-only lists use `Annotated[..., add]`. `recursion_limit=15`.
- **Six deterministic tools, no more.** A new tool needs a justification starting with "the model cannot do this from existing tools because…". The LLM never computes the call graph — the AST does.
- **Lane C language constraints.** Suspicions use guarded language ("worth investigating", not "bug") and always end with a `confirm_before_pr` step. Enforced in prompt and post-checked by the Verifier.
- **Prompt budget ≤ 2000 input tokens per node.** Enforced in CI. Past that, chunk harder or split the agent.
- **Quality gates:** `ruff` (lint), `mypy --strict` (from day one), `pytest` with **80% coverage**, `pre-commit` (ruff + mypy + gitleaks), GitHub Actions CI. `gitleaks` blocks secret leaks.

---

## 7. Definition of Done

A major task is **not** complete until:

- [ ] Code/docs changes done and self-reviewed against §6.
- [ ] Tests/lints relevant to the change pass.
- [ ] `graphify update .` ran successfully (if the change was major — §4).
- [ ] Graph status verified and any `graph.json` / `manifest.json` changes staged.
- [ ] The GRAPH STATUS block below is emitted.

Always end a major task with:

```
### GRAPH STATUS
- Graph updated:        Yes/No
- graph.json changed:   Yes/No
- manifest.json changed: Yes/No
- Graph files staged:   Yes/No
- Commit recommended:   Yes/No
```

If graph files changed, give the user the exact commit command (do not run it unless asked):

```bash
git add graphify-out/graph.json graphify-out/manifest.json
git commit -m "Update knowledge graph"
git push
```

---

## 8. For contributors (human or AI)

1. **Read this file first**, then query the graph (`graphify query "<your question>"`) instead of grepping.
2. **Edit the right layer** (§2): shared rules → here + `.agents/rules/`; harness wiring → `.claude/`; design depth → `docs/`.
3. **Keep `CLAUDE.md` and `.agents/rules/project.md` in sync** — they say the same things for different tools.
4. **Run `/graph-update` (or `graphify update .`) after major work** and stage the graph so the next person pulls an accurate map.
5. **Use unique, descriptive section headings** in this file and in `docs/` — Graphify turns each heading into a graph node, so duplicate headings create ambiguous nodes.
