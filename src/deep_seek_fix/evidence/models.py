from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from deep_seek_fix.types import Classification


class EvidenceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: str = Field(pattern=r"^EV-[A-Za-z0-9_.-]+$")
    task_id: str = Field(pattern=r"^TASK-[A-Za-z0-9_.-]+$")
    run_id: str = Field(pattern=r"^RUN-[A-Za-z0-9_.-]+$")
    contract_hash: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    repository_head_sha: str
    working_tree_hash: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    environment_hash: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    command: str
    normalized_command: str
    started_at: datetime
    finished_at: datetime
    exit_code: int
    stdout_sha256: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    stderr_sha256: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    artifact_paths: list[str] = Field(default_factory=list)
    classification: Classification = Classification.COMMAND_RESULT


def new_evidence_id() -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
    return f"EV-{stamp}"
