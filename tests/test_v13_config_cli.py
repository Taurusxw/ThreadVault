from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.app_config import describe_app_config, diagnose_app_config
from threadvault.cli import app


def test_describe_app_config_missing_file_is_safe(tmp_path: Path) -> None:
    config = tmp_path / "missing.toml"

    payload = describe_app_config(config)

    assert payload["exists"] is False
    assert payload["loaded"] is False
    assert payload["privacy"]["allowlist_count"] == 0
    assert payload["audit_history"]["keep"] is None


def test_config_show_hides_allowlist_values_by_default(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    config.write_text(
        """
[privacy]
allowlist = [
  { kind = "email", text = "dev@example.com" },
  { kind = "windows_abs_path", pattern = '^E:\\\\Codex\\\\' },
]

[audit_history]
keep = 5
""",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["config", "show", "--config", str(config), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["loaded"] is True
    assert payload["sections"] == ["audit_history", "privacy"]
    assert payload["privacy"]["allowlist_count"] == 2
    assert payload["privacy"]["allowlist_kinds"] == ["email", "windows_abs_path"]
    assert payload["privacy"]["allowlist_rules"] is None
    assert "dev@example.com" not in result.output
    assert payload["audit_history"]["keep"] == 5


def test_config_show_can_include_values_with_explicit_opt_in(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    config.write_text("[privacy]\nallowlist = [{ kind = \"email\", text = \"dev@example.com\" }]\n", encoding="utf-8")

    result = runner.invoke(app, ["config", "show", "--config", str(config), "--include-values", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["privacy"]["allowlist_rules"][0]["text"] == "dev@example.com"


def test_config_show_reports_governance_identity_actor_count(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    config.write_text(
        """
[governance]
enabled = true

[governance.identity]
actors = [
  { id = "reviewer@example", roles = ["reviewer"] },
]
""",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["config", "show", "--config", str(config), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["governance"]["enabled"] is True
    assert payload["governance"]["identity"]["actor_count"] == 1
    assert payload["governance"]["identity"]["actors"][0]["id"] == "reviewer@example"


def test_config_doctor_reports_invalid_toml_as_json(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    config.write_text("[privacy\n", encoding="utf-8")

    result = runner.invoke(app, ["config", "doctor", "--config", str(config), "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["errors"][0]["code"] == "invalid_toml"


def test_config_doctor_reports_invalid_regex(tmp_path: Path) -> None:
    config = tmp_path / "threadvault.toml"
    config.write_text("[privacy]\nallowlist = [{ pattern = \"[\" }]\n", encoding="utf-8")

    payload = diagnose_app_config(config)

    assert payload["ok"] is False
    assert payload["errors"][0]["code"] == "invalid_privacy_allowlist_regex"


def test_config_doctor_reports_invalid_keep(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    config.write_text("[audit_history]\nkeep = 0\n", encoding="utf-8")

    result = runner.invoke(app, ["config", "doctor", "--config", str(config), "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["errors"][0]["code"] == "invalid_config_value"


def test_config_outputs_have_schemas(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    config.write_text("[audit_history]\nkeep = 2\n", encoding="utf-8")
    show_payload = tmp_path / "config-show.json"
    doctor_payload = tmp_path / "config-doctor.json"

    result = runner.invoke(app, ["config", "show", "--config", str(config), "--json"])
    assert result.exit_code == 0, result.output
    show_payload.write_text(result.output, encoding="utf-8")

    result = runner.invoke(app, ["config", "doctor", "--config", str(config), "--json"])
    assert result.exit_code == 0, result.output
    doctor_payload.write_text(result.output, encoding="utf-8")

    result = runner.invoke(app, ["validate-json", "--schema", "config_show", "--input", str(show_payload), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["ok"] is True

    result = runner.invoke(app, ["validate-json", "--schema", "config_doctor", "--input", str(doctor_payload), "--json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["ok"] is True


def test_v13_docs_exist() -> None:
    for path in [
        Path("docs/progress/archive/legacy-v0/phases/phase-13-config-observability/plan.md"),
        Path("docs/progress/archive/legacy-v0/phases/phase-13-config-observability/external-review.md"),
    ]:
        assert path.exists(), f"missing {path}"
