from __future__ import annotations

from pathlib import Path

from threadvault.retention import resolve_retention_keep


def test_resolve_retention_keep_uses_cli_first(tmp_path: Path) -> None:
    config = tmp_path / "threadvault.toml"
    config.write_text("[audit_history]\nkeep = 3\n", encoding="utf-8")

    keep, source = resolve_retention_keep(7, config, "audit_history")

    assert keep == 7
    assert source == "cli"


def test_resolve_retention_keep_uses_each_config_section(tmp_path: Path) -> None:
    config = tmp_path / "threadvault.toml"
    config.write_text(
        """
[audit_history]
keep = 2

[backup_history]
keep = 4

[restore_history]
keep = 6
""",
        encoding="utf-8",
    )

    assert resolve_retention_keep(None, config, "audit_history") == (2, "config")
    assert resolve_retention_keep(None, config, "backup_history") == (4, "config")
    assert resolve_retention_keep(None, config, "restore_history") == (6, "config")


def test_resolve_retention_keep_reports_missing_section(tmp_path: Path) -> None:
    config = tmp_path / "threadvault.toml"
    config.write_text("[audit_history]\nkeep = 2\n", encoding="utf-8")

    try:
        resolve_retention_keep(None, config, "restore_history")
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("expected ValueError")

    assert "Provide --keep or configure [restore_history].keep" in message
    assert str(config) in message


def test_resolve_retention_keep_preserves_config_validation_errors(tmp_path: Path) -> None:
    config = tmp_path / "threadvault.toml"
    config.write_text("[backup_history]\nkeep = true\n", encoding="utf-8")

    try:
        resolve_retention_keep(None, config, "backup_history")
    except ValueError as exc:
        assert "backup_history.keep must be an integer" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_v26_docs_exist() -> None:
    for path in [
        Path("docs/v0/phases/phase-26-retention-resolution-helper/plan.md"),
        Path("docs/v0/phases/phase-26-retention-resolution-helper/external-review.md"),
    ]:
        assert path.exists(), f"missing {path}"
