from pathlib import Path

from deep_seek_fix.contracts.model import create_contract
from deep_seek_fix.evidence.ledger import EvidenceLedger
from deep_seek_fix.execution.executor import ExecutionRequest, GovernedExecutor
from deep_seek_fix.policies.engine import PolicyEffect


def test_executor_records_process_exit_code(tmp_path: Path) -> None:
    ledger = EvidenceLedger.from_path(tmp_path / "ledger.sqlite3")
    contract = create_contract(task_id="TASK-EXEC", objective="run", allowed_paths=["."])
    executor = GovernedExecutor(Path.cwd(), ledger)
    result = executor.run(
        ExecutionRequest(command=["python", "-c", "raise SystemExit(3)"]),
        contract,
        task_id="TASK-EXEC",
        run_id="RUN-EXEC",
    )
    assert result.exit_code == 3
    assert result.evidence_id is not None
    assert ledger.get(result.evidence_id).exit_code == 3


def test_executor_denies_policy_violation(tmp_path: Path) -> None:
    ledger = EvidenceLedger.from_path(tmp_path / "ledger.sqlite3")
    contract = create_contract(
        task_id="TASK-EXEC",
        objective="run",
        forbidden_commands=["git push"],
    )
    executor = GovernedExecutor(Path.cwd(), ledger)
    result = executor.run(
        ExecutionRequest(command=["git", "push", "--no-verify"]),
        contract,
        task_id="TASK-EXEC",
        run_id="RUN-EXEC",
    )
    assert result.policy_effect == PolicyEffect.DENY
    assert result.evidence_id is None
