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


def test_agent_manifest_contract_and_privacy_defaults() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["agent", "manifest", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("agent_interface_manifest", payload)["ok"] is True
    assert payload["contract_version"] == "agent_interface.v1"
    assert payload["interface"]["default_mode"] == "hybrid"
    assert payload["interface"]["modes"] == ["hybrid", "fts"]
    assert payload["capabilities"]["mcp_runtime_included"] is False
    assert payload["privacy"]["raw_paths_in_default_output"] is False
    assert payload["schemas"]["retrieval"] == "agent_retrieval"


def test_agent_retrieve_defaults_to_hybrid_and_degrades_to_fts(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(app, ["agent", "retrieve", "pytest", "--db", str(db), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("agent_retrieval", payload)["ok"] is True
    assert payload["contract_version"] == "agent_retrieval.v1"
    assert payload["request"]["requested_mode"] == "hybrid"
    assert payload["request"]["used_mode"] == "hybrid"
    assert payload["diagnostics"]["capabilities_used"] == ["fts", "hybrid"]
    assert payload["diagnostics"]["hybrid"]["vector"]["status"] == "disabled_by_config"
    assert payload["privacy"]["raw_paths_included"] is False
    assert payload["results"]
    assert {item["source"] for item in payload["results"]} == {"fts"}
    assert all(item["evidence_event_ids"] for item in payload["results"])
    assert all("metadata" not in item for item in payload["results"])


def test_agent_retrieve_fts_mode_uses_retrieval_contract(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(app, ["agent", "retrieve", "pytest", "--mode", "fts", "--db", str(db), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("agent_retrieval", payload)["ok"] is True
    assert payload["request"]["requested_mode"] == "fts"
    assert payload["diagnostics"]["used_mode"] == "fts"
    assert payload["diagnostics"]["underlying_contract"] == "retrieval.v1"
    assert payload["diagnostics"]["capabilities_used"] == ["fts"]
    assert payload["results"]
    assert all(item["source"] == "fts" for item in payload["results"])


def test_agent_retrieve_local_debug_includes_metadata(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(
        app,
        ["agent", "retrieve", "pytest", "--mode", "fts", "--db", str(db), "--local-debug", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("agent_retrieval", payload)["ok"] is True
    assert payload["privacy"]["raw_paths_included"] is True
    assert payload["results"]
    assert all("metadata" in item for item in payload["results"])
    assert any("file_path" in item["metadata"] for item in payload["results"])


def test_capabilities_robot_docs_and_schema_registry_include_agent_interface() -> None:
    caps = capabilities()
    assert "agent" in caps["commands"]
    assert "agent manifest" in caps["json_outputs"]
    assert "agent retrieve" in caps["json_outputs"]
    assert caps["feature_flags"]["agent_retrieval_interface"] is True

    guide = robot_guide()
    assert guide["agent_interface"]["manifest_contract_version"] == "agent_interface.v1"
    assert guide["agent_interface"]["retrieval_contract_version"] == "agent_retrieval.v1"
    assert guide["agent_interface"]["schemas"] == ["agent_interface_manifest", "agent_retrieval"]
    assert "threadvault agent retrieve QUERY --json" in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "agent_interface_manifest" in schemas
    assert "agent_retrieval" in schemas
    assert get_schema("agent_interface_manifest")["type"] == "object"
    assert get_schema("agent_retrieval")["type"] == "object"


def test_v206_docs_exist() -> None:
    for path in [
        Path("docs/v2/phases/phase-06-agent-facing-retrieval-interface/plan.md"),
        Path("docs/v2/phases/phase-06-agent-facing-retrieval-interface/design-notes.md"),
        Path("docs/v2/README.md"),
        Path("docs/development-progress.md"),
    ]:
        assert path.exists(), f"missing {path}"
