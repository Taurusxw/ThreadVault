from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.governance import CENTRAL_BACKUP_POLICY_COMMAND
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import capabilities, robot_guide, robot_schemas


def _write_backup_policy(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "contract_version": "threadvault_central_backup_policy.v1",
                "policy_id": "team-backup-policy",
                "version": "2026-07-01",
                "provenance": {
                    "author": "owner@example",
                    "reviewed_by": ["security@example"],
                    "approved_by": ["owner@example"],
                    "source": "phase-31-smoke",
                },
                "repository": {
                    "type": "local-file-policy",
                    "local_path": "central-backups",
                    "replication_required": False,
                },
                "backup": {
                    "scope": ["sqlite-db", "backup-manifest", "restore-history"],
                    "cadence": "manual-or-daily",
                    "operator_roles": ["owner", "maintainer"],
                },
                "restore": {
                    "approvals_required": 1,
                    "approver_roles": ["owner", "maintainer"],
                    "dry_run_required": True,
                    "pre_restore_backup_required": True,
                },
                "retention": {
                    "keep_latest": 10,
                    "prune_requires_approval": True,
                    "approver_roles": ["owner", "maintainer"],
                },
                "legal_hold": {
                    "enabled": True,
                    "bypass_allowed": False,
                    "approver_roles": ["owner"],
                },
                "recovery_testing": {
                    "required": True,
                    "cadence": "monthly",
                    "operator_roles": ["owner", "maintainer"],
                },
                "migration": {
                    "local_history_supported": True,
                    "review_required": True,
                    "operator_roles": ["owner", "maintainer"],
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_config(path: Path, policy: Path, audit_store: Path | None = None) -> None:
    audit_section = ""
    if audit_store is not None:
        audit_section = f'\n[governance.audit]\ncentral_store = "{audit_store.as_posix()}"\n'
    path.write_text(
        f"""
[governance]
enabled = true

[governance.identity]
actors = [
  {{ id = "maintainer@example", display = "Maintainer", roles = ["maintainer"], source = "local-static" }},
  {{ id = "reader@example", display = "Reader", roles = ["reader"], source = "local-static" }},
]

[governance.backup]
policy = "{policy.as_posix()}"
{audit_section}
""".strip()
        + "\n",
        encoding="utf-8",
    )


def test_central_backup_policy_default_missing_policy_preserves_local_first() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "backup", "policy", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_central_backup_policy", payload)["ok"] is True
    assert payload["contract_version"] == "governance_central_backup_policy.v1"
    assert payload["governance"]["enabled"] is False
    assert payload["governance"]["central_backup_policy_ready"] is False
    assert payload["governance"]["server_required"] is False
    assert payload["governance"]["server_opt_in"] is True
    assert payload["governance"]["cloud_sync"] is False
    assert payload["policy"]["valid"] is False
    assert payload["validation"]["errors"][0]["code"] == "central_backup_policy_not_configured"
    assert payload["diagnostics"]["local_first"] is True
    assert payload["diagnostics"]["privacy_first"] is True
    assert payload["diagnostics"]["v2_retrieval_core_changed"] is False


def test_central_backup_policy_valid_document_allows_maintainer_restore_preview(tmp_path: Path) -> None:
    runner = CliRunner()
    policy = tmp_path / "central-backup-policy.json"
    config = tmp_path / "threadvault.toml"
    _write_backup_policy(policy)
    _write_config(config, policy)

    result = runner.invoke(
        app,
        [
            "governance",
            "backup",
            "policy",
            "--config",
            str(config),
            "--operation",
            "restore_backup",
            "--actor",
            "maintainer@example",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_central_backup_policy", payload)["ok"] is True
    assert payload["policy"]["valid"] is True
    assert payload["provenance"]["approval_recorded"] is True
    assert payload["restore"]["approval_workflow_implemented"] is True
    assert payload["retention"]["policy_implemented"] is True
    assert payload["legal_hold"]["enabled"] is True
    assert payload["migration"]["local_history_supported"] is True
    assert payload["operation_resolution"]["known"] is True
    assert payload["operation_resolution"]["section"] == "restore"
    assert payload["operation_resolution"]["required_roles"] == ["owner", "maintainer"]
    assert payload["operation_resolution"]["actor_roles"] == ["maintainer"]
    assert payload["operation_resolution"]["allowed"] is True
    assert payload["enforcement"]["status"] == "would_allow"
    assert payload["enforcement"]["shared_execution_ready"] is False


def test_central_backup_policy_denies_actor_without_policy_role(tmp_path: Path) -> None:
    runner = CliRunner()
    policy = tmp_path / "central-backup-policy.json"
    config = tmp_path / "threadvault.toml"
    _write_backup_policy(policy)
    _write_config(config, policy)

    result = runner.invoke(
        app,
        [
            "governance",
            "backup",
            "policy",
            "--config",
            str(config),
            "--operation",
            "restore_backup",
            "--actor",
            "reader@example",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    blocker_codes = {item["code"] for item in payload["blockers"]}
    assert validate_payload("governance_central_backup_policy", payload)["ok"] is True
    assert payload["policy"]["valid"] is True
    assert payload["operation_resolution"]["allowed"] is False
    assert payload["enforcement"]["status"] == "would_block"
    assert "central_backup_policy_operation_denied" in blocker_codes


def test_central_backup_policy_updates_readiness_and_v3_gap_audit(tmp_path: Path) -> None:
    runner = CliRunner()
    policy = tmp_path / "central-backup-policy.json"
    config = tmp_path / "threadvault.toml"
    audit_store = tmp_path / "central-audit.jsonl"
    audit_store.write_text("", encoding="utf-8")
    _write_backup_policy(policy)
    _write_config(config, policy, audit_store=audit_store)

    readiness_result = runner.invoke(
        app,
        ["governance", "backup", "central-readiness", "--config", str(config), "--json"],
    )
    assert readiness_result.exit_code == 0, readiness_result.output
    readiness = json.loads(readiness_result.output)
    assert validate_payload("governance_central_backup_readiness", readiness)["ok"] is True
    assert readiness["governance"]["central_backup_ready"] is True
    assert readiness["policy"]["backup_policy_implemented"] is True
    assert readiness["readiness"]["safe_to_enable_central_backup"] is True
    assert readiness["diagnostics"]["central_backup_policy_runtime"] is True
    assert readiness["diagnostics"]["central_backup_policy_valid"] is True

    gap_result = runner.invoke(app, ["governance", "v3", "gap-audit", "--json"])
    assert gap_result.exit_code == 0, gap_result.output
    gap = json.loads(gap_result.output)
    blocker_codes = {item["code"] for item in gap["blockers"]}
    assert "centralized_backup_restore_policy_missing" not in blocker_codes
    assert "automatic_governance_instrumentation_incomplete" not in blocker_codes
    assert "v3_acceptance_smoke_missing" not in blocker_codes
    assert gap["completion"]["accepted_phase_count"] == 33
    assert gap["completion"]["current_phase"] == "phase-33-v3-final-acceptance-smoke"
    assert gap["completion"]["blocking_count"] == 0
    assert "central_backup_policy_runtime" in gap["implemented_capabilities"]


def test_central_backup_policy_discovery_schema_and_docs() -> None:
    caps = capabilities()
    assert "governance backup policy" in caps["json_outputs"]
    assert caps["feature_flags"]["governance_central_backup_policy"] is True

    guide = robot_guide()
    assert guide["governance"]["central_backup_policy_contract_version"] == "governance_central_backup_policy.v1"
    assert guide["governance"]["central_backup_policy_schema"] == "governance_central_backup_policy"
    assert CENTRAL_BACKUP_POLICY_COMMAND in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "governance_central_backup_policy" in schemas
    assert get_schema("governance_central_backup_policy")["type"] == "object"
    assert Path("docs/schemas/governance_central_backup_policy.schema.json").exists()

    for path in [
        Path("docs/progress/archive/legacy-v3/phases/phase-31-centralized-backup-restore-policy-runtime/plan.md"),
        Path("docs/progress/archive/legacy-v3/phases/phase-31-centralized-backup-restore-policy-runtime/design-notes.md"),
        Path("docs/progress/archive/legacy-v3/phases/phase-31-centralized-backup-restore-policy-runtime/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()
