from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.database import connect
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas
from threadvault.summary_pipeline import SummaryChunkRequest, build_summary_chunks

FIXTURES = Path("tests/fixtures/codex_home")
FIXTURE_PROJECT = "E:\\Codex\\ThreadVault"


def import_fixture(tmp_path: Path) -> Path:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"
    result = runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    return db


def test_summary_chunks_cli_session_contract(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(app, ["summary-pipeline", "chunks", "--session", "sess-current", "--db", str(db), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("summary_chunks", payload)["ok"] is True
    assert payload["contract_version"] == "summary_chunks.v1"
    assert payload["selection"]["selected_session_ids"] == ["sess-current"]
    assert payload["diagnostics"]["embedding_ready"] is True
    assert payload["diagnostics"]["embedding_generated"] is False
    assert {chunk["chunk_type"] for chunk in payload["chunks"]} >= {"session_summary", "turn_summary", "evidence"}
    assert all(chunk["evidence_event_ids"] for chunk in payload["chunks"])
    assert any("1 failed in parser.py" in chunk["text"] for chunk in payload["chunks"])
    assert all("approval_policy" not in chunk["text"] for chunk in payload["chunks"])
    assert all(2 not in chunk["evidence_event_ids"] for chunk in payload["chunks"])


def test_summary_chunks_project_selection_and_limits(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(
        app,
        [
            "summary-pipeline",
            "chunks",
            "--project",
            FIXTURE_PROJECT,
            "--max-chunks-per-session",
            "2",
            "--max-chars",
            "300",
            "--db",
            str(db),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("summary_chunks", payload)["ok"] is True
    assert payload["selection"]["project"] == FIXTURE_PROJECT
    assert "sess-current" in payload["selection"]["selected_session_ids"]
    assert "sess-fork" in payload["selection"]["selected_session_ids"]
    assert len(payload["chunks"]) <= 4
    assert all(chunk["text_chars"] <= 315 for chunk in payload["chunks"])


def test_summary_chunks_unknown_session_is_skipped(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(
        app,
        ["summary-pipeline", "chunks", "--session", "missing-session", "--db", str(db), "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["chunks"] == []
    assert payload["skipped"] == [{"kind": "session", "session_id": "missing-session", "reason": "session_not_found"}]
    assert validate_payload("summary_chunks", payload)["ok"] is True


def test_summary_pipeline_module_direct_contract(tmp_path: Path) -> None:
    db = import_fixture(tmp_path)

    with connect(db) as conn:
        payload = build_summary_chunks(conn, SummaryChunkRequest(session_ids=["sess-current"], max_chunks_per_session=3, max_chars=500))

    assert payload["diagnostics"]["chunks_count"] == len(payload["chunks"])
    assert payload["diagnostics"]["chunk_type_counts"]["session_summary"] == 1
    assert len(payload["chunks"]) <= 3
    assert validate_payload("summary_chunks", payload)["ok"] is True


def test_capabilities_robot_docs_and_schema_registry_include_summary_chunks() -> None:
    caps = capabilities()
    assert "summary-pipeline" in caps["commands"]
    assert "summary-pipeline chunks" in caps["json_outputs"]
    assert caps["feature_flags"]["summary_evidence_chunks"] is True

    guide = robot_guide()
    assert guide["summary_pipeline"]["contract_version"] == "summary_chunks.v1"
    assert guide["summary_pipeline"]["schemas"] == ["summary_chunks"]
    assert "threadvault summary-pipeline chunks --session SESSION_ID --json" in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "summary_chunks" in schemas
    assert get_schema("summary_chunks")["type"] == "object"


def test_v203_docs_exist() -> None:
    for path in [
        Path("docs/progress/archive/legacy-v2/phases/phase-03-summary-evidence-chunks/plan.md"),
        Path("docs/progress/archive/legacy-v2/phases/phase-03-summary-evidence-chunks/design-notes.md"),
        Path("docs/progress/archive/legacy-v2/README.md"),
        Path("docs/THREADVAULT_USAGE_MANUAL.md"),
        Path("docs/progress/archive/legacy-development-progress.md"),
    ]:
        assert path.exists(), f"missing {path}"
