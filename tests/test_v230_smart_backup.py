from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.database import connect
from threadvault.smart_backup import run_smart_backup

FIXTURES = Path(__file__).parent / "fixtures" / "codex_home"


def _import_fixture(db: Path) -> None:
    result = CliRunner().invoke(
        app,
        ["import", "--db", str(db), "--codex-home", str(FIXTURES), "--json"],
    )
    assert result.exit_code == 0, result.output


def _mark_changed(db: Path, value: str) -> None:
    with connect(db) as conn:
        conn.execute("UPDATE sessions SET updated_at = ?", (value,))
        conn.commit()


def test_smart_backup_bootstraps_evidence_then_skips_unchanged(tmp_path: Path) -> None:
    db = tmp_path / "threadvault.db"
    out = tmp_path / "backups"
    _import_fixture(db)
    now = datetime.now(UTC)

    plan = run_smart_backup(db, out_root=out, codex_home=FIXTURES, now=now)
    assert plan["action"] == "backup"
    assert plan["profile"] == "evidence"
    assert plan["reason"] == "bootstrap_evidence"
    assert not out.exists()

    applied = run_smart_backup(db, out_root=out, codex_home=FIXTURES, now=now, apply=True)
    assert applied["ok"] is True
    assert applied["action"] == "created"
    assert applied["verification"]["ok"] is True

    unchanged = run_smart_backup(db, out_root=out, codex_home=FIXTURES, now=now + timedelta(days=2))
    assert unchanged["action"] == "skip"
    assert unchanged["reason"] == "fresh_or_unchanged"


def test_smart_backup_promotes_daily_weekly_and_monthly_profiles(tmp_path: Path) -> None:
    db = tmp_path / "threadvault.db"
    out = tmp_path / "backups"
    _import_fixture(db)
    now = datetime.now(UTC)
    assert run_smart_backup(db, out_root=out, codex_home=FIXTURES, now=now, apply=True)["profile"] == "evidence"

    _mark_changed(db, "2026-07-15T00:00:00Z")
    daily = run_smart_backup(db, out_root=out, codex_home=FIXTURES, now=now + timedelta(days=2), apply=True)
    assert daily["profile"] == "core"
    assert daily["reason"] == "daily_core_due"

    _mark_changed(db, "2026-07-22T00:00:00Z")
    weekly = run_smart_backup(db, out_root=out, codex_home=FIXTURES, now=now + timedelta(days=8), apply=True)
    assert weekly["profile"] == "evidence"
    assert weekly["reason"] == "weekly_evidence_due"

    _mark_changed(db, "2026-08-15T00:00:00Z")
    monthly = run_smart_backup(db, out_root=out, codex_home=FIXTURES, now=now + timedelta(days=31), apply=True)
    assert monthly["profile"] == "forensic"
    assert monthly["reason"] == "monthly_forensic_due"


def test_smart_backup_retains_only_three_automatic_core_backups(tmp_path: Path) -> None:
    db = tmp_path / "threadvault.db"
    out = tmp_path / "backups"
    _import_fixture(db)
    now = datetime.now(UTC)
    run_smart_backup(db, out_root=out, codex_home=FIXTURES, now=now, apply=True, include_forensic=False)

    for index in range(1, 5):
        _mark_changed(db, f"2026-07-{14 + index:02d}T00:00:00Z")
        result = run_smart_backup(
            db,
            out_root=out,
            codex_home=FIXTURES,
            now=now + timedelta(days=index * 1.1),
            apply=True,
            include_forensic=False,
        )
        assert result["profile"] == "core"

    manifests = list((out / "auto" / "core").glob("*.storage-manifest.json"))
    databases = list((out / "auto" / "core").glob("*.db"))
    assert len(manifests) == 3
    assert len(databases) == 3


def test_smart_backup_blocks_before_writing_when_disk_is_insufficient(tmp_path: Path, monkeypatch) -> None:
    db = tmp_path / "threadvault.db"
    out = tmp_path / "backups"
    _import_fixture(db)
    monkeypatch.setattr(
        "threadvault.smart_backup.shutil.disk_usage",
        lambda _path: shutil._ntuple_diskusage(total=100, used=99, free=1),
    )

    payload = run_smart_backup(db, out_root=out, codex_home=FIXTURES, apply=True)
    assert payload["ok"] is False
    assert payload["action"] == "blocked"
    assert payload["reason"] == "insufficient_disk_space"
    assert not out.exists()


def test_storage_auto_cli_and_schema_contract(tmp_path: Path) -> None:
    db = tmp_path / "threadvault.db"
    out = tmp_path / "backups"
    _import_fixture(db)
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["storage", "auto", "--db", str(db), "--out", str(out), "--codex-home", str(FIXTURES), "--json"],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["profile"] == "evidence"
    payload_path = tmp_path / "storage-auto.json"
    payload_path.write_text(result.output, encoding="utf-8")
    validated = runner.invoke(
        app,
        ["validate-json", "--schema", "storage_auto", "--input", str(payload_path), "--json"],
    )
    assert validated.exit_code == 0, validated.output
    assert json.loads(validated.output)["ok"] is True
