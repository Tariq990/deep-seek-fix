from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from deep_seek_fix.contracts.io import load_contract
from deep_seek_fix.evidence.ledger import EvidenceLedger
from deep_seek_fix.git_state import is_worktree_clean
from deep_seek_fix.types import FinalVerdict


class DeliveryReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verdict: FinalVerdict
    reasons: list[str] = Field(default_factory=list)
    evidence_count: int = 0


def verify_delivery(repo: Path, contract_path: Path, ledger_path: Path) -> DeliveryReport:
    reasons: list[str] = []
    try:
        contract = load_contract(contract_path)
    except ValueError as exc:
        return DeliveryReport(verdict=FinalVerdict.VERIFIED_FAIL, reasons=[str(exc)])

    ledger = EvidenceLedger.from_path(ledger_path)
    records = ledger.list()
    if not records:
        reasons.append("no evidence records found")
    if not is_worktree_clean(repo):
        reasons.append("working tree is not clean")
    for required in contract.required_commands:
        if not any(required in record.normalized_command for record in records):
            reasons.append(f"required command was not evidenced: {required}")
    for required_test in contract.required_tests:
        if not any(required_test in record.command for record in records):
            reasons.append(f"required test was not evidenced: {required_test}")
    return DeliveryReport(
        verdict=FinalVerdict.VERIFIED_FAIL if reasons else FinalVerdict.VERIFIED_PASS,
        reasons=reasons,
        evidence_count=len(records),
    )
