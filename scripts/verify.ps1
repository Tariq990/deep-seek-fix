uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
pnpm check
uv run python -m compileall src
uv run dsfix benchmark smoke
uv run dsfix verify delivery
python scripts/verified_push.py --dry-run

