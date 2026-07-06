# Archive

Historical planning docs. **Reference only — not load-bearing for current work.**

The active doc set is:

- [`../CURRENT_PHASE.md`](../CURRENT_PHASE.md) — where the build is right now
- [`../RAG_PLAN.md`](../RAG_PLAN.md) — the 7-phase retrieval-quality plan
- [`../03_ARCHITECTURE.md`](../03_ARCHITECTURE.md) — agent topology, state, tools, verifier
- [`../rag/`](../rag/) — per-phase specs (canonical location)

## What lives here

- `01_PROBLEM_AND_SOLUTION.md` — product thesis. Still true (juniors/OSS contributors on Python repos, purpose-driven guided tours). Kept for context on why the RAG plan targets these metrics.
- `02_TECH_STACK.md` — tech choices + rationale. Still true; the `fastembed` addition in RAG Phase 4 is the only deviation and is justified inline in the phase spec.

Git history retains everything previously here (`00_CLAUDE_BUILD_GUIDE.md`, `04_BUILD_PLAN.md`, `05_PHASE_PROMPTS.md`, `06_FUTURE_IMPROVEMENTS.md`). Use `git log --all -- docs/` to explore.
