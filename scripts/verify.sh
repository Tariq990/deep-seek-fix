#!/usr/bin/env sh
set -eu
uv run python scripts/collect_evidence.py --run-id RUN-LOCAL
uv run dsfix verify delivery
python scripts/verified_push.py --dry-run
