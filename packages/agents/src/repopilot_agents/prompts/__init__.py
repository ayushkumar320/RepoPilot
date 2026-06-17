"""Shared prompt-shaping helpers used by every generation node.

The most important piece here is ``goal_anchor.render(profile, plan)`` —
the prompt header that every Cartographer / Flow Tracer / Teacher / lane /
Q&A prompt prepends. Pinning it in one place keeps the trust spine honest:
if the header changes, the snapshot test fails and reviewers see it.
"""

from repopilot_agents.prompts.goal_anchor import render_goal_anchor

__all__ = ["render_goal_anchor"]
