"""Test 5 from the Phase 0 TDD checklist."""

from __future__ import annotations

from pathlib import Path

from repopilot_core.settings import Settings


def test_settings_loads_from_env_example() -> None:
    """`.env.example` shipped at the repo root must be a valid pydantic-settings source.

    This guards against drift between the example file and the `Settings` model —
    if a new field is added without updating `.env.example`, this test still passes
    (extras are ignored), but if a *typed* field's example value violates its
    schema, pydantic raises here.
    """
    env_example = Path(__file__).resolve().parents[3] / ".env.example"
    assert env_example.exists(), f"missing {env_example}"

    settings = Settings(_env_file=env_example)

    # Known defaults from the example file:
    assert settings.repopilot_env == "development"
    assert settings.huggingface_base_url.startswith("https://router.huggingface.co/")
    assert settings.llm_max_429_retries == 5
    assert settings.huggingface_embedding_model == "nomic-ai/nomic-embed-text-v1.5"
