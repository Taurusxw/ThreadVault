from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.schemas import get_schema, validate_payload
from threadvault.shared_server import (
    READ_ONLY_SERVER_MANIFEST_COMMAND,
    READ_ONLY_SERVER_SMOKE_COMMAND,
    handle_read_only_request,
)
from threadvault.store import ArchiveStore, capabilities, robot_guide, robot_schemas

FIXTURES = Path("tests/fixtures/codex_home")


def import_fixture(tmp_path: Path) -> Path:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"
    result = runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    return db


def test_read_only_server_manifest_preserves_opt_in_local_first_boundaries(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(app, ["governance", "server", "read-only-manifest", "--db", str(db), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_read_only_server_manifest", payload)["ok"] is True
    assert payload["contract_version"] == "governance_read_only_server_manifest.v1"
    assert payload["governance"]["server_required"] is False
    assert payload["governance"]["server_opt_in"] is True
    assert payload["governance"]["cloud_sync"] is False
    assert payload["governance"]["team_enforcement_ready"] is False
    assert payload["runtime"]["implemented"] is True
    assert payload["runtime"]["prototype"] is True
    assert payload["runtime"]["production_ready"] is False
    assert payload["runtime"]["bind_requires_enable"] is True
    assert payload["runtime"]["required_for_local_cli"] is False
    assert payload["read_only"]["all_routes_read_only"] is True
    assert payload["read_only"]["write_routes"] == []
    assert payload["read_only"]["mutation_commands_exposed"] is False
    assert payload["read_only"]["external_model_calls"] is False
    assert payload["security"]["loopback_default"] is True
    assert payload["security"]["authentication_implemented"] is False
    assert payload["integration"]["uses_archive_store"] is True
    assert payload["integration"]["reuses_agent_interface"] is True
    assert payload["integration"]["reparses_codex_transcripts"] is False
    assert payload["integration"]["v2_retrieval_core_changed"] is False
    assert {route["method"] for route in payload["routes"]} == {"GET"}
    assert all(route["mutates_state"] is False for route in payload["routes"])
    assert payload["diagnostics"]["new_dependency_required"] is False


def test_read_only_server_handler_exposes_only_existing_read_interfaces(tmp_path: Path) -> None:
    db = import_fixture(tmp_path)
    store = ArchiveStore(db)

    overview = handle_read_only_request(store, "/client/overview?query=pytest&limit=5")
    retrieve = handle_read_only_request(store, "/agent/retrieve?query=pytest&limit=5")
    missing_query = handle_read_only_request(store, "/agent/retrieve")
    missing_route = handle_read_only_request(store, "/export/apply")

    assert overview["ok"] is True
    assert overview["schema"] == "client_overview"
    assert validate_payload("client_overview", overview["payload"])["ok"] is True
    assert overview["payload"]["privacy"]["raw_paths_included"] is False
    assert retrieve["ok"] is True
    assert retrieve["schema"] == "agent_retrieval"
    assert validate_payload("agent_retrieval", retrieve["payload"])["ok"] is True
    assert retrieve["payload"]["privacy"]["raw_paths_included"] is False
    assert missing_query["status_code"] == 400
    assert missing_query["payload"]["error"] == "query_required"
    assert missing_route["status_code"] == 404
    assert missing_route["payload"]["error"] == "route_not_found"


def test_read_only_server_smoke_runs_in_process_without_binding_socket(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(app, ["governance", "server", "read-only-smoke", "--db", str(db), "--query", "pytest", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_read_only_server_smoke", payload)["ok"] is True
    assert payload["contract_version"] == "governance_read_only_server_smoke.v1"
    assert payload["ok"] is True
    assert payload["summary"]["checked_route_count"] == 7
    assert payload["summary"]["failed_route_count"] == 0
    assert payload["governance"]["server_required"] is False
    assert payload["governance"]["server_opt_in"] is True
    assert payload["governance"]["read_only"] is True
    assert payload["governance"]["team_enforcement_ready"] is False
    assert payload["diagnostics"]["v2_retrieval_core_changed"] is False


def test_serve_read_only_requires_explicit_enable() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "server", "serve-read-only"])

    assert result.exit_code != 0
    assert "requires explicit --enable" in result.output


def test_read_only_server_discovery_schema_docs_and_gap_audit() -> None:
    caps = capabilities()
    assert "governance server read-only-manifest" in caps["json_outputs"]
    assert "governance server read-only-smoke" in caps["json_outputs"]
    assert caps["feature_flags"]["governance_read_only_server_manifest"] is True
    assert caps["feature_flags"]["governance_read_only_server_smoke"] is True

    guide = robot_guide()
    assert guide["governance"]["read_only_server_manifest_contract_version"] == "governance_read_only_server_manifest.v1"
    assert guide["governance"]["read_only_server_manifest_schema"] == "governance_read_only_server_manifest"
    assert guide["governance"]["read_only_server_smoke_contract_version"] == "governance_read_only_server_smoke.v1"
    assert guide["governance"]["read_only_server_smoke_schema"] == "governance_read_only_server_smoke"
    assert READ_ONLY_SERVER_MANIFEST_COMMAND in guide["recommended_commands"]
    assert READ_ONLY_SERVER_SMOKE_COMMAND in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "governance_read_only_server_manifest" in schemas
    assert "governance_read_only_server_smoke" in schemas
    assert get_schema("governance_read_only_server_manifest")["type"] == "object"
    assert get_schema("governance_read_only_server_smoke")["type"] == "object"
    assert Path("docs/schemas/governance_read_only_server_manifest.schema.json").exists()
    assert Path("docs/schemas/governance_read_only_server_smoke.schema.json").exists()

    gap = ArchiveStore(Path("unused.db")).governance_v3_completion_gap_audit()
    blocker_codes = {item["code"] for item in gap["blockers"]}
    gap_codes = {item["code"]: item for item in gap["remaining_gaps"]}
    assert "optional_shared_server_runtime_missing" not in blocker_codes
    assert gap_codes["shared_read_only_deployment"]["status"] == "prototype_accepted"
    assert "read_only_shared_server_prototype" in gap["implemented_capabilities"]
    assert gap["completion"]["accepted_phase_count"] == 33
    assert gap["completion"]["current_phase"] == "phase-33-v3-final-acceptance-smoke"

    for path in [
        Path("docs/v3/phases/phase-25-read-only-shared-server-prototype/plan.md"),
        Path("docs/v3/phases/phase-25-read-only-shared-server-prototype/design-notes.md"),
        Path("docs/v3/phases/phase-25-read-only-shared-server-prototype/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()
