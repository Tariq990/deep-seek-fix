from __future__ import annotations

import json
import platform
import shutil
from pathlib import Path
from typing import Annotated

import typer
import uvicorn

from deep_seek_fix import __version__
from deep_seek_fix.benchmarks import smoke_report
from deep_seek_fix.contracts.io import contract_schema_json, load_contract, write_contract
from deep_seek_fix.evidence.ledger import EvidenceLedger
from deep_seek_fix.execution.executor import ExecutionRequest, GovernedExecutor
from deep_seek_fix.policies.engine import CombinedPolicyEngine, PolicyRequest
from deep_seek_fix.verification.delivery import verify_delivery

app = typer.Typer(no_args_is_help=True)
contract_app = typer.Typer(no_args_is_help=True)
run_app = typer.Typer(no_args_is_help=True)
policy_app = typer.Typer(no_args_is_help=True)
evidence_app = typer.Typer(no_args_is_help=True)
verify_app = typer.Typer(no_args_is_help=True)
benchmark_app = typer.Typer(no_args_is_help=True)
app.add_typer(contract_app, name="contract")
app.add_typer(run_app, name="run")
app.add_typer(policy_app, name="policy")
app.add_typer(evidence_app, name="evidence")
app.add_typer(verify_app, name="verify")
app.add_typer(benchmark_app, name="benchmark")


def repo_path() -> Path:
    return Path.cwd()


def default_ledger_path() -> Path:
    return repo_path() / ".dsfix" / "evidence.sqlite3"


@app.command()
def doctor() -> None:
    info = {
        "version": __version__,
        "os": platform.platform(),
        "python": platform.python_version(),
        "uv": shutil.which("uv") is not None,
        "pnpm": shutil.which("pnpm") is not None,
        "git": shutil.which("git") is not None,
    }
    typer.echo(json.dumps(info, indent=2, sort_keys=True))


@app.command()
def serve(host: str = "127.0.0.1", port: int = 9876) -> None:
    uvicorn.run("deep_seek_fix.api.app:app", host=host, port=port)


@contract_app.command("create")
def contract_create(
    task_id: str,
    objective: str,
    output: Annotated[Path, typer.Option("--output", "-o")] = Path("contract.json"),
    allowed_path: Annotated[list[str] | None, typer.Option("--allowed-path")] = None,
    protected_path: Annotated[list[str] | None, typer.Option("--protected-path")] = None,
    required_command: Annotated[list[str] | None, typer.Option("--required-command")] = None,
    required_test: Annotated[list[str] | None, typer.Option("--required-test")] = None,
) -> None:
    contract = write_contract(
        output,
        task_id=task_id,
        objective=objective,
        allowed_paths=allowed_path or [],
        protected_paths=protected_path or [],
        required_commands=required_command or [],
        required_tests=required_test or [],
    )
    typer.echo(contract.model_dump_json(indent=2))


@contract_app.command("validate")
def contract_validate(path: Path) -> None:
    contract = load_contract(path)
    typer.echo(contract.model_dump_json(indent=2))


@contract_app.command("show")
def contract_show(path: Path) -> None:
    typer.echo(load_contract(path).model_dump_json(indent=2))


@contract_app.command("hash")
def contract_hash(path: Path) -> None:
    typer.echo(load_contract(path).computed_hash())


@contract_app.command("schema")
def contract_schema() -> None:
    typer.echo(contract_schema_json())


@run_app.command("command")
def run_command(
    contract_path: Path,
    task_id: str,
    run_id: str,
    command: list[str],
    dry_run: bool = False,
) -> None:
    contract = load_contract(contract_path)
    ledger = EvidenceLedger.from_path(default_ledger_path())
    executor = GovernedExecutor(repo_path(), ledger)
    result = executor.run(
        ExecutionRequest(command=command, dry_run=dry_run),
        contract,
        task_id=task_id,
        run_id=run_id,
    )
    typer.echo(result.model_dump_json(indent=2))


@run_app.command("task")
def run_task() -> None:
    typer.echo("run task orchestration is intentionally minimal in v0.1")


@run_app.command("status")
def run_status(run_id: str) -> None:
    records = EvidenceLedger.from_path(default_ledger_path()).list(run_id=run_id)
    typer.echo(json.dumps({"run_id": run_id, "evidence_count": len(records)}, indent=2))


@run_app.command("cancel")
def run_cancel(run_id: str) -> None:
    typer.echo(json.dumps({"run_id": run_id, "status": "cancel_requested"}, indent=2))


@policy_app.command("check")
def policy_check(contract_path: Path, command: list[str]) -> None:
    contract = load_contract(contract_path)
    request = PolicyRequest(command=command, cwd=str(repo_path()), writes=[])
    result = CombinedPolicyEngine().evaluate(request, contract, repo_path())
    typer.echo(result.model_dump_json(indent=2))


@evidence_app.command("list")
def evidence_list(run_id: str | None = None) -> None:
    records = EvidenceLedger.from_path(default_ledger_path()).list(run_id=run_id)
    typer.echo(json.dumps([record.model_dump(mode="json") for record in records], indent=2))


@evidence_app.command("show")
def evidence_show(evidence_id: str) -> None:
    record = EvidenceLedger.from_path(default_ledger_path()).get(evidence_id)
    typer.echo(record.model_dump_json(indent=2))


@evidence_app.command("verify")
def evidence_verify(evidence_id: str) -> None:
    record = EvidenceLedger.from_path(default_ledger_path()).get(evidence_id)
    typer.echo(
        json.dumps({"evidence_id": record.evidence_id, "exit_code": record.exit_code}, indent=2)
    )


@evidence_app.command("verify-run")
def evidence_verify_run(run_id: str) -> None:
    records = EvidenceLedger.from_path(default_ledger_path()).list(run_id=run_id)
    typer.echo(json.dumps({"run_id": run_id, "evidence_count": len(records)}, indent=2))


@verify_app.command("claims")
def verify_claims() -> None:
    typer.echo(
        json.dumps({"verdict": "INCOMPLETE", "reason": "claim file input is planned"}, indent=2)
    )


@verify_app.command("delivery")
def verify_delivery_command(
    contract_path: Path = Path("contract.json"),
    ledger_path: Path = Path(".dsfix/evidence.sqlite3"),
) -> None:
    report = verify_delivery(repo_path(), contract_path, ledger_path)
    typer.echo(report.model_dump_json(indent=2))
    if report.verdict != "VERIFIED_PASS":
        raise typer.Exit(1)


@benchmark_app.command("smoke")
def benchmark_smoke(
    dataset: Path = Path("benchmarks/harbor/deep-seek-fix/dataset/smoke.json"),
) -> None:
    report = smoke_report(dataset)
    typer.echo(report.model_dump_json(indent=2))
    if report.false_pass_count != 0:
        raise typer.Exit(1)


@benchmark_app.command("run")
def benchmark_run() -> None:
    benchmark_smoke()


@benchmark_app.command("report")
def benchmark_report() -> None:
    benchmark_smoke()
