# First verified run (no model keys required)

This walkthrough shows how to run Deep Seek Fix's **local, deterministic** checks. It does **not** make a live model call and does not claim that a model's generated code has been independently verified until you provide task-specific evidence.

> **License:** This is a source-available project under the Personal Non-Commercial Software License 1.0, **not** an OSI-approved open-source license. Review [LICENSE](../LICENSE) before using it, especially for commercial work or redistribution.

## Prerequisites

- Python **3.12+**
- Node.js **22+**
- [uv](https://docs.astral.sh/uv/)
- pnpm **11.7.0** (via Corepack or a compatible installation)
- Git

## 1. Set up the workspace

```bash
git clone https://github.com/Tariq990/deep-seek-fix.git
cd deep-seek-fix
uv sync --all-extras --dev
corepack pnpm install --frozen-lockfile
```

No provider API key is required for the default unit tests or the deterministic benchmark smoke run.

## 2. Inspect the local environment

```bash
uv run dsfix doctor
```

Review the output and resolve missing dependencies rather than treating a command exit as proof of readiness.

## 3. Run the deterministic benchmark

```bash
uv run dsfix benchmark smoke
```

The benchmark uses local fixtures. Consult [benchmark methodology](benchmark.md) and [limitations](limitations.md) before drawing conclusions about real model performance. A false pass is a critical failure.

## 4. Create and validate a task contract

```bash
uv run dsfix contract create --task-id TASK-0001 --objective "Add a focused feature" --allowed-path src --required-test tests/unit
uv run dsfix contract validate contract.json
```

A valid contract describes what is permitted and what evidence is required. It **does not** establish that the requested feature was implemented.

## 5. Verify the repository's local test baseline

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
corepack pnpm --filter @deep-seek-fix/opencode-plugin check
```

The default test configuration enforces a minimum coverage percentage. Passing fixtures alone do not establish correctness on untested tasks.

## 6. Collect and verify delivery evidence

```bash
uv run python scripts/collect_evidence.py --run-id RUN-LOCAL
uv run dsfix verify delivery
```

Read the reported verdict: `VERIFIED_PASS`, `VERIFIED_FAIL`, `BLOCKED`, `INCOMPLETE`, or `UNKNOWN`. Only `VERIFIED_PASS` can be interpreted as a successful verification **for the encoded requirements and evidence**. Never translate `UNKNOWN` or `INCOMPLETE` into success.

## Next steps

- [Architecture](architecture.md) — why the model is outside the trust boundary
- [Evidence model](evidence-model.md) — what counts as observable proof
- [Task contracts](task-contract.md) — authorized scope and required checks
- [OpenCode integration](opencode-integration.md) — hooking into an agent workflow
- [Provider setup](provider-setup.md) — optional live integrations
- [Contributing](../CONTRIBUTING.md) — propose reproducible fixes and tests
- [Security](../SECURITY.md) — responsible disclosure

**Troubleshooting:** If setup or tests fail, include OS, Python/Node/uv versions, the exact failing command, and **redacted** output in a bug report. Never post credentials, personal data, provider keys, or complete environment files.

_These commands are documented against the repository's existing scripts and configuration; their success on a particular machine is not assumed._
