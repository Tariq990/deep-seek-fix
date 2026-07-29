#!/usr/bin/env sh
set -eu
uv sync --all-extras --dev
pnpm install --frozen-lockfile

