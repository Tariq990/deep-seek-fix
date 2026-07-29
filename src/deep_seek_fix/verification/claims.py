from __future__ import annotations

import re
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from deep_seek_fix.contracts.model import TaskContract
from deep_seek_fix.evidence.freshness import verify_evidence_freshness
from deep_seek_fix.evidence.ledger import EvidenceLedger
from deep_seek_fix.evidence.models import EvidenceRecord
from deep_seek_fix.git_state import is_worktree_clean
from deep_seek_fix.types import Classification, FinalVerdict, PushClassification


class ClaimType(StrEnum):
    FOCUSED_TESTS_PASSED = "FOCUSED_TESTS_PASSED"
    FULL_TESTS_PASSED = "FULL_TESTS_PASSED"
    LINT_PASSED = "LINT_PASSED"
    TYPECHECK_PASSED = "TYPECHECK_PASSED"
    SECURITY_SCAN_PASSED = "SECURITY_SCAN_PASSED"
    WORKTREE_CLEAN = "WORKTREE_CLEAN"
    SCOPE_VALID = "SCOPE_VALID"
    REMOTE_PUSH_UPDATED = "REMOTE_PUSH_UPDATED"
    REMOTE_ALREADY_UP_TO_DATE = "REMOTE_ALREADY_UP_TO_DATE"
    REQUIRED_TESTS_EXECUTED = "REQUIRED_TESTS_EXECUTED"
    CONTRACT_UNCHANGED = "CONTRACT_UNCHANGED"
    NO_SECRET_DETECTED = "NO_SECRET_DETECTED"  # nosec B105
    DELIVERABLE_EXISTS = "DELIVERABLE_EXISTS"


class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_type: ClaimType
    statement: str
    required_evidence: list[Classification]
    evidence_ids: list[str]


class ClaimVerification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_type: ClaimType
    verdict: FinalVerdict
    reasons: list[str] = Field(default_factory=list)


ZERO_TEST_PATTERNS = [
    re.compile(r"\bcollected\s+0\s+items\b", re.IGNORECASE),
    re.compile(r"\b0\s+tests?\b", re.IGNORECASE),
    re.compile(r"\bno\s+tests?\s+(ran|found)\b", re.IGNORECASE),
]

NOT_EXECUTED_PATTERNS = [
    re.compile(r"\bcollected\b.*\b0\s+items\b", re.IGNORECASE | re.DOTALL),
    re.compile(r"\bdeselected\b", re.IGNORECASE),
    re.compile(r"\bnot\s+found\b", re.IGNORECASE),
    re.compile(r"\bno\s+tests?\s+(ran|found)\b", re.IGNORECASE),
]


def output_mentions_zero_tests(output: str) -> bool:
    return any(pattern.search(output) for pattern in ZERO_TEST_PATTERNS)


def output_mentions_not_executed(output: str) -> bool:
    return any(pattern.search(output) for pattern in NOT_EXECUTED_PATTERNS)


def combined_output(record: EvidenceRecord) -> str:
    return "\n".join(part for part in [record.stdout_redacted, record.stderr_redacted] if part)


def command_matches_claim(command: str, claim_type: ClaimType) -> bool:
    normalized = command.lower()
    mapping = {
        ClaimType.FOCUSED_TESTS_PASSED: ["pytest", "vitest", "node --test"],
        ClaimType.FULL_TESTS_PASSED: ["pytest", "pnpm test", "vitest", "node --test"],
        ClaimType.LINT_PASSED: ["ruff check", "eslint"],
        ClaimType.TYPECHECK_PASSED: ["mypy", "tsc", "pyright"],
        ClaimType.SECURITY_SCAN_PASSED: ["bandit", "pip-audit", "secret"],
        ClaimType.REQUIRED_TESTS_EXECUTED: ["pytest", "vitest", "node --test"],
    }
    expected = mapping.get(claim_type)
    if expected is None:
        return True
    return any(fragment in normalized for fragment in expected)


class ClaimVerifier:
    def __init__(self, repo: Path, ledger: EvidenceLedger, contract: TaskContract) -> None:
        self.repo = repo
        self.ledger = ledger
        self.contract = contract

    def verify(self, claim: Claim) -> ClaimVerification:
        reasons: list[str] = []
        if not claim.evidence_ids and claim.claim_type != ClaimType.WORKTREE_CLEAN:
            reasons.append("missing evidence")

        records: list[EvidenceRecord] = []
        for evidence_id in claim.evidence_ids:
            try:
                record = self.ledger.get(evidence_id)
            except KeyError:
                reasons.append(f"evidence not found: {evidence_id}")
                continue
            fresh, freshness_reasons = verify_evidence_freshness(self.repo, self.contract, record)
            if not fresh:
                reasons.extend(freshness_reasons)
            if record.exit_code != 0:
                reasons.append(f"nonzero exit code for {evidence_id}: {record.exit_code}")
            if record.classification not in claim.required_evidence:
                reasons.append(f"wrong evidence classification: {record.classification}")
            if not command_matches_claim(record.normalized_command, claim.claim_type):
                reasons.append(f"command does not prove claim: {record.normalized_command}")
            records.append(record)

        if claim.claim_type == ClaimType.WORKTREE_CLEAN and not is_worktree_clean(self.repo):
            reasons.append("working tree is not clean")
        if claim.claim_type in {
            ClaimType.FOCUSED_TESTS_PASSED,
            ClaimType.FULL_TESTS_PASSED,
            ClaimType.REQUIRED_TESTS_EXECUTED,
        }:
            if not records:
                reasons.append("no test command evidence")
            for record in records:
                output = combined_output(record)
                if not output.strip():
                    reasons.append(f"empty output cannot verify test claim: {record.evidence_id}")
                if output_mentions_zero_tests(output):
                    reasons.append(
                        f"zero executed tests cannot verify a test claim: {record.evidence_id}"
                    )
                if output_mentions_not_executed(output):
                    reasons.append(
                        f"collected-but-not-executed tests cannot verify claim: "
                        f"{record.evidence_id}"
                    )
                if record.stdout_truncated or record.stderr_truncated:
                    reasons.append(
                        f"truncated output cannot verify test claim: {record.evidence_id}"
                    )
        if claim.claim_type == ClaimType.REQUIRED_TESTS_EXECUTED:
            proof_parts: list[str] = []
            for record in records:
                proof_parts.extend(
                    [record.command, record.normalized_command, combined_output(record)]
                )
            proof_text = "\n".join(proof_parts)
            for required in self.contract.required_tests:
                if required not in proof_text:
                    reasons.append(f"required test node id absent: {required}")

        verdict = FinalVerdict.VERIFIED_FAIL if reasons else FinalVerdict.VERIFIED_PASS
        return ClaimVerification(claim_type=claim.claim_type, verdict=verdict, reasons=reasons)


def classify_push(
    before_sha: str | None,
    local_sha: str,
    after_sha: str | None,
    exit_code: int,
) -> PushClassification:
    if exit_code != 0:
        return PushClassification.PUSH_FAILED
    if after_sha is None:
        return PushClassification.PUSH_NOT_ATTEMPTED
    if after_sha != local_sha:
        return PushClassification.PUSH_FAILED
    if before_sha == after_sha:
        return PushClassification.VERIFIED_NO_OP
    return PushClassification.FRESH_VERIFIED_PUSH
