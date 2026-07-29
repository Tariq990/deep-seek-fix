from __future__ import annotations

import subprocess  # nosec B404
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from deep_seek_fix.contracts.model import TaskContract
from deep_seek_fix.evidence.ledger import EvidenceLedger
from deep_seek_fix.evidence.models import EvidenceRecord, new_evidence_id
from deep_seek_fix.git_state import repository_head_sha, working_tree_hash
from deep_seek_fix.policies.engine import CombinedPolicyEngine, PolicyEffect, PolicyRequest
from deep_seek_fix.security import environment_fingerprint, redact_secrets, safe_output_hash


class ExecutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command: list[str] = Field(min_length=1)
    cwd: str = "."
    timeout_seconds: int = Field(default=120, ge=1, le=3600)
    output_limit_bytes: int = Field(default=262_144, ge=1024)
    writes: list[str] = Field(default_factory=list)
    dry_run: bool = False
    read_only: bool = False


class ExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str | None
    exit_code: int
    stdout: str
    stderr: str
    policy_effect: PolicyEffect
    policy_reasons: list[str]
    timed_out: bool = False


class GovernedExecutor:
    def __init__(
        self,
        repo: Path,
        ledger: EvidenceLedger,
        policy: CombinedPolicyEngine | None = None,
    ) -> None:
        self.repo = repo.resolve()
        self.ledger = ledger
        self.policy = policy or CombinedPolicyEngine()

    def run(
        self,
        request: ExecutionRequest,
        contract: TaskContract,
        *,
        task_id: str,
        run_id: str,
    ) -> ExecutionResult:
        cwd = (self.repo / request.cwd).resolve()
        policy_request = PolicyRequest(
            command=request.command,
            cwd=str(cwd),
            writes=request.writes,
            network=False,
        )
        policy_result = self.policy.evaluate(policy_request, contract, self.repo)
        if policy_result.effect != PolicyEffect.ALLOW:
            return ExecutionResult(
                evidence_id=None,
                exit_code=126,
                stdout="",
                stderr="; ".join(policy_result.reasons),
                policy_effect=policy_result.effect,
                policy_reasons=policy_result.reasons,
            )
        if request.dry_run:
            return ExecutionResult(
                evidence_id=None,
                exit_code=0,
                stdout=policy_result.normalized_command,
                stderr="",
                policy_effect=policy_result.effect,
                policy_reasons=[],
            )

        started = datetime.now(UTC)
        timed_out = False
        try:
            completed = subprocess.run(  # nosec B603
                request.command,
                cwd=cwd,
                shell=False,
                check=False,
                capture_output=True,
                timeout=request.timeout_seconds,
            )
            stdout_raw = completed.stdout[: request.output_limit_bytes]
            stderr_raw = completed.stderr[: request.output_limit_bytes]
            exit_code = completed.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout_raw = (exc.stdout or b"")[: request.output_limit_bytes]
            stderr_raw = (exc.stderr or b"")[: request.output_limit_bytes] + b"\nTIMEOUT"
            exit_code = 124
        finished = datetime.now(UTC)

        stdout_text = stdout_raw.decode("utf-8", errors="replace")
        stderr_text = stderr_raw.decode("utf-8", errors="replace")
        record = EvidenceRecord(
            evidence_id=new_evidence_id(),
            task_id=task_id,
            run_id=run_id,
            contract_hash=contract.computed_hash(),
            repository_head_sha=repository_head_sha(self.repo),
            working_tree_hash=working_tree_hash(self.repo),
            environment_hash=environment_fingerprint(),
            command=" ".join(request.command),
            normalized_command=policy_result.normalized_command,
            started_at=started,
            finished_at=finished,
            exit_code=exit_code,
            stdout_sha256=safe_output_hash(stdout_text),
            stderr_sha256=safe_output_hash(stderr_text),
            artifact_paths=[],
        )
        self.ledger.append(record)
        return ExecutionResult(
            evidence_id=record.evidence_id,
            exit_code=exit_code,
            stdout=redact_secrets(stdout_text),
            stderr=redact_secrets(stderr_text),
            policy_effect=policy_result.effect,
            policy_reasons=[],
            timed_out=timed_out,
        )
