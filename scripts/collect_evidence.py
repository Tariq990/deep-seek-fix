from __future__ import annotations

import argparse
import os
import shlex
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from deep_seek_fix.contracts.io import load_contract  # noqa: E402
from deep_seek_fix.evidence.ledger import EvidenceLedger  # noqa: E402
from deep_seek_fix.execution.executor import ExecutionRequest, GovernedExecutor  # noqa: E402


def split_command(command: str) -> list[str]:
    return shlex.split(command, posix=os.name != "nt")


def safe_print(text: str) -> None:
    encoding = sys.stdout.encoding or "utf-8"
    safe_text = text.encode(encoding, errors="backslashreplace").decode(
        encoding,
        errors="replace",
    )
    print(safe_text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", default="contract.json")
    parser.add_argument("--ledger", default=".dsfix/evidence.sqlite3")
    parser.add_argument("--run-id", default="RUN-CI")
    args = parser.parse_args()

    repo = Path.cwd()
    contract = load_contract(repo / args.contract)
    ledger_path = repo / args.ledger
    if ledger_path.exists():
        ledger_path.unlink()
    ledger = EvidenceLedger.from_path(ledger_path)
    executor = GovernedExecutor(repo, ledger)

    for command in contract.required_commands:
        result = executor.run(
            ExecutionRequest(command=split_command(command)),
            contract,
            task_id=contract.task_id,
            run_id=args.run_id,
        )
        safe_print(result.model_dump_json(indent=2))
        if result.exit_code != 0:
            return result.exit_code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
