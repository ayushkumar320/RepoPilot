"""Structlog setup: JSON renderer in prod/CI, human-friendly renderer in dev/tests."""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from repopilot_core.settings import get_settings


def _drop_chunk_content(_logger: Any, _name: str, event_dict: EventDict) -> EventDict:
    """Strip any field carrying raw repo content. Logs must never persist source code."""
    for key in ("chunk_content", "content", "raw_chunk"):
        event_dict.pop(key, None)
    return event_dict


def configure_logging(*, force: bool = False) -> None:
    """Wire up structlog. Idempotent — safe to call from app startup and from tests."""
    if structlog.is_configured() and not force:
        return

    settings = get_settings()
    level = getattr(logging, settings.repopilot_log_level.upper(), logging.INFO)

    is_prod_like = settings.repopilot_env.lower() in {"production", "prod", "ci"}

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _drop_chunk_content,
    ]

    if is_prod_like:
        renderer: Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
