from __future__ import annotations

from pathlib import Path

from threadvault.app_config import AppConfig, load_app_config
from threadvault.privacy_config import PrivacyConfig, load_privacy_config


def test_load_app_config_parses_privacy_and_audit_history(tmp_path: Path) -> None:
    config = tmp_path / "threadvault.toml"
    config.write_text(
        """
[privacy]
allowlist = [
  { kind = "email", text = "dev@example.com" },
  { kind = "windows_abs_path", pattern = '^E:\\\\Codex\\\\' },
]

[audit_history]
keep = 7

[backup_history]
keep = 4

[restore_history]
keep = 6
""",
        encoding="utf-8",
    )

    loaded = load_app_config(config)

    assert isinstance(loaded, AppConfig)
    assert loaded.source_path == config
    assert loaded.audit_history_keep == 7
    assert loaded.backup_history_keep == 4
    assert loaded.restore_history_keep == 6
    assert len(loaded.allowlist) == 2
    assert loaded.allowlist[0].kind == "email"
    assert loaded.allowlist[0].text == "dev@example.com"
    assert loaded.allowlist[1].pattern is not None
    assert loaded.allowlist[1].pattern.search("E:\\Codex\\ThreadVault")


def test_privacy_config_compatibility_wrapper(tmp_path: Path) -> None:
    config = tmp_path / "threadvault.toml"
    config.write_text("[audit_history]\nkeep = 3\n", encoding="utf-8")

    loaded = load_privacy_config(config)

    assert isinstance(loaded, PrivacyConfig)
    assert loaded.audit_history_keep == 3


def test_load_app_config_parses_governance_identity_actors(tmp_path: Path) -> None:
    config = tmp_path / "threadvault.toml"
    config.write_text(
        """
[governance]
enabled = true

[governance.identity]
actors = [
  { id = "reviewer@example", display = "Reviewer", roles = ["reviewer"], source = "local-static" },
]
""",
        encoding="utf-8",
    )

    loaded = load_app_config(config)

    assert loaded.governance_enabled is True
    assert loaded.governance_identity_actors == [
        {
            "id": "reviewer@example",
            "display": "Reviewer",
            "roles": ["reviewer"],
            "source": "local-static",
        }
    ]


def test_load_app_config_rejects_boolean_audit_keep(tmp_path: Path) -> None:
    config = tmp_path / "threadvault.toml"
    config.write_text("[audit_history]\nkeep = true\n", encoding="utf-8")

    try:
        load_app_config(config)
    except ValueError as exc:
        assert "audit_history.keep must be an integer" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_load_app_config_rejects_invalid_backup_keep(tmp_path: Path) -> None:
    config = tmp_path / "threadvault.toml"
    config.write_text("[backup_history]\nkeep = 0\n", encoding="utf-8")

    try:
        load_app_config(config)
    except ValueError as exc:
        assert "backup_history.keep must be greater than or equal to 1" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_load_app_config_rejects_boolean_restore_keep(tmp_path: Path) -> None:
    config = tmp_path / "threadvault.toml"
    config.write_text("[restore_history]\nkeep = true\n", encoding="utf-8")

    try:
        load_app_config(config)
    except ValueError as exc:
        assert "restore_history.keep must be an integer" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_v12_docs_exist() -> None:
    for path in [
        Path("docs/v0/phases/phase-12-app-config-module/plan.md"),
        Path("docs/v0/phases/phase-12-app-config-module/external-review.md"),
    ]:
        assert path.exists(), f"missing {path}"
