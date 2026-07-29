from deep_seek_fix.verification.claims import (
    PushClassification,
    classify_push,
    output_mentions_zero_tests,
)


def test_zero_tests_are_detected() -> None:
    assert output_mentions_zero_tests("collected 0 items")
    assert output_mentions_zero_tests("no tests ran")


def test_noop_push_is_not_fresh_update() -> None:
    assert classify_push("abc", "abc", "abc", 0) == PushClassification.VERIFIED_NO_OP


def test_fresh_push_requires_remote_sha_change_to_local() -> None:
    assert classify_push("abc", "def", "def", 0) == PushClassification.FRESH_VERIFIED_PUSH


def test_failed_push_is_failed() -> None:
    assert classify_push("abc", "def", "abc", 1) == PushClassification.PUSH_FAILED
