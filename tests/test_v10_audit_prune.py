from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app


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


def seed_reports(report_dir: Path) -> list[Path]:
    report_dir.mkdir()
    paths = [
        report_dir / "threadvault-audit-20260630T000000Z.json",
        report_dir / "threadvault-audit-20260630T000100Z.json",
        report_dir / "threadvault-audit-20260630T000200Z.json",
    ]
    for index, path in enumerate(paths):
        write_report(path, f"2026-06-30T00:0{index}:00Z", warnings=index)
    return paths


def test_audit_history_prune_dry_run_does_not_delete(tmp_path: Path) -> None:
    runner = CliRunner()
    paths = seed_reports(tmp_path / "reports")
    result = runner.invoke(app, ["audit-history", "prune", "--dir", str(paths[0].parent), "--keep", "2", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["apply"] is False
    assert len(payload["kept"]) == 2
    assert len(payload["deletable"]) == 1
    assert payload["deleted"] == []
    assert all(path.exists() for path in paths)


def test_audit_history_prune_apply_deletes_only_valid_old_reports(tmp_path: Path) -> None:
    runner = CliRunner()
    paths = seed_reports(tmp_path / "reports")
    malformed = paths[0].parent / "threadvault-audit-bad.json"
    malformed.write_text("{bad json", encoding="utf-8")

    result = runner.invoke(app, ["audit-history", "prune", "--dir", str(paths[0].parent), "--keep", "1", "--apply", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["apply"] is True
    assert len(payload["deleted"]) == 2
    assert not paths[0].exists()
    assert not paths[1].exists()
    assert paths[2].exists()
    assert malformed.exists()
    assert payload["warnings"][0]["code"] == "invalid_report_json"


def test_audit_history_prune_schema_and_docs(tmp_path: Path) -> None:
    runner = CliRunner()
    paths = seed_reports(tmp_path / "reports")
    payload_path = tmp_path / "prune.json"
    result = runner.invoke(app, ["audit-history", "prune", "--dir", str(paths[0].parent), "--keep", "2", "--json"])
    assert result.exit_code == 0, result.output
    payload_path.write_text(result.output, encoding="utf-8")

    result = runner.invoke(app, ["validate-json", "--schema", "audit_history_prune", "--input", str(payload_path), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["ok"] is True

    for path in [
        Path("docs/v0/phases/phase-10-audit-history-retention/plan.md"),
        Path("docs/v0/phases/phase-10-audit-history-retention/external-review.md"),
        Path("docs/schemas/audit_history_prune.schema.json"),
    ]:
        assert path.exists(), f"missing {path}"
