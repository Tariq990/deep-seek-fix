from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from deep_seek_fix.contracts.model import TaskContract, create_contract
from deep_seek_fix.evidence.ledger import EvidenceLedger
from deep_seek_fix.evidence.models import EvidenceRecord
from deep_seek_fix.git_state import repository_head_sha, working_tree_hash
from deep_seek_fix.security import environment_fingerprint, sha256_text
from deep_seek_fix.types import Classification, FinalVerdict
from deep_seek_fix.verification.claims import Claim, ClaimType, ClaimVerifier


def make_fresh_record(
    contract: TaskContract,
    *,
    evidence_id: str,
    command: str,
    stdout: str,
    exit_code: int = 0,
    stdout_truncated: bool = False,
) -> EvidenceRecord:
    now = datetime.now(UTC)
    return EvidenceRecord(
        evidence_id=evidence_id,
        task_id=contract.task_id,
        run_id="RUN-CLAIMS",
        contract_hash=contract.computed_hash(),
        repository_head_sha=repository_head_sha(Path.cwd()),
        working_tree_hash=working_tree_hash(Path.cwd()),
        environment_hash=environment_fingerprint(),
        command=command,
        normalized_command=command,
        started_at=now,
        finished_at=now,
        exit_code=exit_code,
        stdout_sha256=sha256_text(stdout),
        stderr_sha256=sha256_text(""),
        stdout_redacted=stdout,
        stderr_redacted="",
        stdout_truncated=stdout_truncated,
        stderr_truncated=False,
        artifact_paths=[],
        classification=Classification.COMMAND_RESULT,
    )


def test_zero_test_output_rejects_test_pass_claim(tmp_path: Path) -> None:
    contract = create_contract(task_id="TASK-CLAIMS", objective="claims")
    ledger = EvidenceLedger.from_path(tmp_path / "ledger.sqlite3")
    record = make_fresh_record(
        contract,
        evidence_id="EV-ZERO",
        command="pytest",
        stdout="collected 0 items\n",
    )
    ledger.append(record)

    result = ClaimVerifier(Path.cwd(), ledger, contract).verify(
        Claim(
            claim_type=ClaimType.FULL_TESTS_PASSED,
            statement="full tests passed",
            required_evidence=[Classification.COMMAND_RESULT],
            evidence_ids=["EV-ZERO"],
        )
    )

    assert result.verdict == FinalVerdict.VERIFIED_FAIL
    assert any("zero executed tests" in reason for reason in result.reasons)


def test_required_test_claim_requires_node_id_in_evidence(tmp_path: Path) -> None:
    contract = create_contract(
        task_id="TASK-CLAIMS",
        objective="claims",
        required_tests=["tests/adversarial/test_reliability_scenarios.py"],
    )
    ledger = EvidenceLedger.from_path(tmp_path / "ledger.sqlite3")
    ledger.append(
        make_fresh_record(
            contract,
            evidence_id="EV-MISSING-NODE",
            command="pytest tests/unit",
            stdout="collected 10 items\n10 passed\n",
        )
    )

    result = ClaimVerifier(Path.cwd(), ledger, contract).verify(
        Claim(
            claim_type=ClaimType.REQUIRED_TESTS_EXECUTED,
            statement="required tests ran",
            required_evidence=[Classification.COMMAND_RESULT],
            evidence_ids=["EV-MISSING-NODE"],
        )
    )

    assert result.verdict == FinalVerdict.VERIFIED_FAIL
    assert any("required test node id absent" in reason for reason in result.reasons)


def test_required_test_claim_passes_when_node_id_is_evidenced(tmp_path: Path) -> None:
    required = "tests/adversarial/test_reliability_scenarios.py"
    contract = create_contract(
        task_id="TASK-CLAIMS",
        objective="claims",
        required_tests=[required],
    )
    ledger = EvidenceLedger.from_path(tmp_path / "ledger.sqlite3")
    ledger.append(
        make_fresh_record(
            contract,
            evidence_id="EV-REQUIRED-NODE",
            command=f"pytest {required}",
            stdout="collected 51 items\n51 passed\n",
        )
    )

    result = ClaimVerifier(Path.cwd(), ledger, contract).verify(
        Claim(
            claim_type=ClaimType.REQUIRED_TESTS_EXECUTED,
            statement="required tests ran",
            required_evidence=[Classification.COMMAND_RESULT],
            evidence_ids=["EV-REQUIRED-NODE"],
        )
    )

    assert result.verdict == FinalVerdict.VERIFIED_PASS
    assert result.reasons == []


def test_truncated_output_rejects_test_claim(tmp_path: Path) -> None:
    contract = create_contract(task_id="TASK-CLAIMS", objective="claims")
    ledger = EvidenceLedger.from_path(tmp_path / "ledger.sqlite3")
    ledger.append(
        make_fresh_record(
            contract,
            evidence_id="EV-TRUNCATED",
            command="pytest",
            stdout="collected 1 item\n",
            stdout_truncated=True,
        )
    )

    result = ClaimVerifier(Path.cwd(), ledger, contract).verify(
        Claim(
            claim_type=ClaimType.FULL_TESTS_PASSED,
            statement="full tests passed",
            required_evidence=[Classification.COMMAND_RESULT],
            evidence_ids=["EV-TRUNCATED"],
        )
    )

    assert result.verdict == FinalVerdict.VERIFIED_FAIL
    assert any("truncated output" in reason for reason in result.reasons)
