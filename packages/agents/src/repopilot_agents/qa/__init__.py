"""Q&A subgraph — hybrid retrieval (vector → graph) with grounding."""

from repopilot_agents.qa.graph import QAResult, answer_question
from repopilot_agents.qa.types import SufficiencyVerdict

__all__ = ["QAResult", "SufficiencyVerdict", "answer_question"]
