from pydantic import ValidationError

from deep_seek_fix.contracts.model import TaskContract, create_contract


def test_contract_hash_is_deterministic() -> None:
    first = create_contract(task_id="TASK-0001", objective="ship", allowed_paths=["src"])
    second = TaskContract.model_validate(first.model_dump())
    assert first.contract_hash == second.contract_hash
    assert first.computed_hash() == first.contract_hash


def test_contract_rejects_model_supplied_wrong_hash() -> None:
    data = create_contract(task_id="TASK-0002", objective="ship").model_dump()
    data["contract_hash"] = "sha256:" + "0" * 64
    try:
        TaskContract.model_validate(data)
    except ValidationError as exc:
        assert "contract_hash" in str(exc)
    else:
        raise AssertionError("wrong contract hash was accepted")


def test_protected_paths_cannot_be_allowed() -> None:
    try:
        create_contract(
            task_id="TASK-0003",
            objective="ship",
            allowed_paths=["contract.json"],
            protected_paths=["contract.json"],
        )
    except ValidationError as exc:
        assert "protected paths cannot be allowed paths" in str(exc)
    else:
        raise AssertionError("overlapping paths were accepted")


def test_unknown_schema_version_fails_closed() -> None:
    data = create_contract(task_id="TASK-0004", objective="ship").model_dump()
    data["schema_version"] = "9.9"
    try:
        TaskContract.model_validate(data)
    except ValidationError as exc:
        assert "schema_version" in str(exc)
    else:
        raise AssertionError("unknown schema version was accepted")


def test_missing_required_contract_fields_fail_closed() -> None:
    try:
        TaskContract.model_validate({"task_id": "TASK-0005", "objective": "ship"})
    except ValidationError as exc:
        assert "missing required contract fields" in str(exc)
    else:
        raise AssertionError("missing required contract fields were accepted")
