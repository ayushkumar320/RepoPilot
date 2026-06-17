"""Helpers for formatting and parsing the Phase 4 SSE protocol."""

from __future__ import annotations

import json

from repopilot_api.models import BaseTourEvent, event_payload


def format_sse_event(event: BaseTourEvent) -> str:
    payload = event_payload(event)
    event_name = str(payload.pop("event"))
    return f"event: {event_name}\ndata: {json.dumps(payload, separators=(',', ':'))}\n\n"


__all__ = ["format_sse_event"]
