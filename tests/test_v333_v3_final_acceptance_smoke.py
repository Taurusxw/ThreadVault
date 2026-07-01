from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.governance import V3_ACCEPTANCE_SMOKE_COMMAND
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas

FIXTURES = Path("tests/fixtures/codex_home")


def import_fixture(tmp_path: Path) -> Path:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"
    result = runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    return db


def test_v3_acceptance_smoke_passes_on_fixture_archive_and_preserves_boundaries(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    work_dir = tmp_path / "smoke"

    result = runner.invoke(
        app,
        [
            "governance",
            "v3",
            "acceptance-smoke",
            "--db",
            str(db),
            "--work-dir",
            str(work_dir),
            "--query",
            "pytest",
            "--session",
            "sess-current",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_v3_acceptance_smoke", payload)["ok"] is True
    assert payload["contract_version"] == "governance_v3_acceptance_smoke.v1"
    assert payload["ok"] is True
    assert payload["status"] == "accepted"
    assert payload["governance"]["server_required"] is False
    assert payload["governance"]["server_opt_in"] is True
    assert payload["governance"]["cloud_sync"] is False
    assert payload["governance"]["production_shared_enforcement_claimed"] is False
    assert payload["summary"]["failed_check_count"] == 0
    assert payload["summary"]["passed_check_count"] == payload["summary"]["required_check_count"]
    assert {item["status"] for item in payload["criteria"]} == {"satisfied"}

    checks = {item["code"]: item for item in payload["checks"]}
    assert checks["accepted_v2_retrieval_reused"]["ok"] is True
    assert checks["richer_client_runtime"]["ok"] is True
    assert checks["optional_read_only_server"]["ok"] is True
    assert checks["governance_access_separation_and_instrumentation"]["ok"] is True
    assert checks["governance_runtime_discovery"]["ok"] is True
    assert checks["discovery_schema_and_docs"]["ok"] is True
    assert checks["governance_access_separation_and_instrumentation"]["evidence"]["audit_written"] is True
    assert checks["governance_access_separation_and_instrumentation"]["evidence"]["blocked_backup_exists"] is False
    assert payload["diagnostics"]["v2_retrieval_core_changed"] is False
    assert payload["diagnostics"]["deep_research_report_retired"] is True


def test_v3_gap_audit_reports_complete_after_final_acceptance() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "v3", "gap-audit", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_v3_completion_gap_audit", payload)["ok"] is True
    assert payload["completion"]["overall_status"] == "complete"
    assert payload["completion"]["v3_complete"] is True
    assert payload["completion"]["accepted_phase_count"] == 33
    assert payload["completion"]["current_phase"] == "phase-33-v3-final-acceptance-smoke"
    assert payload["completion"]["blocking_count"] == 0
    assert payload["blockers"] == []
    assert "v3_acceptance_smoke" in payload["implemented_capabilities"]
    gaps = {item["code"]: item for item in payload["remaining_gaps"]}
    assert gaps["v3_acceptance_smoke"]["status"] == "accepted"
    assert payload["governance"]["server_required"] is False
    assert payload["governance"]["server_opt_in"] is True
    assert payload["governance"]["cloud_sync"] is False


def test_v3_acceptance_smoke_discovery_schema_and_docs() -> None:
    caps = capabilities()
    assert "governance v3 acceptance-smoke" in caps["json_outputs"]
    assert caps["feature_flags"]["governance_v3_acceptance_smoke"] is True

    guide = robot_guide()
    assert V3_ACCEPTANCE_SMOKE_COMMAND in guide["recommended_commands"]
    assert guide["governance"]["v3_acceptance_smoke_contract_version"] == "governance_v3_acceptance_smoke.v1"
    assert guide["governance"]["v3_acceptance_smoke_schema"] == "governance_v3_acceptance_smoke"

    schemas = robot_schemas()
    assert "governance_v3_acceptance_smoke" in schemas
    assert get_schema("governance_v3_acceptance_smoke")["type"] == "object"
    assert Path("docs/schemas/governance_v3_acceptance_smoke.schema.json").exists()

    for path in [
        Path("docs/v3/phases/phase-33-v3-final-acceptance-smoke/plan.md"),
        Path("docs/v3/phases/phase-33-v3-final-acceptance-smoke/design-notes.md"),
        Path("docs/v3/phases/phase-33-v3-final-acceptance-smoke/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()
