import subprocess  # nosec B404
from pathlib import Path

from deep_seek_fix.security import sha256_text


def run_git(repo: Path, args: list[str]) -> str:
    result = subprocess.run(  # nosec
        ["git", *args],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def repository_head_sha(repo: Path) -> str:
    head = run_git(repo, ["rev-parse", "HEAD"])
    return head or "NO_COMMIT"


def working_tree_hash(repo: Path) -> str:
    status = run_git(repo, ["status", "--porcelain=v1", "-z"])
    diff = run_git(repo, ["diff", "--binary"])
    staged = run_git(repo, ["diff", "--cached", "--binary"])
    return sha256_text(status + "\0" + diff + "\0" + staged)


def is_worktree_clean(repo: Path) -> bool:
    return run_git(repo, ["status", "--porcelain=v1"]) == ""


def newest_file_mtime(repo: Path) -> float:
    newest = 0.0
    ignored = {
        ".dsfix",
        ".git",
        ".venv",
        ".coverage",
        "coverage",
        "dist",
        "node_modules",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
    }
    for path in repo.rglob("*"):
        if any(part in ignored for part in path.parts):
            continue
        if path.is_file():
            newest = max(newest, path.stat().st_mtime)
    return newest
