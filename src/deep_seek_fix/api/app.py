from pathlib import Path

from fastapi import FastAPI, HTTPException

from deep_seek_fix.contracts.io import write_contract
from deep_seek_fix.contracts.model import TaskContract
from deep_seek_fix.evidence.ledger import EvidenceLedger
from deep_seek_fix.evidence.models import EvidenceRecord
from deep_seek_fix.policies.engine import CombinedPolicyEngine, PolicyRequest, PolicyResult
from deep_seek_fix.types import FinalVerdict
from deep_seek_fix.verification.delivery import DeliveryReport

app = FastAPI(title="Deep Seek Fix Control Plane", version="0.1.0")
REPO = Path.cwd()
LEDGER = EvidenceLedger.from_path(REPO / ".dsfix" / "evidence.sqlite3")
CONTRACTS: dict[str, TaskContract] = {}
RUNS: dict[str, dict[str, str]] = {}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/contracts")
def create_contract_endpoint(contract: TaskContract) -> TaskContract:
    created = contract.with_recomputed_hash()
    CONTRACTS[created.task_id] = created
    path = REPO / ".dsfix" / "contracts" / f"{created.task_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    write_contract(path, **created.model_dump(exclude={"contract_hash"}))
    return created


@app.get("/v1/contracts/{task_id}")
def get_contract(task_id: str) -> TaskContract:
    try:
        return CONTRACTS[task_id]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail={"error": "contract not found"}) from exc


@app.post("/v1/runs")
def create_run(payload: dict[str, str]) -> dict[str, str]:
    run_id = payload.get("run_id")
    task_id = payload.get("task_id")
    if not run_id or not task_id:
        raise HTTPException(status_code=422, detail={"error": "run_id and task_id are required"})
    RUNS[run_id] = {"run_id": run_id, "task_id": task_id}
    return RUNS[run_id]


@app.get("/v1/runs/{run_id}")
def get_run(run_id: str) -> dict[str, str]:
    try:
        return RUNS[run_id]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail={"error": "run not found"}) from exc


@app.post("/v1/policy/evaluate")
def evaluate_policy(request: PolicyRequest) -> PolicyResult:
    if not CONTRACTS:
        raise HTTPException(status_code=409, detail={"error": "no active contract"})
    contract = next(iter(CONTRACTS.values()))
    return CombinedPolicyEngine().evaluate(request, contract, REPO)


@app.post("/v1/evidence")
def append_evidence(record: EvidenceRecord) -> EvidenceRecord:
    LEDGER.append(record)
    return record


@app.get("/v1/evidence/{evidence_id}")
def get_evidence(evidence_id: str) -> EvidenceRecord:
    try:
        return LEDGER.get(evidence_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail={"error": "evidence not found"}) from exc


@app.post("/v1/verify/run/{run_id}")
def verify_run(run_id: str) -> DeliveryReport:
    records = LEDGER.list(run_id=run_id)
    if not records:
        return DeliveryReport(
            verdict=FinalVerdict.VERIFIED_FAIL,
            reasons=["no evidence"],
            evidence_count=0,
        )
    return DeliveryReport(
        verdict=FinalVerdict.UNKNOWN,
        reasons=["delivery gate CLI is authoritative"],
        evidence_count=len(records),
    )


@app.get("/v1/verdict/{run_id}")
def verdict(run_id: str) -> dict[str, str]:
    records = LEDGER.list(run_id=run_id)
    verdict_value = FinalVerdict.UNKNOWN if records else FinalVerdict.INCOMPLETE
    return {"run_id": run_id, "verdict": verdict_value}
