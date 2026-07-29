import json
from pathlib import Path

from pydantic import ValidationError

from deep_seek_fix.contracts.model import TaskContract, create_contract


def load_contract(path: Path) -> TaskContract:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"malformed contract JSON: {exc}") from exc
    try:
        return TaskContract.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"invalid task contract: {exc}") from exc


def write_contract(path: Path, **data: object) -> TaskContract:
    contract = create_contract(**data)
    path.write_text(
        json.dumps(contract.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return contract


def contract_schema_json() -> str:
    return json.dumps(TaskContract.model_json_schema(), indent=2, sort_keys=True) + "\n"
