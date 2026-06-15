.PHONY: help install lint typecheck test cov ci precommit fmt clean docker-up docker-down

help:
	@echo "RepoPilot — common targets"
	@echo "  install      uv sync (install workspace + dev deps)"
	@echo "  lint         ruff check"
	@echo "  fmt          ruff format"
	@echo "  typecheck    mypy --strict on every package"
	@echo "  test         pytest (fast lane — slow/integration markers skipped)"
	@echo "  cov          pytest with coverage gate (80%)"
	@echo "  ci           lint + typecheck + test (matches GitHub Actions)"
	@echo "  precommit    run pre-commit on all files"
	@echo "  docker-up    docker compose up -d"
	@echo "  docker-down  docker compose down -v"

install:
	uv sync --all-packages --all-groups

lint:
	uv run ruff check .

fmt:
	uv run ruff format .
	uv run ruff check . --fix

typecheck:
	uv run mypy packages apps

test:
	uv run pytest -m "not slow and not integration"

cov:
	uv run pytest -m "not slow and not integration" --cov-fail-under=80

ci: lint typecheck cov

precommit:
	uv run pre-commit run --all-files

docker-up:
	docker compose up -d

docker-down:
	docker compose down -v

clean:
	find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .mypy_cache -o -name .ruff_cache \) -prune -exec rm -rf {} +
	rm -rf .coverage htmlcov
