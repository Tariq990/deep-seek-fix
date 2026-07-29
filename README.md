# Deep Seek Fix

Deep Seek Fix is a deterministic reliability control plane for inexpensive coding models and agents such as DeepSeek, GLM/Z.ai, Qwen, Kimi, MiniMax, OpenAI-compatible APIs, and OpenCode-based agents.

It does not make any language model mathematically incapable of error. Instead, it keeps the model out of the trust boundary: the model proposes actions, deterministic code authorizes tool use, and deterministic evidence decides whether work can be delivered.

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

## Local Setup

```powershell
uv sync --all-extras --dev
pnpm install --frozen-lockfile
```

No live provider keys are needed for default tests or benchmark smoke runs.

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

