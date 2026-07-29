.PHONY: bootstrap verify

bootstrap:
	uv sync --all-extras --dev
	pnpm install --frozen-lockfile

verify:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy src
	uv run pytest
	pnpm check
	uv run python -m compileall src
	uv run dsfix benchmark smoke
	uv run dsfix verify delivery

