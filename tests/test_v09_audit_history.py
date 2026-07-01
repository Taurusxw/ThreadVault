from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app

FIXTURES = Path(__file__).parent / "fixtures" / "codex_home"


def write_report(path: Path, generated_at: str, warnings: int) -> None:
    path.write_text(
        json.dumps({
            "report_version": "0.8",
            "generated_at": generated_at,
            "source": "<codex_home>",
            "limit": None,
            "privacy_note": "x",
            "include_paths": False,
            "files": 1,
            "parseable_files": 1,
            "parseable_ratio": 1.0,
            "events": 10,
            "warnings": warnings,
            "warning_codes": {"invalid_json": warnings},
            "classifications": {"current": 10},
            "samples": [],
        }),
        encoding="utf-8",
    )


def test_audit_history_list_latest_and_diff_latest(tmp_path: Path) -> None:
    runner = CliRunner()
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    before = report_dir / "threadvault-audit-20260630T000000Z.json"
    after = report_dir / "threadvault-audit-20260630T000100Z.json"
    ignored = report_dir / "not-a-threadvault-report.json"
    malformed = report_dir / "threadvault-audit-bad.json"
    write_report(before, "2026-06-30T00:00:00Z", warnings=1)
    write_report(after, "2026-06-30T00:01:00Z", warnings=3)
    ignored.write_text("{}", encoding="utf-8")
    malformed.write_text("{bad json", encoding="utf-8")

    result = runner.invoke(app, ["audit-history", "list", "--dir", str(report_dir), "--json"])
    assert result.exit_code == 0, result.output
    listing = json.loads(result.output)
    assert [Path(item["path"]).name for item in listing["reports"]] == [before.name, after.name]
    assert listing["warnings"][0]["code"] == "invalid_report_json"

    result = runner.invoke(app, ["audit-history", "latest", "--dir", str(report_dir), "--json"])
    assert result.exit_code == 0, result.output
    latest = json.loads(result.output)
    assert Path(latest["latest"]["path"]).name == after.name

    result = runner.invoke(app, ["audit-history", "diff-latest", "--dir", str(report_dir), "--json"])
    assert result.exit_code == 0, result.output
    diff = json.loads(result.output)
    assert diff["ok"] is True
    assert diff["before"]["path"].endswith(before.name)
    assert diff["after"]["path"].endswith(after.name)
    assert diff["diff"]["warnings_delta"] == 2


def test_audit_history_diff_latest_requires_two_reports(tmp_path: Path) -> None:
    runner = CliRunner()
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    write_report(report_dir / "threadvault-audit-20260630T000000Z.json", "2026-06-30T00:00:00Z", warnings=1)

    result = runner.invoke(app, ["audit-history", "diff-latest", "--dir", str(report_dir), "--json"])
    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["error"] == "not_enough_reports"


def test_audit_history_schema_files_and_cli_contract(tmp_path: Path) -> None:
    runner = CliRunner()
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    write_report(report_dir / "threadvault-audit-20260630T000000Z.json", "2026-06-30T00:00:00Z", warnings=1)

    list_payload = tmp_path / "list.json"
    result = runner.invoke(app, ["audit-history", "list", "--dir", str(report_dir), "--json"])
    assert result.exit_code == 0, result.output
    list_payload.write_text(result.output, encoding="utf-8")
    result = runner.invoke(app, ["validate-json", "--schema", "audit_history_list", "--input", str(list_payload), "--json"])
    assert result.exit_code == 0, result.output

    latest_payload = tmp_path / "latest.json"
    result = runner.invoke(app, ["audit-history", "latest", "--dir", str(report_dir), "--json"])
    assert result.exit_code == 0, result.output
    latest_payload.write_text(result.output, encoding="utf-8")
    result = runner.invoke(app, ["validate-json", "--schema", "audit_history_latest", "--input", str(latest_payload), "--json"])
    assert result.exit_code == 0, result.output

    for path in [
        Path("docs/v0/phases/phase-09-audit-history-workflow/plan.md"),
        Path("docs/v0/phases/phase-09-audit-history-workflow/external-review.md"),
        Path("docs/schemas/audit_history_list.schema.json"),
        Path("docs/schemas/audit_history_latest.schema.json"),
    ]:
        assert path.exists(), f"missing {path}"


def test_audit_history_with_generated_reports(tmp_path: Path) -> None:
    runner = CliRunner()
    report_dir = tmp_path / "reports"
    for _ in range(2):
        result = runner.invoke(app, ["audit-corpus", "--codex-home", str(FIXTURES), "--out", str(report_dir), "--json"])
        assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["audit-history", "list", "--dir", str(report_dir), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert len(payload["reports"]) >= 1
