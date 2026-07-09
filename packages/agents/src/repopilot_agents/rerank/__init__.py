"""RAG Phase 4 — rerank stage: cross-encoder relevance + MMR diversity.

Sits between ``hybrid_search``'s ~50-chunk pool and the answerer's ~8-chunk
prompt. The pool is high-recall but order-blind past the top few; the
cross-encoder scores every (query, chunk) pair directly, and MMR suppresses
near-duplicates so the final top-k isn't five methods of one class.
"""

from repopilot_agents.rerank.cross_encoder import CrossEncoderReranker
from repopilot_agents.rerank.mmr import mmr_select
from repopilot_agents.rerank.pipeline import rerank_and_diversify

__all__ = ["CrossEncoderReranker", "mmr_select", "rerank_and_diversify"]
