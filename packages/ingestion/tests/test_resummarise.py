"""Contract for the re-summarise pass.

The pass exists because a rate-limited indexing run leaves real chunks with
placeholder summaries, and re-indexing to recover them would rebuild several
minutes of work that is already correct. The rules it must not break:

* **A placeholder is defined once.** ``_fallback_summary`` writes the marker and
  ``is_placeholder_summary`` reads it. A second definition (a SQL ``LIKE``, say)
  is a thing to keep in step, and when it drifts the pass silently finds
  nothing to do.
* **A run that fixed nothing is not a success.** If the provider is still
  exhausted the summariser hands back fallbacks, and writing those over the
  fallbacks already stored would report progress that did not happen.
"""

from __future__ import annotations

from repopilot_ingestion.chunk import Chunk
from repopilot_ingestion.resummarise import ResummariseResult
from repopilot_ingestion.summary import (
    SUMMARY_UNAVAILABLE_SUFFIX,
    is_placeholder_summary,
)


def _chunk(symbol: str = "pkg.mod.thing") -> Chunk:
    return Chunk(
        file_path="pkg/mod.py",
        symbol=symbol,
        kind="function",
        start_line=1,
        end_line=5,
        content="def thing():\n    return 1\n",
    )


def test_the_fallback_is_recognised_as_a_placeholder() -> None:
    """The round trip that matters: what the pipeline writes when a provider is
    exhausted must be what the re-summarise pass looks for."""
    from repopilot_ingestion.summary import _fallback_summary

    written = _fallback_summary(_chunk())
    assert is_placeholder_summary(written)
    assert written.endswith(SUMMARY_UNAVAILABLE_SUFFIX)


def test_a_missing_summary_counts_as_a_placeholder() -> None:
    """A chunk written before summaries existed is in the same position as one
    whose summary failed."""
    assert is_placeholder_summary(None)


def test_a_real_summary_is_left_alone() -> None:
    assert not is_placeholder_summary("Builds the WSGI application object.")
    # Not fooled by a real summary that merely mentions availability.
    assert not is_placeholder_summary("Reports whether the summary service is unavailable.")


def test_a_pass_that_rewrote_nothing_is_not_complete() -> None:
    """The provider was still exhausted: every chunk came back a fallback."""
    result = ResummariseResult(
        repo_id="owner/name@sha", examined=90, rewritten=0, still_placeholder=90
    )
    assert result.complete is False


def test_a_pass_with_nothing_to_do_is_not_reported_as_complete() -> None:
    """Zero placeholders is a no-op, not a success — `complete` says "this
    snapshot's summaries were repaired", and nothing was."""
    result = ResummariseResult(
        repo_id="owner/name@sha", examined=0, rewritten=0, still_placeholder=0
    )
    assert result.complete is False


def test_a_fully_repaired_pass_is_complete() -> None:
    result = ResummariseResult(
        repo_id="owner/name@sha", examined=90, rewritten=90, still_placeholder=0
    )
    assert result.complete is True
