# Agent Instructions

This repository is a deterministic reliability control plane. Agent output is never accepted as proof of completion.

- Do not use `git push --no-verify`, force-push, `git commit --amend`, or rebase published history.
- Do not place real API keys or authorization headers in files, logs, tests, screenshots, or commits.
- Treat task contracts, evidence ledgers, gates, and policies as protected during active runs.
- Use `scripts/verify.ps1` on Windows or `scripts/verify.sh` on POSIX before delivery claims.
- Final verdicts are produced by deterministic code only.

