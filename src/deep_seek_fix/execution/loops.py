from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from deep_seek_fix.security import canonical_json, sha256_text
from deep_seek_fix.types import FailureClassification


class ActionFingerprint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tool_name: str
    normalized_arguments: list[str]
    relevant_state_hash: str
    previous_result_classification: FailureClassification

    def digest(self) -> str:
        return sha256_text(canonical_json(self.model_dump(mode="json")))


def classify_failed_action(command: str, exit_code: int, stderr: str) -> FailureClassification:
    normalized = command.lower()
    output = stderr.lower()
    if exit_code == 124 or "timeout" in output:
        return FailureClassification.TIMEOUT
    if "rate limit" in output or "429" in output:
        return FailureClassification.RATE_LIMIT
    if "policy" in output or exit_code == 126:
        return FailureClassification.POLICY_DENIAL
    if "pytest" in normalized or "vitest" in normalized or "node --test" in normalized:
        return FailureClassification.TEST_FAILURE
    return FailureClassification.TOOL_RUNTIME_ERROR


def command_tool_name(command: list[str]) -> str:
    return command[0].lower() if command else "unknown"
