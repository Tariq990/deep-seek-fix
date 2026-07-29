from pathlib import Path

from deep_seek_fix.contracts.model import create_contract
from deep_seek_fix.policies.engine import CombinedPolicyEngine, PolicyEffect, PolicyRequest


def evaluate(command: list[str], tmp_path: Path, writes: list[str] | None = None) -> PolicyEffect:
    contract = create_contract(
        task_id="TASK-POLICY",
        objective="policy",
        allowed_paths=["src"],
        protected_paths=["contract.json"],
        forbidden_commands=["git push"],
    )
    request = PolicyRequest(command=command, cwd=str(tmp_path), writes=writes or [])
    return CombinedPolicyEngine().evaluate(request, contract, tmp_path).effect


def test_denies_no_verify() -> None:
    effect = evaluate(["git", "push", "--no-verify"], Path.cwd())
    assert effect == PolicyEffect.DENY


def test_denies_nested_shell_chaining() -> None:
    effect = evaluate(["powershell", "-Command", "pytest || true"], Path.cwd())
    assert effect == PolicyEffect.DENY


def test_denies_write_outside_workspace(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.txt"
    effect = evaluate(["python", "-m", "compileall", "src"], tmp_path, [str(outside)])
    assert effect == PolicyEffect.DENY


def test_denies_missing_field_bypass() -> None:
    contract = create_contract(task_id="TASK-POLICY-2", objective="policy")
    result = CombinedPolicyEngine(require_agt=True).evaluate(
        PolicyRequest(command=["python", "--version"], cwd=str(Path.cwd()), writes=[]),
        contract,
        Path.cwd(),
    )
    assert result.effect == PolicyEffect.DENY
