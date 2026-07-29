# Deep Seek Fix Handoff

## Objective

Build a model-independent reliability control plane for inexpensive coding models and agents. The model proposes actions, deterministic code authorizes actions, and deterministic evidence decides completion.

## Current State

Initial implementation is in progress. The repository contains the core Python package, CLI/API surfaces, policy/evidence/verification modules, an OpenCode plugin scaffold, adversarial tests, Harbor smoke data, Promptfoo deterministic fixtures, and CI configuration.

## Commands

```powershell
uv sync --all-extras --dev
pnpm install --frozen-lockfile
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
pnpm check
uv run python -m compileall src
uv run dsfix benchmark smoke
uv run dsfix verify delivery
python scripts/verified_push.py --dry-run
```

## Limitations

- Docker is not available on the current PATH, so the optional Langfuse Docker profile cannot be executed in this environment yet.
- ZCode integration is deferred until a supported extension interface is verified.
- Live provider tests are disabled by default and require explicit environment flags plus provider keys.

