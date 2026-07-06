from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from threadvault.cli import app
from threadvault.governance import CENTRALIZED_AUDIT_STORE_COMMAND
from threadvault.schemas import get_schema, validate_payload
from threadvault.store import ArchiveStore, capabilities, robot_guide, robot_schemas


def test_centralized_audit_store_default_missing_store_preserves_local_first() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["governance", "audit", "centralized-store", "--action", "verify", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert validate_payload("governance_centralized_audit_store", payload)["ok"] is True
    assert payload["contract_version"] == "governance_centralized_audit_store.v1"
    assert payload["store"]["available"] is False
    assert payload["store"]["path"] is None
    assert payload["errors"][0]["code"] == "centralized_audit_store_not_configured"
    assert payload["governance"]["server_required"] is False
    assert payload["governance"]["server_opt_in"] is True
    assert payload["governance"]["cloud_sync"] is False
    assert payload["diagnostics"]["local_first"] is True
    assert payload["diagnostics"]["privacy_first"] is True
    assert payload["diagnostics"]["v2_retrieval_core_changed"] is False


def test_centralized_audit_store_append_list_and_verify(tmp_path: Path) -> None:
    runner = CliRunner()
    store = tmp_path / "central-audit.jsonl"

    append_result = runner.invoke(
        app,
        [
            "governance",
            "audit",
            "centralized-store",
            "--action",
            "append",
            "--store",
            str(store),
            "--operation",
            "export_archive",
            "--actor",
            "reviewer@example",
            "--status",
            "ok",
            "--target-type",
            "session",
            "--target-id",
            "sess-current",
            "--metadata",
            "client=threadvault-local-tui",
            "--json",
        ],
    )
    list_result = runner.invoke(
        app,
        [
            "governance",
            "audit",
            "centralized-store",
            "--action",
            "list",
            "--store",
            str(store),
            "--actor",
            "reviewer@example",
            "--json",
        ],
    )
    verify_result = runner.invoke(
        app,
        ["governance", "audit", "centralized-store", "--action", "verify", "--store", str(store), "--json"],
    )

    assert append_result.exit_code == 0, append_result.output
    assert list_result.exit_code == 0, list_result.output
    assert verify_result.exit_code == 0, verify_result.output
    append_payload = json.loads(append_result.output)
    list_payload = json.loads(list_result.output)
    verify_payload = json.loads(verify_result.output)
    assert validate_payload("governance_centralized_audit_store", append_payload)["ok"] is True
    assert append_payload["append"]["written"] is True
    assert append_payload["append"]["record"]["record_version"] == "governance_centralized_audit_record.v1"
    assert append_payload["append"]["record"]["previous_hash"] is None
    assert append_payload["append"]["record"]["record_hash"]
    assert append_payload["append"]["record"]["provenance"]["binding_method"] == "manual_actor_label"
    assert list_payload["query"]["returned_count"] == 1
    assert list_payload["records"][0]["operation"] == "export_archive"
    assert list_payload["records"][0]["metadata"]["client"] == "threadvault-local-tui"
    assert verify_payload["verification"]["ok"] is True
    assert verify_payload["verification"]["record_count"] == 1
    assert verify_payload["verification"]["hash_chain_valid"] is True


def test_centralized_audit_store_detects_tampering(tmp_path: Path) -> None:
    runner = CliRunner()
    store = tmp_path / "central-audit.jsonl"
    result = runner.invoke(
        app,
        [
            "governance",
            "audit",
            "centralized-store",
            "--action",
            "append",
            "--store",
            str(store),
            "--operation",
            "export_archive",
            "--actor",
            "reviewer@example",
            "--status",
            "ok",
            "--target-type",
            "session",
            "--target-id",
            "sess-current",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    record = json.loads(store.read_text(encoding="utf-8").splitlines()[0])
    record["status"] = "tampered"
    store.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")

    verify_result = runner.invoke(
        app,
        ["governance", "audit", "centralized-store", "--action", "verify", "--store", str(store), "--json"],
    )

    assert verify_result.exit_code == 0, verify_result.output
    payload = json.loads(verify_result.output)
    assert payload["verification"]["ok"] is False
    assert payload["verification"]["hash_chain_valid"] is False
    assert "record_hash_mismatch" in {error["code"] for error in payload["verification"]["errors"]}
    assert "centralized_audit_integrity_failed" in {blocker["code"] for blocker in payload["blockers"]}


def test_centralized_audit_store_config_drives_readiness_and_gap_audit(tmp_path: Path) -> None:
    runner = CliRunner()
    store = tmp_path / "central-audit.jsonl"
    config = tmp_path / "threadvault.toml"
    config.write_text(
        f"""
[governance]
enabled = true

[governance.audit]
central_store = "{store.as_posix()}"
""".strip(),
        encoding="utf-8",
    )

    append_result = runner.invoke(
        app,
        [
            "governance",
            "audit",
            "centralized-store",
            "--config",
            str(config),
            "--action",
            "append",
            "--operation",
            "export_archive",
            "--actor",
            "reviewer@example",
            "--status",
            "ok",
            "--target-type",
            "session",
            "--target-id",
            "sess-current",
            "--json",
        ],
    )
    readiness_result = runner.invoke(
        app,
        ["governance", "audit", "centralized-readiness", "--config", str(config), "--json"],
    )

    assert append_result.exit_code == 0, append_result.output
    assert readiness_result.exit_code == 0, readiness_result.output
    readiness = json.loads(readiness_result.output)
    assert readiness["governance"]["centralized_audit_ready"] is True
    assert readiness["centralized_audit"]["store_implemented"] is True
    assert readiness["centralized_audit"]["store_available"] is True
    assert readiness["centralized_audit"]["query_interface_implemented"] is True
    assert readiness["integrity"]["tamper_evidence_implemented"] is True
    assert readiness["integrity"]["record_hashing_implemented"] is True
    assert readiness["review"]["query_workflow_implemented"] is True
    assert readiness["retention"]["policy_implemented"] is True
    assert readiness["retention"]["policy_available"] is False
    assert readiness["backup_export"]["backup_policy_implemented"] is True
    assert readiness["backup_export"]["policy_available"] is False

    gap = ArchiveStore(Path("unused.db")).governance_v3_completion_gap_audit()
    blocker_codes = {item["code"] for item in gap["blockers"]}
    gaps = {item["code"]: item for item in gap["remaining_gaps"]}
    assert "centralized_audit_store_missing" not in blocker_codes
    assert "centralized_audit_store_runtime" in gap["implemented_capabilities"]
    assert gaps["centralized_audit_and_retention"]["status"] == "store_policy_and_instrumentation_accepted"
    assert gap["completion"]["accepted_phase_count"] == 33
    assert gap["completion"]["current_phase"] == "phase-33-v3-final-acceptance-smoke"
    assert gap["completion"]["blocking_count"] == 0


def test_centralized_audit_store_discovery_schema_and_docs() -> None:
    caps = capabilities()
    assert "governance audit centralized-store" in caps["json_outputs"]
    assert caps["feature_flags"]["governance_centralized_audit_store"] is True

    guide = robot_guide()
    assert guide["governance"]["centralized_audit_store_contract_version"] == "governance_centralized_audit_store.v1"
    assert guide["governance"]["centralized_audit_store_schema"] == "governance_centralized_audit_store"
    assert CENTRALIZED_AUDIT_STORE_COMMAND in guide["recommended_commands"]

    schemas = robot_schemas()
    assert "governance_centralized_audit_store" in schemas
    assert get_schema("governance_centralized_audit_store")["type"] == "object"
    assert Path("docs/schemas/governance_centralized_audit_store.schema.json").exists()

    for path in [
        Path("docs/progress/archive/legacy-v3/phases/phase-30-centralized-audit-store-runtime/plan.md"),
        Path("docs/progress/archive/legacy-v3/phases/phase-30-centralized-audit-store-runtime/design-notes.md"),
        Path("docs/progress/archive/legacy-v3/phases/phase-30-centralized-audit-store-runtime/acceptance.md"),
    ]:
        assert path.exists(), f"missing {path}"
    assert not Path("deep-research-report.md").exists()
