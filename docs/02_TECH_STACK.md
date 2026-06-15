# 02 — Tech Stack

Every choice below is paired with **why** and **what we rejected**. The constraint is hard: the whole stack must be runnable on a developer laptop with free-tier external services. No paid APIs, no managed databases, no vendor lock-in we cannot escape in an afternoon.

---

## LLM layer

| Need | Choice | Why | Rejected |
|---|---|---|---|
| Judgment-heavy generation (Cartographer, Issue Triage, Teacher, Q&A) | **Groq `llama-3.3-70b-versatile`** | Free tier, fast inference (~250 tok/s), strong reasoning on long-context code questions. | OpenAI GPT-4o-mini (not free), Together.ai (slower free tier), Anthropic Claude Haiku via Bedrock (no free tier). |
| Trace and explain code paths (Flow Tracer, Q&A fallback) | **Groq `qwen3-32b`** | Excellent at structured reasoning over code traces. Spreads load off the 70B quota. | Mixtral-8x7B (deprecated on Groq), DeepSeek-Coder-V2 (not on Groq). |
| Cheap, high-volume work (Intent Profiler, Code Health, chunk summaries) | **Groq `llama-3.1-8b-instant`** | ≈ 14.4k RPD — by far the highest free quota. Sufficient for free-text intent profiling, classification, and structured summary tasks. Burns the cheap tier for the hot paths so the 70B isn't starved. | Groq Gemma2-9b (smaller context), local Ollama Llama3-8B (slower wall-clock on CPU laptops). |
| Verification (highest call volume of any agent) | **Ollama `qwen2.5-coder:7b`** (local) | Runs on the developer's machine. No quota at all. Specifically tuned for code grounding tasks. Removes the single biggest risk to rate-limit survival — verifier traffic. | Groq for verifier (would burn 70B quota in minutes), GPT-3.5 (not free). |
| Embeddings | **Ollama `nomic-embed-text`** (local) | 768-dim, fast on CPU, no API quota. Quality is competitive with OpenAI `text-embedding-3-small` on code search benchmarks. | OpenAI embeddings (not free), Cohere embed-v3 (paid), bge-small (lower quality on code). |
| Provider abstraction | **Custom `LLMProvider`** with Groq → Cerebras → Ollama fallback, SQLite response cache, exponential backoff on 429. | Agents never import `groq`/`ollama` directly. One place to swap models, one place to cache, one place to handle 429s. Provider-level fallback means a single quota hit doesn't kill the user's session. | Direct SDK use (scattered fallback logic), LangChain LLM wrappers (opinionated and heavy), LiteLLM (additional dep when one file does the job). |

### Per-agent model map

| Agent | Model | Rationale |
|---|---|---|
| Intent Profiler | `llama-3.1-8b-instant` | Fires on every request. Must be cheap. |
| Cartographer | `llama-3.3-70b-versatile` | High-stakes mental-model construction. |
| Flow Tracer | `qwen3-32b` | Path reasoning. Spreads load off 70B. |
| Teacher | `llama-3.3-70b-versatile` | Narrative quality matters most here. |
| Issue Triage (Lane A) | `llama-3.3-70b-versatile` | Approachability judgment is the hardest call. |
| Code Health (Lane B) | `llama-3.1-8b-instant` | LLM only ranks deterministic signals — cheap is fine. |
| Suspicion (Lane C) | `qwen3-32b` | Needs careful epistemic language. |
| Q&A primary | `llama-3.3-70b-versatile` | User-facing quality. |
| Q&A fallback | `qwen3-32b` | When 70B is rate-limited. |
| Verifier | `qwen2.5-coder:7b` (Ollama) | Highest call volume — must be local. |
| Chunk summaries (ingestion) | `llama-3.1-8b-instant` | Batch, cached, low-stakes. |

### Per-tour token budget (rough)

Estimated for a moderately complex `understand`-shaped tour on a 50kLOC repo. Numbers are upper-bound input + output combined per capability.

| Capability | Model | Input tok | Output tok | Notes |
|---|---|---|---|---|
| Intent Profiler | 8B | ~400 | ~150 | Per session (not per tour). |
| Cartographer | 70B | ~1.5k | ~1.5k | Reads graph_query results + chunk summaries. |
| Flow Tracer | qwen3-32b | ~2.0k | ~1.5k | Reads traversal path + chunk content. |
| Teacher | 70B | ~3.0k | ~2.0k | Reads all upstream Insight objects. |
| Verifier (per claim) | qwen2.5-coder:7b (local) | ~500 | ~80 | × ~30 claims = ~17k tok, but local, so zero Groq cost. |
| Q&A (if used) | 70B | ~2.5k | ~1.0k | Per question. |

**70B-specific math.** A single Learn-shaped tour costs **~8k tokens** on `llama-3.3-70b-versatile` (Cartographer + Teacher + 1 Q&A). Groq's 70B free tier is **6k TPM**, so one tour comfortably fits a minute. **Concurrency limit: 1 active 70B-heavy tour per Groq key.** A second concurrent tour triggers the 429-backoff-then-fallback chain. The `MAX_TOURS_PER_IP_PER_HOUR` rate-limit (default 5) protects against single-IP abuse; a server-wide semaphore on 70B calls protects against multi-IP contention.

---

### Groq free-tier survival strategy

Groq limits are **per model**, not per account. As of writing: ≈ 30 RPM / 6k TPM / 1k RPD on `llama-3.3-70b-versatile`; `llama-3.1-8b-instant` gets ≈ 14.4k RPD. The architecture exploits this:

1. **Spread across three models** so any one quota hit only affects part of the system.
2. **Verifier is local Ollama.** This is the biggest single saving — verifying every claim against every chunk on Groq would blow the 70B quota in minutes.
3. **SQLite response cache.** Identical prompts return cached responses. Cuts repeat-query cost to zero, and protects against retry storms.
4. **Exponential backoff with jitter** on 429, capped at 5 attempts.
5. **Provider-level fallback chain.** Groq → Cerebras (free tier, similar models) → Ollama (local, slower but always available). A 429 storm degrades gracefully instead of failing the session.
6. **Prompt budget per node ≤ 2000 input tokens.** Enforced in CI. Past that, the architecture is wrong — chunk more aggressively or split the agent.

---

## Orchestration layer

| Need | Choice | Why | Rejected |
|---|---|---|---|
| Multi-agent graph | **LangGraph** with typed `StateGraph`, conditional edges, Postgres checkpointing | Native typed-state model fits our Pydantic-first design. Conditional edges are the natural primitive for "verifier passed / failed / retry". Postgres checkpointing makes kill/resume free. | LangChain agents (loose, untyped), CrewAI (role-prompt-based, no typed state), AutoGen (chat-paradigm, hard to verify), raw asyncio (we'd reimplement half of LangGraph). |
| Observability | **LangSmith** for tracing + eval datasets | Native LangGraph integration. Free tier sufficient for solo dev. Eval datasets are the right abstraction for our quality gates. | OpenTelemetry + custom traces (more work, weaker eval story), Weights & Biases (overkill for v1). |

---

## Code intelligence layer (deterministic, NO LLM)

This is the layer where principle 1 (truthful) is actually purchased. **An LLM does not invent the call graph. The AST parser produces it.** The LLM only ranks, explains, and narrates what the deterministic layer has discovered.

| Need | Choice | Why | Rejected |
|---|---|---|---|
| Structural chunking | **tree-sitter + tree-sitter-python** | Chunks land on function/class boundaries — not arbitrary 1000-char windows. Citations point at semantically meaningful spans. | Naive line-window chunking (citations point mid-function), LangChain `PythonCodeTextSplitter` (less precise on classes). |
| Dependency graph | **NetworkX** with call/import/inheritance edges parsed from the AST | In-memory graph, fast traversal, well-tested algorithms. Entry-point detection = `in_degree == 0`. Hub detection = top fan-in. Layer detection = community detection (Louvain). | Graphviz (visualization-only), Neo4j (operational overhead in v1), asking an LLM to build the graph (would be slow, expensive, and unreliable — the whole point of this layer is that it is exact). |
| Git history | **GitPython** | Used for `git blame` archaeology and churn × complexity in Lane B. | `subprocess` calls to `git` (slower, harder to test). |
| GitHub API | **PyGithub** | Used for Lane A issue triage. Auth via PAT (read-only). | Raw REST via `httpx` (we'd reimplement pagination, rate-limit handling). |

---

## Storage layer

| Need | Choice | Why | Rejected |
|---|---|---|---|
| Chunks, vectors, graph adjacency JSON, LangGraph checkpoints | **Postgres + pgvector** | One database for the whole hot path. pgvector is mature for our scale (≤ 50 kLOC × few-hundred-token chunks). Graph adjacency stored as JSONB sidecars on chunk rows. | Qdrant/Weaviate (separate service to run), Chroma (no good story for relational state). |
| Background indexing queue | **Redis + arq** | arq is the lightest async Python job queue. Tour generation must not block on cloning + indexing a 50 kLOC repo. | Celery (heavy, sync-friendly), RQ (sync), Dramatiq (smaller community), raw `asyncio.create_task` (no persistence across restarts). |
| LLM response cache | **SQLite** | Lives next to the worker. Single file, no admin. Cache key = SHA256(model + prompt). | Redis for cache (works fine but Redis is already busy with arq), in-memory (lost on restart). |

---

## Backend layer

| Need | Choice | Why | Rejected |
|---|---|---|---|
| HTTP API | **FastAPI** (async) | Native async, OpenAPI built in, Pydantic models are first-class — same models we use for state. | Flask (sync), Starlette (we'd add the FastAPI conveniences ourselves). |
| Server-Sent Events | **sse-starlette** | Drop-in SSE for FastAPI. Token streaming is the demo. | WebSockets (overkill, harder to reverse-proxy), polling (not a streaming demo). |

---

## Frontend layer

| Need | Choice | Why | Rejected |
|---|---|---|---|
| Framework | **Next.js 15** (App Router, RSC) | The streaming UI is the product. Next.js streams well, hosts cheaply, deploys to Vercel free tier. | Vite + React (would build streaming plumbing ourselves), Remix (smaller ecosystem). |
| Language | **TypeScript** | Types match the Pydantic state schema. Generated client from FastAPI's OpenAPI is type-safe end-to-end. | JavaScript (we lose the schema match). |
| Styling | **Tailwind v4** | Fast iteration on a focused UI. v4 is the current default. | CSS modules (slower iteration on a small surface). |
| Syntax highlighting | **shiki** | The synchronized code viewer is the key demo moment — click a claim, watch shiki highlight the exact lines. shiki gives us VS Code-quality rendering. | Prism (lower fidelity), highlight.js (looks dated), Monaco (heavy editor we don't need). |
| Diagrams | **mermaid** | The Teacher emits mermaid; the client renders. No round-trip image generation. | Excalidraw (not LLM-emit-friendly), PlantUML (server dep). |
| State | **Zustand** | Minimal, no boilerplate, plays well with React 19 + RSC. | Redux Toolkit (heavy for this surface), Jotai (atom-first model doesn't match our use case). |

---

## Quality layer

| Need | Choice | Why | Rejected |
|---|---|---|---|
| Python lint | **ruff** | Fast, all-in-one. | Flake8 + plugins (slower, scattered config). |
| Python types | **mypy `--strict`** | Strict from day 1. Loosening later is easy; tightening later is impossible. | pyright (works fine, but mypy has better LangChain/LangGraph plugin stories). |
| Tests | **pytest + pytest-asyncio + pytest-cov** | Standard. 80% coverage gate. | unittest (verbose, less expressive). |
| Pre-commit | **pre-commit** with ruff, mypy, gitleaks hooks | Bad code never reaches CI. | Husky-style git hooks (Python world standard is pre-commit). |
| CI | **GitHub Actions** | Free for public repos. | CircleCI / GitLab CI (no equivalent free tier for our needs). |
| Local services | **Docker Compose** (postgres+pgvector, redis, ollama) | One-command bringup is part of the demo. | Native installs per dev (onboarding hostile). |
| Secret scanning | **gitleaks** in pre-commit and CI | Catches a `.env` slip before it lands on origin. | TruffleHog (heavier), manual review (humans are not a security control). |

---

## ASCII full-stack diagram

```
                          ┌─────────────────────────────────────────────────────┐
                          │                       BROWSER                       │
                          │  Next.js 15 + TS + Tailwind v4                      │
                          │  ┌──────────────────┐   ┌──────────────────────┐    │
                          │  │ Tour stream view │◄──┤  shiki code viewer    │   │
                          │  │ (SSE tokens,     │   │  (synchronized        │   │
                          │  │  mermaid)        │──►│   highlighting)       │   │
                          │  └──────────────────┘   └──────────────────────┘    │
                          └────────────────────────┬────────────────────────────┘
                                                   │  SSE / HTTP
                          ┌────────────────────────▼────────────────────────────┐
                          │                  FastAPI (async)                    │
                          │                                                     │
                          │  POST /repos                  ─► arq job (clone+idx)│
                          │  GET  /repos/{id}/status                            │
                          │  POST /tours                                        │
                          │  GET  /tours/{id}/stream      ─► sse-starlette      │
                          │  POST /tours/{id}/ask                               │
                          └────────────────────────┬────────────────────────────┘
                                                   │
            ┌──────────────────────────────────────┼─────────────────────────────────────────┐
            │                                      │                                         │
            ▼                                      ▼                                         ▼
   ┌───────────────────┐                ┌─────────────────────┐                 ┌────────────────────────┐
   │   LangGraph       │                │  Tools (det.)       │                 │  LLMProvider           │
   │   StateGraph      │                │  vector_search      │                 │  Groq → Cerebras → Ollama
   │  ─ Intent Profiler│                │  graph_traverse     │                 │  SQLite cache          │
   │  ─ LEARN subgraph │ ──tool calls──►│  graph_query        │ ◄──reads from── │  Backoff on 429        │
   │  ─ CONTRIBUTE sub │                │  graph_metrics      │                 │  Per-model quota mgmt  │
   │  ─ Q&A subgraph   │                │  read_chunks        │                 └────────────┬───────────┘
   │  ─ Verifier loop  │                │  github_issues      │                              │
   └────────┬──────────┘                └──────────┬──────────┘                              │
            │ checkpoint                           │                                         │
            ▼                                      ▼                                         ▼
   ┌──────────────────────────────────────────────────────────────────────────────────────────────┐
   │                            Postgres + pgvector                                               │
   │  chunks (with line spans, structural type)                                                   │
   │  embeddings (nomic-embed-text, 768-d)                                                        │
   │  graph_adjacency JSONB                                                                       │
   │  langgraph_checkpoints                                                                       │
   └──────────────────────────────────────────────────────────────────────────────────────────────┘

   ┌───────────────────┐   ┌──────────────────────────┐   ┌───────────────────────────────────────┐
   │   Redis + arq     │   │   Ollama (local)         │   │   Groq API (free tier)                │
   │   indexing jobs   │   │   qwen2.5-coder:7b (verif)│   │   llama-3.3-70b / qwen3-32b /         │
   └───────────────────┘   │   nomic-embed-text (emb) │   │   llama-3.1-8b-instant                │
                           └──────────────────────────┘   └───────────────────────────────────────┘
                                                       
   ┌──────────────────────────┐    ┌──────────────────────────────────┐
   │  tree-sitter (parse)     │    │   LangSmith (tracing + evals)    │
   │  NetworkX  (graph)       │    │   ─ traces every node             │
   │  GitPython (history)     │    │   ─ eval datasets per phase gate │
   │  PyGithub  (issues)      │    └──────────────────────────────────┘
   └──────────────────────────┘
```

The shape of the system reads top-to-bottom: browser streams tokens from FastAPI, which drives LangGraph over typed state, which calls deterministic tools that read from Postgres and a graph parsed by tree-sitter / NetworkX, with the LLMProvider hiding Groq/Ollama details and the Verifier running entirely on local Ollama to protect the Groq quota.
