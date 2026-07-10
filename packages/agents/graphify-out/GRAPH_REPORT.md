# Graph Report - agents  (2026-07-10)

## Corpus Check
- 67 files · ~29,240 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 759 nodes · 1627 edges · 39 communities (30 shown, 9 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 312 edges (avg confidence: 0.74)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c9d63e40`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_IntentProfile|IntentProfile]]
- [[_COMMUNITY_CodeRef|CodeRef]]
- [[_COMMUNITY_types.py|types.py]]
- [[_COMMUNITY_verify_claim|verify_claim]]
- [[_COMMUNITY_CrossEncoderReranker|CrossEncoderReranker]]
- [[_COMMUNITY_ArchaeologistState|ArchaeologistState]]
- [[_COMMUNITY_profile_intent|profile_intent]]
- [[_COMMUNITY_test_vector_search_filters.py|test_vector_search_filters.py]]
- [[_COMMUNITY_plan|plan]]
- [[_COMMUNITY_bm25_search|bm25_search]]
- [[_COMMUNITY_graph_query|graph_query]]
- [[_COMMUNITY_answer_question|answer_question]]
- [[_COMMUNITY_graph_metrics|graph_metrics]]
- [[_COMMUNITY_conftest.py|conftest.py]]
- [[_COMMUNITY_triage_issues|triage_issues]]
- [[_COMMUNITY_render_goal_anchor|render_goal_anchor]]
- [[_COMMUNITY_test_state.py|test_state.py]]
- [[_COMMUNITY_CapabilityPlan|CapabilityPlan]]
- [[_COMMUNITY_test_qa_graph.py|test_qa_graph.py]]
- [[_COMMUNITY_mmr_select|mmr_select]]
- [[_COMMUNITY_test_compress.py|test_compress.py]]
- [[_COMMUNITY_Opportunity|Opportunity]]
- [[_COMMUNITY_test_contribute.py|test_contribute.py]]
- [[_COMMUNITY_compress_chunk|compress_chunk]]
- [[_COMMUNITY_ChunkContent|ChunkContent]]
- [[_COMMUNITY_test_compress_integration.py|test_compress_integration.py]]
- [[_COMMUNITY_run_lane_c_suspicion|run_lane_c_suspicion]]
- [[_COMMUNITY_detect_quality_opportunities|detect_quality_opportunities]]
- [[_COMMUNITY_read_chunks|read_chunks]]
- [[_COMMUNITY_types.py|types.py]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY_repopilot-agents|repopilot-agents]]

## God Nodes (most connected - your core abstractions)
1. `IntentProfile` - 62 edges
2. `CodeRef` - 50 edges
3. `CapabilityPlan` - 34 edges
4. `ChunkContent` - 29 edges
5. `ArchaeologistState` - 25 edges
6. `answer_question()` - 24 edges
7. `verify_claim()` - 21 edges
8. `profile_intent()` - 20 edges
9. `Opportunity` - 20 edges
10. `plan()` - 19 edges

## Surprising Connections (you probably didn't know these)
- `test_intent_profile_defaults()` --calls--> `IntentProfile`  [INFERRED]
  tests/test_state.py → src/repopilot_agents/state.py
- `test_intent_profile_rejects_out_of_unit_modality_weights()` --calls--> `IntentProfile`  [INFERRED]
  tests/test_state.py → src/repopilot_agents/state.py
- `test_state_defaults_are_empty()` --calls--> `ArchaeologistState`  [INFERRED]
  tests/test_state.py → src/repopilot_agents/state.py
- `test_coderef_accepts_equal_lines()` --calls--> `CodeRef`  [INFERRED]
  tests/test_types.py → src/repopilot_agents/types.py
- `test_coderef_rejects_end_before_start()` --calls--> `CodeRef`  [INFERRED]
  tests/test_types.py → src/repopilot_agents/types.py

## Import Cycles
- None detected.

## Communities (39 total, 9 thin omitted)

### Community 0 - "IntentProfile"
Cohesion: 0.07
Nodes (65): BaseModel, ClaimStatus, Modality, Phase2Claim, SourceRetry, ArchaeologistError, Claim, IntentProfile (+57 more)

### Community 1 - "CodeRef"
Cohesion: 0.06
Nodes (55): AsyncEngine, LLMProvider, Cartographer — produces ``system_map`` Insights from the call graph.  The Cartog, Run the Cartographer once.      Returns the state diff for the LangGraph reducer, Resolve each symbol's CodeRef from graph_metrics's underlying lookup.      The m, _refs_for_symbols(), _resolve_refs(), run_cartographer() (+47 more)

### Community 2 - "types.py"
Cohesion: 0.05
Nodes (49): _format_paths(), AsyncEngine, LLMProvider, Flow Tracer — produces ``traced_flows`` Insights from call-graph paths.  Reads `, Choose which symbols to trace. Prefer the planner's explicit     targets; otherw, Run the Flow Tracer once.      Returns ``{"traced_flows": [Insight, …]}``. Empty, run_flow_tracer(), _seed_targets() (+41 more)

### Community 3 - "verify_claim"
Cohesion: 0.08
Nodes (45): _apply(), _Cache, Claim, _objection_if_rejected(), _parse_verdict(), AsyncEngine, LLMProvider, Per-claim grounding check against ``read_chunks``.  The Verifier is the single l (+37 more)

### Community 4 - "CrossEncoderReranker"
Cohesion: 0.06
Nodes (37): attribute_refs(), Claim → ref attribution via the Phase 4 cross-encoder.  The verifier judges each, Return the refs of the ``k`` chunks most relevant to ``claim_text``.      Best-f, CrossEncoderReranker, Any, Cross-encoder reranker over (query, chunk) pairs via ``fastembed``.  Unlike the, The text the cross-encoder sees for one chunk (symbol-prefixed)., Lazy-loading, score-caching wrapper around ``fastembed.TextCrossEncoder``. (+29 more)

### Community 5 - "ArchaeologistState"
Cohesion: 0.10
Nodes (42): build_graph(), _capability_planner_node(), _cartographer_node(), _flow_tracer_node(), _intent_profiler_node(), _lane_a_node(), _lane_b_node(), _lane_c_node() (+34 more)

### Community 6 - "profile_intent"
Cohesion: 0.13
Nodes (28): _coerce_keywords(), _coerce_modality_weights(), _coerce_optional_str(), _coerce_output_shape(), _fallback_profile(), _parse_json(), profile_intent(), Any (+20 more)

### Community 7 - "test_vector_search_filters.py"
Cohesion: 0.10
Nodes (21): build_search_sql(), AsyncEngine, LLMProvider, ``vector_search`` — pgvector cosine k-NN over indexed chunks.  Embeds the query, Compose the k-NN query with optional metadata filters.      Pure string composit, Return the top chunks for ``query`` in ``repo_id``.      ``recall_k`` (when give, vector_search(), Any (+13 more)

### Community 8 - "plan"
Cohesion: 0.14
Nodes (26): _derive_ranker_weights(), _infer_flow_targets(), _infer_shape(), _pick_hub_bias(), plan(), CapabilityName, OutputShape, Capability Planner — deterministic ``IntentProfile`` → ``CapabilityPlan``.  The (+18 more)

### Community 9 - "bm25_search"
Cohesion: 0.12
Nodes (17): bm25_search(), build_bm25_sql(), clean_query(), AsyncEngine, ``bm25_search`` — Postgres full-text (BM25-style) keyword search.  The sparse ha, Compose the FTS query with optional metadata filters (pure)., Return up to ``k`` keyword-matched chunks for ``query`` in ``repo_id``.      Emp, Drop stopwords, keeping content words and identifiers for the sparse lane. (+9 more)

### Community 10 - "graph_query"
Cohesion: 0.19
Nodes (21): QueryKind, _call_subgraph(), _entry_points(), graph_query(), _hubs(), _layers(), _neighbours(), AsyncEngine (+13 more)

### Community 11 - "answer_question"
Cohesion: 0.17
Nodes (19): answer_question(), _Context, _estimate_tokens(), _extend_context(), _generate_answer(), _is_not_found(), _judge_sufficiency(), _parse_claims() (+11 more)

### Community 12 - "graph_metrics"
Cohesion: 0.13
Nodes (18): invalidate(), load_graph(), AsyncEngine, DiGraph, Shared loader/cache for the per-repo NetworkX graph.  Per Phase 2 decision **D5*, Return the cached NetworkX graph for ``repo_id``; build it on miss., Drop the cached graph for ``repo_id``. Call when re-indexing., Test helper — clear all cached graphs. (+10 more)

### Community 13 - "conftest.py"
Cohesion: 0.12
Nodes (11): FakeChunk, FakeEngine, FakeProvider, make_content(), make_ref(), Any, Shared fixtures: stubbed engine + LLMProvider for the unit-testable layer.  We c, LLM provider double — queues canned responses, records calls. (+3 more)

### Community 14 - "triage_issues"
Cohesion: 0.16
Nodes (17): _build_fact_bundle_for_test(), _fact_bundle(), Render the fact bundle as a compact text block.      We deliberately avoid prose, approachability_score(), Lane A — issue triage backed by graph approachability., Score issue approachability from graph facts, not GitHub labels., Rank issues and keep the next three rejected reasons., _ref_for_issue() (+9 more)

### Community 15 - "render_goal_anchor"
Cohesion: 0.20
Nodes (17): _format_active(), _format_keywords(), _format_tilt_line(), _format_weights(), Goal-anchor prompt block — shared across every generation node.  Every generatio, Render the goal-anchor block for the given (profile, plan) pair.      Output is, render_goal_anchor(), _profile() (+9 more)

### Community 16 - "test_state.py"
Cohesion: 0.16
Nodes (17): Insight, QAExchange, One completed Q&A turn. v1 keeps the last 8; the prompt only consumes     the cu, Iteration-2 output shape — no stat dumps reach the Teacher., Validator tests for ``ArchaeologistState`` and its sub-models.  These tests pin, _ref(), test_claim_defaults_unverified(), test_claim_rejects_relevance_out_of_unit_interval() (+9 more)

### Community 17 - "CapabilityPlan"
Cohesion: 0.14
Nodes (14): build_opportunity_briefing(), ranker_rationale(), Teacher-facing briefing helpers for Phase 5 opportunity cards., Attach the UI-visible Phase 5 briefing surfaces without reranking., Plain-English explanation of planner-derived ranker weights., CapabilityPlan, CapabilityName, Deterministic Planner output. Verifiable in CI. (+6 more)

### Community 18 - "test_qa_graph.py"
Cohesion: 0.18
Nodes (12): _chunk(), _patch_tools(), Any, MonkeyPatch, End-to-end Q&A tests against fully stubbed dependencies.  We monkey-patch the th, Returns canned text responses in queue order., _ref(), _ScriptedProvider (+4 more)

### Community 19 - "mmr_select"
Cohesion: 0.21
Nodes (13): jaccard(), mmr_select(), Maximal Marginal Relevance — diversity-aware top-k selection (pure).  ``MMR(c) =, Return indices of up to ``k`` items, MMR-ordered (pure function).      ``relevan, _tokens(), RAG Phase 4: MMR diversity selection (pure function)., test_constant_relevance_normalises_safely(), test_empty_and_zero_k() (+5 more)

### Community 20 - "test_compress.py"
Cohesion: 0.24
Nodes (10): Return the answerer-visible chunk text, respecting kept spans if any., render_chunk_view(), _chunk(), Any, Phase 5 compression tests: safe parsing, clipping, and answerer-only view., _StubProvider, test_answer_prompt_uses_compressed_view_only(), test_compress_chunk_falls_back_on_invalid_json() (+2 more)

### Community 21 - "Opportunity"
Cohesion: 0.23
Nodes (10): _lane_weight(), opportunity_score(), rank_opportunities(), Deterministic Phase 5 opportunity ranker., Compute a deterministic weighted score for one opportunity., Return opportunities in stable best-first order. No LLM reranking., Opportunity, One unified shape across all scanner lanes. (+2 more)

### Community 22 - "test_contribute.py"
Cohesion: 0.35
Nodes (11): _metrics(), _opp(), _profile(), Phase 5 Contribute-mode unit tests., _ref(), test_briefing_surfaces_intent_match_and_rationale(), test_lane_a_approachability_uses_graph_not_labels(), test_lane_b_dead_code_excludes_entry_points() (+3 more)

### Community 23 - "compress_chunk"
Cohesion: 0.27
Nodes (9): _clip_ranges(), compress_chunk(), compress_chunks(), _KeepRanges, _merge_ranges(), _parse_keep_ranges(), LLMProvider, Phase 5 context compression: keep the answerer's view lean, not the verifier's. (+1 more)

### Community 24 - "ChunkContent"
Cohesion: 0.38
Nodes (9): _compression_user_prompt(), answer_user_prompt(), _chunk_view(), Q&A prompt templates.  Three prompts, all under the 2000-token budget from ``doc, _render_chunks(), _render_numbered_chunk(), sufficiency_user_prompt(), ChunkContent (+1 more)

### Community 25 - "test_compress_integration.py"
Cohesion: 0.31
Nodes (6): _chunk(), Any, Phase 5 safety invariant: verifier must always see the full chunk content.  The, _StubProvider, test_compress_chunks_runs_in_parallel_and_handles_errors(), test_verifier_sees_full_content_after_compression()

### Community 26 - "run_lane_c_suspicion"
Cohesion: 0.32
Nodes (7): lane_c_language_violation(), _matches_focus(), Lane C — guarded structural suspicions., Return the banned phrase when Lane C language is too certain., Build guarded suspicion opportunities from deterministic candidates.      Phase, run_lane_c_suspicion(), test_lane_c_banned_vocabulary_rejected()

### Community 27 - "detect_quality_opportunities"
Cohesion: 0.48
Nodes (6): detect_quality_opportunities(), _difficulty(), QualityCandidate, Lane B — deterministic code-health opportunities., Transform deterministic detector hits into unified opportunities., run_lane_b_quality()

### Community 28 - "read_chunks"
Cohesion: 0.40
Nodes (4): AsyncEngine, ``read_chunks`` — the ONLY tool that returns source text.  Per Phase 2 decision, Fetch the content of every chunk whose ``(file_path, start_line, end_line)``, read_chunks()

### Community 29 - "types.py"
Cohesion: 0.50
Nodes (3): QAClaim, Types specific to the Q&A subgraph (sufficiency judge + final answer)., A single grounded claim in the Q&A answer.

## Knowledge Gaps
- **1 isolated node(s):** `repopilot-agents`
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `CodeRef` connect `CodeRef` to `IntentProfile`, `types.py`, `verify_claim`, `CrossEncoderReranker`, `ArchaeologistState`, `test_vector_search_filters.py`, `bm25_search`, `conftest.py`, `triage_issues`, `test_state.py`, `test_qa_graph.py`, `test_compress.py`, `test_contribute.py`, `test_compress_integration.py`, `run_lane_c_suspicion`, `read_chunks`?**
  _High betweenness centrality (0.172) - this node is a cross-community bridge._
- **Why does `IntentProfile` connect `IntentProfile` to `CodeRef`, `types.py`, `ArchaeologistState`, `profile_intent`, `plan`, `triage_issues`, `render_goal_anchor`, `test_state.py`, `CapabilityPlan`, `test_contribute.py`, `run_lane_c_suspicion`, `detect_quality_opportunities`?**
  _High betweenness centrality (0.170) - this node is a cross-community bridge._
- **Why does `ChunkContent` connect `ChunkContent` to `IntentProfile`, `types.py`, `verify_claim`, `CrossEncoderReranker`, `answer_question`, `conftest.py`, `test_qa_graph.py`, `test_compress.py`, `compress_chunk`, `test_compress_integration.py`, `read_chunks`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Are the 27 inferred relationships involving `IntentProfile` (e.g. with `QualityCandidate` and `ActionabilityVerdict`) actually correct?**
  _`IntentProfile` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `CodeRef` (e.g. with `bm25_search()` and `vector_search()`) actually correct?**
  _`CodeRef` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `CapabilityPlan` (e.g. with `_ScriptedProvider` and `_StubResponse`) actually correct?**
  _`CapabilityPlan` has 17 INFERRED edges - model-reasoned connections that need verification._
- **What connects `repopilot-agents`, `LangGraph nodes + capability library.  Phase 2 surface: the six deterministic to`, `Capability library: Cartographer, Flow Tracer, Teacher.  Every capability is a L` to the rest of the system?**
  _177 weakly-connected nodes found - possible documentation gaps or missing edges._