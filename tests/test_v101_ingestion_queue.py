from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.database import connect, init_db
from threadvault.ingestion import IngestionRequest, enqueue_ingestion, list_ingestion_queue, process_ingestion_queue
from threadvault.schemas import validate_payload

FIXTURES = Path("tests/fixtures/codex_home")


def test_enqueue_and_deduplicate_active_request(tmp_path: Path) -> None:
    db = tmp_path / "threadvault.db"
    with connect(db) as conn:
        init_db(conn)
        first = enqueue_ingestion(conn, IngestionRequest(source="hook", codex_home=FIXTURES, reason="session-stop"))
        second = enqueue_ingestion(conn, IngestionRequest(source="hook", codex_home=FIXTURES, reason="session-stop"))
        queued = list_ingestion_queue(conn)

    assert first["ok"] is True
    assert first["enqueued"] is True
    assert first["request"]["status"] == "pending"
    assert second["ok"] is True
    assert second["enqueued"] is False
    assert second["request"]["request_id"] == first["request"]["request_id"]
    assert queued["count"] == 1


def test_process_dry_run_does_not_import_or_mutate_status(tmp_path: Path) -> None:
    db = tmp_path / "threadvault.db"
    with connect(db) as conn:
        init_db(conn)
        enqueue_ingestion(conn, IngestionRequest(source="manual", codex_home=FIXTURES, reason="scan"))
        dry_run = process_ingestion_queue(conn, apply=False)
        after = list_ingestion_queue(conn)
        imported = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]

    assert dry_run["ok"] is True
    assert dry_run["apply"] is False
    assert dry_run["processed"] == 0
    assert dry_run["requests"][0]["would_process"] is True
    assert after["requests"][0]["status"] == "pending"
    assert imported == 0


def test_process_apply_imports_fixture_sessions(tmp_path: Path) -> None:
    db = tmp_path / "threadvault.db"
    with connect(db) as conn:
        init_db(conn)
        enqueue_ingestion(conn, IngestionRequest(source="manual", codex_home=FIXTURES, reason="scan"))
        processed = process_ingestion_queue(conn, apply=True)
        after = list_ingestion_queue(conn)
        imported = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]

    assert processed["ok"] is True
    assert processed["apply"] is True
    assert processed["processed"] == 1
    assert processed["requests"][0]["status"] == "completed"
    assert processed["requests"][0]["import_stats"]["imported"] >= 1
    assert after["requests"][0]["attempts"] == 1
    assert imported >= 1


def test_ingest_queue_cli_json_outputs_validate_against_schemas(tmp_path: Path) -> None:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"

    result = runner.invoke(
        app,
        [
            "ingest-queue",
            "enqueue",
            "--db",
            str(db),
            "--source",
            "hook",
            "--codex-home",
            str(FIXTURES),
            "--reason",
            "session-stop",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    enqueue_payload = json.loads(result.output)
    assert validate_payload("ingestion_enqueue", enqueue_payload)["ok"] is True
    assert enqueue_payload["enqueued"] is True

    result = runner.invoke(app, ["ingest-queue", "list", "--db", str(db), "--json"])
    assert result.exit_code == 0, result.output
    list_payload = json.loads(result.output)
    assert validate_payload("ingestion_queue_list", list_payload)["ok"] is True
    assert list_payload["count"] == 1

    result = runner.invoke(app, ["ingest-queue", "process", "--db", str(db), "--json"])
    assert result.exit_code == 0, result.output
    dry_run_payload = json.loads(result.output)
    assert validate_payload("ingestion_process", dry_run_payload)["ok"] is True
    assert dry_run_payload["apply"] is False
    assert dry_run_payload["processed"] == 0

    result = runner.invoke(app, ["ingest-queue", "process", "--db", str(db), "--apply", "--json"])
    assert result.exit_code == 0, result.output
    process_payload = json.loads(result.output)
    assert validate_payload("ingestion_process", process_payload)["ok"] is True
    assert process_payload["apply"] is True
    assert process_payload["processed"] == 1


def test_capabilities_and_schema_registry_include_ingestion_queue() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["capabilities", "--json"])
    assert result.exit_code == 0, result.output
    capabilities = json.loads(result.output)
    assert "ingest-queue" in capabilities["commands"]
    assert "ingest-queue enqueue" in capabilities["json_outputs"]
    assert capabilities["feature_flags"]["ingestion_queue"] is True

    result = runner.invoke(app, ["schemas", "list", "--json"])
    assert result.exit_code == 0, result.output
    schemas = json.loads(result.output)["schemas"]
    assert "ingestion_enqueue" in schemas
    assert "ingestion_queue_list" in schemas
    assert "ingestion_process" in schemas


def test_v101_docs_exist() -> None:
    for path in [
        Path("docs/progress/archive/legacy-v1/README.md"),
        Path("docs/progress/archive/legacy-v1/phases/phase-01-ingestion-automation-queue/plan.md"),
        Path("docs/progress/archive/legacy-development-progress.md"),
    ]:
        assert path.exists(), f"missing {path}"
