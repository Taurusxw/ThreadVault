from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.database import SCHEMA_VERSION, connect
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas

FIXTURES = Path("tests/fixtures/codex_home")


def import_fixture(tmp_path: Path) -> Path:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"
    result = runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    return db


def enabled_vector_config(tmp_path: Path) -> Path:
    config = tmp_path / "threadvault.toml"
    config.write_text(
        "\n".join([
            "[retrieval.vector]",
            "enabled = true",
            'adapter = "local-hash"',
            "dimensions = 64",
            "",
        ]),
        encoding="utf-8",
    )
    return config


def test_vector_index_requires_explicit_config_gate(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(app, ["vector", "index", "--session", "sess-current", "--db", str(db), "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["code"] == "vector_disabled"
    assert "retrieval.vector.enabled" in payload["error"]


def test_vector_index_query_and_status_contracts(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    config = enabled_vector_config(tmp_path)

    index_result = runner.invoke(
        app,
        ["vector", "index", "--session", "sess-current", "--db", str(db), "--config", str(config), "--json"],
    )

    assert index_result.exit_code == 0, index_result.output
    index_payload = json.loads(index_result.output)
    assert validate_payload("vector_index", index_payload)["ok"] is True
    assert index_payload["adapter"] == "local-hash"
    assert index_payload["dimensions"] == 64
    assert index_payload["source"]["schema"] == "summary_chunks"
    assert index_payload["indexed"]["chunks"] >= 3
    assert index_payload["diagnostics"]["raw_events_indexed"] is False
    assert index_payload["diagnostics"]["external_provider"] is False

    with connect(db) as conn:
        row = conn.execute("SELECT COUNT(*) AS count FROM vector_chunks").fetchone()
        schema_row = conn.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
    assert row["count"] == index_payload["indexed"]["total_chunks"]
    assert int(schema_row["value"]) == SCHEMA_VERSION == 4

    query_result = runner.invoke(
        app,
        ["vector", "query", "parser failure", "--db", str(db), "--config", str(config), "--json"],
    )

    assert query_result.exit_code == 0, query_result.output
    query_payload = json.loads(query_result.output)
    assert validate_payload("vector_query", query_payload)["ok"] is True
    assert query_payload["diagnostics"]["indexed_chunks"] == index_payload["indexed"]["total_chunks"]
    assert query_payload["results"]
    assert query_payload["results"][0]["score"] > 0
    assert query_payload["results"][0]["evidence_event_ids"]
    assert any("parser.py" in result["text"] for result in query_payload["results"])

    status_result = runner.invoke(app, ["vector", "status", "--db", str(db), "--config", str(config), "--json"])

    assert status_result.exit_code == 0, status_result.output
    status_payload = json.loads(status_result.output)
    assert validate_payload("vector_status", status_payload)["ok"] is True
    assert status_payload["config"]["enabled"] is True
    assert status_payload["index"]["exists"] is True
    assert status_payload["index"]["matching_chunks"] == index_payload["indexed"]["total_chunks"]


def test_vector_project_index_uses_summary_chunks_selection(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    config = enabled_vector_config(tmp_path)

    result = runner.invoke(
        app,
        [
            "vector",
            "index",
            "--project",
            "E:\\Codex\\ThreadVault",
            "--db",
            str(db),
            "--config",
            str(config),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("vector_index", payload)["ok"] is True
    assert payload["source"]["selection"]["project"] == "E:\\Codex\\ThreadVault"
    assert "sess-current" in payload["source"]["selection"]["selected_session_ids"]
    assert "sess-fork" in payload["source"]["selection"]["selected_session_ids"]
    assert payload["indexed"]["chunks"] >= 5


def test_capabilities_robot_docs_and_schema_registry_include_vector_adapter() -> None:
    caps = capabilities()
    assert "vector" in caps["commands"]
    assert "vector index" in caps["json_outputs"]
    assert "vector query" in caps["json_outputs"]
    assert "vector status" in caps["json_outputs"]
    assert caps["feature_flags"]["local_vector_adapter"] is True
    assert caps["feature_flags"]["local_vector_enabled_by_default"] is False

    guide = robot_guide()
    assert guide["vector"]["contract_version"] == "vector.v1"
    assert guide["vector"]["schemas"] == ["vector_index", "vector_query", "vector_status"]
    assert guide["vector"]["adapter"] == "local-hash"
    assert guide["vector"]["enabled_by_default"] is False
    assert "threadvault vector query QUERY --config threadvault.toml --json" in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "vector_index" in schemas
    assert "vector_query" in schemas
    assert "vector_status" in schemas
    assert get_schema("vector_index")["type"] == "object"
    assert get_schema("vector_query")["type"] == "object"
    assert get_schema("vector_status")["type"] == "object"


def test_v204_docs_exist() -> None:
    for path in [
        Path("docs/v2/phases/phase-04-local-vector-adapter/plan.md"),
        Path("docs/v2/phases/phase-04-local-vector-adapter/design-notes.md"),
        Path("docs/v2/README.md"),
        Path("docs/development-progress.md"),
    ]:
        assert path.exists(), f"missing {path}"
