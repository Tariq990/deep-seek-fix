from datetime import UTC, datetime
from pathlib import Path

from deep_seek_fix.contracts.model import create_contract
from deep_seek_fix.evidence.freshness import verify_evidence_freshness
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


def test_stale_contract_hash_is_rejected() -> None:
    contract = create_contract(task_id="TASK-LEDGER", objective="fresh")
    record = make_record("EV-FRESH")
    fresh, reasons = verify_evidence_freshness(
        Path.cwd(),
        contract,
        record,
        require_after_latest_change=False,
    )
    assert not fresh
    assert "contract hash mismatch" in reasons


def test_malformed_evidence_model_fails_closed() -> None:
    data = make_record("EV-MALFORMED").model_dump()
    data["exit_code"] = "not-an-int"
    try:
        EvidenceRecord.model_validate(data)
    except ValueError as exc:
        assert "exit_code" in str(exc)
    else:
        raise AssertionError("malformed evidence was accepted")
