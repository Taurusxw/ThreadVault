from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.database import connect, init_db
from threadvault.schemas import validate_payload
from threadvault.source_sync import inspect_source_freshness, sync_codex_sources

FIXTURE = Path("tests/fixtures/codex_home/sessions/current.jsonl")


def _codex_home(tmp_path: Path) -> tuple[Path, Path]:
    home = tmp_path / ".codex"
    transcript = home / "sessions" / "current.jsonl"
    transcript.parent.mkdir(parents=True)
    shutil.copy2(FIXTURE, transcript)
    return home, transcript


def test_source_freshness_reports_missing_archive_without_creating_it(tmp_path: Path) -> None:
    home, _transcript = _codex_home(tmp_path)
    db = tmp_path / "threadvault.db"

    payload = inspect_source_freshness(db, codex_home=home)

    assert payload["ok"] is False
    assert payload["pending_files"] == 1
    assert payload["pending_reasons"] == {"archive_missing": 1}
    assert not db.exists()


def test_source_sync_imports_only_pending_transcripts_and_becomes_fresh(tmp_path: Path) -> None:
    home, _transcript = _codex_home(tmp_path)
    db = tmp_path / "threadvault.db"

    planned = sync_codex_sources(db, codex_home=home)
    applied = sync_codex_sources(db, codex_home=home, apply=True)

    assert planned["pending_files"] == 1
    assert applied["ok"] is True
    assert applied["fresh"] is True
    assert applied["before"]["pending_files"] == 1
    assert applied["import_stats"]["imported"] == 1
    assert applied["pending_files"] == 0


def test_source_sync_refreshes_unchanged_file_check_timestamp(tmp_path: Path) -> None:
    home, transcript = _codex_home(tmp_path)
    db = tmp_path / "threadvault.db"
    sync_codex_sources(db, codex_home=home, apply=True)
    time.sleep(1.1)
    original = transcript.read_bytes()
    transcript.write_bytes(original)

    stale = inspect_source_freshness(db, codex_home=home)
    refreshed = sync_codex_sources(db, codex_home=home, apply=True)

    assert stale["pending_reasons"] == {"modified_after_import": 1}
    assert refreshed["ok"] is True
    assert refreshed["import_stats"]["skipped"] == 1
    assert refreshed["pending_files"] == 0


def test_source_sync_detects_stale_parser_version(tmp_path: Path) -> None:
    home, _transcript = _codex_home(tmp_path)
    db = tmp_path / "threadvault.db"
    sync_codex_sources(db, codex_home=home, apply=True)
    with connect(db) as conn:
        init_db(conn)
        conn.execute("UPDATE sessions SET parse_version = 1")
        conn.commit()

    payload = inspect_source_freshness(db, codex_home=home)

    assert payload["pending_reasons"] == {"parser_version_changed": 1}


def test_storage_sync_cli_contract(tmp_path: Path) -> None:
    home, _transcript = _codex_home(tmp_path)
    db = tmp_path / "threadvault.db"
    result = CliRunner().invoke(
        app,
        ["storage", "sync", "--db", str(db), "--codex-home", str(home), "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("storage_sync", payload)["ok"] is True
    assert payload["applied"] is False
    assert payload["pending_files"] == 1
