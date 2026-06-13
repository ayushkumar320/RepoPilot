---
description: Run the mandatory Graphify graph update, verify it, stage changed graph files, and emit the GRAPH STATUS block.
allowed-tools: Bash(graphify update .), Bash(git add graphify-out/graph.json graphify-out/manifest.json), Bash(git status:*), Bash(git diff:*)
---

Perform RepoPilot's mandatory graph-maintenance step (see `CLAUDE.md` §4).

1. Run `graphify update .` and confirm it succeeded. If it fails, stop and explain the failure plus a proposed fix — do not continue.
2. Run `git status --short graphify-out/` to see whether `graphify-out/graph.json` and/or `graphify-out/manifest.json` changed.
3. If either changed, stage **only** those two files: `git add graphify-out/graph.json graphify-out/manifest.json`. Do not commit or push.
4. Summarize the graph impact in one or two sentences (e.g. node/edge count delta, which files were re-indexed).
5. Emit exactly this block:

```
### GRAPH STATUS
- Graph updated:         Yes/No
- graph.json changed:    Yes/No
- manifest.json changed: Yes/No
- Graph files staged:    Yes/No
- Commit recommended:    Yes/No
```

6. If graph files changed, show (do not run) the commit command:

```bash
git add graphify-out/graph.json graphify-out/manifest.json
git commit -m "Update knowledge graph"
git push
```
