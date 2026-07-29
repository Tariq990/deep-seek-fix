from __future__ import annotations

from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import Any, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from deep_seek_fix.security import canonical_json, sha256_text

NetworkPolicy = Literal["deny_by_default", "allow_list", "offline_only", "read_only_diagnostic"]

REQUIRED_CONTRACT_FIELDS = [
    "schema_version",
    "task_id",
    "objective",
    "non_goals",
    "allowed_paths",
    "protected_paths",
    "forbidden_commands",
    "required_commands",
    "required_tests",
    "acceptance_criteria",
    "maximum_cost_usd",
    "maximum_steps",
    "maximum_repeated_action_count",
    "network_policy",
    "created_at",
    "contract_hash",
]


class TaskContract(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        json_schema_extra=cast(dict[str, Any], {"required": REQUIRED_CONTRACT_FIELDS}),
    )

    schema_version: Literal["1.0"] = "1.0"
    task_id: str = Field(pattern=r"^TASK-[A-Za-z0-9_.-]+$")
    objective: str = Field(min_length=1)
    non_goals: list[str] = Field(default_factory=list)
    allowed_paths: list[str] = Field(default_factory=list)
    protected_paths: list[str] = Field(default_factory=list)
    forbidden_commands: list[str] = Field(default_factory=list)
    required_commands: list[str] = Field(default_factory=list)
    required_tests: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    maximum_cost_usd: float = Field(default=5.0, ge=0.0)
    maximum_steps: int = Field(default=100, ge=1)
    maximum_repeated_action_count: int = Field(default=1, ge=0)
    network_policy: NetworkPolicy = "deny_by_default"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    contract_hash: str | None = Field(default=None, pattern=r"^sha256:[a-f0-9]{64}$")

    @model_validator(mode="before")
    @classmethod
    def require_all_contract_fields(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        missing = [field for field in REQUIRED_CONTRACT_FIELDS if field not in data]
        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"missing required contract fields: {joined}")
        return data

    @field_validator("allowed_paths", "protected_paths")
    @classmethod
    def normalize_paths(cls, paths: list[str]) -> list[str]:
        normalized: list[str] = []
        for raw_path in paths:
            path = raw_path.replace("\\", "/").strip()
            if not path or path.startswith("/") or ".." in PurePosixPath(path).parts:
                raise ValueError(f"path is not repository-relative and safe: {raw_path}")
            normalized.append(path.rstrip("/"))
        return normalized

    @model_validator(mode="after")
    def validate_contract(self) -> TaskContract:
        allowed = set(self.allowed_paths)
        protected = set(self.protected_paths)
        overlap = {
            protected_path
            for allowed_path in allowed
            for protected_path in protected
            if protected_path == allowed_path
            or protected_path.startswith(f"{allowed_path}/")
            or allowed_path.startswith(f"{protected_path}/")
        }
        if overlap:
            joined = ", ".join(sorted(overlap))
            raise ValueError(f"protected paths cannot be allowed paths: {joined}")
        if self.contract_hash is not None and self.contract_hash != self.computed_hash():
            raise ValueError("contract_hash does not match canonical contract payload")
        return self

    def canonical_payload(self) -> dict[str, object]:
        payload = self.model_dump(mode="json", exclude={"contract_hash"})
        return dict(sorted(payload.items()))

    def canonical_json(self) -> str:
        return canonical_json(self.canonical_payload())

    def computed_hash(self) -> str:
        return sha256_text(self.canonical_json())

    def with_recomputed_hash(self) -> TaskContract:
        return self.model_copy(update={"contract_hash": self.computed_hash()})


def create_contract(**data: object) -> TaskContract:
    defaults: dict[str, object] = {
        "schema_version": "1.0",
        "non_goals": [],
        "allowed_paths": [],
        "protected_paths": [],
        "forbidden_commands": [],
        "required_commands": [],
        "required_tests": [],
        "acceptance_criteria": [],
        "maximum_cost_usd": 5.0,
        "maximum_steps": 100,
        "maximum_repeated_action_count": 1,
        "network_policy": "deny_by_default",
        "created_at": datetime.now(UTC),
        "contract_hash": None,
    }
    defaults.update(data)
    contract = TaskContract(**defaults)
    return contract.with_recomputed_hash()
