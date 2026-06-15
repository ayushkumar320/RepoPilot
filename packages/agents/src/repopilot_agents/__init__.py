"""LangGraph nodes + capability library.

Phase 2 surface: the six deterministic tools, the verifier, and the Q&A
mini-graph. Phase 3 layers ``ArchaeologistState`` and the full StateGraph
on top of these.
"""

from repopilot_agents.qa import QAResult, answer_question
from repopilot_agents.tools import (
    github_issues,
    graph_metrics,
    graph_query,
    graph_traverse,
    read_chunks,
    vector_search,
)
from repopilot_agents.types import (
    ChunkContent,
    ChunkHit,
    CodeRef,
    GraphQueryResult,
    Path,
    SymbolMetrics,
)
from repopilot_agents.verifier import (
    Claim,
    VerifierObjection,
    VerifierVerdict,
    verify_claim,
    verify_claims,
)

__all__ = [
    "ChunkContent",
    "ChunkHit",
    "Claim",
    "CodeRef",
    "GraphQueryResult",
    "Path",
    "QAResult",
    "SymbolMetrics",
    "VerifierObjection",
    "VerifierVerdict",
    "answer_question",
    "github_issues",
    "graph_metrics",
    "graph_query",
    "graph_traverse",
    "read_chunks",
    "vector_search",
    "verify_claim",
    "verify_claims",
]
