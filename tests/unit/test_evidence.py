from datetime import UTC, datetime
from pathlib import Path

from deep_seek_fix.evidence.ledger import EvidenceLedger
from deep_seek_fix.evidence.models import EvidenceRecord
from deep_seek_fix.security import environment_fingerprint, sha256_text
from deep_seek_fix.types import Classification


def make_record(evidence_id: str) -> EvidenceRecord:
    now = datetime.now(UTC)
    return EvidenceRecord(
        evidence_id=evidence_id,
        task_id="TASK-LEDGER",
        run_id="RUN-1",
        contract_hash="sha256:" + "a" * 64,
        repository_head_sha="HEAD",
        working_tree_hash=sha256_text("tree"),
        environment_hash=environment_fingerprint(),
        command="pytest",
        normalized_command="pytest",
        started_at=now,
        finished_at=now,
        exit_code=0,
        stdout_sha256=sha256_text("ok"),
        stderr_sha256=sha256_text(""),
        artifact_paths=[],
        classification=Classification.COMMAND_RESULT,
    )


def test_ledger_is_append_only(tmp_path: Path) -> None:
    ledger = EvidenceLedger.from_path(tmp_path / "evidence.sqlite3")
    ledger.append(make_record("EV-1"))
    try:
        ledger.append(make_record("EV-1"))
    except ValueError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("ledger allowed overwriting evidence")


def test_ledger_lists_records(tmp_path: Path) -> None:
    ledger = EvidenceLedger.from_path(tmp_path / "evidence.sqlite3")
    ledger.append(make_record("EV-2"))
    assert [record.evidence_id for record in ledger.list()] == ["EV-2"]
