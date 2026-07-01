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


def test_client_overview_browse_mode_hides_raw_paths(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(app, ["client", "overview", "--db", str(db), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("client_overview", payload)["ok"] is True
    assert payload["contract_version"] == "client_overview.v1"
    assert payload["request"]["query"] is None
    assert payload["sessions"]
    assert all("raw_path" not in session for session in payload["sessions"])
    assert payload["search"]["results"] == []
    assert payload["privacy"]["raw_paths_included"] is False
    assert payload["privacy"]["external_model_calls"] is False
    assert payload["diagnostics"]["server_required"] is False


def test_client_overview_query_mode_reuses_agent_retrieval_defaults(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(app, ["client", "overview", "--db", str(db), "--query", "pytest", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("client_overview", payload)["ok"] is True
    assert payload["search"]["query"] == "pytest"
    assert payload["search"]["results"]
    assert payload["search"]["diagnostics"]["used_mode"] == "hybrid"
    assert payload["search"]["diagnostics"]["capabilities_used"] == ["fts", "hybrid"]
    assert all(result["evidence_event_ids"] for result in payload["search"]["results"])
    assert all("metadata" not in result for result in payload["search"]["results"])
    assert payload["actions"]["export_markdown"].startswith("threadvault export-target markdown")


def test_client_overview_local_debug_is_explicit(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(
        app,
        ["client", "overview", "--db", str(db), "--query", "pytest", "--local-debug", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("client_overview", payload)["ok"] is True
    assert payload["privacy"]["raw_paths_included"] is True
    assert any("raw_path" in session for session in payload["sessions"])
    assert payload["search"]["results"]
    assert any("metadata" in result for result in payload["search"]["results"])


def test_client_overview_discovery_and_docs() -> None:
    caps = capabilities()
    assert "client overview" in caps["json_outputs"]
    assert caps["feature_flags"]["client_overview"] is True

    guide = robot_guide()
    assert guide["client_interface"]["overview_contract_version"] == "client_overview.v1"
    assert guide["client_interface"]["schemas"] == [
        "client_interface_manifest",
        "client_overview",
        "client_tui_runtime",
        "client_session",
        "client_export_preview",
        "client_warnings",
    ]
    assert "threadvault client overview --json" in guide["recommended_commands"]
    assert "threadvault client overview --query QUERY --json" in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "client_overview" in schemas
    assert get_schema("client_overview")["type"] == "object"
    assert Path("docs/schemas/client_overview.schema.json").exists()

    for path in [
        Path("docs/v3/phases/phase-03-client-overview-workflow/plan.md"),
        Path("docs/v3/phases/phase-03-client-overview-workflow/design-notes.md"),
        Path("docs/v3/phases/phase-03-client-overview-workflow/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()
