from deep_seek_fix.execution.loops import (
    ActionFingerprint,
    classify_failed_action,
    command_tool_name,
)
from deep_seek_fix.types import FailureClassification


def test_action_fingerprint_is_deterministic() -> None:
    first = ActionFingerprint(
        tool_name="python",
        normalized_arguments=["-m", "pytest"],
        relevant_state_hash="sha256:" + "a" * 64,
        previous_result_classification=FailureClassification.TEST_FAILURE,
    )
    second = ActionFingerprint.model_validate(first.model_dump())
    assert first.digest() == second.digest()


def test_action_fingerprint_changes_with_state() -> None:
    base = {
        "tool_name": "python",
        "normalized_arguments": ["-m", "pytest"],
        "previous_result_classification": FailureClassification.TEST_FAILURE,
    }
    first = ActionFingerprint(**base, relevant_state_hash="sha256:" + "a" * 64)
    second = ActionFingerprint(**base, relevant_state_hash="sha256:" + "b" * 64)
    assert first.digest() != second.digest()


def test_failed_action_classification() -> None:
    assert classify_failed_action("pytest tests/unit", 1, "") == FailureClassification.TEST_FAILURE
    assert classify_failed_action("provider", 124, "timeout") == FailureClassification.TIMEOUT
    assert (
        classify_failed_action("provider", 1, "429 rate limit") == FailureClassification.RATE_LIMIT
    )
    assert classify_failed_action("git push", 126, "policy") == FailureClassification.POLICY_DENIAL
    assert classify_failed_action("tool", 2, "boom") == FailureClassification.TOOL_RUNTIME_ERROR


def test_command_tool_name() -> None:
    assert command_tool_name(["Python", "-m", "pytest"]) == "python"
    assert command_tool_name([]) == "unknown"
