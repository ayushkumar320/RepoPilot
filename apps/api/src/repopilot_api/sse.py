"""Helpers for formatting and parsing the Phase 4 SSE protocol."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from repopilot_api.models import BaseTourEvent, event_payload


def format_sse_event(event: BaseTourEvent) -> str:
    payload = event_payload(event)
    event_name = str(payload.pop("event"))
    return f"event: {event_name}\ndata: {json.dumps(payload, separators=(',', ':'))}\n\n"


def format_sse_comment(comment: str = "heartbeat") -> str:
    return f": {comment}\n\n"


async def with_heartbeats(
    source: AsyncIterator[BaseTourEvent],
    *,
    interval_seconds: float = 15.0,
) -> AsyncIterator[str]:
    iterator = source.__aiter__()
    pending_event: asyncio.Future[BaseTourEvent] | None = None
    while True:
        if pending_event is None:
            pending_event = asyncio.ensure_future(iterator.__anext__())
        try:
            event = await asyncio.wait_for(asyncio.shield(pending_event), timeout=interval_seconds)
        except TimeoutError:
            yield format_sse_comment()
            continue
        except StopAsyncIteration:
            break
        pending_event = None
        yield format_sse_event(event)


__all__ = ["format_sse_comment", "format_sse_event", "with_heartbeats"]
