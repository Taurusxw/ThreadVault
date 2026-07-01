from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas

FIXTURES = Path("tests/fixtures/codex_home")


def import_fixture(tmp_path: Path) -> Path:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"
    result = runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    return db


def test_client_tui_runtime_browse_mode_is_local_and_schema_valid(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(app, ["client", "tui", "--db", str(db), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("client_tui_runtime", payload)["ok"] is True
    assert payload["contract_version"] == "client_tui_runtime.v1"
    assert payload["runtime"]["family"] == "tui"
    assert payload["runtime"]["status"] == "accepted_minimal_runtime"
    assert payload["overview"]["sessions"]
    assert payload["export_preview"] is None
    assert payload["privacy"]["local_first"] is True
    assert payload["privacy"]["server_required"] is False
    assert payload["privacy"]["cloud_sync"] is False
    assert payload["privacy"]["external_model_calls"] is False
    assert payload["privacy"]["raw_paths_included"] is False
    assert all("raw_path" not in session for session in payload["overview"]["sessions"])


def test_client_tui_runtime_query_reuses_agent_retrieval(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(app, ["client", "tui", "--db", str(db), "--query", "pytest", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("client_tui_runtime", payload)["ok"] is True
    assert payload["request"]["query"] == "pytest"
    assert payload["screen"]["search_rows"]
    assert payload["overview"]["search"]["diagnostics"]["used_mode"] == "hybrid"
    assert payload["overview"]["search"]["diagnostics"]["capabilities_used"] == ["fts", "hybrid"]
    assert payload["diagnostics"]["v2_retrieval_reused"] is True
    assert all(row["evidence_event_ids"] for row in payload["screen"]["search_rows"])


def test_client_tui_runtime_export_preview_is_read_only(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "tui-preview"

    result = runner.invoke(
        app,
        [
            "client",
            "tui",
            "--db",
            str(db),
            "--export-preview-session",
            "sess-current",
            "--out",
            str(out),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("client_tui_runtime", payload)["ok"] is True
    assert payload["export_preview"]["contract_version"] == "client_export_preview.v1"
    assert payload["export_preview"]["selection"]["selected_session_ids"] == ["sess-current"]
    assert payload["screen"]["export_rows"]
    assert payload["privacy"]["export_preview_writes_files"] is False
    assert payload["diagnostics"]["export_preview_included"] is True
    assert payload["diagnostics"]["export_preview_planned_file_count"] > 0
    assert not out.exists()


def test_client_tui_runtime_non_json_renders_sections(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(
        app,
        [
            "client",
            "tui",
            "--db",
            str(db),
            "--query",
            "pytest",
            "--export-preview-session",
            "sess-current",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "ThreadVault" in result.output
    assert "Sessions" in result.output
    assert "Search" in result.output
    assert "Export Preview" in result.output


def test_client_tui_runtime_discovery_schema_docs_and_gap_audit() -> None:
    caps = capabilities()
    assert "client tui" in caps["json_outputs"]
    assert caps["feature_flags"]["client_tui_runtime"] is True

    guide = robot_guide()
    assert guide["client_interface"]["tui_runtime_contract_version"] == "client_tui_runtime.v1"
    assert "client_tui_runtime" in guide["client_interface"]["schemas"]
    assert "threadvault client tui --json" in guide["recommended_commands"]
    assert "threadvault client tui --query QUERY --json" in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "client_tui_runtime" in schemas
    assert get_schema("client_tui_runtime")["type"] == "object"
    assert Path("docs/schemas/client_tui_runtime.schema.json").exists()

    for path in [
        Path("docs/v3/phases/phase-27-local-tui-client-runtime/plan.md"),
        Path("docs/v3/phases/phase-27-local-tui-client-runtime/design-notes.md"),
        Path("docs/v3/phases/phase-27-local-tui-client-runtime/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()

    runner = CliRunner()
    result = runner.invoke(app, ["governance", "v3", "gap-audit", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["completion"]["accepted_phase_count"] == 33
    assert payload["completion"]["current_phase"] == "phase-33-v3-final-acceptance-smoke"
    assert payload["completion"]["v3_complete"] is True
    assert "client_tui_runtime" in payload["implemented_capabilities"]
    assert "richer_client_runtime_not_accepted" not in {blocker["code"] for blocker in payload["blockers"]}
    gaps = {gap["code"]: gap for gap in payload["remaining_gaps"]}
    assert gaps["richer_client_runtime"]["status"] == "accepted_minimal_tui_runtime"
