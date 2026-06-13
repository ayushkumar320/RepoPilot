## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists.
- Use `graphify path "<A>" "<B>"` for relationships.
- Use `graphify explain "<concept>"` for focused concepts.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- Follow the Graphify Workflow section below for all graph maintenance and update requirements.
# Graphify Workflow (Mandatory)

Graphify is part of this project's development workflow and Definition of Done.

## Knowledge Graph First

Before exploring the codebase:

1. Prefer Graphify over raw file searching.
2. Use:

   * `graphify query "<question>"` for architecture and feature discovery.
   * `graphify explain "<concept>"` for focused understanding.
   * `graphify path "<A>" "<B>"` for dependency and relationship analysis.
3. Only read source files after Graphify has provided sufficient context.

## Mandatory Graph Maintenance

After completing any major change, automatically run:

```bash
graphify update .
```

If update fails, explain the failure and propose a fix before proceeding.

## What Counts as a Major Change

Major changes include:

* Creating, deleting, or moving files
* Multi-file refactors
* Adding new modules, services, components, agents, workflows, or tools
* Architecture changes
* API changes
* Database schema changes
* Significant Claude-generated code modifications
* Any task affecting more than one source file

Minor formatting, comments, documentation-only edits, typo fixes, or very small single-file edits do not require a graph update.

## Verification Requirements

After running:

```bash
graphify update .
```

you must:

1. Verify the command succeeded.

2. Check whether:

   * `graphify-out/graph.json`
   * `graphify-out/manifest.json`

   changed.

3. Summarize the graph impact.

## Definition of Done

A major task is NOT complete until:
## Definition of Done

A major task is NOT complete until:

* Graphify has been updated successfully.
* Graph status has been verified.
* Any graph changes have been reported.
* If graphify-out/graph.json or graphify-out/manifest.json changes, stage them automatically and remind the user before finishing the task.

Before ending a task, always output:

### GRAPH STATUS

* Graph updated: Yes/No
* graph.json changed: Yes/No
* manifest.json changed: Yes/No
* Commit recommended: Yes/No

If graph files changed, provide:

```bash
git add graphify-out/graph.json graphify-out/manifest.json
git commit -m "Update knowledge graph"
git push
```

## Collaboration Rule

The committed Graphify graph is treated as a shared project artifact.

Whenever graph files change after major work, update and commit them so all collaborators receive the latest architectural knowledge graph when pulling the repository.

## Automatic Graph Staging

If `graphify update .` succeeds and either of the following files changes:

* `graphify-out/graph.json`
* `graphify-out/manifest.json`

then automatically:

```bash
git add graphify-out/graph.json graphify-out/manifest.json
```

and report:

### GRAPH STATUS

* Graph updated: Yes
* graph.json changed: Yes/No
* manifest.json changed: Yes/No
* Graph files staged: Yes

Then provide the exact commit command:

```bash
git commit -m "Update knowledge graph"
```

Do not automatically push to GitHub.

Do not automatically create commits unless explicitly requested by the user.

Graph staging is mandatory whenever graph files change after a successful Graphify update.
