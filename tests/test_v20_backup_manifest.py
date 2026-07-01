from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from tests.test_v15_backup import import_fixture
from threadvault.cli import app


def test_backup_writes_manifest_and_manifest_schema_validates(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    backup = tmp_path / "backup.db"

    result = runner.invoke(app, ["backup", "--db", str(db), "--out", str(backup), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    manifest_path = Path(payload["manifest"]["path"])
    assert manifest_path.exists()
    assert payload["manifest"]["manifest"]["backup_sha256"]
    assert payload["manifest"]["manifest"]["source_db_sha256"]

    result = runner.invoke(app, ["backup-manifest", "--backup", str(backup), "--json"])
    assert result.exit_code == 0, result.output
    manifest_payload_path = tmp_path / "backup-manifest.json"
    manifest_payload_path.write_text(result.output, encoding="utf-8")
    assert json.loads(result.output)["ok"] is True

    result = runner.invoke(app, ["validate-json", "--schema", "backup_manifest", "--input", str(manifest_payload_path), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["ok"] is True


def test_backup_no_manifest_skips_sidecar(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    backup = tmp_path / "backup.db"

    result = runner.invoke(app, ["backup", "--db", str(db), "--out", str(backup), "--no-manifest", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["manifest"] is None
    assert not backup.with_name(f"{backup.name}.manifest.json").exists()


def test_backup_manifest_detects_modified_backup(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    backup = tmp_path / "backup.db"
    result = runner.invoke(app, ["backup", "--db", str(db), "--out", str(backup), "--json"])
    assert result.exit_code == 0, result.output
    with backup.open("ab") as handle:
        handle.write(b"changed")

    result = runner.invoke(app, ["backup-manifest", "--backup", str(backup), "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    codes = {error["code"] for error in payload["errors"]}
    assert "backup_bytes_mismatch" in codes
    assert "backup_sha256_mismatch" in codes


def test_backup_verify_with_manifest_embeds_manifest_result(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    backup = tmp_path / "backup.db"
    payload_path = tmp_path / "backup-verify.json"
    result = runner.invoke(app, ["backup", "--db", str(db), "--out", str(backup), "--json"])
    assert result.exit_code == 0, result.output

    result = runner.invoke(app, ["backup-verify", "--backup", str(backup), "--manifest", "--json"])

    assert result.exit_code == 0, result.output
    payload_path.write_text(result.output, encoding="utf-8")
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["manifest"]["ok"] is True

    result = runner.invoke(app, ["validate-json", "--schema", "backup_verify", "--input", str(payload_path), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["ok"] is True


def test_v20_docs_exist() -> None:
    for path in [
        Path("docs/v0/phases/phase-20-backup-provenance-manifest/plan.md"),
        Path("docs/v0/phases/phase-20-backup-provenance-manifest/external-review.md"),
    ]:
        assert path.exists(), f"missing {path}"
