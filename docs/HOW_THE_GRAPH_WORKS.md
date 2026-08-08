# How the code graph works

Written for someone who wants to know what the graph *is* and what it *costs*,
without reading the parser. The short version of the cost question:

> **The graph uses no AI and costs no tokens.** Not "few tokens" — zero. No
> model is called at any point while building it. It is produced by reading the
> code the way a compiler does.

If you only read one section, read [What actually costs money](#what-actually-costs-money).

---

## What the graph is

A map of how the pieces of a repository refer to each other.

Every named thing in the code — a module, a class, a function, a method —
becomes a **node**. Every reference between them becomes an **edge**:

| Edge | Plain meaning |
|---|---|
| `calls` | this function runs that one |
| `imports` | this file needs that one |
| `inherits` | this class is built on that one |
| `defines` | this class or file contains that symbol |

Each edge is also readable backwards, which is usually the more useful
direction: `called_by` answers "who depends on this?" — the question you
actually have before changing something.

That is the entire vocabulary. Eight directions, four relationships.

`defines` is the odd one out, and deliberately so. The other three describe
what a symbol *reaches*; this one describes what is *inside* it, and needs no
name resolution at all — the parent is simply whatever the source nests it
under. It is also the only edge kind the AI-facing tools cannot see: the loader
they use whitelists the other three, because a link from every class to every
one of its methods would swamp the "what calls what" structure that hub and
entry-point ranking depends on. The panel reads it; the agents do not.

## How it gets built

When a repository is indexed, the pipeline runs:

```
clone → parse → chunk → graph → (summarise ‖ embed) → save
```

The **graph** step opens each Python file and parses it into a syntax tree —
the same structural view Python itself uses to run the file. It then walks that
tree and writes down what it literally sees: this function contains a call to
that name; this class lists that base class; this file imports that module.

The comparison worth holding onto: an AI model *reads* code the way a person
skims it, forming an impression. This step *parses* it, the way a compiler
does, producing a fact. The parser cannot be persuaded, cannot be confused by a
misleading comment, and returns the same answer every time on the same input.

### The hard part: what does this name refer to?

Finding the word `send` in a file is easy. Knowing *which* `send` it means is
the actual work, because the same short name can mean different things in
different files.

The resolver works this out from what the code declares:

- an import — `from .transports import HTTPTransport` tells it exactly which one
- a type annotation — `self._transport: BaseTransport`
- a constructor — `self._transport = HTTPTransport()`
- a declared return type — `def _pick(self) -> Transport:`

**When the code doesn't say, the graph doesn't guess.** An untyped
`self.thing = build_it()` produces no edge at all. The call is simply left out
and logged as unresolved.

That is a deliberate trade, and it's the rule most worth understanding: the
graph is *incomplete on purpose* rather than *complete and partly wrong*. A
missing connection is a gap you can notice. An invented one is a lie you'd act
on. Roughly, an edge exists only if a human reading the same two files could
point at the line that proves it.

### One consequence to know about

If a variable is declared as a general type and holds a specific one at
runtime, the graph records the general one. In `httpx`, `Client.send`
eventually calls `transport.handle_request(...)`, where `transport` is declared
`BaseTransport`. Which *concrete* transport is in there is decided while the
program runs, and no amount of reading the source settles it.

So the graph says `send → BaseTransport.handle_request`, and connects
`HTTPTransport` to `BaseTransport` by an inherits edge. It does not claim
`send` calls `HTTPTransport`. That claim would be a guess wearing a fact's
clothing.

## What actually costs money

Indexing has several steps and they are not alike. Only one of them talks to a
paid AI service.

| Step | What it uses | Paid tokens? |
|---|---|---|
| Clone | git | No |
| Parse & chunk | tree-sitter | No |
| **Build the graph** | **Python's own parser** | **No** |
| Embed | a model that runs on this machine | No — downloads once, then local |
| Summarise chunks | a hosted LLM | **Yes** — one small call per chunk, cached |
| Answer a question | a hosted LLM | **Yes** |

Two things people reasonably assume cost tokens and don't:

**Embeddings.** These are the numeric fingerprints that make search work. They
are produced by a model running locally. Its weights download once on first
use; after that it costs electricity and time, not API credits.

**Browsing the graph in the app.** Clicking "Related code" runs a database read
and no model. The endpoint is deliberately unmetered — the reasoning recorded
in the code is that charging for it would push people away from the one surface
that shows where a claim's code actually lives.

So: **summaries and answers cost tokens. Structure does not.**

A practical consequence — when a provider is rate-limited or out of quota,
indexing still succeeds and the graph is still correct and complete. Only the
written summaries fall back to placeholders. That has already happened on this
project, and the graph was unaffected.

## Why build it this way

Because the product's central promise is that every factual claim points at
real code. An AI asked to describe how a codebase fits together will produce a
fluent, plausible answer that is sometimes wrong, and nothing in the output
marks which parts. The failure is invisible, which is what makes it dangerous.

So the roles are split:

- **The parser establishes facts.** Deterministic, checkable, no model.
- **The model explains them.** It works only from facts already established.

The model is never asked "what calls this?" It is handed the answer and asked
to put it in useful words. This is why the project rules state that the LLM
never computes the call graph.

## What it doesn't do

- **Python only.** Other languages are indexed and searchable, but produce no
  graph. Of eight repositories indexed on this project, two have no graph for
  exactly this reason. The app says so in words rather than showing an empty
  list.
- **Runtime behaviour is out of reach.** Dynamic dispatch, `getattr`,
  decorators that rewrite functions — all unresolvable from source, all
  deliberately omitted.
- **It's a snapshot.** It reflects the code at the moment of indexing.

## Roughly how big it gets

From repositories indexed on this project:

| Repository | Nodes |
|---|---|
| fastapi | 7,470 |
| flask | 2,106 |
| httpx | 1,582 |
| requests | 1,148 |

Most nodes have very few connections — a median of one or two. This is why the
graph is shown as "what's related to *this*" rather than as one giant picture:
at repository scale a node-link diagram of every function is visual noise, not
structure.

The **module map** is the same graph seen from further away, and it is drawn,
because at that level the shape is real: flask has 83 modules joined by 81
dependencies, httpx 60 and 72. One box per module, one arrow per import that
stays inside the repository — an import of `os` or `httpx` is a true edge and
tells a reader nothing about how *this* codebase is arranged. Big repositories
are scoped to the busiest modules, and the map says so rather than quietly
drawing a subset.

---

*Deeper detail: [`03_ARCHITECTURE.md`](03_ARCHITECTURE.md) covers the agent
tools that read this graph. The builder itself is
`packages/ingestion/src/repopilot_ingestion/graph.py`, and the rules above are
enforced by tests in `packages/ingestion/tests/test_graph_builder.py` —
including two that assert nothing is invented.*
