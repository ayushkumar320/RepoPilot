---
trigger: always_on
description: RepoPilot project rules and engineering conventions. Tool-neutral mirror of CLAUDE.md for non-Claude AI assistants and Graphify indexing.
---

# RepoPilot — Project Rules (portable)

> This is the tool-neutral mirror of [`CLAUDE.md`](../../CLAUDE.md). `CLAUDE.md` is the single source of truth; keep this in sync with it. Editing one without the other is a bug.

## What this project is
RepoPilot ("Codebase Archaeologist") generates purpose-driven, multi-agent guided tours of unfamiliar Python codebases. The core bet: capture user pre-context (purpose + focus) **before** any analysis, then inject it into every downstream agent. Full design lives in `docs/`.

## Knowledge graph first
A Graphify graph at `graphify-out/` indexes code, docs, and these rule files. For any architecture/codebase question, when `graphify-out/graph.json` exists:
- `graphify query "<question>"` — scoped subgraph (start here).
- `graphify explain "<concept>"` — focused node + neighbors.
- `graphify path "<A>" "<B>"` — relationships.
- `graphify-out/GRAPH_REPORT.md` — broad review only.

Only read raw files after the graph has oriented you. This applies to subagents too.

## Graph maintenance (mandatory)
After any major change (new/moved/deleted files, multi-file refactor, new module/agent/tool, architecture/API/schema change, or any change touching >1 source file), run `graphify update .`. Then verify, and if `graph.json`/`manifest.json` changed, stage them and report. Never auto-commit or auto-push.

## Engineering conventions
- Truthful over fluent: every agent claim carries a `file:line` ref; unknowns are stated, never invented.
- No stat dumps: emit `Insight` objects (finding/because/so_what/goal_link), not raw metrics.
- State discipline: Pydantic v2; mutate only via node returns; append-only lists use `Annotated[..., add]`; `recursion_limit=15`.
- Six deterministic tools only; the AST builds the call graph, never the LLM.
- Lane C uses guarded language and always ends with `confirm_before_pr`.
- Prompt budget ≤ 2000 input tokens per node.
- Gates: `ruff`, `mypy --strict`, `pytest` (80% coverage), `pre-commit` (ruff + mypy + gitleaks), GitHub Actions.

## Authoring
Use unique, descriptive headings in Markdown — Graphify turns each heading into a graph node, so duplicates create ambiguous nodes.
