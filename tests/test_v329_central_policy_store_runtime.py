from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.governance import CENTRAL_POLICY_STORE_COMMAND
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import ArchiveStore, capabilities, robot_guide, robot_schemas


def _policy(path: Path) -> Path:
    path.write_text(
        json.dumps(
            {
                "contract_version": "threadvault_central_policy.v1",
                "policy_id": "team-local",
                "version": "2026-07-01.1",
                "provenance": {
                    "author": "owner@example",
                    "reviewed_by": ["reviewer@example"],
                    "approved_by": ["owner@example"],
                    "source": "local-file",
                },
                "roles": [
                    {"name": "reader", "access_levels": ["summary_search"]},
                    {"name": "reviewer", "access_levels": ["summary_search", "export"]},
                    {"name": "maintainer", "access_levels": ["summary_search", "export", "restore"]},
                ],
                "actors": [
                    {"id": "reviewer@example", "roles": ["reviewer"]},
                    {"id": "reader@example", "roles": ["reader"]},
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def test_central_policy_store_default_missing_policy_preserves_local_first() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "policy", "central-store", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_central_policy_store", payload)["ok"] is True
    assert payload["contract_version"] == "governance_central_policy_store.v1"
    assert payload["store"]["available"] is False
    assert payload["policy"]["valid"] is False
    assert payload["validation"]["ok"] is False
    assert payload["validation"]["errors"][0]["code"] == "central_policy_not_configured"
    assert payload["governance"]["server_required"] is False
    assert payload["governance"]["server_opt_in"] is True
    assert payload["governance"]["cloud_sync"] is False
    assert payload["diagnostics"]["local_first"] is True
    assert payload["diagnostics"]["privacy_first"] is True
    assert payload["diagnostics"]["v2_retrieval_core_changed"] is False


def test_central_policy_store_valid_policy_resolves_actor_and_operation(tmp_path: Path) -> None:
    runner = CliRunner()
    policy = _policy(tmp_path / "central-policy.json")

    result = runner.invoke(
        app,
        [
            "governance",
            "policy",
            "central-store",
            "--policy",
            str(policy),
            "--actor",
            "reviewer@example",
            "--operation",
            "export_archive",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_central_policy_store", payload)["ok"] is True
    assert payload["store"]["available"] is True
    assert payload["policy"]["valid"] is True
    assert payload["policy"]["policy_id"] == "team-local"
    assert payload["policy"]["version"] == "2026-07-01.1"
    assert payload["provenance"]["author_recorded"] is True
    assert payload["provenance"]["review_recorded"] is True
    assert payload["provenance"]["approval_recorded"] is True
    assert payload["provenance"]["source_hash_recorded"] is True
    assert payload["actor_resolution"]["known"] is True
    assert payload["actor_resolution"]["roles"] == ["reviewer"]
    assert payload["actor_resolution"]["access_levels"] == ["export", "summary_search"]
    assert payload["operation_resolution"]["known"] is True
    assert payload["operation_resolution"]["required_access_level"] == "export"
    assert payload["operation_resolution"]["allowed"] is True
    assert payload["enforcement"]["would_allow"] is True
    assert payload["enforcement"]["shared_enforcement_ready"] is False


def test_central_policy_store_blocks_unknown_actor_or_denied_operation(tmp_path: Path) -> None:
    runner = CliRunner()
    policy = _policy(tmp_path / "central-policy.json")

    result = runner.invoke(
        app,
        [
            "governance",
            "policy",
            "central-store",
            "--policy",
            str(policy),
            "--actor",
            "reader@example",
            "--operation",
            "export_archive",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["actor_resolution"]["roles"] == ["reader"]
    assert payload["operation_resolution"]["allowed"] is False
    assert payload["enforcement"]["status"] == "would_block"
    assert "central_policy_operation_denied" in {blocker["code"] for blocker in payload["blockers"]}


def test_central_policy_store_invalid_policy_reports_structured_errors(tmp_path: Path) -> None:
    runner = CliRunner()
    policy = tmp_path / "bad-policy.json"
    policy.write_text(
        json.dumps(
            {
                "contract_version": "wrong",
                "policy_id": "team-local",
                "version": "1",
                "provenance": {"author": "owner@example", "source": "local-file"},
                "roles": [{"name": "unknown", "access_levels": ["raw_transcript"]}],
                "actors": [{"id": "reviewer@example", "roles": ["reviewer"]}],
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["governance", "policy", "central-store", "--policy", str(policy), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    error_codes = {error["code"] for error in payload["validation"]["errors"]}
    assert payload["policy"]["valid"] is False
    assert "invalid_contract_version" in error_codes
    assert "unknown_role" in error_codes
    assert "actor_unknown_role" in error_codes


def test_central_policy_store_config_drives_readiness_and_gap_audit(tmp_path: Path) -> None:
    runner = CliRunner()
    policy = _policy(tmp_path / "central-policy.json")
    config = tmp_path / "threadvault.toml"
    config.write_text(
        f"""
[governance]
enabled = true

[governance.policy]
central_store = "{policy.as_posix()}"
""".strip(),
        encoding="utf-8",
    )

    store_result = runner.invoke(app, ["governance", "policy", "central-store", "--config", str(config), "--json"])
    readiness_result = runner.invoke(app, ["governance", "policy", "central-readiness", "--config", str(config), "--json"])

    assert store_result.exit_code == 0, store_result.output
    assert readiness_result.exit_code == 0, readiness_result.output
    store_payload = json.loads(store_result.output)
    readiness_payload = json.loads(readiness_result.output)
    assert store_payload["store"]["available"] is True
    assert readiness_payload["governance"]["central_policy_ready"] is True
    assert readiness_payload["central_policy"]["store_implemented"] is True
    assert readiness_payload["adapter"]["local_adapter_implemented"] is True
    assert readiness_payload["versioning"]["policy_versioning_implemented"] is True
    assert readiness_payload["identity_dependency"]["actor_policy_resolution_ready"] is True

    gap = ArchiveStore(Path("unused.db")).governance_v3_completion_gap_audit()
    blocker_codes = {item["code"] for item in gap["blockers"]}
    gaps = {item["code"]: item for item in gap["remaining_gaps"]}
    assert "central_policy_store_missing" not in blocker_codes
    assert "central_policy_store_runtime" in gap["implemented_capabilities"]
    assert gaps["team_identity_and_policy"]["status"] == "identity_and_policy_store_accepted_enforcement_pending"
    assert gap["completion"]["accepted_phase_count"] == 33
    assert gap["completion"]["current_phase"] == "phase-33-v3-final-acceptance-smoke"
    assert gap["completion"]["blocking_count"] == 0


def test_central_policy_store_discovery_schema_and_docs() -> None:
    caps = capabilities()
    assert "governance policy central-store" in caps["json_outputs"]
    assert caps["feature_flags"]["governance_central_policy_store"] is True

    guide = robot_guide()
    assert guide["governance"]["central_policy_store_contract_version"] == "governance_central_policy_store.v1"
    assert guide["governance"]["central_policy_store_schema"] == "governance_central_policy_store"
    assert CENTRAL_POLICY_STORE_COMMAND in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "governance_central_policy_store" in schemas
    assert get_schema("governance_central_policy_store")["type"] == "object"
    assert Path("docs/schemas/governance_central_policy_store.schema.json").exists()

    for path in [
        Path("docs/v3/phases/phase-29-central-policy-store-runtime/plan.md"),
        Path("docs/v3/phases/phase-29-central-policy-store-runtime/design-notes.md"),
        Path("docs/v3/phases/phase-29-central-policy-store-runtime/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()
