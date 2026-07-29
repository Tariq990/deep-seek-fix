from __future__ import annotations

import re
import shlex
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from deep_seek_fix.contracts.model import TaskContract
from deep_seek_fix.security import resolve_under


class PolicyEffect(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


class PolicyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command: list[str] = Field(min_length=1)
    cwd: str
    writes: list[str] = Field(default_factory=list)
    network: bool = False


class PolicyResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    effect: PolicyEffect
    reasons: list[str] = Field(default_factory=list)
    normalized_command: str


FORBIDDEN_REGEXES = [
    re.compile(r"\bgit\s+push\b.*--no-verify", re.IGNORECASE),
    re.compile(r"\bgit\s+push\b.*--force(?:-with-lease)?\b", re.IGNORECASE),
    re.compile(r"\bgit\s+commit\b.*--amend\b", re.IGNORECASE),
    re.compile(r"\b(rm|del|erase|Remove-Item)\b.*(-rf|-r|-Recurse)", re.IGNORECASE),
    re.compile(r"(curl|Invoke-WebRequest|wget).*(\||iex|bash|sh)", re.IGNORECASE),
    re.compile(r"\b(env|Get-ChildItem\s+Env:|printenv)\b", re.IGNORECASE),
]

SEPARATORS = ["&&", "||", ";", "|"]
UNICODE_CONTROLS = re.compile(r"[\u202a-\u202e\u2066-\u2069]")


def normalize_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part.strip()) for part in command if part.strip())


class LocalPolicyEngine:
    def evaluate(self, request: PolicyRequest, contract: TaskContract, repo: Path) -> PolicyResult:
        normalized = normalize_command(request.command)
        reasons: list[str] = []
        if not request.command:
            reasons.append("missing command")
        if UNICODE_CONTROLS.search(normalized):
            reasons.append("hidden unicode control character")
        if any(separator in normalized for separator in SEPARATORS):
            reasons.append("command chaining or piping is denied")
        for forbidden in contract.forbidden_commands:
            if forbidden.lower() in normalized.lower():
                reasons.append(f"contract-forbidden command: {forbidden}")
        for pattern in FORBIDDEN_REGEXES:
            if pattern.search(normalized):
                reasons.append(f"policy-forbidden command pattern: {pattern.pattern}")
        if request.network and contract.network_policy in {"deny_by_default", "offline_only"}:
            reasons.append("network denied by contract")
        for raw_write in request.writes:
            write_path = (Path(request.cwd) / raw_write).resolve()
            if not resolve_under(repo, write_path):
                reasons.append(f"write outside workspace: {raw_write}")
                continue
            relative = write_path.relative_to(repo.resolve()).as_posix()
            protected = (
                relative == path or relative.startswith(f"{path}/")
                for path in contract.protected_paths
            )
            if any(protected):
                reasons.append(f"write touches protected path: {raw_write}")
            if contract.allowed_paths and not any(
                relative == path or relative.startswith(f"{path}/")
                for path in contract.allowed_paths
            ):
                reasons.append(f"write outside allowed paths: {raw_write}")
        effect = PolicyEffect.DENY if reasons else PolicyEffect.ALLOW
        return PolicyResult(effect=effect, reasons=reasons, normalized_command=normalized)


class AgentGovernanceToolkitAdapter:
    def evaluate(self, request: PolicyRequest, contract: TaskContract, repo: Path) -> PolicyResult:
        del request, repo
        if contract.network_policy == "read_only_diagnostic":
            return PolicyResult(
                effect=PolicyEffect.REQUIRE_APPROVAL,
                reasons=["AGT adapter unavailable in diagnostic mode"],
                normalized_command="",
            )
        return PolicyResult(
            effect=PolicyEffect.DENY,
            reasons=["AGT adapter unavailable"],
            normalized_command="",
        )


class CombinedPolicyEngine:
    def __init__(self, *, require_agt: bool = False) -> None:
        self.local = LocalPolicyEngine()
        self.agt = AgentGovernanceToolkitAdapter()
        self.require_agt = require_agt

    def evaluate(self, request: PolicyRequest, contract: TaskContract, repo: Path) -> PolicyResult:
        local = self.local.evaluate(request, contract, repo)
        if not self.require_agt:
            return local
        agt = self.agt.evaluate(request, contract, repo)
        reasons = [*local.reasons, *agt.reasons]
        normalized = local.normalized_command
        if PolicyEffect.DENY in {local.effect, agt.effect}:
            return PolicyResult(
                effect=PolicyEffect.DENY,
                reasons=reasons,
                normalized_command=normalized,
            )
        if PolicyEffect.REQUIRE_APPROVAL in {local.effect, agt.effect}:
            return PolicyResult(
                effect=PolicyEffect.REQUIRE_APPROVAL,
                reasons=reasons,
                normalized_command=normalized,
            )
        return PolicyResult(
            effect=PolicyEffect.ALLOW,
            reasons=reasons,
            normalized_command=normalized,
        )
