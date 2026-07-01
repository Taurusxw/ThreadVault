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


def test_obsidian_target_single_session_writes_vault_layout(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "vault"

    result = runner.invoke(
        app,
        ["export-target", "obsidian", "--db", str(db), "--session", "sess-current", "--out", str(out), "--json"],
    )

    assert result.exit_code == 0, result.output
    manifest = json.loads(result.output)
    assert validate_payload("export_target_manifest", manifest)["ok"] is True
    assert manifest["target_profile"] == "obsidian"
    assert manifest["selection"]["sessions"] == ["sess-current"]
    assert {item["kind"] for item in manifest["files"]} == {"vault_index", "session_summary", "session_evidence"}
    assert (out / "index.md").exists()
    assert (out / "sessions" / "sess-current.md").exists()
    assert (out / "evidence" / "sess-current-evidence.md").exists()
    assert json.loads((out / "threadvault-export-manifest.json").read_text(encoding="utf-8")) == manifest


def test_obsidian_target_session_and_evidence_pages_link_each_other(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "vault"

    result = runner.invoke(
        app,
        ["export-target", "obsidian", "--db", str(db), "--session", "sess-current", "--out", str(out), "--json"],
    )

    assert result.exit_code == 0, result.output
    session_page = (out / "sessions" / "sess-current.md").read_text(encoding="utf-8")
    evidence_page = (out / "evidence" / "sess-current-evidence.md").read_text(encoding="utf-8")
    index_page = (out / "index.md").read_text(encoding="utf-8")
    assert "threadvault_target_profile: \"obsidian\"" in session_page
    assert "[[index|Vault Index]]" in session_page
    assert "[[evidence/sess-current-evidence|Evidence]]" in session_page
    assert "## Evidence Event IDs" in session_page
    assert "Run pytest and fix parser.py failure" in evidence_page
    assert "[[sessions/sess-current|Session Summary]]" in evidence_page
    assert "[[sessions/sess-current|Session]]" in index_page


def test_obsidian_target_multiple_sessions_are_deduplicated(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "vault"

    result = runner.invoke(
        app,
        [
            "export-target",
            "obsidian",
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
    summary_files = [item for item in manifest["files"] if item["kind"] == "session_summary"]
    assert {item["session_id"] for item in summary_files} == {"sess-current", "sess-fork"}
    assert len(summary_files) == 2


def test_obsidian_target_project_export_writes_index_and_session_pairs(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "vault"
    project = "E:\\Codex\\ThreadVault"

    result = runner.invoke(
        app,
        ["export-target", "obsidian", "--db", str(db), "--project", project, "--out", str(out), "--json"],
    )

    assert result.exit_code == 0, result.output
    manifest = json.loads(result.output)
    assert manifest["selection"]["project"] == project
    assert any(item["kind"] == "vault_index" for item in manifest["files"])
    assert any(item["kind"] == "session_summary" for item in manifest["files"])
    assert any(item["kind"] == "session_evidence" for item in manifest["files"])
    assert "Project: `E:\\Codex\\ThreadVault`" in (out / "index.md").read_text(encoding="utf-8")


def test_obsidian_target_unknown_session_is_skipped(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "vault"

    result = runner.invoke(
        app,
        ["export-target", "obsidian", "--db", str(db), "--session", "missing-session", "--out", str(out), "--json"],
    )

    assert result.exit_code == 0, result.output
    manifest = json.loads(result.output)
    assert manifest["files"][0]["kind"] == "vault_index"
    assert manifest["skipped"] == [{"kind": "session", "session_id": "missing-session", "reason": "session_not_found"}]
    assert "missing-session" in (out / "index.md").read_text(encoding="utf-8")


def test_obsidian_target_privacy_fail_skips_high_risk_session_pages(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "vault"

    result = runner.invoke(
        app,
        [
            "export-target",
            "obsidian",
            "--db",
            str(db),
            "--session",
            "sess-privacy",
            "--out",
            str(out),
            "--privacy-mode",
            "fail",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    manifest = json.loads(result.output)
    assert (out / "index.md").exists()
    assert not (out / "sessions" / "sess-privacy.md").exists()
    assert not (out / "evidence" / "sess-privacy-evidence.md").exists()
    assert manifest["files"] == [
        {
            "kind": "vault_index",
            "session_id": None,
            "path": "index.md",
            "format": "md",
            "privacy_findings_count": 0,
            "evidence_event_ids": [],
        }
    ]
    assert manifest["skipped"][0]["reason"] == "high_risk_privacy_findings"
    assert manifest["privacy"]["effective_findings_count"] > 0


def test_obsidian_target_capabilities_and_docs_exist() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["capabilities", "--json"])
    assert result.exit_code == 0, result.output
    capabilities = json.loads(result.output)
    assert "export-target obsidian" in capabilities["json_outputs"]
    assert capabilities["feature_flags"]["obsidian_vault_target"] is True

    result = runner.invoke(app, ["schemas", "list", "--json"])
    assert result.exit_code == 0, result.output
    assert "export_target_manifest" in json.loads(result.output)["schemas"]

    for path in [
        Path("docs/v1/README.md"),
        Path("docs/v1/phases/phase-04-obsidian-markdown-vault/plan.md"),
        Path("docs/v1/phases/phase-04-obsidian-markdown-vault/acceptance.md"),
        Path("docs/development-progress.md"),
    ]:
        assert path.exists(), f"missing {path}"
