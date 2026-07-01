from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.app_config import describe_app_config, load_app_config
from threadvault.cli import app
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas


def test_governance_status_default_is_disabled_and_local_first() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "status", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_status", payload)["ok"] is True
    assert payload["contract_version"] == "governance_status.v1"
    assert payload["enabled"] is False
    assert payload["mode"] == "disabled"
    assert payload["defaults"]["local_first"] is True
    assert payload["defaults"]["server_required"] is False
    assert payload["defaults"]["cloud_sync"] is False
    assert payload["defaults"]["external_model_calls"] is False
    assert payload["defaults"]["permissions_enforced"] is False
    assert payload["diagnostics"]["shared_server_implemented"] is False
    assert payload["diagnostics"]["team_permissions_implemented"] is False
    assert payload["diagnostics"]["audit_log_implemented"] is True


def test_governance_status_config_opt_in_does_not_require_server(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "threadvault.toml"
    config.write_text("[governance]\nenabled = true\n", encoding="utf-8")

    result = runner.invoke(app, ["governance", "status", "--config", str(config), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_status", payload)["ok"] is True
    assert payload["enabled"] is True
    assert payload["mode"] == "local_opt_in"
    assert payload["diagnostics"]["config_enabled"] is True
    assert payload["diagnostics"]["config_path"] == str(config)
    assert payload["defaults"]["server_required"] is False
    assert payload["defaults"]["server_available"] is False


def test_governance_vocabularies_match_v3_roadmap() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "status", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    access_levels = {item["name"] for item in payload["access_levels"]}
    assert access_levels == {"raw_transcript", "summary_search", "export", "delete_retention", "restore"}
    roles = {item["name"] for item in payload["roles"]}
    assert roles == {"owner", "maintainer", "reviewer", "reader"}
    operations = {item["name"] for item in payload["sensitive_operations"]}
    assert {
        "read_raw_transcript",
        "read_summary_search",
        "export_archive",
        "delete_or_prune",
        "restore_backup",
        "external_model_call",
    } <= operations
    assert "external_model_call" in payload["audit_requirements"]["operations_requiring_audit"]


def test_governance_config_is_visible_in_app_config(tmp_path: Path) -> None:
    config = tmp_path / "threadvault.toml"
    config.write_text("[governance]\nenabled = true\n", encoding="utf-8")

    loaded = load_app_config(config)
    described = describe_app_config(config)

    assert loaded.governance_enabled is True
    assert described["governance"]["enabled"] is True
    assert "governance" in described["sections"]


def test_governance_discovery_schema_and_docs() -> None:
    caps = capabilities()
    assert "governance" in caps["commands"]
    assert "governance status" in caps["json_outputs"]
    assert caps["feature_flags"]["governance_baseline"] is True

    guide = robot_guide()
    assert guide["governance"]["status_contract_version"] == "governance_status.v1"
    assert guide["governance"]["schema"] == "governance_status"
    assert guide["governance"]["enabled_by_default"] is False
    assert "threadvault governance status --json" in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "governance_status" in schemas
    assert get_schema("governance_status")["type"] == "object"
    assert Path("docs/schemas/governance_status.schema.json").exists()

    manifest = runner_manifest()
    assert manifest["governance"]["contract_version"] == "governance_status.v1"
    assert manifest["governance"]["enabled"] is False
    assert manifest["schemas"]["governance"] == "governance_status"

    for path in [
        Path("docs/v3/phases/phase-07-governance-baseline/plan.md"),
        Path("docs/v3/phases/phase-07-governance-baseline/design-notes.md"),
        Path("docs/v3/phases/phase-07-governance-baseline/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()


def runner_manifest() -> dict:
    runner = CliRunner()
    result = runner.invoke(app, ["client", "manifest", "--json"])
    assert result.exit_code == 0, result.output
    return json.loads(result.output)
