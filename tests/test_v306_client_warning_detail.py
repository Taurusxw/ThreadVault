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


def test_client_warnings_default_payload_is_safe(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(app, ["client", "warnings", "--db", str(db), "--session", "sess-privacy", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("client_warnings", payload)["ok"] is True
    assert payload["contract_version"] == "client_warnings.v1"
    assert payload["session"]["session_id"] == "sess-privacy"
    assert "raw_path" not in payload["session"]
    assert payload["warnings"]["count"] > 0
    assert all("raw_path" not in warning for warning in payload["warnings"]["items"])
    assert all("raw_excerpt" not in warning for warning in payload["warnings"]["items"])
    assert payload["privacy"]["has_effective_findings"] is True
    assert payload["privacy"]["summary"]["effective_findings_count"] > 0
    assert payload["privacy"]["raw_paths_included"] is False
    assert payload["privacy"]["raw_transcript_included"] is False
    assert payload["privacy"]["external_model_calls"] is False
    assert payload["diagnostics"]["server_required"] is False
    assert all("start" not in finding for finding in payload["privacy"]["findings"])
    path_findings = [finding for finding in payload["privacy"]["findings"] if finding["kind"] in {"windows_abs_path", "posix_abs_path"}]
    assert path_findings
    assert all(finding["excerpt"] == "[local path omitted]" for finding in path_findings)


def test_client_warnings_local_debug_is_explicit(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(
        app,
        ["client", "warnings", "--db", str(db), "--session", "sess-current", "--local-debug", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("client_warnings", payload)["ok"] is True
    assert payload["privacy"]["raw_paths_included"] is True
    assert "raw_path" in payload["session"]
    assert payload["warnings"]["count"] > 0
    assert "raw_path" in payload["warnings"]["items"][0]
    assert "raw_excerpt" in payload["warnings"]["items"][0]


def test_client_warnings_unknown_session_is_controlled_error(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(app, ["client", "warnings", "--db", str(db), "--session", "missing", "--json"])

    assert result.exit_code != 0
    assert "Unknown session: missing" in result.output


def test_client_warnings_discovery_schema_and_docs() -> None:
    caps = capabilities()
    assert "client warnings" in caps["json_outputs"]
    assert caps["feature_flags"]["client_warnings"] is True

    guide = robot_guide()
    assert guide["client_interface"]["warnings_contract_version"] == "client_warnings.v1"
    assert guide["client_interface"]["schemas"] == [
        "client_interface_manifest",
        "client_overview",
        "client_tui_runtime",
        "client_session",
        "client_export_preview",
        "client_warnings",
    ]
    assert "threadvault client warnings --session SESSION_ID --json" in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "client_warnings" in schemas
    assert get_schema("client_warnings")["type"] == "object"
    assert Path("docs/schemas/client_warnings.schema.json").exists()

    for path in [
        Path("docs/progress/archive/legacy-v3/phases/phase-06-client-warning-detail-workflow/plan.md"),
        Path("docs/progress/archive/legacy-v3/phases/phase-06-client-warning-detail-workflow/design-notes.md"),
        Path("docs/progress/archive/legacy-v3/phases/phase-06-client-warning-detail-workflow/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()
