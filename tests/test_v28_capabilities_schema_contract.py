from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.schemas import get_schema, validate_payload

REQUIRED_CAPABILITIES_FIELDS = [
    "name",
    "contract_version",
    "schema_version",
    "stability_policy",
    "commands",
    "json_outputs",
    "export_formats",
    "export_profiles",
    "privacy_modes",
    "search_fields",
    "feature_flags",
]


def test_capabilities_schema_requires_runtime_discovery_fields() -> None:
    schema = get_schema("capabilities")

    for field in REQUIRED_CAPABILITIES_FIELDS:
        assert field in schema["required"]
        assert field in schema["properties"]


def test_real_capabilities_output_validates_against_schema() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["capabilities", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    validation = validate_payload("capabilities", payload)
    assert validation["ok"] is True
    assert payload["json_outputs"]
    assert payload["export_profiles"] == ["full", "brief", "agent", "review"]
    assert payload["privacy_modes"] == ["warn", "redact", "fail"]
    assert payload["search_fields"] == ["minimal", "standard", "full"]


def test_capabilities_schema_rejects_missing_json_outputs() -> None:
    payload = {
        "name": "threadvault",
        "contract_version": "0.6",
        "schema_version": 2,
        "stability_policy": "append-only",
        "commands": [],
        "export_formats": [],
        "export_profiles": [],
        "privacy_modes": [],
        "search_fields": [],
        "feature_flags": {},
    }

    result = validate_payload("capabilities", payload)

    assert result["ok"] is False
    assert any("json_outputs" in error["message"] for error in result["errors"])


def test_robot_docs_capabilities_summary_matches_schema_fields() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["robot-docs", "schemas", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    summary = payload["capabilities"]
    for field in REQUIRED_CAPABILITIES_FIELDS:
        assert field in summary


def test_v28_docs_exist() -> None:
    for path in [
        Path("docs/v0/phases/phase-28-capabilities-schema-contract/plan.md"),
        Path("docs/v0/phases/phase-28-capabilities-schema-contract/external-review.md"),
    ]:
        assert path.exists(), f"missing {path}"
