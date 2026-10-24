# Contributing to Deep Seek Fix

Thanks for considering a contribution. This project prioritizes **reproducible evidence, narrowly scoped changes, and honest failure reporting** over impressive-looking success claims.

> **Important licensing note:** The repository is **source-available, not OSI open source**. Read [LICENSE](LICENSE) before contributing or redistributing. A pull request does not by itself grant permission for commercial use or redistribution.

## Good first contributions

- A minimal, reproducible failing test for an incorrect `VERIFIED_PASS`.
- An example task contract that demonstrates a real edge case without credentials or private data.
- Documentation fixes that make installation, policies or verdict meanings clearer.
- Deterministic test coverage for failure classifications, redaction or retry-loop handling.
- A small bug fix with a failing test before the change and a passing test afterwards.

If you are planning a large change or new integration, [open an issue](https://github.com/Tariq990/deep-seek-fix/issues) first and describe the motivating use case and required trust boundary.

## Local setup (no provider keys)

Follow the [quickstart](docs/quickstart.md) using Python 3.12+, Node.js 22+, uv and pnpm 11.7.0.

```bash
uv sync --all-extras --dev
corepack pnpm install --frozen-lockfile
```

Before requesting review, run the same deterministic checks as the proposed GitHub Actions workflow:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
corepack pnpm --filter @deep-seek-fix/opencode-plugin check
uv run dsfix benchmark smoke
```

The repository also provides the local evidence-gated verification scripts:

```bash
# macOS / Linux
scripts/verify.sh
```

```powershell
# Windows
scripts\verify.ps1
```

If a command fails, report that failure; do **not** skip, loosen, or silently replace required gates to make a PR appear green.

## Pull request expectations

1. Explain the bug or improvement and provide a minimal reproducer or clear expected behavior.
2. Keep the change scoped. Avoid unrelated formatting, broad refactors or configuration churn.
3. Add or update deterministic tests, especially for rejection/failure paths.
4. Include commands actually run and their results. Clearly mark tests **not run**.
5. Redact all tokens, credentials, user information, provider responses and authorization headers.
6. Document any behavior, compatibility or security implications in the PR description.

Use [SECURITY.md](SECURITY.md) rather than a public issue to disclose security vulnerabilities. Never commit live provider credentials, `.env` files with secrets, or proprietary datasets.

## Trust and evidence rules

- A model-generated explanation is **not** proof of successful execution.
- Do not weaken task contracts, risk policies, verification gates or evidence checks merely to pass a test.
- The valid verdicts are `VERIFIED_PASS`, `VERIFIED_FAIL`, `BLOCKED`, `INCOMPLETE`, and `UNKNOWN`. Do not treat `UNKNOWN` as success.
- Default tests are offline and deterministic. Live provider tests are opt-in and may incur charges.
- Treat external model output and third-party fixture content as untrusted input.

Maintainers may request a smaller patch or additional evidence before merging; no automated test suite proves correctness outside its encoded requirements.
