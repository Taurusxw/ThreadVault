from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.parser import parse_session_file

FIXTURES = Path(__file__).parent / "fixtures" / "codex_home"


def import_fixture(tmp_path: Path) -> Path:
    runner = CliRunner()
    db = tmp_path / "threadvault.db"
    result = runner.invoke(app, ["import", "--db", str(db), "--codex-home", str(FIXTURES), "--json"])
    assert result.exit_code == 0, result.output
    return db


def test_parser_pairing_warnings_and_object_content() -> None:
    parsed = parse_session_file(FIXTURES / "sessions" / "privacy_pairing.jsonl")
    warning_codes = {warning.code for warning in parsed.warnings}
    assert {"missing_function_call_output", "orphan_function_call_output", "duplicate_function_call_output"} <= warning_codes
    assert any(event.text_content and "secret.py" in event.text_content for event in parsed.events)


def test_ingest_sample_and_warning_summary(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)

    result = runner.invoke(app, ["ingest-sample", "--codex-home", str(FIXTURES), "--limit", "4", "--dry-run", "--json"])
    assert result.exit_code == 0, result.output
    sample = json.loads(result.output)
    assert sample["files"] == 4
    assert sample["warnings"] >= 1
    assert "samples" in sample

    result = runner.invoke(app, ["warnings", "--db", str(db), "--summary", "--json"])
    assert result.exit_code == 0, result.output
    summary = json.loads(result.output)
    assert any(item["code"] == "invalid_json" for item in summary)


def test_privacy_scan_and_export_modes(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    out = tmp_path / "out"

    result = runner.invoke(app, ["privacy-scan", "--session", "sess-privacy", "--db", str(db), "--json"])
    assert result.exit_code == 0, result.output
    scan = json.loads(result.output)
    assert scan["summary"]["by_severity"]["high"] >= 1

    result = runner.invoke(
        app,
        ["export", "--session", "sess-privacy", "--db", str(db), "--out", str(out), "--privacy-mode", "redact", "--json"],
    )
    assert result.exit_code == 0, result.output
    exported = Path(json.loads(result.output)["path"])
    text = exported.read_text(encoding="utf-8")
    assert "supersecrettoken123" not in text
    assert "[REDACTED:token_assignment]" in text

    fail_out = tmp_path / "fail-out"
    result = runner.invoke(
        app,
        ["export", "--session", "sess-privacy", "--db", str(db), "--out", str(fail_out), "--privacy-mode", "fail", "--json"],
    )
    assert result.exit_code == 2
    assert not (fail_out / "sess-privacy.md").exists()
    assert json.loads(result.output)["ok"] is False


def test_summary_evidence_quality_fields(tmp_path: Path) -> None:
    runner = CliRunner()
    db = import_fixture(tmp_path)
    result = runner.invoke(app, ["summarize", "--session", "sess-current", "--db", str(db), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert "evidence_coverage" in payload
    assert "missing_evidence_warnings" in payload
    assert payload["evidence_coverage"]["ratio"] >= 0


def test_v04_docs_and_gitignore_policy() -> None:
    for path in [
        Path("docs/progress/archive/legacy-v0/phases/phase-04-real-corpus-privacy-hardening/plan.md"),
        Path("docs/progress/archive/legacy-v0/phases/phase-04-real-corpus-privacy-hardening/external-review.md"),
        Path("docs/progress/archive/legacy-development-progress.md"),
    ]:
        assert path.exists(), f"missing {path}"
    gitignore = Path(".gitignore").read_text(encoding="utf-8")
    for pattern in ["__pycache__/", ".pytest_cache/", "*.db", "threadvault-export/"]:
        assert pattern in gitignore
