from pathlib import Path

from deep_seek_fix.contracts.model import TaskContract
from deep_seek_fix.evidence.models import EvidenceRecord
from deep_seek_fix.git_state import newest_file_mtime, repository_head_sha, working_tree_hash
from deep_seek_fix.security import environment_fingerprint


def verify_evidence_freshness(
    repo: Path,
    contract: TaskContract,
    record: EvidenceRecord,
    *,
    require_after_latest_change: bool = True,
) -> tuple[bool, list[str]]:
    problems: list[str] = []
    if record.contract_hash != contract.computed_hash():
        problems.append("contract hash mismatch")
    if record.repository_head_sha != repository_head_sha(repo):
        problems.append("repository head mismatch")
    if record.working_tree_hash != working_tree_hash(repo):
        problems.append("working tree hash mismatch")
    if record.environment_hash != environment_fingerprint():
        problems.append("environment hash mismatch")
    if require_after_latest_change and record.finished_at.timestamp() < newest_file_mtime(repo):
        problems.append("evidence predates the newest file change")
    return not problems, problems
