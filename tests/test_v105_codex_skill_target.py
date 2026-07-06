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


def test_skill_target_single_session_writes_candidate_layout(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "skill"

    result = runner.invoke(
        app,
        [
            "export-target",
            "skill",
            "--db",
            str(db),
            "--session",
            "sess-current",
            "--out",
            str(out),
            "--skill-name",
            "Project Memory!",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    manifest = json.loads(result.output)
    assert validate_payload("export_target_manifest", manifest)["ok"] is True
    assert manifest["target_profile"] == "skill"
    assert {item["path"] for item in manifest["files"]} == {
        "SKILL.md",
        "references/sessions.md",
        "references/evidence.md",
    }
    assert (out / "SKILL.md").exists()
    assert (out / "references" / "sessions.md").exists()
    assert (out / "references" / "evidence.md").exists()
    assert json.loads((out / "threadvault-export-manifest.json").read_text(encoding="utf-8")) == manifest


def test_skill_target_skill_md_frontmatter_and_references(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "skill"

    result = runner.invoke(
        app,
        [
            "export-target",
            "skill",
            "--db",
            str(db),
            "--session",
            "sess-current",
            "--out",
            str(out),
            "--skill-name",
            "Project Memory!",
            "--skill-description",
            "Use when ThreadVault fixture context is needed.",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    skill_md = (out / "SKILL.md").read_text(encoding="utf-8")
    sessions = (out / "references" / "sessions.md").read_text(encoding="utf-8")
    evidence = (out / "references" / "evidence.md").read_text(encoding="utf-8")
    assert "name: project-memory" in skill_md
    assert 'description: "Use when ThreadVault fixture context is needed."' in skill_md
    assert "- `references/sessions.md`: summary-level memory." in skill_md
    assert "Run pytest and fix parser.py failure" in sessions
    assert "### Evidence Event IDs" in sessions
    assert "Run pytest and fix parser.py failure" in evidence


def test_skill_target_multiple_sessions_are_deduplicated(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "skill"

    result = runner.invoke(
        app,
        [
            "export-target",
            "skill",
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
    sessions = (out / "references" / "sessions.md").read_text(encoding="utf-8")
    assert sessions.count("- Session: `sess-current`") == 1
    assert sessions.count("- Session: `sess-fork`") == 1


def test_skill_target_project_export_uses_project_sessions(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "skill"
    project = "E:\\Codex\\ThreadVault"

    result = runner.invoke(
        app,
        [
            "export-target",
            "skill",
            "--db",
            str(db),
            "--project",
            project,
            "--out",
            str(out),
            "--skill-name",
            "ThreadVault Memory",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    manifest = json.loads(result.output)
    assert manifest["selection"]["project"] == project
    assert "sess-current" in manifest["selection"]["selected_session_ids"]
    sessions = (out / "references" / "sessions.md").read_text(encoding="utf-8")
    assert f"- Project: `{project}`" in sessions
    assert "sess-current" in sessions


def test_skill_target_unknown_session_is_skipped(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "skill"

    result = runner.invoke(
        app,
        ["export-target", "skill", "--db", str(db), "--session", "missing-session", "--out", str(out), "--json"],
    )

    assert result.exit_code == 0, result.output
    manifest = json.loads(result.output)
    assert manifest["files"]
    assert manifest["skipped"] == [{"kind": "session", "session_id": "missing-session", "reason": "session_not_found"}]
    assert "missing-session" in (out / "references" / "sessions.md").read_text(encoding="utf-8")


def test_skill_target_privacy_fail_skips_high_risk_session_content(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "skill"

    result = runner.invoke(
        app,
        [
            "export-target",
            "skill",
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
    assert (out / "SKILL.md").exists()
    assert (out / "references" / "sessions.md").exists()
    assert (out / "references" / "evidence.md").exists()
    assert manifest["skipped"][0]["reason"] == "high_risk_privacy_findings"
    assert manifest["privacy"]["effective_findings_count"] > 0
    assert "api_key=supersecrettoken123" not in (out / "references" / "sessions.md").read_text(encoding="utf-8")
    assert "api_key=supersecrettoken123" not in (out / "references" / "evidence.md").read_text(encoding="utf-8")


def test_skill_target_capabilities_and_docs_exist() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["capabilities", "--json"])
    assert result.exit_code == 0, result.output
    capabilities = json.loads(result.output)
    assert "export-target skill" in capabilities["json_outputs"]
    assert capabilities["feature_flags"]["codex_skill_target"] is True

    result = runner.invoke(app, ["schemas", "list", "--json"])
    assert result.exit_code == 0, result.output
    assert "export_target_manifest" in json.loads(result.output)["schemas"]

    for path in [
        Path("docs/progress/archive/legacy-v1/README.md"),
        Path("docs/progress/archive/legacy-v1/phases/phase-05-codex-skill-target/plan.md"),
        Path("docs/progress/archive/legacy-v1/phases/phase-05-codex-skill-target/acceptance.md"),
        Path("docs/progress/archive/legacy-development-progress.md"),
    ]:
        assert path.exists(), f"missing {path}"
