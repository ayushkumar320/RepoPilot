"""The persona may re-rank an answer; it may never loosen its grounding.

These tests pin the invariants that make personas safe: the grounding rules
survive, retrieval is untouched, and no-persona is byte-identical to the
pre-persona prompt.
"""

from __future__ import annotations

from repopilot_agents.qa.prompts import ANSWER_SYSTEM, answer_system, reader_context
from repopilot_agents.state import IntentProfile

CONTRIBUTOR = IntentProfile(
    raw_text="I want to contribute and need to know where a change would go",
    audience_framing="a first-time outside contributor",
    focus_keywords=["entry points", "tests"],
    output_shape_preference="ranked_list",
    success_criterion="find a file to edit",
)

COMPETITOR = IntentProfile(
    raw_text="I am evaluating this against a competing product",
    audience_framing="a product strategist at a competing company",
    focus_keywords=["features", "limits"],
    output_shape_preference="ranked_list",
)


def test_no_profile_reproduces_the_pre_persona_prompt() -> None:
    assert answer_system(None) == ANSWER_SYSTEM
    assert reader_context(None) == ""


def test_persona_fields_reach_the_prompt() -> None:
    rendered = answer_system(CONTRIBUTOR)

    assert "a first-time outside contributor" in rendered
    assert "entry points, tests" in rendered
    assert "find a file to edit" in rendered
    assert CONTRIBUTOR.raw_text in rendered


def test_grounding_rules_survive_the_persona_block() -> None:
    rendered = answer_system(COMPETITOR)

    # The original four rules are still there, ahead of the reader context...
    assert "ONLY use facts present in the supplied code chunks" in rendered
    assert "I couldn't find that in the repo." in rendered
    assert rendered.index("ONLY use facts") < rendered.index("READER CONTEXT")
    # ...and the persona block re-subordinates itself to them.
    assert "Rules 1-4 above still bind absolutely" in rendered
    assert "never drop a citation" in rendered
    assert "manufacturing relevance" in rendered


def test_two_personas_differ_only_in_the_reader_block() -> None:
    contributor = answer_system(CONTRIBUTOR)
    competitor = answer_system(COMPETITOR)

    assert contributor != competitor
    prefix = ANSWER_SYSTEM
    assert contributor.startswith(prefix)
    assert competitor.startswith(prefix)
    # Everything that differs lives after the shared grounding preamble.
    assert contributor.removeprefix(prefix) != competitor.removeprefix(prefix)


def test_output_shape_selects_one_ordering_directive() -> None:
    ranked = answer_system(COMPETITOR)
    narrative = answer_system(
        COMPETITOR.model_copy(update={"output_shape_preference": "narrative"})
    )
    unspecified = answer_system(
        COMPETITOR.model_copy(update={"output_shape_preference": "unspecified"})
    )

    assert "most-consequential first" in ranked
    assert "cause before effect" in narrative
    assert "ordering:" not in unspecified


def test_sparse_profile_renders_without_empty_lines() -> None:
    rendered = reader_context(IntentProfile(raw_text="just tell me how it works"))

    assert "goal:" in rendered
    for absent in ("reader:", "priorities:", "success:", "ordering:"):
        assert absent not in rendered


def test_persona_block_stays_within_the_prompt_budget() -> None:
    # ~4 chars/token; the node budget is 2000 input tokens and the chunks need
    # nearly all of it, so the persona block must stay marginal.
    assert len(reader_context(CONTRIBUTOR)) // 4 < 200
