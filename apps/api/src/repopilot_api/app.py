"""FastAPI scaffold — health-check only in Phase 0."""

from __future__ import annotations

from fastapi import FastAPI

from repopilot_core.logging import configure_logging
from repopilot_core.settings import get_settings


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(
        title="RepoPilot API",
        version="0.0.1",
        docs_url="/docs" if settings.repopilot_env != "production" else None,
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "env": settings.repopilot_env}

    return app


app = create_app()
