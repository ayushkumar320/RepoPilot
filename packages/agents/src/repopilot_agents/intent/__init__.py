"""Phase 3 generic-intent layer: Intent Profiler + Capability Planner.

The Profiler takes the user's free-text intent and emits a structured
``IntentProfile``. The Planner is a pure deterministic function over that
profile that emits a ``CapabilityPlan``. Both feed every downstream
capability node. See ``docs/03_ARCHITECTURE.md`` § "Generic intent layer".
"""

from repopilot_agents.intent.planner import plan
from repopilot_agents.intent.profiler import profile_intent

__all__ = ["plan", "profile_intent"]
