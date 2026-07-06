from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.personal_ui import PersonalUIServerConfig, run_personal_ui_smoke
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import ArchiveStore, capabilities, robot_guide, robot_schemas

FIXTURES = Path("tests/fixtures/codex_home")
PHASE_DIR = Path("docs/progress/archive/legacy-v4/phases/phase-05-v4-acceptance-smoke")


def import_fixture(tmp_path: Path) -> Path:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"
    result = runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    return db


def test_personal_ui_smoke_runtime_accepts_fixture_archive(tmp_path: Path) -> None:
    db = import_fixture(tmp_path)
    store = ArchiveStore(db)
    config = PersonalUIServerConfig(db_path=db)

    payload = run_personal_ui_smoke(store, config, work_dir=tmp_path / "smoke")

    assert validate_payload("personal_ui_smoke", payload)["ok"] is True
    assert payload["contract_version"] == "personal_ui_smoke.v1"
    assert payload["status"] == "accepted"
    assert payload["ok"] is True
    assert payload["summary"]["failed_required_check_count"] == 0
    assert {check["code"] for check in payload["checks"]} >= {
        "health_route_ok",
        "client_overview_lists_sessions",
        "retrieve_route_returns_results",
        "client_session_returns_preview",
        "safe_action_executes",
        "export_preview_does_not_write",
        "dangerous_actions_require_confirm",
        "v2_retrieval_non_regression",
        "v3_acceptance_non_regression",
        "retired_deep_research_report_absent",
    }
    assert payload["boundaries"]["cloud_sync_default"] is False
    assert payload["boundaries"]["external_model_calls_default"] is False


def test_personal_ui_smoke_cli_outputs_json(tmp_path: Path) -> None:
    db = import_fixture(tmp_path)
    runner = CliRunner()

    result = runner.invoke(app, ["ui", "smoke", "--db", str(db), "--work-dir", str(tmp_path / "cli-smoke"), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("personal_ui_smoke", payload)["ok"] is True
    assert payload["ok"] is True
    assert payload["server"]["default_host"] == "127.0.0.1"
    assert payload["summary"]["criteria_satisfied_count"] == payload["summary"]["criteria_count"]


def test_personal_ui_smoke_reports_missing_fixture_data(tmp_path: Path) -> None:
    db = tmp_path / "empty.db"
    store = ArchiveStore(db)
    store.init()

    payload = run_personal_ui_smoke(store, PersonalUIServerConfig(db_path=db), work_dir=tmp_path / "empty-smoke")

    assert validate_payload("personal_ui_smoke", payload)["ok"] is True
    assert payload["ok"] is False
    assert payload["status"] == "failed"
    failed_codes = {check["code"] for check in payload["checks"] if not check["ok"]}
    assert "client_overview_lists_sessions" in failed_codes
    assert "retrieve_route_returns_results" in failed_codes


def test_personal_ui_smoke_discovery_docs_and_schema_artifact() -> None:
    caps = capabilities()
    guide = robot_guide()
    schemas = robot_schemas()

    assert "ui smoke" in caps["json_outputs"]
    assert caps["feature_flags"]["personal_ui_acceptance_smoke"] is True
    assert guide["personal_ui"]["smoke_command"] == "threadvault ui smoke --json"
    assert guide["personal_ui"]["smoke_schema"] == "personal_ui_smoke"
    assert "personal_ui_smoke" in schemas
    assert get_schema("personal_ui_smoke")["type"] == "object"

    for path in [
        PHASE_DIR / "plan.md",
        PHASE_DIR / "design-notes.md",
        PHASE_DIR / "acceptance.md",
        Path("docs/progress/archive/legacy-v4/README.md"),
        Path("docs/progress/archive/legacy-development-progress.md"),
        Path("docs/schemas/personal_ui_smoke.schema.json"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()
