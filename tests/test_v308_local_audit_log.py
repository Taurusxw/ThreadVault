from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.governance import AUDIT_APPEND_COMMAND
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas


def test_governance_audit_append_creates_jsonl_record(tmp_path: Path) -> None:
    runner = CliRunner()
    log = tmp_path / "audit.jsonl"

    result = runner.invoke(
        app,
        [
            "governance",
            "audit",
            "append",
            "--log",
            str(log),
            "--operation",
            "export_archive",
            "--actor",
            "local-user",
            "--status",
            "ok",
            "--target-type",
            "session",
            "--target-id",
            "sess-current",
            "--metadata",
            "profile=markdown",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_audit_append", payload)["ok"] is True
    assert payload["contract_version"] == "governance_audit_append.v1"
    assert payload["ok"] is True
    assert payload["log"]["path"] == str(log)
    assert payload["log"]["local_only"] is True
    assert payload["log"]["server_required"] is False
    assert payload["record"]["record_version"] == "governance_audit_record.v1"
    assert payload["record"]["operation"] == "export_archive"
    assert payload["record"]["actor"] == "local-user"
    assert payload["record"]["target"] == {"type": "session", "id": "sess-current"}
    assert payload["record"]["metadata"] == {"profile": "markdown"}
    assert payload["record"]["local_only"] is True
    assert payload["diagnostics"]["append_only"] is True
    assert log.exists()
    assert len(log.read_text(encoding="utf-8").splitlines()) == 1


def test_governance_audit_list_reads_records_and_limit(tmp_path: Path) -> None:
    runner = CliRunner()
    log = tmp_path / "audit.jsonl"
    for index in range(3):
        result = runner.invoke(
            app,
            [
                "governance",
                "audit",
                "append",
                "--log",
                str(log),
                "--operation",
                "read_summary_search",
                "--actor",
                "local-user",
                "--status",
                "ok",
                "--target-type",
                "session",
                "--target-id",
                f"sess-{index}",
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output

    result = runner.invoke(app, ["governance", "audit", "list", "--log", str(log), "--limit", "2", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_audit_list", payload)["ok"] is True
    assert payload["contract_version"] == "governance_audit_list.v1"
    assert payload["log"]["exists"] is True
    assert payload["warnings"] == []
    assert payload["diagnostics"]["record_count"] == 2
    assert [record["target"]["id"] for record in payload["records"]] == ["sess-1", "sess-2"]


def test_governance_audit_list_tolerates_malformed_lines(tmp_path: Path) -> None:
    runner = CliRunner()
    log = tmp_path / "audit.jsonl"
    log.write_text('{"record_version":"governance_audit_record.v1"}\nnot-json\n[]\n', encoding="utf-8")

    result = runner.invoke(app, ["governance", "audit", "list", "--log", str(log), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_audit_list", payload)["ok"] is True
    assert payload["records"] == []
    assert [warning["code"] for warning in payload["warnings"]] == [
        "invalid_audit_record",
        "invalid_audit_json",
        "invalid_audit_record",
    ]
    assert payload["diagnostics"]["warning_count"] == 3


def test_governance_audit_discovery_schema_and_docs() -> None:
    caps = capabilities()
    assert "governance audit append" in caps["json_outputs"]
    assert "governance audit list" in caps["json_outputs"]
    assert caps["feature_flags"]["governance_audit_log"] is True

    guide = robot_guide()
    assert guide["governance"]["audit_append_contract_version"] == "governance_audit_append.v1"
    assert guide["governance"]["audit_list_contract_version"] == "governance_audit_list.v1"
    assert guide["governance"]["audit_schemas"] == ["governance_audit_append", "governance_audit_list"]
    assert guide["governance"]["audit_log_implemented"] is True
    assert AUDIT_APPEND_COMMAND in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "governance_audit_append" in schemas
    assert "governance_audit_list" in schemas
    assert get_schema("governance_audit_append")["type"] == "object"
    assert get_schema("governance_audit_list")["type"] == "object"
    assert Path("docs/schemas/governance_audit_append.schema.json").exists()
    assert Path("docs/schemas/governance_audit_list.schema.json").exists()

    for path in [
        Path("docs/v3/phases/phase-08-local-audit-log-workflow/plan.md"),
        Path("docs/v3/phases/phase-08-local-audit-log-workflow/design-notes.md"),
        Path("docs/v3/phases/phase-08-local-audit-log-workflow/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()
