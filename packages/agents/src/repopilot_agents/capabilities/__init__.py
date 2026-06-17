"""Capability library: Cartographer, Flow Tracer, Teacher.

Every capability is a LangGraph node that:

1. Reads the **deterministic tool output** for its slice (graph queries,
   metrics, traverses) — never the raw graph, never raw LLM-derived
   numbers.
2. Renders the shared **goal anchor** prompt header, then asks the LLM
   for a strict JSON list of `Insight` / `Claim` objects.
3. Coerces the response into typed state objects (drops malformed
   entries silently — the verifier loop will surface anything that
   slipped through and the empty-tour failsafe will catch a total
   miss).
4. Returns a state diff dict — never mutates state in place.

Iteration-2 contract (docs/03 § "Iteration 2"): no stat dumps. Raw
numbers from the tools are transformed into `Insight` objects (each with
`finding`, `because`, `so_what`, `goal_link`) **before** any text
generation reaches the Teacher. Validators on those Pydantic types are
the safety net.
"""

from repopilot_agents.capabilities.cartographer import run_cartographer
from repopilot_agents.capabilities.flow_tracer import run_flow_tracer
from repopilot_agents.capabilities.teacher import run_teacher

__all__ = ["run_cartographer", "run_flow_tracer", "run_teacher"]
