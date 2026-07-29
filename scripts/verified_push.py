from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from deep_seek_fix.git_state import is_worktree_clean, repository_head_sha
from deep_seek_fix.types import FinalVerdict
from deep_seek_fix.verification.claims import classify_push
from deep_seek_fix.verification.delivery import verify_delivery


def run_git(repo: Path, args: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(  # noqa: S603
        ["git", *args],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--contract", default="contract.json")
    parser.add_argument("--ledger", default=".dsfix/evidence.sqlite3")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--branch", default="main")
    args = parser.parse_args()

    repo = Path.cwd()
    report = verify_delivery(repo, repo / args.contract, repo / args.ledger)
    if report.verdict != FinalVerdict.VERIFIED_PASS:
        print(report.model_dump_json(indent=2))
        return 1
    if not is_worktree_clean(repo):
        print("FAILED: working tree is not clean")
        return 1
    local_sha = repository_head_sha(repo)
    _, before_sha, _ = run_git(repo, ["ls-remote", args.remote, f"refs/heads/{args.branch}"])
    before = before_sha.split("\t")[0] if before_sha else None
    if args.dry_run:
        print("verified_push dry run: delivery gate verified; push not attempted")
        return 0
    exit_code, stdout, stderr = run_git(repo, ["push", args.remote, args.branch])
    print(stdout)
    print(stderr)
    _, after_sha, _ = run_git(repo, ["ls-remote", args.remote, f"refs/heads/{args.branch}"])
    after = after_sha.split("\t")[0] if after_sha else None
    classification = classify_push(before, local_sha, after, exit_code)
    print(classification)
    return 0 if "VERIFIED" in classification else 1


if __name__ == "__main__":
    raise SystemExit(main())
