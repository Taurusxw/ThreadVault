from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.schemas import validate_payload

FIXTURES = Path("tests/fixtures/codex_home")


def import_fixture(tmp_path: Path) -> Path:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"
    result = runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    return db


def test_export_target_single_session_writes_manifest(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "target"

    result = runner.invoke(
        app,
        ["export-target", "markdown", "--db", str(db), "--session", "sess-current", "--out", str(out), "--json"],
    )

    assert result.exit_code == 0, result.output
    manifest = json.loads(result.output)
    assert validate_payload("export_target_manifest", manifest)["ok"] is True
    assert manifest["target_profile"] == "markdown"
    assert manifest["selection"]["sessions"] == ["sess-current"]
    assert manifest["selection"]["selected_session_ids"] == ["sess-current"]
    assert manifest["files"][0]["path"] == "sessions/sess-current.md"
    assert manifest["files"][0]["evidence_event_ids"]
    assert (out / "sessions" / "sess-current.md").exists()
    assert json.loads((out / "threadvault-export-manifest.json").read_text(encoding="utf-8")) == manifest


def test_export_target_multiple_sessions_are_deduplicated(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "target"

    result = runner.invoke(
        app,
        [
            "export-target",
            "markdown",
            "--db",
            str(db),
            "--session",
            "sess-current",
            "--session",
            "sess-current",
            "--session",
            "sess-fork",
            "--out",
            str(out),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    manifest = json.loads(result.output)
    assert manifest["selection"]["sessions"] == ["sess-current", "sess-fork"]
    session_files = [item for item in manifest["files"] if item["kind"] == "session"]
    assert {item["session_id"] for item in session_files} == {"sess-current", "sess-fork"}
    assert len(session_files) == 2


def test_export_target_project_writes_project_index_and_sessions(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "target"
    project = "E:\\Codex\\ThreadVault"

    result = runner.invoke(
        app,
        ["export-target", "markdown", "--db", str(db), "--project", project, "--out", str(out), "--json"],
    )

    assert result.exit_code == 0, result.output
    manifest = json.loads(result.output)
    assert manifest["selection"]["project"] == project
    assert any(item["kind"] == "project_index" and item["path"] == "project-index.md" for item in manifest["files"])
    assert any(item["kind"] == "session" for item in manifest["files"])
    assert (out / "project-index.md").exists()
    assert (out / "sessions").exists()


def test_export_target_unknown_session_is_skipped(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "target"

    result = runner.invoke(
        app,
        ["export-target", "markdown", "--db", str(db), "--session", "missing-session", "--out", str(out), "--json"],
    )

    assert result.exit_code == 0, result.output
    manifest = json.loads(result.output)
    assert manifest["files"] == []
    assert manifest["skipped"] == [{"kind": "session", "session_id": "missing-session", "reason": "session_not_found"}]
    assert (out / "threadvault-export-manifest.json").exists()


def test_export_target_manifest_schema_validates_saved_file(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "target"
    payload_path = tmp_path / "manifest.json"

    result = runner.invoke(
        app,
        ["export-target", "markdown", "--db", str(db), "--session", "sess-current", "--out", str(out), "--json"],
    )
    assert result.exit_code == 0, result.output
    payload_path.write_text(result.output, encoding="utf-8")

    result = runner.invoke(app, ["validate-json", "--schema", "export_target_manifest", "--input", str(payload_path), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["ok"] is True


def test_capabilities_and_schema_registry_include_export_target_manifest() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["capabilities", "--json"])
    assert result.exit_code == 0, result.output
    capabilities = json.loads(result.output)
    assert "export-target" in capabilities["commands"]
    assert "export-target markdown" in capabilities["json_outputs"]
    assert capabilities["feature_flags"]["export_target_manifest"] is True

    result = runner.invoke(app, ["schemas", "list", "--json"])
    assert result.exit_code == 0, result.output
    assert "export_target_manifest" in json.loads(result.output)["schemas"]


def test_v103_docs_exist() -> None:
    for path in [
        Path("docs/v1/README.md"),
        Path("docs/v1/phases/phase-03-export-target-manifest/plan.md"),
        Path("docs/v1/phases/phase-03-export-target-manifest/acceptance.md"),
        Path("docs/development-progress.md"),
    ]:
        assert path.exists(), f"missing {path}"
