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


def test_audit_history_prune_uses_config_keep(tmp_path: Path) -> None:
    runner = CliRunner()
    paths = seed_reports(tmp_path / "reports")
    config = tmp_path / "threadvault.toml"
    config.write_text("[audit_history]\nkeep = 2\n", encoding="utf-8")

    result = runner.invoke(app, ["audit-history", "prune", "--dir", str(paths[0].parent), "--config", str(config), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["keep"] == 2
    assert payload["keep_source"] == "config"
    assert len(payload["kept"]) == 2
    assert len(payload["deletable"]) == 1
    assert all(path.exists() for path in paths)


def test_audit_history_prune_cli_keep_overrides_config(tmp_path: Path) -> None:
    runner = CliRunner()
    paths = seed_reports(tmp_path / "reports")
    config = tmp_path / "threadvault.toml"
    config.write_text("[audit_history]\nkeep = 1\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["audit-history", "prune", "--dir", str(paths[0].parent), "--config", str(config), "--keep", "2", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["keep"] == 2
    assert payload["keep_source"] == "cli"
    assert len(payload["kept"]) == 2


def test_audit_history_prune_requires_keep_or_config(tmp_path: Path) -> None:
    runner = CliRunner()
    paths = seed_reports(tmp_path / "reports")
    missing_config = tmp_path / "missing.toml"

    result = runner.invoke(app, ["audit-history", "prune", "--dir", str(paths[0].parent), "--config", str(missing_config), "--json"])

    assert result.exit_code != 0
    assert "Provide --keep or configure [audit_history].keep" in result.output


def test_audit_history_prune_rejects_invalid_config_keep(tmp_path: Path) -> None:
    runner = CliRunner()
    paths = seed_reports(tmp_path / "reports")
    config = tmp_path / "threadvault.toml"
    config.write_text("[audit_history]\nkeep = 0\n", encoding="utf-8")

    result = runner.invoke(app, ["audit-history", "prune", "--dir", str(paths[0].parent), "--config", str(config), "--json"])

    assert result.exit_code != 0
    assert "audit_history.keep must be greater than or equal to 1" in result.output


def test_v11_docs_exist() -> None:
    for path in [
        Path("docs/v0/phases/phase-11-audit-retention-config/plan.md"),
        Path("docs/v0/phases/phase-11-audit-retention-config/external-review.md"),
    ]:
        assert path.exists(), f"missing {path}"
