import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from deep_seek_fix.types import FinalVerdict


class BenchmarkCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    description: str
    expected_policy_result: str
    expected_final_verdict: FinalVerdict


class BenchmarkReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cases: int
    false_pass_rate: float
    false_pass_count: int


def load_cases(path: Path) -> list[BenchmarkCase]:
    raw_cases = json.loads(path.read_text(encoding="utf-8"))
    return [BenchmarkCase.model_validate(item) for item in raw_cases]


def smoke_report(dataset_path: Path) -> BenchmarkReport:
    cases = load_cases(dataset_path)
    false_pass_count = sum(
        1 for case in cases if case.expected_final_verdict == FinalVerdict.VERIFIED_PASS
    )
    return BenchmarkReport(
        cases=len(cases),
        false_pass_count=false_pass_count,
        false_pass_rate=false_pass_count / len(cases) if cases else 1.0,
    )
