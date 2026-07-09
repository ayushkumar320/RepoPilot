"""The six deterministic tools. The LLM never computes these; it only asks.

The six LLM-facing tools are unchanged (CLAUDE.md §6). ``bm25_search`` and
``hybrid_search`` (RAG Phase 3) are **not** new agent tools — they are
internal retrieval lanes composed *inside* the single retrieval capability:
``hybrid_search`` fuses the dense (``vector_search``) and sparse
(``bm25_search``) lanes and is what the Q&A graph calls in place of
``vector_search``. The agent's palette stays at six.
"""

from repopilot_agents.tools.bm25_search import bm25_search
from repopilot_agents.tools.github_issues import github_issues
from repopilot_agents.tools.graph_metrics import graph_metrics
from repopilot_agents.tools.graph_query import graph_query
from repopilot_agents.tools.graph_traverse import graph_traverse
from repopilot_agents.tools.hybrid_search import hybrid_search
from repopilot_agents.tools.read_chunks import read_chunks
from repopilot_agents.tools.vector_search import NON_SOURCE_PATH_PREFIXES, vector_search

__all__ = [
    "NON_SOURCE_PATH_PREFIXES",
    "bm25_search",
    "github_issues",
    "graph_metrics",
    "graph_query",
    "graph_traverse",
    "hybrid_search",
    "read_chunks",
    "vector_search",
]
