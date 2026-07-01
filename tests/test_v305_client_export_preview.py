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


def test_client_export_preview_session_is_read_only(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "preview-out"

    result = runner.invoke(
        app,
        ["client", "export-preview", "--db", str(db), "--session", "sess-current", "--out", str(out), "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("client_export_preview", payload)["ok"] is True
    assert payload["contract_version"] == "client_export_preview.v1"
    assert payload["request"]["profile"] == "markdown"
    assert payload["selection"]["selected_session_ids"] == ["sess-current"]
    assert payload["planned_files"][0]["path"] == "sessions/sess-current.md"
    assert payload["planned_files"][0]["evidence_event_ids"]
    assert payload["diagnostics"]["preview"] is True
    assert payload["diagnostics"]["writes_files"] is False
    assert payload["diagnostics"]["manifest_written"] is False
    assert payload["diagnostics"]["server_required"] is False
    assert payload["actions"]["execute"].startswith("threadvault export-target markdown")
    assert not out.exists()


def test_client_export_preview_project_lists_selected_sessions(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "project-preview"
    project = "E:\\Codex\\ThreadVault"

    result = runner.invoke(
        app,
        ["client", "export-preview", "--db", str(db), "--project", project, "--out", str(out), "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("client_export_preview", payload)["ok"] is True
    assert payload["selection"]["project"] == project
    assert "sess-current" in payload["selection"]["selected_session_ids"]
    assert any(file["kind"] == "project_index" for file in payload["planned_files"])
    assert any(file["kind"] == "session" for file in payload["planned_files"])
    assert not out.exists()


def test_client_export_preview_privacy_fail_blocks_high_risk_session(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "privacy-preview"

    result = runner.invoke(
        app,
        [
            "client",
            "export-preview",
            "--db",
            str(db),
            "--session",
            "sess-privacy",
            "--out",
            str(out),
            "--privacy-mode",
            "fail",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("client_export_preview", payload)["ok"] is True
    assert payload["privacy"]["mode"] == "fail"
    assert payload["privacy"]["blocked"] is True
    assert payload["privacy"]["effective_findings_count"] > 0
    assert payload["planned_files"] == []
    assert payload["skipped"][0]["reason"] == "high_risk_privacy_findings"
    assert not out.exists()


def test_client_export_preview_discovery_schema_and_docs() -> None:
    caps = capabilities()
    assert "client export-preview" in caps["json_outputs"]
    assert caps["feature_flags"]["client_export_preview"] is True

    guide = robot_guide()
    assert guide["client_interface"]["export_preview_contract_version"] == "client_export_preview.v1"
    assert guide["client_interface"]["schemas"] == [
        "client_interface_manifest",
        "client_overview",
        "client_tui_runtime",
        "client_session",
        "client_export_preview",
        "client_warnings",
    ]
    assert "threadvault client export-preview --session SESSION_ID --out OUT --json" in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "client_export_preview" in schemas
    assert get_schema("client_export_preview")["type"] == "object"
    assert Path("docs/schemas/client_export_preview.schema.json").exists()

    for path in [
        Path("docs/v3/phases/phase-05-client-export-preview-workflow/plan.md"),
        Path("docs/v3/phases/phase-05-client-export-preview-workflow/design-notes.md"),
        Path("docs/v3/phases/phase-05-client-export-preview-workflow/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()
