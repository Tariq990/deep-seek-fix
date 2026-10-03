# Deep Seek Fix

Deep Seek Fix is a deterministic reliability control plane for inexpensive coding models and agents such as DeepSeek, GLM/Z.ai, Qwen, Kimi, MiniMax, OpenAI-compatible APIs, and OpenCode-based agents.

It does not make any language model mathematically incapable of error. Instead, it keeps the model out of the trust boundary: the model proposes actions, deterministic code authorizes tool use, and deterministic evidence decides whether work can be delivered.

The executor also blocks repeated failed actions when the command, repository state, and prior failure classification match the task contract's loop threshold. This prevents blind "try again" loops from creating new evidence without a meaningful state change.

Evidence records include bounded redacted stdout/stderr snapshots in addition to hashes. Claim verification uses those snapshots to reject zero-test output, truncated test output, and missing required test node IDs.

## Architecture

```text
User task
  -> Task Contract Compiler
  -> Immutable task contract
  -> Planner or external agent
  -> Governed tool gateway
  -> Sandboxed executor
  -> Evidence ledger
  -> Deterministic verification gates
  -> Independent final verdict
```

Final verdicts are limited to `VERIFIED_PASS`, `VERIFIED_FAIL`, `BLOCKED`, `INCOMPLETE`, and `UNKNOWN`.

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 22+
- `uv`
- pnpm 11.7.0, either directly or through Corepack

### Clone and install

```powershell
git clone https://github.com/Tariq990/deep-seek-fix.git
cd deep-seek-fix
uv sync --all-extras --dev
corepack pnpm install --frozen-lockfile
```

No live provider keys are needed for the default tests, deterministic benchmark smoke run, or delivery verification.

### Verify the repository

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
corepack pnpm --filter @deep-seek-fix/opencode-plugin check
uv run python -m compileall src
uv run dsfix benchmark smoke
uv run python scripts/collect_evidence.py
uv run dsfix verify delivery
```

The default Python test suite contains 80 tests and enforces a 70% coverage floor. Provider live tests remain opt-in.

## CLI

```powershell
uv run dsfix doctor
uv run dsfix contract create --task-id TASK-0001 --objective "Add a focused feature" --allowed-path src --required-test tests/unit
uv run dsfix contract validate contract.json
uv run dsfix benchmark smoke
uv run dsfix verify delivery
```

## OpenCode

The workspace plugin lives in `packages/opencode-plugin`. Install it into `.opencode/plugins/` or reference the workspace package from `opencode.json` during development. The plugin fails closed when the local control plane is unavailable or returns a malformed decision.

## Providers

Provider keys are configured through environment variables only:

- `DEEPSEEK_API_KEY`
- `ZAI_API_KEY`
- `QWEN_API_KEY`
- `KIMI_API_KEY`
- `MINIMAX_API_KEY`

Live tests require `DSFIX_ENABLE_LIVE_TESTS=1` and the provider-specific key. Default tests use deterministic fake providers.

## Benchmarks and Evals

Harbor adapter files are under `benchmarks/harbor/deep-seek-fix`. Promptfoo deterministic fixtures are under `evals/promptfoo`. The smoke benchmark treats any false `PASS` as a critical failure.

## Limitations

Tests only cover encoded requirements. LLM judges, when used later, are advisory. Provider behavior can change. Microsoft Agent Governance Toolkit is treated as defense-in-depth because it is a public-preview dependency. ZCode support is deferred until its extension interface is verified.

## License

This repository is **source-available**, not OSI open source. It is licensed under the included **Personal Non-Commercial Software License 1.0**: personal, educational, evaluation, and other non-commercial use is permitted; commercial use and redistribution require prior written permission. Third-party dependencies remain under their own licenses.
