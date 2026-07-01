from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from typer.testing import CliRunner

import threadvault.retrieval as retrieval
from threadvault.cli import app
from threadvault.database import connect
from threadvault.retrieval import RetrievalQuery, retrieve_response
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas

FIXTURES = Path("tests/fixtures/codex_home")


def import_fixture(tmp_path: Path) -> Path:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"
    result = runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    return db


def test_retrieval_query_json_contract_includes_diagnostics(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(app, ["retrieval", "query", "pytest", "--db", str(db), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("retrieval_query", payload)["ok"] is True
    assert payload["contract_version"] == "retrieval.v1"
    assert payload["query"]["text"] == "pytest"
    assert payload["diagnostics"]["requested_mode"] == "fts"
    assert payload["diagnostics"]["used_mode"] == "fts"
    assert payload["diagnostics"]["engine"] == "sqlite_fts5"
    assert payload["diagnostics"]["index_status"]["ok"] is True
    assert payload["diagnostics"]["result_count"] == len(payload["results"])
    assert payload["results"]


def test_retrieval_diagnose_json_contract_reports_index_status(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(app, ["retrieval", "diagnose", "--db", str(db), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("retrieval_diagnostics", payload)["ok"] is True
    diagnostics = payload["diagnostics"]
    assert diagnostics["used_mode"] == "fts"
    assert diagnostics["engine"] == "sqlite_fts5"
    assert diagnostics["result_count"] == 0
    assert diagnostics["index_status"]["ok"] is True
    assert diagnostics["index_status"]["event_count"] == diagnostics["index_status"]["fts_count"]


def test_retrieval_response_records_sqlite_operational_fallback(monkeypatch, tmp_path: Path) -> None:
    db = import_fixture(tmp_path)
    calls = {"count": 0}
    original = retrieval.search_events

    def flaky_search_events(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise sqlite3.OperationalError("forced fts parse failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(retrieval, "search_events", flaky_search_events)

    with connect(db) as conn:
        response = retrieve_response(conn, RetrievalQuery(text="pytest"))

    payload = response.to_payload()
    assert calls["count"] == 2
    assert payload["diagnostics"]["fallback"]["used"] is True
    assert payload["diagnostics"]["fallback"]["reason"] == "sqlite_operational_error"
    assert payload["diagnostics"]["result_count"] == len(payload["results"])
    assert payload["results"]


def test_legacy_search_json_contracts_still_validate(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    for fields, schema in [
        ("minimal", "search_minimal"),
        ("standard", "search_standard"),
        ("full", "search_full"),
    ]:
        result = runner.invoke(app, ["search", "pytest", "--db", str(db), "--json", "--fields", fields])
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert isinstance(payload, list)
        assert validate_payload(schema, payload)["ok"] is True


def test_capabilities_robot_docs_and_schema_registry_include_retrieval_contracts() -> None:
    caps = capabilities()
    assert "retrieval" in caps["commands"]
    assert "retrieval query" in caps["json_outputs"]
    assert "retrieval diagnose" in caps["json_outputs"]
    assert caps["feature_flags"]["retrieval_diagnostics"] is True

    guide = robot_guide()
    assert guide["retrieval"]["contract_version"] == "retrieval.v1"
    assert "retrieval_query" in guide["retrieval"]["schemas"]
    assert "threadvault retrieval query QUERY --json" in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "retrieval_query" in schemas
    assert "retrieval_diagnostics" in schemas
    assert get_schema("retrieval_query")["type"] == "object"
    assert get_schema("retrieval_diagnostics")["type"] == "object"


def test_v202_docs_exist() -> None:
    for path in [
        Path("docs/v2/phases/phase-02-retrieval-json-contracts-diagnostics/plan.md"),
        Path("docs/v2/phases/phase-02-retrieval-json-contracts-diagnostics/design-notes.md"),
        Path("docs/v2/README.md"),
        Path("docs/THREADVAULT_USAGE_MANUAL.md"),
        Path("docs/development-progress.md"),
    ]:
        assert path.exists(), f"missing {path}"
