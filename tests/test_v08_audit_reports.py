from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app

FIXTURES = Path(__file__).parent / "fixtures" / "codex_home"


def test_audit_corpus_writes_anonymous_report_and_validates(tmp_path: Path) -> None:
    runner = CliRunner()
    out = tmp_path / "reports"
    result = runner.invoke(app, ["audit-corpus", "--codex-home", str(FIXTURES), "--out", str(out), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    report_path = Path(payload["report_path"])
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report_text = json.dumps(report, ensure_ascii=False)
    assert report["report_version"] == "0.8"
    assert report["source"] == "<codex_home>"
    assert str(FIXTURES) not in report_text
    assert "sess-current" not in report_text

    result = runner.invoke(app, ["validate-json", "--schema", "corpus_audit_report", "--input", str(report_path), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["ok"] is True


def test_audit_diff_reports_deltas_and_schema_validation(tmp_path: Path) -> None:
    runner = CliRunner()
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    before.write_text(
        json.dumps({
            "report_version": "0.8",
            "generated_at": "2026-06-30T00:00:00Z",
            "privacy_note": "x",
            "include_paths": False,
            "files": 1,
            "parseable_files": 1,
            "parseable_ratio": 1.0,
            "events": 10,
            "warnings": 1,
            "warning_codes": {"invalid_json": 1},
            "classifications": {"current": 10},
            "samples": [],
        }),
        encoding="utf-8",
    )
    after.write_text(
        json.dumps({
            "report_version": "0.8",
            "generated_at": "2026-06-30T00:01:00Z",
            "privacy_note": "x",
            "include_paths": False,
            "files": 2,
            "parseable_files": 1,
            "parseable_ratio": 0.5,
            "events": 12,
            "warnings": 3,
            "warning_codes": {"invalid_json": 2, "unknown_record": 1},
            "classifications": {"current": 11, "unknown": 1},
            "samples": [],
        }),
        encoding="utf-8",
    )
    result = runner.invoke(app, ["audit-diff", "--before", str(before), "--after", str(after), "--json"])
    assert result.exit_code == 0, result.output
    diff = json.loads(result.output)
    assert diff["files_delta"] == 1
    assert diff["warnings_delta"] == 2
    assert diff["warning_code_deltas"]["unknown_record"] == 1
    assert diff["regressions"]["warnings_increased"] is True
    assert diff["regressions"]["parseable_ratio_decreased"] is True

    diff_path = tmp_path / "diff.json"
    diff_path.write_text(result.output, encoding="utf-8")
    result = runner.invoke(app, ["validate-json", "--schema", "corpus_audit_diff", "--input", str(diff_path), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["ok"] is True


def test_v08_docs_and_schemas_exist() -> None:
    for path in [
        Path("docs/progress/archive/legacy-v0/phases/phase-08-audit-report-history-diff/plan.md"),
        Path("docs/progress/archive/legacy-v0/phases/phase-08-audit-report-history-diff/external-review.md"),
        Path("docs/schemas/corpus_audit_report.schema.json"),
        Path("docs/schemas/corpus_audit_diff.schema.json"),
    ]:
        assert path.exists(), f"missing {path}"
