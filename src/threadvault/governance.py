from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .app_config import AppConfig

GOVERNANCE_STATUS_CONTRACT_VERSION = "governance_status.v1"
GOVERNANCE_AUDIT_APPEND_CONTRACT_VERSION = "governance_audit_append.v1"
GOVERNANCE_AUDIT_LIST_CONTRACT_VERSION = "governance_audit_list.v1"
GOVERNANCE_AUDIT_RECORD_VERSION = "governance_audit_record.v1"
GOVERNANCE_CENTRALIZED_AUDIT_STORE_CONTRACT_VERSION = "governance_centralized_audit_store.v1"
GOVERNANCE_CENTRALIZED_AUDIT_RECORD_VERSION = "governance_centralized_audit_record.v1"
GOVERNANCE_PERMISSION_CHECK_CONTRACT_VERSION = "governance_permission_check.v1"
GOVERNANCE_ENFORCEMENT_GAPS_CONTRACT_VERSION = "governance_enforcement_gaps.v1"
GOVERNANCE_ENFORCEMENT_CHECK_CONTRACT_VERSION = "governance_enforcement_check.v1"
GOVERNANCE_POLICY_READINESS_CONTRACT_VERSION = "governance_policy_readiness.v1"
GOVERNANCE_SERVER_POLICY_READINESS_CONTRACT_VERSION = "governance_server_policy_readiness.v1"
GOVERNANCE_CENTRALIZED_AUDIT_READINESS_CONTRACT_VERSION = "governance_centralized_audit_readiness.v1"
GOVERNANCE_V3_COMPLETION_GAP_AUDIT_CONTRACT_VERSION = "governance_v3_completion_gap_audit.v1"
GOVERNANCE_IDENTITY_ACTOR_READINESS_CONTRACT_VERSION = "governance_identity_actor_readiness.v1"
GOVERNANCE_IDENTITY_ACTOR_BINDING_CONTRACT_VERSION = "governance_identity_actor_binding.v1"
GOVERNANCE_CENTRAL_POLICY_READINESS_CONTRACT_VERSION = "governance_central_policy_readiness.v1"
GOVERNANCE_CENTRAL_POLICY_STORE_CONTRACT_VERSION = "governance_central_policy_store.v1"
CENTRAL_POLICY_DOCUMENT_CONTRACT_VERSION = "threadvault_central_policy.v1"
GOVERNANCE_CENTRAL_BACKUP_READINESS_CONTRACT_VERSION = "governance_central_backup_readiness.v1"
GOVERNANCE_CENTRAL_BACKUP_POLICY_CONTRACT_VERSION = "governance_central_backup_policy.v1"
CENTRAL_BACKUP_POLICY_DOCUMENT_CONTRACT_VERSION = "threadvault_central_backup_policy.v1"
GOVERNANCE_BUSINESS_COMMAND_INSTRUMENTATION_CONTRACT_VERSION = "governance_business_command_instrumentation.v1"
GOVERNANCE_V3_ACCEPTANCE_SMOKE_CONTRACT_VERSION = "governance_v3_acceptance_smoke.v1"
GOVERNANCE_EXPORT_BACKUP_PREFLIGHT_CONTRACT_VERSION = "governance_export_backup_preflight.v1"
GOVERNANCE_RESTORE_RETENTION_PREFLIGHT_CONTRACT_VERSION = "governance_restore_retention_preflight.v1"
GOVERNANCE_RAW_READ_PREFLIGHT_CONTRACT_VERSION = "governance_raw_read_preflight.v1"
GOVERNANCE_SUMMARY_SEARCH_PREFLIGHT_CONTRACT_VERSION = "governance_summary_search_preflight.v1"
GOVERNANCE_EXPORT_PREVIEW_PREFLIGHT_CONTRACT_VERSION = "governance_export_preview_preflight.v1"
GOVERNANCE_EXTERNAL_MODEL_PREFLIGHT_CONTRACT_VERSION = "governance_external_model_preflight.v1"
AUDIT_APPEND_COMMAND = (
    "threadvault governance audit append --log LOG --operation OPERATION --actor ACTOR --status STATUS "
    "--target-type TYPE --target-id ID --json"
)
AUDIT_LIST_COMMAND = "threadvault governance audit list --log LOG --json"
CENTRALIZED_AUDIT_STORE_COMMAND = "threadvault governance audit centralized-store --action verify --store STORE --json"
PERMISSION_CHECK_COMMAND = "threadvault governance permission check --operation OPERATION --role ROLE --json"
ENFORCEMENT_GAPS_COMMAND = "threadvault governance enforcement gaps --json"
ENFORCEMENT_CHECK_COMMAND = (
    'threadvault governance enforcement check --command "threadvault export" --role reviewer --json'
)
POLICY_READINESS_COMMAND = "threadvault governance policy readiness --json"
SERVER_POLICY_READINESS_COMMAND = "threadvault governance server policy-readiness --json"
CENTRALIZED_AUDIT_READINESS_COMMAND = "threadvault governance audit centralized-readiness --json"
V3_COMPLETION_GAP_AUDIT_COMMAND = "threadvault governance v3 gap-audit --json"
V3_ACCEPTANCE_SMOKE_COMMAND = "threadvault governance v3 acceptance-smoke --json"
IDENTITY_ACTOR_READINESS_COMMAND = "threadvault governance identity actor-readiness --json"
IDENTITY_ACTOR_BINDING_COMMAND = "threadvault governance identity bind --actor ACTOR --json"
CENTRAL_POLICY_READINESS_COMMAND = "threadvault governance policy central-readiness --json"
CENTRAL_POLICY_STORE_COMMAND = "threadvault governance policy central-store --policy POLICY --json"
CENTRAL_BACKUP_READINESS_COMMAND = "threadvault governance backup central-readiness --json"
CENTRAL_BACKUP_POLICY_COMMAND = "threadvault governance backup policy --policy POLICY --json"
BUSINESS_COMMAND_INSTRUMENTATION_COMMAND = (
    'threadvault governance instrumentation business-command --command "threadvault backup" --role maintainer --json'
)
EXPORT_BACKUP_PREFLIGHT_COMMAND = (
    'threadvault governance preflight export-backup --command "threadvault export" --role reviewer --json'
)
RESTORE_RETENTION_PREFLIGHT_COMMAND = (
    'threadvault governance preflight restore-retention --command "threadvault restore" --role maintainer --json'
)
RAW_READ_PREFLIGHT_COMMAND = (
    'threadvault governance preflight raw-read --command "threadvault client session" --role owner --json'
)
SUMMARY_SEARCH_PREFLIGHT_COMMAND = (
    'threadvault governance preflight summary-search --command "threadvault retrieval query" --role reader --json'
)
EXPORT_PREVIEW_PREFLIGHT_COMMAND = (
    'threadvault governance preflight export-preview --command "threadvault client export-preview" --role reviewer --json'
)
EXTERNAL_MODEL_PREFLIGHT_COMMAND = (
    'threadvault governance preflight external-model --command "external model adapters" --role reviewer --json'
)

EXPORT_BACKUP_PREFLIGHT_COMMANDS = {
    "threadvault export",
    "threadvault export-target markdown",
    "threadvault export-target obsidian",
    "threadvault export-target skill",
    "threadvault backup",
}
RESTORE_RETENTION_PREFLIGHT_COMMANDS = {
    "threadvault restore",
    "threadvault restore-history prune",
    "threadvault backup-history prune",
    "threadvault audit-history prune",
}
RAW_READ_PREFLIGHT_COMMANDS = {
    "threadvault client session",
}
SUMMARY_SEARCH_PREFLIGHT_COMMANDS = {
    "threadvault client warnings",
    "threadvault agent retrieve",
    "threadvault retrieval query",
    "threadvault retrieval hybrid",
}
EXPORT_PREVIEW_PREFLIGHT_COMMANDS = {
    "threadvault client export-preview",
}
EXTERNAL_MODEL_PREFLIGHT_COMMANDS = {
    "external model adapters",
}
INSTRUMENTED_BUSINESS_COMMANDS = {
    "external model adapters",
    "threadvault agent retrieve",
    "threadvault audit-history prune",
    "threadvault backup",
    "threadvault backup-history prune",
    "threadvault client export-preview",
    "threadvault client session",
    "threadvault client warnings",
    "threadvault export",
    "threadvault export-target markdown",
    "threadvault export-target obsidian",
    "threadvault export-target skill",
    "threadvault restore",
    "threadvault restore-history prune",
    "threadvault retrieval hybrid",
    "threadvault retrieval query",
}

CENTRAL_BACKUP_POLICY_OPERATIONS = {
    "backup_archive": {"section": "backup", "role_field": "operator_roles", "audit_required": True},
    "restore_backup": {"section": "restore", "role_field": "approver_roles", "audit_required": True},
    "delete_or_prune": {"section": "retention", "role_field": "approver_roles", "audit_required": True},
    "recovery_test": {"section": "recovery_testing", "role_field": "operator_roles", "audit_required": True},
    "migrate_local_history": {"section": "migration", "role_field": "operator_roles", "audit_required": True},
}

ACCESS_LEVELS = [
    {
        "name": "raw_transcript",
        "description": "Read raw imported transcript events and raw local transcript metadata.",
        "sensitivity": "high",
    },
    {
        "name": "summary_search",
        "description": "Read summaries, evidence IDs, warnings, and retrieval results without raw local metadata by default.",
        "sensitivity": "medium",
    },
    {
        "name": "export",
        "description": "Preview or write archive exports after privacy policy checks.",
        "sensitivity": "high",
    },
    {
        "name": "delete_retention",
        "description": "Delete, prune, or retain local archive-derived artifacts.",
        "sensitivity": "critical",
    },
    {
        "name": "restore",
        "description": "Restore archive backups or recovery history.",
        "sensitivity": "critical",
    },
]

ROLES = [
    {"name": "owner", "access_levels": [level["name"] for level in ACCESS_LEVELS]},
    {"name": "maintainer", "access_levels": ["summary_search", "export", "delete_retention", "restore"]},
    {"name": "reviewer", "access_levels": ["summary_search", "export"]},
    {"name": "reader", "access_levels": ["summary_search"]},
]

SENSITIVE_OPERATIONS = [
    {"name": "read_raw_transcript", "access_level": "raw_transcript", "audit_required": True},
    {"name": "read_summary_search", "access_level": "summary_search", "audit_required": False},
    {"name": "export_archive", "access_level": "export", "audit_required": True},
    {"name": "delete_or_prune", "access_level": "delete_retention", "audit_required": True},
    {"name": "restore_backup", "access_level": "restore", "audit_required": True},
    {"name": "external_model_call", "access_level": "export", "audit_required": True},
]

ENFORCEMENT_GAP_COMMANDS = [
    {
        "command": "threadvault client session",
        "operation": "read_raw_transcript",
        "access_level": "raw_transcript",
        "audit_required": True,
        "future_phase": "governance_enforcement_raw_read",
        "notes": "Session detail exposes bounded event previews and may include local metadata with --local-debug.",
    },
    {
        "command": "threadvault client warnings",
        "operation": "read_summary_search",
        "access_level": "summary_search",
        "audit_required": False,
        "future_phase": "governance_enforcement_client_read",
        "notes": "Warning/privacy details are safe by default but still disclose archive-derived metadata.",
    },
    {
        "command": "threadvault agent retrieve",
        "operation": "read_summary_search",
        "access_level": "summary_search",
        "audit_required": False,
        "future_phase": "governance_enforcement_search",
        "notes": "Agent retrieval omits raw metadata by default and should remain available for summary/search roles.",
    },
    {
        "command": "threadvault retrieval query",
        "operation": "read_summary_search",
        "access_level": "summary_search",
        "audit_required": False,
        "future_phase": "governance_enforcement_search",
        "notes": "FTS retrieval can expose snippets; future team mode should authorize summary/search access.",
    },
    {
        "command": "threadvault retrieval hybrid",
        "operation": "read_summary_search",
        "access_level": "summary_search",
        "audit_required": False,
        "future_phase": "governance_enforcement_search",
        "notes": "Hybrid retrieval should reuse the same summary/search access level.",
    },
    {
        "command": "threadvault export",
        "operation": "export_archive",
        "access_level": "export",
        "audit_required": True,
        "future_phase": "governance_enforcement_export",
        "notes": "Direct export writes files and should call permission preflight before writing in team mode.",
    },
    {
        "command": "threadvault export-target markdown",
        "operation": "export_archive",
        "access_level": "export",
        "audit_required": True,
        "future_phase": "governance_enforcement_export",
        "notes": "Batch markdown export writes durable artifacts and manifests.",
    },
    {
        "command": "threadvault export-target obsidian",
        "operation": "export_archive",
        "access_level": "export",
        "audit_required": True,
        "future_phase": "governance_enforcement_export",
        "notes": "Obsidian export writes a vault-ready shared knowledge surface.",
    },
    {
        "command": "threadvault export-target skill",
        "operation": "export_archive",
        "access_level": "export",
        "audit_required": True,
        "future_phase": "governance_enforcement_export",
        "notes": "Skill export produces artifacts intended for reuse by agents.",
    },
    {
        "command": "threadvault client export-preview",
        "operation": "export_archive",
        "access_level": "export",
        "audit_required": False,
        "future_phase": "governance_enforcement_export_preview",
        "notes": "Preview is read-only but should reflect whether execution would be allowed.",
    },
    {
        "command": "threadvault backup",
        "operation": "export_archive",
        "access_level": "export",
        "audit_required": True,
        "future_phase": "governance_enforcement_backup_restore",
        "notes": "Backup copies the archive database and should be treated as export-like in team mode.",
    },
    {
        "command": "threadvault restore",
        "operation": "restore_backup",
        "access_level": "restore",
        "audit_required": True,
        "future_phase": "governance_enforcement_backup_restore",
        "notes": "Restore can replace archive state and should require restore access.",
    },
    {
        "command": "threadvault restore-history prune",
        "operation": "delete_or_prune",
        "access_level": "delete_retention",
        "audit_required": True,
        "future_phase": "governance_enforcement_retention",
        "notes": "History pruning mutates local governance evidence.",
    },
    {
        "command": "threadvault backup-history prune",
        "operation": "delete_or_prune",
        "access_level": "delete_retention",
        "audit_required": True,
        "future_phase": "governance_enforcement_retention",
        "notes": "Backup pruning deletes recovery artifacts.",
    },
    {
        "command": "threadvault audit-history prune",
        "operation": "delete_or_prune",
        "access_level": "delete_retention",
        "audit_required": True,
        "future_phase": "governance_enforcement_retention",
        "notes": "Audit report pruning deletes audit evidence and needs a later explicit policy.",
    },
    {
        "command": "external model adapters",
        "operation": "external_model_call",
        "access_level": "export",
        "audit_required": True,
        "future_phase": "external_model_policy_adapter",
        "notes": "No external model summary adapter is enabled by default; this is a readiness gap for future adapters.",
    },
]


def governance_status(config: AppConfig) -> dict[str, Any]:
    return {
        "contract_version": GOVERNANCE_STATUS_CONTRACT_VERSION,
        "enabled": config.governance_enabled,
        "mode": "local_opt_in" if config.governance_enabled else "disabled",
        "access_levels": ACCESS_LEVELS,
        "roles": ROLES,
        "sensitive_operations": SENSITIVE_OPERATIONS,
        "audit_requirements": {
            "implemented": True,
            "required_before_team_mode": True,
            "operations_requiring_audit": [
                operation["name"] for operation in SENSITIVE_OPERATIONS if operation["audit_required"]
            ],
            "commands": [AUDIT_APPEND_COMMAND, AUDIT_LIST_COMMAND],
        },
        "permission_preflight": {
            "implemented": True,
            "contract_version": GOVERNANCE_PERMISSION_CHECK_CONTRACT_VERSION,
            "command": PERMISSION_CHECK_COMMAND,
            "enforced_by_default": False,
        },
        "enforcement_gap_audit": {
            "implemented": True,
            "contract_version": GOVERNANCE_ENFORCEMENT_GAPS_CONTRACT_VERSION,
            "command": ENFORCEMENT_GAPS_COMMAND,
        },
        "enforcement_dry_run": {
            "implemented": True,
            "contract_version": GOVERNANCE_ENFORCEMENT_CHECK_CONTRACT_VERSION,
            "command": ENFORCEMENT_CHECK_COMMAND,
            "enforced_by_default": False,
        },
        "policy_readiness": {
            "implemented": True,
            "contract_version": GOVERNANCE_POLICY_READINESS_CONTRACT_VERSION,
            "command": POLICY_READINESS_COMMAND,
            "team_enforcement_ready": False,
        },
        "identity_actor_binding": {
            "implemented": True,
            "contract_version": GOVERNANCE_IDENTITY_ACTOR_BINDING_CONTRACT_VERSION,
            "command": IDENTITY_ACTOR_BINDING_COMMAND,
            "provider": "local_static_config",
            "configured_actor_count": len(config.governance_identity_actors),
            "shared_enforcement_ready": False,
        },
        "export_backup_preflight": {
            "implemented": True,
            "contract_version": GOVERNANCE_EXPORT_BACKUP_PREFLIGHT_CONTRACT_VERSION,
            "command": EXPORT_BACKUP_PREFLIGHT_COMMAND,
            "business_command_executed": False,
        },
        "restore_retention_preflight": {
            "implemented": True,
            "contract_version": GOVERNANCE_RESTORE_RETENTION_PREFLIGHT_CONTRACT_VERSION,
            "command": RESTORE_RETENTION_PREFLIGHT_COMMAND,
            "business_command_executed": False,
        },
        "defaults": {
            "local_first": True,
            "server_required": False,
            "server_available": False,
            "server_opt_in": True,
            "cloud_sync": False,
            "external_model_calls": False,
            "permissions_enforced": False,
            "raw_transcript_access_default": "local_owner_only",
        },
        "diagnostics": {
            "config_path": str(config.source_path) if config.source_path else None,
            "config_enabled": config.governance_enabled,
            "shared_server_implemented": False,
            "team_permissions_implemented": False,
            "audit_log_implemented": True,
        },
}


def governance_enforcement_gaps(config: AppConfig) -> dict[str, Any]:
    commands = []
    for item in ENFORCEMENT_GAP_COMMANDS:
        instrumented = item["command"] in INSTRUMENTED_BUSINESS_COMMANDS
        commands.append({
            **item,
            "current_state": {
                "automatic_preflight": instrumented,
                "automatic_audit": instrumented,
                "enforced": instrumented and config.governance_enabled,
            },
        })
    by_access_level: dict[str, int] = {}
    audit_required_count = 0
    for item in commands:
        by_access_level[item["access_level"]] = by_access_level.get(item["access_level"], 0) + 1
        if item["audit_required"]:
            audit_required_count += 1
    return {
        "contract_version": GOVERNANCE_ENFORCEMENT_GAPS_CONTRACT_VERSION,
        "governance": {
            "enabled": config.governance_enabled,
            "mode": "local_opt_in" if config.governance_enabled else "disabled",
            "enforcement_enabled": False,
            "server_required": False,
            "cloud_sync": False,
        },
        "commands": commands,
        "summary": {
            "command_count": len(commands),
            "audit_required_count": audit_required_count,
            "instrumented_command_count": len(INSTRUMENTED_BUSINESS_COMMANDS),
            "by_access_level": by_access_level,
        },
        "recommendations": [
            "Wire export and backup commands to permission preflight before team mode.",
            "Wire restore and retention commands to permission preflight before shared deployments.",
            "Keep local-only personal CLI behavior unenforced until governance is explicitly enabled.",
            "Add automatic audit writes only after command-level enforcement decisions are documented.",
        ],
        "diagnostics": {
            "inventory_source": "threadvault.governance.ENFORCEMENT_GAP_COMMANDS",
            "v2_retrieval_core_changed": False,
            "permissions_enforced_now": config.governance_enabled,
            "automatic_audit_now": False,
        },
    }


def governance_enforcement_check(
    config: AppConfig,
    *,
    command: str,
    role: str,
    audit_log: Path | None = None,
    actor: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
) -> dict[str, Any]:
    command_policy = _command_policy(command)
    operation = command_policy["operation"] if command_policy else ""
    permission_payload = check_permission(
        config,
        operation=operation,
        role=role,
        audit_log=None,
    )
    known_command = command_policy is not None
    future_enforcement_recommended = known_command and bool(command_policy["audit_required"])
    would_block_if_enforced = known_command and not permission_payload["decision"]["would_allow"]
    dry_run_status = "would_allow"
    if not known_command:
        dry_run_status = "unknown_command"
    elif would_block_if_enforced:
        dry_run_status = "would_block"
    audit_payload = None
    if audit_log is not None:
        audit_payload = append_audit_record(
            audit_log,
            operation="enforcement_dry_run",
            actor=actor or role,
            status=dry_run_status,
            target_type=target_type or "command",
            target_id=target_id or command,
            metadata={
                "checked_command": command,
                "checked_role": role,
                "known_command": str(known_command).lower(),
                "operation": operation,
                "access_level": str(command_policy["access_level"]) if command_policy else "",
                "would_allow": str(permission_payload["decision"]["would_allow"]).lower(),
                "would_block_if_enforced": str(would_block_if_enforced).lower(),
                "dry_run_only": "true",
            },
        )
    return {
        "contract_version": GOVERNANCE_ENFORCEMENT_CHECK_CONTRACT_VERSION,
        "request": {
            "command": command,
            "role": role,
            "audit_log": str(audit_log.expanduser()) if audit_log else None,
            "actor": actor,
            "target_type": target_type,
            "target_id": target_id,
        },
        "command_policy": {
            "known": known_command,
            "command": command_policy["command"] if command_policy else command,
            "operation": command_policy["operation"] if command_policy else None,
            "access_level": command_policy["access_level"] if command_policy else None,
            "audit_required": command_policy["audit_required"] if command_policy else False,
            "future_phase": command_policy["future_phase"] if command_policy else None,
            "notes": command_policy["notes"] if command_policy else "Command is not in the governance enforcement inventory.",
        },
        "permission": permission_payload["decision"],
        "enforcement": {
            "dry_run": True,
            "current_enforced": False,
            "current_automatic_preflight": False,
            "current_automatic_audit": False,
            "future_enforcement_recommended": future_enforcement_recommended,
            "would_block_if_enforced": would_block_if_enforced,
            "status": dry_run_status,
            "reasons": _enforcement_reasons(
                known_command=known_command,
                would_block_if_enforced=would_block_if_enforced,
                permission_reasons=permission_payload["decision"]["reasons"],
                audit_required=bool(command_policy["audit_required"]) if command_policy else False,
            ),
        },
        "audit": {
            "written": audit_payload is not None,
            "record": audit_payload["record"] if audit_payload else None,
            "log": audit_payload["log"] if audit_payload else None,
        },
        "diagnostics": {
            "known_command": known_command,
            "inventory_source": "threadvault.governance.ENFORCEMENT_GAP_COMMANDS",
            "governance_enabled": config.governance_enabled,
            "server_required": False,
            "cloud_sync": False,
            "external_model_calls": False,
            "business_command_executed": False,
            "v2_retrieval_core_changed": False,
        },
    }


def governance_business_command_instrumentation(
    config: AppConfig,
    *,
    command: str,
    role: str,
    audit_log: Path | None = None,
    actor: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
) -> dict[str, Any]:
    command_policy = _command_policy(command)
    category = _business_command_preflight_category(command)
    preflight = _business_command_preflight(
        config,
        command=command,
        role=role,
        audit_log=audit_log,
        actor=actor,
        target_type=target_type,
        target_id=target_id,
        category=category,
    )
    permission = preflight.get("permission") if isinstance(preflight, dict) else {}
    blocked = bool(permission.get("enforced") and not permission.get("allowed"))
    return {
        "contract_version": GOVERNANCE_BUSINESS_COMMAND_INSTRUMENTATION_CONTRACT_VERSION,
        "request": {
            "command": command,
            "role": role,
            "audit_log": str(audit_log.expanduser()) if audit_log else None,
            "actor": actor,
            "target_type": target_type,
            "target_id": target_id,
        },
        "governance": {
            "enabled": config.governance_enabled,
            "mode": "local_opt_in" if config.governance_enabled else "disabled",
            "server_required": False,
            "server_opt_in": True,
            "cloud_sync": False,
        },
        "command_policy": {
            "known": command_policy is not None,
            "command": command_policy["command"] if command_policy else command,
            "operation": command_policy["operation"] if command_policy else None,
            "access_level": command_policy["access_level"] if command_policy else None,
            "audit_required": bool(command_policy["audit_required"]) if command_policy else False,
            "category": category,
        },
        "instrumentation": {
            "enabled": True,
            "instrumented": category != "unknown",
            "blocked": blocked,
            "reason": "preflight_blocked" if blocked else ("preflight_allowed" if category != "unknown" else "unknown_command"),
            "business_command_should_execute": not blocked,
        },
        "preflight": preflight,
        "audit": preflight.get("audit") if isinstance(preflight, dict) else None,
        "execution": {
            "business_command_executed": False,
            "blocked_before_execution": blocked,
            "side_effects_allowed": not blocked,
            "shared_execution_ready": False,
        },
        "diagnostics": {
            "config_path": str(config.source_path) if config.source_path else None,
            "local_first": True,
            "privacy_first": True,
            "server_required": False,
            "server_opt_in": True,
            "cloud_sync": False,
            "v2_retrieval_core_changed": False,
            "instrumented_command_count": len(INSTRUMENTED_BUSINESS_COMMANDS),
            "inventory_command_count": len(ENFORCEMENT_GAP_COMMANDS),
        },
    }


def governance_policy_readiness(config: AppConfig) -> dict[str, Any]:
    implemented_prerequisites = [
        "governance_baseline",
        "local_audit_log",
        "permission_preflight",
        "enforcement_gap_inventory",
        "enforcement_dry_run",
        "schema_contracts",
    ]
    missing_prerequisites = [
        "server_identity_model",
        "central_policy_store",
        "automatic_command_preflight",
        "automatic_command_audit",
        "centralized_audit_store",
        "shared_backup_restore_policy",
    ]
    blockers = [
        {
            "code": "server_identity_model_missing",
            "severity": "blocking",
            "description": "Shared deployments need an actor and role source before team enforcement can be trusted.",
            "required_before": "team_enforcement",
        },
        {
            "code": "central_policy_store_missing",
            "severity": "blocking",
            "description": "Team deployments need a policy source beyond local static role vocabulary.",
            "required_before": "team_enforcement",
        },
        {
            "code": "business_command_instrumentation_missing",
            "severity": "blocking",
            "description": "Export, backup, restore, retention, retrieval, and client commands do not call preflight yet.",
            "required_before": "command_enforcement",
        },
        {
            "code": "centralized_audit_missing",
            "severity": "blocking",
            "description": "Local JSONL audit is available, but shared deployments need centralized audit retention.",
            "required_before": "shared_deployment",
        },
    ]
    command_categories = [
        _readiness_category(
            "raw_transcript",
            "Raw transcript and local metadata reads.",
            commands=["threadvault client session"],
            recommended_next_phase="governance_enforcement_raw_read",
        ),
        _readiness_category(
            "summary_search",
            "Summary, warning, retrieval, and agent search workflows.",
            commands=[
                "threadvault client warnings",
                "threadvault agent retrieve",
                "threadvault retrieval query",
                "threadvault retrieval hybrid",
            ],
            recommended_next_phase="governance_enforcement_search",
            audit_required=False,
        ),
        _readiness_category(
            "export_backup",
            "Export and backup workflows that can create durable shared artifacts.",
            commands=[
                "threadvault export",
                "threadvault export-target markdown",
                "threadvault export-target obsidian",
                "threadvault export-target skill",
                "threadvault backup",
            ],
            recommended_next_phase="governance_enforcement_export_backup",
        ),
        _readiness_category(
            "restore_retention",
            "Restore, delete, prune, and retention workflows.",
            commands=[
                "threadvault restore",
                "threadvault restore-history prune",
                "threadvault backup-history prune",
                "threadvault audit-history prune",
            ],
            recommended_next_phase="governance_enforcement_restore_retention",
        ),
        _readiness_category(
            "external_model",
            "Future external model calls and outbound data adapters.",
            commands=["external model adapters"],
            recommended_next_phase="external_model_policy_adapter",
        ),
    ]
    return {
        "contract_version": GOVERNANCE_POLICY_READINESS_CONTRACT_VERSION,
        "governance": {
            "enabled": config.governance_enabled,
            "mode": "local_opt_in" if config.governance_enabled else "disabled",
            "team_enforcement_ready": False,
            "current_permissions_enforced": False,
            "server_required": False,
            "server_available": False,
            "cloud_sync": False,
        },
        "readiness": {
            "overall_status": "not_ready_for_team_enforcement",
            "implemented_prerequisites": implemented_prerequisites,
            "missing_prerequisites": missing_prerequisites,
            "blocking_count": len(blockers),
            "safe_to_keep_local_cli": True,
            "safe_to_enable_team_enforcement": False,
        },
        "capabilities": {
            "audit_log": {
                "implemented": True,
                "centralized": False,
                "schema": "governance_audit_append",
            },
            "permission_preflight": {
                "implemented": True,
                "automatic_for_business_commands": True,
                "instrumented_commands": sorted(INSTRUMENTED_BUSINESS_COMMANDS),
                "schema": "governance_permission_check",
            },
            "enforcement_gap_inventory": {
                "implemented": True,
                "schema": "governance_enforcement_gaps",
            },
            "enforcement_dry_run": {
                "implemented": True,
                "schema": "governance_enforcement_check",
            },
        },
        "command_categories": command_categories,
        "blockers": blockers,
        "recommended_next_phases": [
            "Add explicitly opt-in export/backup command preflight before writing shared artifacts.",
            "Add restore and retention preflight after export/backup instrumentation is accepted.",
            "Design server identity and centralized policy storage before shared team enforcement.",
            "Design centralized audit retention before claiming shared deployment readiness.",
        ],
        "diagnostics": {
            "config_path": str(config.source_path) if config.source_path else None,
            "local_first": True,
            "privacy_first": True,
            "server_opt_in": True,
            "external_model_calls": False,
            "business_commands_instrumented": True,
            "automatic_audit_now": False,
            "instrumented_command_count": len(INSTRUMENTED_BUSINESS_COMMANDS),
            "v2_retrieval_core_changed": False,
            "inventory_command_count": len(ENFORCEMENT_GAP_COMMANDS),
        },
    }


def governance_server_policy_readiness(config: AppConfig) -> dict[str, Any]:
    policy_runtime = governance_central_policy_store(config)
    policy_document_valid = bool(policy_runtime["policy"]["valid"])
    backup_policy_runtime = governance_central_backup_policy(config)
    backup_policy_valid = bool(backup_policy_runtime["policy"]["valid"])
    audit_runtime = governance_centralized_audit_store(config, action="verify")
    centralized_audit_ready = bool(audit_runtime["request"]["resolved_store"] and audit_runtime["verification"]["ok"])
    blockers = [
        _server_policy_blocker(
            "outbound_external_model_policy_missing",
            "External model calls have a preflight boundary but no executable outbound policy adapter.",
            "outbound_policy",
        ),
    ]
    implemented_prerequisites = [
        "governance_baseline",
        "local_audit_log",
        "permission_preflight",
        "enforcement_gap_inventory",
        "enforcement_dry_run",
        "policy_readiness_manifest",
        "business_preflight_contracts",
        "external_model_preflight",
        "read_only_shared_server_prototype",
        "local_identity_actor_binding",
        "central_policy_store_runtime",
        "centralized_audit_store_runtime",
        "central_backup_policy_runtime",
    ]
    missing_prerequisites = [blocker["code"].removesuffix("_missing") for blocker in blockers]
    return {
        "contract_version": GOVERNANCE_SERVER_POLICY_READINESS_CONTRACT_VERSION,
        "governance": {
            "enabled": config.governance_enabled,
            "mode": "local_opt_in" if config.governance_enabled else "disabled",
            "team_enforcement_ready": False,
            "shared_enforcement_ready": False,
            "current_permissions_enforced": False,
            "server_required": False,
            "server_available": True,
            "server_opt_in": True,
            "cloud_sync": False,
        },
        "readiness": {
            "overall_status": "not_ready_for_shared_enforcement",
            "implemented_prerequisites": implemented_prerequisites,
            "missing_prerequisites": missing_prerequisites,
            "blocking_count": len(blockers),
            "safe_to_keep_local_cli": True,
            "safe_to_enable_server_mode": False,
            "safe_to_enable_team_enforcement": False,
        },
        "server": {
            "implemented": True,
            "required_for_local_cli": False,
            "opt_in": True,
            "read_only_shared_prototype_ready": True,
            "deployment_modes": ["local_cli", "read_only_loopback_prototype"],
            "runtime": "python_stdlib_http_server",
            "start_command": "threadvault governance server serve-read-only --enable --host 127.0.0.1 --port 8765",
            "manifest_command": "threadvault governance server read-only-manifest --json",
            "missing": ["shared_request_context", "central_policy_adapter"],
        },
        "policy": {
            "central_store_implemented": True,
            "central_store_available": policy_document_valid,
            "store_type": "local_json_file",
            "policy_versioning_implemented": True,
            "policy_provenance_implemented": policy_document_valid,
            "local_static_role_vocabulary_available": True,
            "schemas_available": True,
            "missing": ["policy_migration", "server_policy_adapter"]
            + ([] if policy_document_valid else ["configured_central_policy_document"]),
        },
        "identity": {
            "identity_provider_implemented": True,
            "identity_provider_type": "local_static_config",
            "actor_binding_implemented": True,
            "role_mapping_implemented": True,
            "central_policy_role_resolution": policy_document_valid,
            "configured_actor_count": len(config.governance_identity_actors),
            "sufficient_for_shared_enforcement": False,
            "supported_roles": [role["name"] for role in ROLES],
            "missing": ["authenticated_provider", "shared_request_context"]
            + ([] if policy_document_valid else ["configured_central_policy_role_resolution"]),
        },
        "instrumentation": {
            "preflight_contracts_available": True,
            "automatic_business_preflight": True,
            "automatic_business_audit": True,
            "command_inventory_available": True,
            "instrumented_commands": sorted(INSTRUMENTED_BUSINESS_COMMANDS),
            "instrumented_command_count": len(INSTRUMENTED_BUSINESS_COMMANDS),
            "inventory_command_count": len(ENFORCEMENT_GAP_COMMANDS),
        },
        "audit": {
            "local_jsonl_available": True,
            "centralized_store_implemented": True,
            "centralized_store_available": centralized_audit_ready,
            "centralized_store_type": "local_jsonl_hash_chain",
            "retention_policy_implemented": True,
            "append_only_contract_available": True,
            "missing": ["audit_export_review_workflow"]
            + ([] if centralized_audit_ready else ["configured_centralized_audit_store"]),
        },
        "backup_restore": {
            "local_backup_restore_available": True,
            "centralized_policy_implemented": True,
            "centralized_policy_available": backup_policy_valid,
            "shared_retention_policy_implemented": True,
            "restore_approval_workflow_implemented": True,
            "missing": [] if backup_policy_valid else ["configured_central_backup_policy"],
        },
        "outbound_policy": {
            "external_model_preflight_available": True,
            "adapter_implemented": False,
            "outbound_policy_implemented": False,
            "provider_allowlist_implemented": False,
            "default_external_calls_enabled": False,
        },
        "blockers": blockers,
        "recommended_next_phases": [
            "Keep the read-only server prototype opt-in while designing identity and actor binding.",
            "Design centralized policy storage and policy versioning before shared enforcement.",
            "Design centralized audit retention, backup/export, and review policy before shared deployments.",
            "Expand automatic governance instrumentation beyond the first read-only client export-preview slice.",
        ],
        "diagnostics": {
            "config_path": str(config.source_path) if config.source_path else None,
            "local_first": True,
            "privacy_first": True,
            "server_opt_in": True,
            "cloud_sync": False,
            "server_required": False,
            "business_commands_instrumented": True,
            "automatic_audit_now": True,
            "instrumented_command_count": len(INSTRUMENTED_BUSINESS_COMMANDS),
            "central_policy_document_valid": policy_document_valid,
            "central_backup_policy_runtime": True,
            "central_backup_policy_valid": backup_policy_valid,
            "centralized_audit_store_runtime": True,
            "centralized_audit_store_configured": bool(audit_runtime["request"]["resolved_store"]),
            "v2_retrieval_core_changed": False,
        },
    }


def governance_centralized_audit_readiness(config: AppConfig) -> dict[str, Any]:
    store_runtime = governance_centralized_audit_store(config, action="verify")
    store_configured = store_runtime["request"]["resolved_store"] is not None
    store_ready = bool(store_configured and store_runtime["verification"]["ok"])
    backup_policy_runtime = governance_central_backup_policy(config)
    backup_policy_valid = bool(backup_policy_runtime["policy"]["valid"])
    blockers = []
    if not store_configured:
        blockers.insert(
            0,
            _centralized_audit_blocker(
                "centralized_audit_store_not_configured",
                "Centralized audit store runtime exists, but no central audit store path is configured.",
                "storage",
            ),
        )
    elif not store_ready:
        blockers.insert(
            0,
            _centralized_audit_blocker(
                "centralized_audit_store_integrity_failed",
                "Centralized audit store exists, but verification failed.",
                "integrity",
            ),
        )
    return {
        "contract_version": GOVERNANCE_CENTRALIZED_AUDIT_READINESS_CONTRACT_VERSION,
        "governance": {
            "enabled": config.governance_enabled,
            "mode": "local_opt_in" if config.governance_enabled else "disabled",
            "server_required": False,
            "server_opt_in": True,
            "cloud_sync": False,
            "centralized_audit_ready": store_ready,
        },
        "readiness": {
            "overall_status": "not_ready_for_centralized_audit",
            "implemented_prerequisites": [
                "local_audit_log",
                "audit_append_schema",
                "audit_list_schema",
                "server_policy_readiness_manifest",
                "client_export_preview_governance_instrumentation",
                "local_identity_actor_binding",
                "centralized_audit_store_runtime",
                "central_backup_policy_runtime",
            ],
            "missing_prerequisites": [blocker["code"].removesuffix("_missing") for blocker in blockers],
            "blocking_count": len(blockers),
            "safe_to_keep_local_jsonl_audit": True,
            "safe_to_enable_centralized_audit": store_ready,
            "safe_to_enable_shared_audit_retention": False,
        },
        "local_audit": {
            "available": True,
            "append_command": AUDIT_APPEND_COMMAND,
            "list_command": AUDIT_LIST_COMMAND,
            "schema_names": ["governance_audit_append", "governance_audit_list"],
            "local_only": True,
            "server_required": False,
        },
        "centralized_audit": {
            "store_implemented": True,
            "store_type": "local_jsonl_hash_chain",
            "store_available": store_ready,
            "adapter_implemented": True,
            "query_interface_implemented": True,
            "migration_from_local_jsonl_implemented": False,
            "missing": [] if store_ready else ["configured_centralized_audit_store"],
        },
        "identity": {
            "actor_binding_implemented": True,
            "identity_provider_implemented": True,
            "identity_provider_type": "local_static_config",
            "role_mapping_implemented": True,
            "configured_actor_count": len(config.governance_identity_actors),
            "authenticated_actor_provenance": False,
            "missing": ["authenticated_actor_provenance", "centralized_actor_provenance"],
        },
        "integrity": {
            "append_only_contract_available": True,
            "tamper_evidence_implemented": True,
            "record_hashing_implemented": True,
            "signature_or_seal_implemented": False,
            "hash_chain_valid": bool(store_runtime["verification"]["hash_chain_valid"]),
            "missing": ["signature_or_seal"],
        },
        "retention": {
            "policy_implemented": True,
            "policy_available": backup_policy_valid,
            "legal_hold_implemented": True,
            "prune_approval_implemented": True,
            "missing": [] if backup_policy_valid else ["configured_central_backup_policy"],
        },
        "review": {
            "query_workflow_implemented": True,
            "export_review_implemented": False,
            "access_review_implemented": False,
            "missing": ["audit_export_review", "audit_access_review"],
        },
        "backup_export": {
            "backup_policy_implemented": True,
            "export_policy_implemented": True,
            "restore_policy_implemented": True,
            "policy_available": backup_policy_valid,
            "missing": [] if backup_policy_valid else ["configured_central_backup_policy"],
        },
        "instrumentation": {
            "manual_audit_append_available": True,
            "automatic_business_audit": False,
            "automatic_preflight_audit": True,
            "instrumented_commands": sorted(INSTRUMENTED_BUSINESS_COMMANDS),
            "instrumented_command_count": len(INSTRUMENTED_BUSINESS_COMMANDS),
            "inventory_command_count": len(ENFORCEMENT_GAP_COMMANDS),
        },
        "blockers": blockers,
        "recommended_next_phases": [
            "Configure a local central backup policy document before using shared audit retention previews.",
            "Design authenticated actor provenance for shared audit evidence.",
            "Run final v3 acceptance smoke across local client and optional shared deployment paths.",
        ],
        "diagnostics": {
            "config_path": str(config.source_path) if config.source_path else None,
            "local_first": True,
            "privacy_first": True,
            "server_opt_in": True,
            "cloud_sync": False,
            "server_required": False,
            "business_commands_instrumented": True,
            "automatic_audit_now": True,
            "instrumented_command_count": len(INSTRUMENTED_BUSINESS_COMMANDS),
            "centralized_audit_store_runtime": True,
            "centralized_audit_store_configured": store_configured,
            "central_backup_policy_runtime": True,
            "central_backup_policy_valid": backup_policy_valid,
            "v2_retrieval_core_changed": False,
        },
    }


def governance_v3_completion_gap_audit(config: AppConfig) -> dict[str, Any]:
    acceptance_criteria = [
        _v3_acceptance_item(
            "local_cli_without_server",
            "CLI remains fully usable without any server.",
            "satisfied",
            ["local_first_default", "server_required_false", "full_cli_regression"],
        ),
        _v3_acceptance_item(
            "richer_client_browse_search_export",
            "A richer client can browse/search/export without duplicating parser logic.",
            "satisfied",
            [
                "client_manifest",
                "client_overview",
                "client_session_detail",
                "client_export_preview",
                "client_warnings",
                "client_tui_runtime",
            ],
        ),
        _v3_acceptance_item(
            "shared_access_separation",
            "Shared deployments can distinguish raw transcript access from summary/search access.",
            "satisfied",
            [
                "governance_preflight_contracts",
                "server_policy_readiness_manifest",
                "read_only_shared_server_prototype",
                "v3_acceptance_smoke",
            ],
        ),
        _v3_acceptance_item(
            "audit_records_for_sensitive_operations",
            "Audit records exist for sensitive operations.",
            "satisfied",
            [
                "local_jsonl_audit_log",
                "manual_audit_append",
                "centralized_audit_readiness_manifest",
                "centralized_audit_store_runtime",
                "client_export_preview_governance_instrumentation",
                "business_command_governance_instrumentation",
                "v3_acceptance_smoke",
            ],
        ),
        _v3_acceptance_item(
            "external_model_cloud_explicit",
            "External model or cloud behavior is explicit, configurable, and visible in diagnostics.",
            "satisfied",
            ["external_model_preflight", "cloud_sync_false", "external_calls_disabled_by_default", "v3_acceptance_smoke"],
        ),
    ]
    milestones = [
        _v3_milestone("v3.0", "Client interface readiness audit", "accepted", ["phase-01"]),
        _v3_milestone(
            "v3.1",
            "Client manifest, local richer-client workflows, and local TUI runtime",
            "accepted",
            ["phase-02", "phase-03", "phase-04", "phase-05", "phase-06", "phase-27"],
        ),
        _v3_milestone(
            "v3.2",
            "Governance baseline, audit, preflight, and policy readiness",
            "accepted",
            [
                "phase-07",
                "phase-08",
                "phase-09",
                "phase-10",
                "phase-11",
                "phase-12",
                "phase-13",
                "phase-14",
                "phase-15",
                "phase-16",
                "phase-17",
                "phase-18",
            ],
        ),
        _v3_milestone(
            "v3.3",
            "Server/shared policy readiness, centralized audit readiness, and read-only server prototype",
            "partial",
            ["phase-19", "phase-20", "phase-25"],
        ),
        _v3_milestone(
            "v3.4",
            "Team permissions and audit logs for shared use",
            "partial",
            ["phase-22", "phase-23", "phase-26", "phase-28", "phase-29", "phase-30"],
        ),
        _v3_milestone(
            "v3.5",
            "Centralized backup/restore and retention policy",
            "accepted",
            ["phase-24", "phase-31"],
        ),
        _v3_milestone(
            "v3.6",
            "v3 acceptance smoke for local client and optional shared deployment",
            "accepted",
            ["phase-33"],
        ),
    ]
    blockers: list[dict[str, Any]] = []
    remaining_gaps = [
        {
            "code": "richer_client_runtime",
            "status": "accepted_minimal_tui_runtime",
            "description": "A concrete local TUI runtime can browse, search, and preview exports through existing client interfaces.",
            "recommended_phase": "Defer heavier desktop, IDE, or Web packaging until governance blockers are closed.",
        },
        {
            "code": "shared_read_only_deployment",
            "status": "prototype_accepted",
            "description": "An opt-in read-only loopback server prototype exists, but shared/team enforcement is not production-ready.",
            "recommended_phase": "Add identity, central policy, central audit, and instrumentation before shared deployment claims.",
        },
        {
            "code": "team_identity_and_policy",
            "status": "identity_and_policy_store_accepted_enforcement_pending",
            "description": (
                "Local static identity actor binding and a local central policy store runtime are implemented; "
                "automatic shared enforcement remains pending."
            ),
            "recommended_phase": "Expand central policy enforcement into instrumented command slices before team enforcement claims.",
        },
        {
            "code": "centralized_audit_and_retention",
            "status": "store_policy_and_instrumentation_accepted",
            "description": (
                "A local centralized audit store runtime and centralized backup/retention policy runtime exist; "
                "broad local business-command instrumentation can write optional preflight audit evidence."
            ),
            "recommended_phase": "Cover centralized audit behavior in final v3 acceptance smoke.",
        },
        {
            "code": "centralized_backup_restore_policy",
            "status": "accepted_local_policy_runtime",
            "description": (
                "A local opt-in centralized backup/restore policy runtime can validate policy documents and preview "
                "backup, restore, retention, recovery-test, and migration decisions."
            ),
            "recommended_phase": "Cover backup, restore, and retention instrumentation in final v3 acceptance smoke.",
        },
        {
            "code": "automatic_instrumentation",
            "status": "accepted_broad_command_instrumentation",
            "description": (
                "Sensitive business command families can run governance preflight and optional preflight audit "
                "through the shared instrumentation runtime."
            ),
            "recommended_phase": "Cover the accepted instrumentation in final v3 acceptance smoke.",
        },
        {
            "code": "v3_acceptance_smoke",
            "status": "accepted",
            "description": "Final v3 acceptance smoke covers local client and optional shared deployment behavior.",
            "recommended_phase": "v3 final acceptance is complete; future work can extend desktop, IDE, or production shared deployment.",
        },
    ]
    implemented_capabilities = [
        "accepted_v2_retrieval_interfaces",
        "client_interface_manifest",
        "client_overview_workflow",
        "client_session_detail_workflow",
        "client_export_preview_workflow",
        "client_warning_detail_workflow",
        "client_tui_runtime",
        "governance_baseline",
        "local_audit_log",
        "permission_preflight",
        "governance_enforcement_gap_audit",
        "governance_enforcement_dry_run",
        "governance_policy_readiness",
        "operation_specific_governance_preflights",
        "server_policy_readiness",
        "centralized_audit_readiness",
        "identity_actor_readiness",
        "identity_actor_binding_runtime",
        "central_policy_readiness",
        "central_policy_store_runtime",
        "central_backup_readiness",
        "central_backup_policy_runtime",
        "business_command_governance_instrumentation",
        "v3_acceptance_smoke",
        "centralized_audit_store_runtime",
        "read_only_shared_server_prototype",
        "client_export_preview_governance_instrumentation",
    ]
    return {
        "contract_version": GOVERNANCE_V3_COMPLETION_GAP_AUDIT_CONTRACT_VERSION,
        "governance": {
            "enabled": config.governance_enabled,
            "mode": "local_opt_in" if config.governance_enabled else "disabled",
            "server_required": False,
            "server_opt_in": True,
            "cloud_sync": False,
            "team_capabilities_opt_in": True,
        },
        "completion": {
            "overall_status": "complete",
            "v3_complete": True,
            "accepted_phase_count": 33,
            "current_phase": "phase-33-v3-final-acceptance-smoke",
            "remaining_gap_count": len(remaining_gaps),
            "blocking_count": len(blockers),
            "safe_to_keep_local_cli": True,
            "safe_to_claim_shared_deployment_ready": False,
            "safe_to_run_final_v3_acceptance": True,
        },
        "milestones": milestones,
        "acceptance_criteria": acceptance_criteria,
        "implemented_capabilities": implemented_capabilities,
        "remaining_gaps": remaining_gaps,
        "blockers": blockers,
        "recommended_next_phases": [
            "Keep production shared enforcement as a future opt-in hardening track.",
            "Extend richer clients only on top of accepted v2/v3 interfaces.",
        ],
        "diagnostics": {
            "config_path": str(config.source_path) if config.source_path else None,
            "local_first": True,
            "privacy_first": True,
            "server_opt_in": True,
            "cloud_sync": False,
            "server_required": False,
            "v2_retrieval_accepted": True,
            "v2_retrieval_core_changed": False,
            "deep_research_report_retired": True,
            "instrumented_command_count": len(INSTRUMENTED_BUSINESS_COMMANDS),
            "accepted_client_runtime": "threadvault-local-tui",
            "identity_actor_binding_runtime": True,
            "central_policy_store_runtime": True,
            "centralized_audit_store_runtime": True,
            "central_backup_policy_runtime": True,
            "business_command_governance_instrumentation": True,
            "v3_acceptance_smoke": True,
        },
    }


def governance_identity_actor_readiness(config: AppConfig) -> dict[str, Any]:
    local_identity_ready = bool(config.governance_identity_actors)
    blockers = [
        _identity_actor_blocker(
            "authenticated_identity_provider_missing",
            "Local static actor binding exists, but no authenticated external identity provider is implemented.",
            "identity_provider",
        ),
        _identity_actor_blocker(
            "centralized_actor_provenance_missing",
            "Local audit can record actor binding evidence, but no centralized authenticated provenance exists.",
            "audit_provenance",
        ),
        _identity_actor_blocker(
            "shared_request_context_missing",
            "Shared server requests are not yet bound to authenticated actors and central policy context.",
            "request_attribution",
        ),
    ]
    return {
        "contract_version": GOVERNANCE_IDENTITY_ACTOR_READINESS_CONTRACT_VERSION,
        "governance": {
            "enabled": config.governance_enabled,
            "mode": "local_opt_in" if config.governance_enabled else "disabled",
            "team_enforcement_ready": False,
            "identity_binding_ready": local_identity_ready,
            "current_permissions_enforced": False,
            "server_required": False,
            "server_opt_in": True,
            "cloud_sync": False,
        },
        "readiness": {
            "overall_status": "not_ready_for_identity_binding",
            "implemented_prerequisites": [
                "governance_role_vocabulary",
                "manual_local_actor_labels",
                "local_jsonl_audit_actor_field",
                "server_policy_readiness_manifest",
                "v3_completion_gap_audit",
                "identity_actor_binding_runtime",
            ],
            "missing_prerequisites": [blocker["code"].removesuffix("_missing") for blocker in blockers],
            "blocking_count": len(blockers),
            "safe_to_keep_local_cli": True,
            "safe_to_use_manual_local_actor_labels": True,
            "safe_to_enable_shared_identity_binding": False,
            "safe_to_enable_team_enforcement": False,
        },
        "identity_provider": {
            "implemented": True,
            "type": "local_static_config",
            "configured_actor_count": len(config.governance_identity_actors),
            "adapter_interface_defined": True,
            "token_validation_implemented": False,
            "external_directory_required_by_default": False,
            "missing": ["authenticated_provider", "token_validation"],
        },
        "actor_binding": {
            "implemented": True,
            "request_context_implemented": True,
            "business_commands_bound": False,
            "server_requests_bound": False,
            "command": IDENTITY_ACTOR_BINDING_COMMAND,
            "missing": ["automatic_command_actor_binding", "server_request_actor_binding"],
        },
        "role_mapping": {
            "local_role_vocabulary_available": True,
            "team_role_mapping_implemented": True,
            "policy_role_resolution_implemented": False,
            "configured_actor_count": len(config.governance_identity_actors),
            "supported_roles": [role["name"] for role in ROLES],
            "missing": ["central_policy_role_resolution", "role_mapping_provenance"],
        },
        "request_attribution": {
            "implemented": True,
            "client_context_available": True,
            "operation_context_available": True,
            "session_context_available": True,
            "missing": ["shared_request_context"],
        },
        "audit_provenance": {
            "manual_actor_field_available": True,
            "authenticated_actor_provenance": False,
            "actor_source_recorded": True,
            "actor_binding_evidence_recorded": True,
            "missing": ["authenticated_actor_provenance", "centralized_actor_provenance"],
        },
        "local_fallback": {
            "manual_actor_labels_available": True,
            "sufficient_for_local_preview": True,
            "sufficient_for_shared_enforcement": False,
            "fallback_policy_implemented": True,
            "missing": ["shared_actor_failure_mode"],
        },
        "blockers": blockers,
        "recommended_next_phases": [
            "Design identity provider and actor adapter interface.",
            "Design request context and actor binding contract for optional shared/server mode.",
            "Design team role mapping and policy role resolution before central policy enforcement.",
            "Record authenticated actor provenance in centralized audit before automatic instrumentation.",
        ],
        "diagnostics": {
            "config_path": str(config.source_path) if config.source_path else None,
            "local_first": True,
            "privacy_first": True,
            "server_opt_in": True,
            "cloud_sync": False,
            "server_required": False,
            "business_commands_instrumented": False,
            "automatic_audit_now": False,
            "v2_retrieval_core_changed": False,
        },
    }


def governance_identity_actor_binding(
    config: AppConfig,
    *,
    actor: str,
    command: str | None = None,
    operation: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    client_id: str | None = None,
    audit_log: Path | None = None,
) -> dict[str, Any]:
    actor_record = _configured_actor(config, actor)
    known_roles = {role["name"] for role in ROLES}
    configured_roles = list(actor_record["roles"]) if actor_record else []
    valid_roles = [role for role in configured_roles if role in known_roles]
    invalid_roles = [role for role in configured_roles if role not in known_roles]
    bound = actor_record is not None and bool(valid_roles) and not invalid_roles
    status = "bound" if bound else "unbound"
    if actor_record is not None and invalid_roles:
        status = "invalid_role_mapping"
    audit_payload = None
    if audit_log is not None:
        audit_payload = append_audit_record(
            audit_log,
            operation="identity_actor_binding",
            actor=actor,
            status=status,
            target_type=target_type or "actor",
            target_id=target_id or actor,
            metadata={
                "bound": str(bound).lower(),
                "roles": ",".join(valid_roles),
                "invalid_roles": ",".join(invalid_roles),
                "source": str(actor_record["source"] if actor_record else "unconfigured"),
                "command": command or "",
                "operation": operation or "",
                "client_id": client_id or "",
                "local_static_identity": str(actor_record is not None).lower(),
            },
        )
    return {
        "contract_version": GOVERNANCE_IDENTITY_ACTOR_BINDING_CONTRACT_VERSION,
        "request": {
            "actor": actor,
            "command": command,
            "operation": operation,
            "target_type": target_type,
            "target_id": target_id,
            "client_id": client_id,
            "audit_log": str(audit_log.expanduser()) if audit_log else None,
        },
        "governance": {
            "enabled": config.governance_enabled,
            "mode": "local_opt_in" if config.governance_enabled else "disabled",
            "identity_binding_ready": bool(config.governance_identity_actors),
            "team_enforcement_ready": False,
            "server_required": False,
            "server_opt_in": True,
            "cloud_sync": False,
        },
        "identity_provider": {
            "type": "local_static_config",
            "implemented": bool(config.governance_identity_actors),
            "source_path": str(config.source_path) if config.source_path else None,
            "external_directory_required": False,
            "authenticated_external_provider": False,
        },
        "actor": {
            "id": actor,
            "configured": actor_record is not None,
            "display": actor_record.get("display") if actor_record else None,
            "source": actor_record.get("source") if actor_record else "unconfigured",
        },
        "binding": {
            "bound": bound,
            "status": status,
            "failure_reason": _actor_binding_failure_reason(actor_record, invalid_roles, valid_roles),
            "local_static_binding": actor_record is not None,
            "sufficient_for_local_governance": bound,
            "sufficient_for_shared_enforcement": False,
        },
        "role_mapping": {
            "roles": valid_roles,
            "configured_roles": configured_roles,
            "invalid_roles": invalid_roles,
            "supported_roles": sorted(known_roles),
            "role_mapping_ready": bound,
            "central_policy_role_resolution_ready": False,
        },
        "request_attribution": {
            "implemented": True,
            "actor": actor,
            "roles": valid_roles,
            "command": command,
            "operation": operation,
            "target": {
                "type": target_type,
                "id": target_id,
            },
            "client_id": client_id,
            "provenance": {
                "source": actor_record.get("source") if actor_record else "unconfigured",
                "binding_method": "local_static_config" if actor_record else "none",
                "authenticated": False,
            },
        },
        "audit": {
            "written": audit_payload is not None,
            "record": audit_payload["record"] if audit_payload else None,
            "log": audit_payload["log"] if audit_payload else None,
            "authenticated_actor_provenance": False,
            "local_actor_binding_evidence": bound,
        },
        "diagnostics": {
            "config_path": str(config.source_path) if config.source_path else None,
            "configured_actor_count": len(config.governance_identity_actors),
            "local_first": True,
            "privacy_first": True,
            "server_required": False,
            "cloud_sync": False,
            "external_model_calls": False,
            "v2_retrieval_core_changed": False,
        },
    }


def governance_central_policy_store(
    config: AppConfig,
    *,
    policy_path: Path | None = None,
    actor: str | None = None,
    operation: str | None = None,
) -> dict[str, Any]:
    resolved_policy_path = (policy_path or config.governance_policy_central_store)
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    policy_document: dict[str, Any] | None = None
    if resolved_policy_path is None:
        errors.append(
            {
                "code": "central_policy_not_configured",
                "message": "No central policy path was provided and governance.policy.central_store is not configured.",
                "path": [],
            }
        )
    else:
        resolved_policy_path = resolved_policy_path.expanduser()
        if not resolved_policy_path.exists():
            errors.append(
                {
                    "code": "central_policy_file_missing",
                    "message": "Central policy file does not exist.",
                    "path": [],
                }
            )
        else:
            try:
                loaded = json.loads(resolved_policy_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(
                    {
                        "code": "central_policy_invalid_json",
                        "message": str(exc),
                        "path": [],
                    }
                )
            else:
                if isinstance(loaded, dict):
                    policy_document = loaded
                    errors.extend(_validate_central_policy_document(policy_document))
                    warnings.extend(_central_policy_document_warnings(policy_document))
                else:
                    errors.append(
                        {
                            "code": "central_policy_document_not_object",
                            "message": "Central policy document must be a JSON object.",
                            "path": [],
                        }
                    )
    policy_valid = policy_document is not None and not errors
    role_map = _central_policy_role_map(policy_document) if policy_valid else {}
    actor_roles = _central_policy_actor_roles(policy_document, actor) if policy_valid and actor else []
    actor_access_levels = _central_policy_access_levels_for_roles(role_map, actor_roles)
    command_policy = _operation_policy(operation) if operation else None
    required_access_level = command_policy["access_level"] if command_policy else None
    operation_known = command_policy is not None
    operation_allowed = bool(operation_known and required_access_level in actor_access_levels)
    actor_known = bool(actor and actor_roles)
    blockers = []
    if not policy_valid:
        blockers.append(
            _central_policy_blocker(
                "central_policy_document_invalid",
                "No valid local central policy document is available.",
                "storage",
            )
        )
    if actor and not actor_known:
        blockers.append(
            _central_policy_blocker(
                "central_policy_actor_unbound",
                "Requested actor is not bound to any known central policy role.",
                "identity",
            )
        )
    if operation and not operation_known:
        blockers.append(
            _central_policy_blocker(
                "central_policy_operation_unknown",
                "Requested operation is not in ThreadVault's governance operation inventory.",
                "operation",
            )
        )
    if actor and operation and operation_known and not operation_allowed:
        blockers.append(
            _central_policy_blocker(
                "central_policy_operation_denied",
                "Requested actor does not have the access level required for the operation.",
                "policy",
            )
        )
    source_hash = _central_policy_source_hash(policy_document) if policy_document is not None else None
    return {
        "contract_version": GOVERNANCE_CENTRAL_POLICY_STORE_CONTRACT_VERSION,
        "request": {
            "policy": str(policy_path.expanduser()) if policy_path else None,
            "configured_policy": str(config.governance_policy_central_store) if config.governance_policy_central_store else None,
            "resolved_policy": str(resolved_policy_path) if resolved_policy_path else None,
            "actor": actor,
            "operation": operation,
        },
        "governance": {
            "enabled": config.governance_enabled,
            "mode": "local_opt_in" if config.governance_enabled else "disabled",
            "central_policy_ready": policy_valid,
            "team_enforcement_ready": False,
            "current_permissions_enforced": False,
            "server_required": False,
            "server_opt_in": True,
            "cloud_sync": False,
        },
        "store": {
            "type": "local_json_file",
            "available": policy_valid,
            "path": str(resolved_policy_path) if resolved_policy_path else None,
            "exists": bool(resolved_policy_path and resolved_policy_path.exists()),
            "shared_persistence": False,
            "server_required": False,
            "cloud_sync": False,
        },
        "policy": {
            "valid": policy_valid,
            "contract_version": str(policy_document.get("contract_version")) if policy_document else None,
            "expected_contract_version": CENTRAL_POLICY_DOCUMENT_CONTRACT_VERSION,
            "policy_id": str(policy_document.get("policy_id")) if policy_document else None,
            "version": str(policy_document.get("version")) if policy_document else None,
            "role_count": len(policy_document.get("roles", [])) if policy_document else 0,
            "actor_count": len(policy_document.get("actors", [])) if policy_document else 0,
            "source_hash": source_hash,
        },
        "validation": {
            "ok": policy_valid,
            "errors": errors,
            "warnings": warnings,
            "known_roles": [role["name"] for role in ROLES],
            "known_access_levels": [level["name"] for level in ACCESS_LEVELS],
            "known_operations": [operation_item["name"] for operation_item in SENSITIVE_OPERATIONS],
        },
        "provenance": _central_policy_provenance(policy_document, source_hash),
        "actor_resolution": {
            "requested": actor,
            "known": actor_known,
            "roles": actor_roles,
            "access_levels": actor_access_levels,
            "configured_identity_actor": _configured_actor(config, actor) is not None if actor else False,
            "sufficient_for_shared_enforcement": False,
        },
        "operation_resolution": {
            "requested": operation,
            "known": operation_known,
            "required_access_level": required_access_level,
            "audit_required": bool(command_policy["audit_required"]) if command_policy else False,
            "allowed": operation_allowed,
        },
        "enforcement": {
            "would_allow": operation_allowed,
            "would_block": bool(operation and not operation_allowed),
            "automatic_business_enforcement": False,
            "shared_enforcement_ready": False,
            "status": _central_policy_enforcement_status(
                policy_valid=policy_valid,
                actor=actor,
                actor_known=actor_known,
                operation=operation,
                operation_known=operation_known,
                operation_allowed=operation_allowed,
            ),
        },
        "blockers": blockers,
        "diagnostics": {
            "config_path": str(config.source_path) if config.source_path else None,
            "local_first": True,
            "privacy_first": True,
            "server_required": False,
            "server_opt_in": True,
            "cloud_sync": False,
            "v2_retrieval_core_changed": False,
            "business_commands_instrumented": False,
            "automatic_policy_enforcement": False,
        },
    }


def governance_central_policy_readiness(config: AppConfig) -> dict[str, Any]:
    policy_runtime = governance_central_policy_store(config)
    policy_document_valid = bool(policy_runtime["policy"]["valid"])
    blockers = []
    if not policy_document_valid:
        blockers.insert(
            0,
            _central_policy_blocker(
                "central_policy_document_missing",
                "Central policy store runtime exists, but no valid local central policy document is configured.",
                "storage",
            ),
        )
    return {
        "contract_version": GOVERNANCE_CENTRAL_POLICY_READINESS_CONTRACT_VERSION,
        "governance": {
            "enabled": config.governance_enabled,
            "mode": "local_opt_in" if config.governance_enabled else "disabled",
            "central_policy_ready": policy_document_valid,
            "team_enforcement_ready": False,
            "current_permissions_enforced": False,
            "server_required": False,
            "server_opt_in": True,
            "cloud_sync": False,
        },
        "readiness": {
            "overall_status": "not_ready_for_central_policy_store",
            "implemented_prerequisites": [
                "local_governance_role_vocabulary",
                "permission_preflight",
                "policy_readiness_manifest",
                "server_policy_readiness_manifest",
                "identity_actor_readiness_manifest",
                "identity_actor_binding_runtime",
                "central_policy_store_runtime",
            ],
            "missing_prerequisites": [blocker["code"].removesuffix("_missing") for blocker in blockers],
            "blocking_count": len(blockers),
            "safe_to_keep_local_cli": True,
            "safe_to_use_local_static_policy": True,
            "safe_to_enable_central_policy_store": policy_document_valid,
            "safe_to_enable_team_enforcement": False,
        },
        "local_policy": {
            "role_vocabulary_available": True,
            "access_levels_available": True,
            "permission_preflight_available": True,
            "centralized": False,
            "sufficient_for_local_preflight": True,
            "sufficient_for_shared_enforcement": False,
        },
        "central_policy": {
            "store_implemented": True,
            "store_type": "local_json_file",
            "store_available": bool(policy_runtime["store"]["available"]),
            "shared_persistence_implemented": False,
            "policy_loader_implemented": True,
            "policy_query_interface_implemented": True,
            "policy_document_valid": policy_document_valid,
            "missing": [] if policy_document_valid else ["central_policy_document"],
        },
        "adapter": {
            "interface_defined": True,
            "local_adapter_implemented": True,
            "server_adapter_implemented": False,
            "test_adapter_implemented": True,
            "missing": ["server_policy_adapter"],
        },
        "versioning": {
            "schema_versioned": True,
            "policy_versioning_implemented": True,
            "compatibility_checks_implemented": True,
            "policy_version": policy_runtime["policy"]["version"],
            "missing": [] if policy_document_valid else ["configured_policy_version"],
        },
        "provenance": {
            "author_recorded": bool(policy_runtime["provenance"]["author_recorded"]),
            "review_recorded": bool(policy_runtime["provenance"]["review_recorded"]),
            "approval_recorded": bool(policy_runtime["provenance"]["approval_recorded"]),
            "source_hash_recorded": bool(policy_runtime["provenance"]["source_hash_recorded"]),
            "source_hash": policy_runtime["provenance"]["source_hash"],
            "missing": [] if policy_document_valid else ["configured_policy_provenance"],
        },
        "migration": {
            "local_to_central_migration_implemented": False,
            "rollback_implemented": False,
            "dry_run_available": True,
            "missing": ["local_to_central_migration", "policy_rollback"],
        },
        "identity_dependency": {
            "identity_actor_readiness_available": True,
            "identity_binding_ready": True,
            "role_mapping_ready": True,
            "actor_policy_resolution_ready": policy_document_valid,
            "configured_actor_count": len(config.governance_identity_actors),
            "missing": [] if policy_document_valid else ["configured_policy_actor_resolution"],
        },
        "fallback": {
            "local_static_policy_available": True,
            "central_policy_required_for_local_cli": False,
            "central_policy_required_for_shared_enforcement": True,
            "fallback_policy_implemented": True,
            "missing": ["shared_policy_failure_mode"],
        },
        "blockers": blockers,
        "recommended_next_phases": [
            "Design policy adapter interface and central policy document contract.",
            "Design policy versioning, provenance, migration, and rollback workflow.",
            "Implement central policy only after identity and actor binding are ready.",
            "Instrument the first opt-in command slice only after central policy and audit actor provenance are explicit.",
        ],
        "diagnostics": {
            "config_path": str(config.source_path) if config.source_path else None,
            "local_first": True,
            "privacy_first": True,
            "server_opt_in": True,
            "cloud_sync": False,
            "server_required": False,
            "business_commands_instrumented": False,
            "automatic_policy_enforcement": False,
            "central_policy_store_runtime": True,
            "central_policy_document_valid": policy_document_valid,
            "v2_retrieval_core_changed": False,
        },
    }


def governance_central_backup_policy(
    config: AppConfig,
    *,
    policy_path: Path | None = None,
    operation: str | None = None,
    actor: str | None = None,
) -> dict[str, Any]:
    resolved_policy_path = policy_path or config.governance_backup_policy
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    document: dict[str, Any] | None = None
    if resolved_policy_path is None:
        errors.append(
            {
                "code": "central_backup_policy_not_configured",
                "message": "No backup policy path was provided and governance.backup.policy is not configured.",
                "path": [],
            }
        )
    else:
        resolved_policy_path = resolved_policy_path.expanduser()
        if not resolved_policy_path.exists():
            errors.append(
                {
                    "code": "central_backup_policy_file_missing",
                    "message": "Central backup policy file does not exist.",
                    "path": [],
                }
            )
        else:
            try:
                loaded = json.loads(resolved_policy_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append({"code": "central_backup_policy_invalid_json", "message": str(exc), "path": []})
            else:
                if isinstance(loaded, dict):
                    document = loaded
                    errors.extend(_validate_central_backup_policy_document(document))
                    warnings.extend(_central_backup_policy_warnings(document))
                else:
                    errors.append(
                        {
                            "code": "central_backup_policy_document_not_object",
                            "message": "Central backup policy document must be a JSON object.",
                            "path": [],
                        }
                    )
    policy_valid = document is not None and not errors
    source_hash = _central_backup_policy_source_hash(document) if document is not None else None
    actor_roles = _central_backup_actor_roles(config, actor)
    operation_policy = CENTRAL_BACKUP_POLICY_OPERATIONS.get(operation or "") if operation else None
    operation_known = operation_policy is not None
    required_section = str(operation_policy["section"]) if operation_policy else None
    required_roles = _central_backup_required_roles(document, operation_policy) if policy_valid and operation_policy else []
    actor_known = bool(actor and actor_roles)
    role_allowed = bool(set(actor_roles) & set(required_roles)) if required_roles else bool(actor_roles)
    operation_allowed = bool(policy_valid and operation_known and (not actor or role_allowed))
    blockers = []
    if not policy_valid:
        blockers.append(
            _central_backup_blocker(
                "central_backup_policy_document_invalid",
                "No valid local centralized backup/restore policy document is available.",
                "policy",
            )
        )
    if actor and not actor_known:
        blockers.append(
            _central_backup_blocker(
                "central_backup_policy_actor_unbound",
                "Requested actor is not configured in local governance identity actors.",
                "identity",
            )
        )
    if operation and not operation_known:
        blockers.append(
            _central_backup_blocker(
                "central_backup_policy_operation_unknown",
                "Requested backup policy operation is not recognized.",
                "operation",
            )
        )
    if actor and operation and operation_known and policy_valid and not role_allowed:
        blockers.append(
            _central_backup_blocker(
                "central_backup_policy_operation_denied",
                "Requested actor lacks a policy role for the operation.",
                "policy",
            )
        )
    audit_runtime = governance_centralized_audit_store(config, action="verify")
    audit_store_configured = audit_runtime["request"]["resolved_store"] is not None
    audit_store_ready = bool(audit_store_configured and audit_runtime["verification"]["ok"])
    return {
        "contract_version": GOVERNANCE_CENTRAL_BACKUP_POLICY_CONTRACT_VERSION,
        "governance": {
            "enabled": config.governance_enabled,
            "mode": "local_opt_in" if config.governance_enabled else "disabled",
            "central_backup_policy_ready": policy_valid,
            "central_backup_ready": policy_valid,
            "shared_restore_ready": False,
            "team_enforcement_ready": False,
            "server_required": False,
            "server_opt_in": True,
            "cloud_sync": False,
        },
        "request": {
            "policy": str(policy_path.expanduser()) if policy_path else None,
            "configured_policy": str(config.governance_backup_policy) if config.governance_backup_policy else None,
            "resolved_policy": str(resolved_policy_path) if resolved_policy_path else None,
            "operation": operation,
            "actor": actor,
        },
        "store": {
            "type": "local_json_file",
            "available": policy_valid,
            "path": str(resolved_policy_path) if resolved_policy_path else None,
            "exists": bool(resolved_policy_path and resolved_policy_path.exists()),
            "server_required": False,
            "cloud_sync": False,
        },
        "policy": {
            "valid": policy_valid,
            "contract_version": str(document.get("contract_version")) if document else None,
            "expected_contract_version": CENTRAL_BACKUP_POLICY_DOCUMENT_CONTRACT_VERSION,
            "policy_id": str(document.get("policy_id")) if document else None,
            "version": str(document.get("version")) if document else None,
            "source_hash": source_hash,
        },
        "validation": {
            "ok": policy_valid,
            "errors": errors,
            "warnings": warnings,
            "known_operations": sorted(CENTRAL_BACKUP_POLICY_OPERATIONS),
        },
        "provenance": _central_backup_policy_provenance(document, source_hash),
        "repository": {
            "policy_implemented": policy_valid,
            "type": _backup_policy_value(document, ["repository", "type"]),
            "local_path": _backup_policy_value(document, ["repository", "local_path"]),
            "remote_required": False,
            "replication_required": bool(_backup_policy_value(document, ["repository", "replication_required"], False)),
            "server_required": False,
        },
        "backup": {
            "policy_implemented": policy_valid,
            "scope": _backup_policy_value(document, ["backup", "scope"], []),
            "cadence": _backup_policy_value(document, ["backup", "cadence"]),
            "operator_roles": _backup_policy_value(document, ["backup", "operator_roles"], []),
        },
        "restore": {
            "policy_implemented": policy_valid,
            "approval_workflow_implemented": policy_valid,
            "approvals_required": _backup_policy_value(document, ["restore", "approvals_required"]),
            "approver_roles": _backup_policy_value(document, ["restore", "approver_roles"], []),
            "dry_run_required": bool(_backup_policy_value(document, ["restore", "dry_run_required"], True)),
            "pre_restore_backup_required": bool(
                _backup_policy_value(document, ["restore", "pre_restore_backup_required"], True)
            ),
        },
        "retention": {
            "policy_implemented": policy_valid,
            "keep_latest": _backup_policy_value(document, ["retention", "keep_latest"]),
            "prune_requires_approval": bool(_backup_policy_value(document, ["retention", "prune_requires_approval"], True)),
            "approver_roles": _backup_policy_value(document, ["retention", "approver_roles"], []),
        },
        "legal_hold": {
            "policy_implemented": policy_valid,
            "enabled": bool(_backup_policy_value(document, ["legal_hold", "enabled"], False)),
            "bypass_allowed": bool(_backup_policy_value(document, ["legal_hold", "bypass_allowed"], False)),
            "approver_roles": _backup_policy_value(document, ["legal_hold", "approver_roles"], []),
        },
        "recovery_testing": {
            "policy_implemented": policy_valid,
            "required": bool(_backup_policy_value(document, ["recovery_testing", "required"], False)),
            "cadence": _backup_policy_value(document, ["recovery_testing", "cadence"]),
            "operator_roles": _backup_policy_value(document, ["recovery_testing", "operator_roles"], []),
        },
        "migration": {
            "policy_implemented": policy_valid,
            "local_history_supported": bool(_backup_policy_value(document, ["migration", "local_history_supported"], False)),
            "review_required": bool(_backup_policy_value(document, ["migration", "review_required"], True)),
            "operator_roles": _backup_policy_value(document, ["migration", "operator_roles"], []),
        },
        "operation_resolution": {
            "requested": operation,
            "known": operation_known,
            "section": required_section,
            "required_roles": required_roles,
            "actor_roles": actor_roles,
            "allowed": operation_allowed,
            "audit_required": bool(operation_policy["audit_required"]) if operation_policy else False,
        },
        "audit": {
            "centralized_audit_store_runtime": True,
            "centralized_audit_store_configured": audit_store_configured,
            "centralized_audit_ready": audit_store_ready,
            "automatic_business_audit": False,
        },
        "enforcement": {
            "would_allow": operation_allowed,
            "would_block": bool(operation and not operation_allowed),
            "automatic_business_enforcement": False,
            "shared_execution_ready": False,
            "status": _central_backup_policy_status(
                policy_valid=policy_valid,
                operation=operation,
                operation_known=operation_known,
                actor=actor,
                actor_known=actor_known,
                operation_allowed=operation_allowed,
            ),
        },
        "blockers": blockers,
        "diagnostics": {
            "config_path": str(config.source_path) if config.source_path else None,
            "local_first": True,
            "privacy_first": True,
            "server_required": False,
            "server_opt_in": True,
            "cloud_sync": False,
            "v2_retrieval_core_changed": False,
            "business_commands_instrumented": False,
            "automatic_backup_policy_enforcement": False,
        },
    }


def governance_central_backup_readiness(config: AppConfig) -> dict[str, Any]:
    central_policy_runtime = governance_central_policy_store(config)
    central_policy_document_valid = bool(central_policy_runtime["policy"]["valid"])
    backup_policy_runtime = governance_central_backup_policy(config)
    backup_policy_valid = bool(backup_policy_runtime["policy"]["valid"])
    audit_runtime = governance_centralized_audit_store(config, action="verify")
    centralized_audit_ready = bool(audit_runtime["request"]["resolved_store"] and audit_runtime["verification"]["ok"])
    blockers = []
    if not backup_policy_valid:
        blockers.append(
            _central_backup_blocker(
                "central_backup_policy_not_configured",
                "Centralized backup/restore policy runtime exists, but no valid local policy document is configured.",
                "policy",
            )
        )
    if not centralized_audit_ready:
        blockers.append(
            _central_backup_blocker(
                "centralized_audit_store_not_ready",
                "Centralized backup/restore policy exists, but centralized audit store is not configured and verified.",
                "audit",
            )
        )
    return {
        "contract_version": GOVERNANCE_CENTRAL_BACKUP_READINESS_CONTRACT_VERSION,
        "governance": {
            "enabled": config.governance_enabled,
            "mode": "local_opt_in" if config.governance_enabled else "disabled",
            "central_backup_ready": backup_policy_valid,
            "shared_restore_ready": False,
            "team_enforcement_ready": False,
            "server_required": False,
            "server_opt_in": True,
            "cloud_sync": False,
        },
        "readiness": {
            "overall_status": (
                "centralized_backup_restore_policy_ready"
                if backup_policy_valid
                else "not_ready_for_centralized_backup_restore_policy"
            ),
            "implemented_prerequisites": [
                "local_backup_command",
                "local_restore_command",
                "backup_manifest",
                "restore_plan",
                "restore_history",
                "local_retention",
                "export_backup_preflight",
                "restore_retention_preflight",
                "central_policy_readiness_manifest",
                "central_policy_store_runtime",
                "centralized_audit_readiness_manifest",
                "centralized_audit_store_runtime",
                "local_identity_actor_binding",
                "central_backup_policy_runtime",
            ],
            "missing_prerequisites": [blocker["code"].removesuffix("_missing") for blocker in blockers],
            "blocking_count": len(blockers),
            "safe_to_keep_local_cli": True,
            "safe_to_use_local_backup_restore": True,
            "safe_to_enable_central_backup": backup_policy_valid,
            "safe_to_enable_shared_restore": False,
        },
        "local_backup": {
            "backup_command_available": True,
            "restore_command_available": True,
            "backup_manifest_available": True,
            "restore_plan_available": True,
            "restore_history_available": True,
            "local_retention_available": True,
            "sufficient_for_local_use": True,
            "sufficient_for_shared_policy": False,
        },
        "central_backup": {
            "repository_implemented": True,
            "repository_available": backup_policy_valid,
            "repository_type": backup_policy_runtime["repository"]["type"],
            "local_policy_store": True,
            "replication_implemented": bool(backup_policy_runtime["repository"]["replication_required"]),
            "shared_index_implemented": False,
            "encryption_policy_implemented": backup_policy_valid,
            "missing": [] if backup_policy_valid else ["configured_central_backup_policy"],
        },
        "policy": {
            "backup_policy_implemented": True,
            "restore_policy_implemented": True,
            "retention_policy_implemented": True,
            "approval_policy_implemented": True,
            "policy_valid": backup_policy_valid,
            "policy_id": backup_policy_runtime["policy"]["policy_id"],
            "policy_version": backup_policy_runtime["policy"]["version"],
            "missing": [] if backup_policy_valid else ["configured_central_backup_policy"],
        },
        "restore": {
            "approval_workflow_implemented": True,
            "shared_restore_dry_run_implemented": True,
            "conflict_resolution_implemented": False,
            "rollback_plan_implemented": False,
            "missing": [] if backup_policy_valid else ["configured_central_backup_policy"],
        },
        "retention": {
            "legal_hold_implemented": True,
            "prune_approval_implemented": True,
            "expiry_policy_implemented": True,
            "migration_from_local_history_implemented": True,
            "missing": [] if backup_policy_valid else ["configured_central_backup_policy"],
        },
        "audit": {
            "local_audit_available": True,
            "centralized_audit_readiness_available": True,
            "centralized_audit_store_runtime": True,
            "centralized_audit_ready": centralized_audit_ready,
            "authenticated_actor_provenance": False,
            "restore_evidence_review_implemented": False,
            "missing": ["authenticated_actor_provenance", "restore_evidence_review"]
            + ([] if centralized_audit_ready else ["configured_centralized_audit_store"]),
        },
        "dependencies": {
            "identity_actor_readiness_available": True,
            "identity_binding_ready": True,
            "configured_actor_count": len(config.governance_identity_actors),
            "central_policy_readiness_available": True,
            "central_policy_ready": central_policy_document_valid,
            "central_policy_store_runtime": True,
            "server_runtime_required_for_local_cli": False,
            "missing": ["shared_server_context", "authenticated_actor_provenance"]
            + ([] if central_policy_document_valid else ["configured_central_policy_document"]),
        },
        "recovery_testing": {
            "local_restore_tests_available": True,
            "shared_restore_smoke_available": False,
            "recovery_drill_policy_implemented": True,
            "disaster_recovery_validation_policy_implemented": True,
            "missing": ["shared_restore_smoke"],
        },
        "blockers": blockers,
        "recommended_next_phases": [
            "Configure a local central backup policy document before previewing shared backup decisions.",
            "Expand automatic governance instrumentation so backup, restore, and retention commands consult this policy.",
            "Keep shared backup/restore execution out of default local CLI behavior.",
            "Include centralized backup/restore policy in the final v3 acceptance smoke.",
        ],
        "diagnostics": {
            "config_path": str(config.source_path) if config.source_path else None,
            "local_first": True,
            "privacy_first": True,
            "server_opt_in": True,
            "cloud_sync": False,
            "server_required": False,
            "business_commands_instrumented": False,
            "automatic_backup_policy_enforcement": False,
            "central_policy_document_valid": central_policy_document_valid,
            "central_backup_policy_runtime": True,
            "central_backup_policy_valid": backup_policy_valid,
            "centralized_audit_store_configured": bool(audit_runtime["request"]["resolved_store"]),
            "v2_retrieval_core_changed": False,
        },
    }


def governance_export_backup_preflight(
    config: AppConfig,
    *,
    command: str,
    role: str,
    audit_log: Path | None = None,
    actor: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
) -> dict[str, Any]:
    command_policy = _command_policy(command)
    in_scope = _is_export_backup_command(command)
    permission_payload = check_permission(
        config,
        operation=command_policy["operation"] if command_policy else "",
        role=role,
        audit_log=None,
    )
    enforcement_payload = governance_enforcement_check(
        config,
        command=command,
        role=role,
        audit_log=None,
    )
    status = _export_backup_preflight_status(
        known_command=command_policy is not None,
        in_scope=in_scope,
        would_block_if_enforced=enforcement_payload["enforcement"]["would_block_if_enforced"],
    )
    audit_payload = None
    if audit_log is not None:
        audit_payload = append_audit_record(
            audit_log,
            operation="export_backup_preflight",
            actor=actor or role,
            status=status,
            target_type=target_type or "command",
            target_id=target_id or command,
            metadata={
                "checked_command": command,
                "checked_role": role,
                "known_command": str(command_policy is not None).lower(),
                "in_scope": str(in_scope).lower(),
                "operation": command_policy["operation"] if command_policy else "",
                "would_allow": str(permission_payload["decision"]["would_allow"]).lower(),
                "would_block_if_enforced": str(
                    enforcement_payload["enforcement"]["would_block_if_enforced"]
                ).lower(),
                "business_command_executed": "false",
            },
        )
    return {
        "contract_version": GOVERNANCE_EXPORT_BACKUP_PREFLIGHT_CONTRACT_VERSION,
        "request": {
            "command": command,
            "role": role,
            "audit_log": str(audit_log.expanduser()) if audit_log else None,
            "actor": actor,
            "target_type": target_type,
            "target_id": target_id,
        },
        "scope": {
            "name": "export_backup",
            "in_scope": in_scope,
            "allowed_commands": sorted(EXPORT_BACKUP_PREFLIGHT_COMMANDS),
            "reason": "ok" if in_scope else "out_of_scope_command",
        },
        "command_policy": {
            "known": command_policy is not None,
            "command": command_policy["command"] if command_policy else command,
            "operation": command_policy["operation"] if command_policy else None,
            "access_level": command_policy["access_level"] if command_policy else None,
            "audit_required": command_policy["audit_required"] if command_policy else False,
            "future_phase": command_policy["future_phase"] if command_policy else None,
            "notes": command_policy["notes"] if command_policy else "Command is not in the governance enforcement inventory.",
        },
        "permission": permission_payload["decision"],
        "enforcement": {
            **enforcement_payload["enforcement"],
            "preflight_status": status,
            "out_of_scope": not in_scope,
        },
        "privacy": {
            "privacy_scan_expected_before_execution": in_scope,
            "privacy_modes": ["warn", "redact", "fail"],
            "default_privacy_mode": "warn",
            "redaction_or_fail_policy_required_for_shared_export": in_scope,
            "external_model_calls": False,
            "outbound_data_policy_required": in_scope,
        },
        "audit": {
            "required_before_execution": bool(command_policy["audit_required"]) if command_policy else False,
            "automatic_audit_now": False,
            "preflight_record_written": audit_payload is not None,
            "record": audit_payload["record"] if audit_payload else None,
            "log": audit_payload["log"] if audit_payload else None,
        },
        "execution": {
            "business_command_executed": False,
            "files_written": False,
            "backup_created": False,
            "server_required": False,
            "cloud_sync": False,
        },
        "diagnostics": {
            "known_command": command_policy is not None,
            "in_scope": in_scope,
            "inventory_source": "threadvault.governance.ENFORCEMENT_GAP_COMMANDS",
            "governance_enabled": config.governance_enabled,
            "v2_retrieval_core_changed": False,
        },
    }


def governance_restore_retention_preflight(
    config: AppConfig,
    *,
    command: str,
    role: str,
    audit_log: Path | None = None,
    actor: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
) -> dict[str, Any]:
    command_policy = _command_policy(command)
    in_scope = _is_restore_retention_command(command)
    permission_payload = check_permission(
        config,
        operation=command_policy["operation"] if command_policy else "",
        role=role,
        audit_log=None,
    )
    enforcement_payload = governance_enforcement_check(
        config,
        command=command,
        role=role,
        audit_log=None,
    )
    status = _restore_retention_preflight_status(
        known_command=command_policy is not None,
        in_scope=in_scope,
        would_block_if_enforced=enforcement_payload["enforcement"]["would_block_if_enforced"],
    )
    audit_payload = None
    if audit_log is not None:
        audit_payload = append_audit_record(
            audit_log,
            operation="restore_retention_preflight",
            actor=actor or role,
            status=status,
            target_type=target_type or "command",
            target_id=target_id or command,
            metadata={
                "checked_command": command,
                "checked_role": role,
                "known_command": str(command_policy is not None).lower(),
                "in_scope": str(in_scope).lower(),
                "operation": command_policy["operation"] if command_policy else "",
                "would_allow": str(permission_payload["decision"]["would_allow"]).lower(),
                "would_block_if_enforced": str(
                    enforcement_payload["enforcement"]["would_block_if_enforced"]
                ).lower(),
                "business_command_executed": "false",
            },
        )
    return {
        "contract_version": GOVERNANCE_RESTORE_RETENTION_PREFLIGHT_CONTRACT_VERSION,
        "request": {
            "command": command,
            "role": role,
            "audit_log": str(audit_log.expanduser()) if audit_log else None,
            "actor": actor,
            "target_type": target_type,
            "target_id": target_id,
        },
        "scope": {
            "name": "restore_retention",
            "in_scope": in_scope,
            "allowed_commands": sorted(RESTORE_RETENTION_PREFLIGHT_COMMANDS),
            "reason": "ok" if in_scope else "out_of_scope_command",
        },
        "command_policy": {
            "known": command_policy is not None,
            "command": command_policy["command"] if command_policy else command,
            "operation": command_policy["operation"] if command_policy else None,
            "access_level": command_policy["access_level"] if command_policy else None,
            "audit_required": command_policy["audit_required"] if command_policy else False,
            "future_phase": command_policy["future_phase"] if command_policy else None,
            "notes": command_policy["notes"] if command_policy else "Command is not in the governance enforcement inventory.",
        },
        "permission": permission_payload["decision"],
        "enforcement": {
            **enforcement_payload["enforcement"],
            "preflight_status": status,
            "out_of_scope": not in_scope,
        },
        "recovery": {
            "restore_plan_expected_before_execution": command.strip() == "threadvault restore",
            "pre_restore_backup_expected": command.strip() == "threadvault restore",
            "retention_policy_expected": in_scope and command.strip() != "threadvault restore",
            "manual_confirmation_expected": in_scope,
            "centralized_policy_required_for_shared_mode": in_scope,
        },
        "audit": {
            "required_before_execution": bool(command_policy["audit_required"]) if command_policy else False,
            "automatic_audit_now": False,
            "preflight_record_written": audit_payload is not None,
            "record": audit_payload["record"] if audit_payload else None,
            "log": audit_payload["log"] if audit_payload else None,
        },
        "execution": {
            "business_command_executed": False,
            "restore_applied": False,
            "retention_applied": False,
            "files_deleted": False,
            "history_rewritten": False,
            "server_required": False,
            "cloud_sync": False,
        },
        "diagnostics": {
            "known_command": command_policy is not None,
            "in_scope": in_scope,
            "inventory_source": "threadvault.governance.ENFORCEMENT_GAP_COMMANDS",
            "governance_enabled": config.governance_enabled,
            "v2_retrieval_core_changed": False,
        },
    }


def governance_raw_read_preflight(
    config: AppConfig,
    *,
    command: str,
    role: str,
    audit_log: Path | None = None,
    actor: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
) -> dict[str, Any]:
    command_policy = _command_policy(command)
    in_scope = _is_raw_read_command(command)
    permission_payload = check_permission(
        config,
        operation=command_policy["operation"] if command_policy else "",
        role=role,
        audit_log=None,
    )
    enforcement_payload = governance_enforcement_check(
        config,
        command=command,
        role=role,
        audit_log=None,
    )
    status = _preflight_status(
        known_command=command_policy is not None,
        in_scope=in_scope,
        would_block_if_enforced=enforcement_payload["enforcement"]["would_block_if_enforced"],
    )
    audit_payload = None
    if audit_log is not None:
        audit_payload = append_audit_record(
            audit_log,
            operation="raw_read_preflight",
            actor=actor or role,
            status=status,
            target_type=target_type or "command",
            target_id=target_id or command,
            metadata={
                "checked_command": command,
                "checked_role": role,
                "known_command": str(command_policy is not None).lower(),
                "in_scope": str(in_scope).lower(),
                "operation": command_policy["operation"] if command_policy else "",
                "would_allow": str(permission_payload["decision"]["would_allow"]).lower(),
                "would_block_if_enforced": str(
                    enforcement_payload["enforcement"]["would_block_if_enforced"]
                ).lower(),
                "business_command_executed": "false",
                "raw_transcript_returned": "false",
            },
        )
    return {
        "contract_version": GOVERNANCE_RAW_READ_PREFLIGHT_CONTRACT_VERSION,
        "request": {
            "command": command,
            "role": role,
            "audit_log": str(audit_log.expanduser()) if audit_log else None,
            "actor": actor,
            "target_type": target_type,
            "target_id": target_id,
        },
        "scope": {
            "name": "raw_read",
            "in_scope": in_scope,
            "allowed_commands": sorted(RAW_READ_PREFLIGHT_COMMANDS),
            "reason": "ok" if in_scope else "out_of_scope_command",
        },
        "command_policy": {
            "known": command_policy is not None,
            "command": command_policy["command"] if command_policy else command,
            "operation": command_policy["operation"] if command_policy else None,
            "access_level": command_policy["access_level"] if command_policy else None,
            "audit_required": command_policy["audit_required"] if command_policy else False,
            "future_phase": command_policy["future_phase"] if command_policy else None,
            "notes": command_policy["notes"] if command_policy else "Command is not in the governance enforcement inventory.",
        },
        "permission": permission_payload["decision"],
        "enforcement": {
            **enforcement_payload["enforcement"],
            "preflight_status": status,
            "out_of_scope": not in_scope,
        },
        "privacy": {
            "raw_transcript_access": in_scope,
            "local_metadata_access": in_scope,
            "session_detail_access": in_scope,
            "privacy_scan_expected_before_shared_display": in_scope,
            "local_debug_requires_explicit_opt_in": True,
            "external_model_calls": False,
            "outbound_data_policy_required": in_scope,
        },
        "audit": {
            "required_before_execution": bool(command_policy["audit_required"]) if command_policy else False,
            "automatic_audit_now": False,
            "preflight_record_written": audit_payload is not None,
            "record": audit_payload["record"] if audit_payload else None,
            "log": audit_payload["log"] if audit_payload else None,
        },
        "execution": {
            "business_command_executed": False,
            "raw_transcript_returned": False,
            "event_preview_returned": False,
            "local_metadata_returned": False,
            "server_required": False,
            "cloud_sync": False,
        },
        "diagnostics": {
            "known_command": command_policy is not None,
            "in_scope": in_scope,
            "inventory_source": "threadvault.governance.ENFORCEMENT_GAP_COMMANDS",
            "governance_enabled": config.governance_enabled,
            "v2_retrieval_core_changed": False,
        },
    }


def governance_summary_search_preflight(
    config: AppConfig,
    *,
    command: str,
    role: str,
    audit_log: Path | None = None,
    actor: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
) -> dict[str, Any]:
    command_policy = _command_policy(command)
    in_scope = _is_summary_search_command(command)
    permission_payload = check_permission(
        config,
        operation=command_policy["operation"] if command_policy else "",
        role=role,
        audit_log=None,
    )
    enforcement_payload = governance_enforcement_check(
        config,
        command=command,
        role=role,
        audit_log=None,
    )
    status = _preflight_status(
        known_command=command_policy is not None,
        in_scope=in_scope,
        would_block_if_enforced=enforcement_payload["enforcement"]["would_block_if_enforced"],
    )
    audit_payload = None
    if audit_log is not None:
        audit_payload = append_audit_record(
            audit_log,
            operation="summary_search_preflight",
            actor=actor or role,
            status=status,
            target_type=target_type or "command",
            target_id=target_id or command,
            metadata={
                "checked_command": command,
                "checked_role": role,
                "known_command": str(command_policy is not None).lower(),
                "in_scope": str(in_scope).lower(),
                "operation": command_policy["operation"] if command_policy else "",
                "would_allow": str(permission_payload["decision"]["would_allow"]).lower(),
                "would_block_if_enforced": str(
                    enforcement_payload["enforcement"]["would_block_if_enforced"]
                ).lower(),
                "business_command_executed": "false",
                "search_executed": "false",
                "retrieval_results_returned": "false",
            },
        )
    return {
        "contract_version": GOVERNANCE_SUMMARY_SEARCH_PREFLIGHT_CONTRACT_VERSION,
        "request": {
            "command": command,
            "role": role,
            "audit_log": str(audit_log.expanduser()) if audit_log else None,
            "actor": actor,
            "target_type": target_type,
            "target_id": target_id,
        },
        "scope": {
            "name": "summary_search",
            "in_scope": in_scope,
            "allowed_commands": sorted(SUMMARY_SEARCH_PREFLIGHT_COMMANDS),
            "reason": "ok" if in_scope else "out_of_scope_command",
        },
        "command_policy": {
            "known": command_policy is not None,
            "command": command_policy["command"] if command_policy else command,
            "operation": command_policy["operation"] if command_policy else None,
            "access_level": command_policy["access_level"] if command_policy else None,
            "audit_required": command_policy["audit_required"] if command_policy else False,
            "future_phase": command_policy["future_phase"] if command_policy else None,
            "notes": command_policy["notes"] if command_policy else "Command is not in the governance enforcement inventory.",
        },
        "permission": permission_payload["decision"],
        "enforcement": {
            **enforcement_payload["enforcement"],
            "preflight_status": status,
            "out_of_scope": not in_scope,
        },
        "privacy": {
            "summary_search_access": in_scope,
            "raw_transcript_access": False,
            "local_metadata_access": in_scope,
            "snippets_or_warning_details_expected_before_execution": in_scope,
            "local_debug_requires_explicit_opt_in": True,
            "external_model_calls": False,
            "outbound_data_policy_required": False,
        },
        "audit": {
            "required_before_execution": bool(command_policy["audit_required"]) if command_policy else False,
            "automatic_audit_now": False,
            "preflight_record_written": audit_payload is not None,
            "record": audit_payload["record"] if audit_payload else None,
            "log": audit_payload["log"] if audit_payload else None,
        },
        "execution": {
            "business_command_executed": False,
            "search_executed": False,
            "retrieval_results_returned": False,
            "warning_details_returned": False,
            "local_metadata_returned": False,
            "server_required": False,
            "cloud_sync": False,
        },
        "diagnostics": {
            "known_command": command_policy is not None,
            "in_scope": in_scope,
            "inventory_source": "threadvault.governance.ENFORCEMENT_GAP_COMMANDS",
            "governance_enabled": config.governance_enabled,
            "v2_retrieval_core_changed": False,
        },
    }


def governance_export_preview_preflight(
    config: AppConfig,
    *,
    command: str,
    role: str,
    audit_log: Path | None = None,
    actor: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
) -> dict[str, Any]:
    command_policy = _command_policy(command)
    in_scope = _is_export_preview_command(command)
    permission_payload = check_permission(
        config,
        operation=command_policy["operation"] if command_policy else "",
        role=role,
        audit_log=None,
    )
    enforcement_payload = governance_enforcement_check(
        config,
        command=command,
        role=role,
        audit_log=None,
    )
    status = _preflight_status(
        known_command=command_policy is not None,
        in_scope=in_scope,
        would_block_if_enforced=enforcement_payload["enforcement"]["would_block_if_enforced"],
    )
    audit_payload = None
    if audit_log is not None:
        audit_payload = append_audit_record(
            audit_log,
            operation="export_preview_preflight",
            actor=actor or role,
            status=status,
            target_type=target_type or "command",
            target_id=target_id or command,
            metadata={
                "checked_command": command,
                "checked_role": role,
                "known_command": str(command_policy is not None).lower(),
                "in_scope": str(in_scope).lower(),
                "operation": command_policy["operation"] if command_policy else "",
                "would_allow": str(permission_payload["decision"]["would_allow"]).lower(),
                "would_block_if_enforced": str(
                    enforcement_payload["enforcement"]["would_block_if_enforced"]
                ).lower(),
                "business_command_executed": "false",
                "preview_generated": "false",
                "files_written": "false",
            },
        )
    return {
        "contract_version": GOVERNANCE_EXPORT_PREVIEW_PREFLIGHT_CONTRACT_VERSION,
        "request": {
            "command": command,
            "role": role,
            "audit_log": str(audit_log.expanduser()) if audit_log else None,
            "actor": actor,
            "target_type": target_type,
            "target_id": target_id,
        },
        "scope": {
            "name": "export_preview",
            "in_scope": in_scope,
            "allowed_commands": sorted(EXPORT_PREVIEW_PREFLIGHT_COMMANDS),
            "reason": "ok" if in_scope else "out_of_scope_command",
        },
        "command_policy": {
            "known": command_policy is not None,
            "command": command_policy["command"] if command_policy else command,
            "operation": command_policy["operation"] if command_policy else None,
            "access_level": command_policy["access_level"] if command_policy else None,
            "audit_required": command_policy["audit_required"] if command_policy else False,
            "future_phase": command_policy["future_phase"] if command_policy else None,
            "notes": command_policy["notes"] if command_policy else "Command is not in the governance enforcement inventory.",
        },
        "permission": permission_payload["decision"],
        "enforcement": {
            **enforcement_payload["enforcement"],
            "preflight_status": status,
            "out_of_scope": not in_scope,
        },
        "privacy": {
            "export_access": in_scope,
            "preview_access": in_scope,
            "privacy_scan_expected_before_execution": in_scope,
            "privacy_findings_returned": False,
            "local_metadata_access": in_scope,
            "local_debug_requires_explicit_opt_in": True,
            "external_model_calls": False,
            "outbound_data_policy_required": in_scope,
        },
        "audit": {
            "required_before_execution": bool(command_policy["audit_required"]) if command_policy else False,
            "automatic_audit_now": False,
            "preflight_record_written": audit_payload is not None,
            "record": audit_payload["record"] if audit_payload else None,
            "log": audit_payload["log"] if audit_payload else None,
        },
        "execution": {
            "business_command_executed": False,
            "preview_generated": False,
            "manifest_returned": False,
            "files_written": False,
            "local_metadata_returned": False,
            "server_required": False,
            "cloud_sync": False,
        },
        "diagnostics": {
            "known_command": command_policy is not None,
            "in_scope": in_scope,
            "inventory_source": "threadvault.governance.ENFORCEMENT_GAP_COMMANDS",
            "governance_enabled": config.governance_enabled,
            "v2_retrieval_core_changed": False,
        },
    }


def governance_external_model_preflight(
    config: AppConfig,
    *,
    command: str,
    role: str,
    audit_log: Path | None = None,
    actor: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
) -> dict[str, Any]:
    command_policy = _command_policy(command)
    in_scope = _is_external_model_command(command)
    permission_payload = check_permission(
        config,
        operation=command_policy["operation"] if command_policy else "",
        role=role,
        audit_log=None,
    )
    enforcement_payload = governance_enforcement_check(
        config,
        command=command,
        role=role,
        audit_log=None,
    )
    status = _preflight_status(
        known_command=command_policy is not None,
        in_scope=in_scope,
        would_block_if_enforced=enforcement_payload["enforcement"]["would_block_if_enforced"],
    )
    audit_payload = None
    if audit_log is not None:
        audit_payload = append_audit_record(
            audit_log,
            operation="external_model_preflight",
            actor=actor or role,
            status=status,
            target_type=target_type or "command",
            target_id=target_id or command,
            metadata={
                "checked_command": command,
                "checked_role": role,
                "known_command": str(command_policy is not None).lower(),
                "in_scope": str(in_scope).lower(),
                "operation": command_policy["operation"] if command_policy else "",
                "would_allow": str(permission_payload["decision"]["would_allow"]).lower(),
                "would_block_if_enforced": str(
                    enforcement_payload["enforcement"]["would_block_if_enforced"]
                ).lower(),
                "business_command_executed": "false",
                "external_call_executed": "false",
                "payload_sent": "false",
            },
        )
    return {
        "contract_version": GOVERNANCE_EXTERNAL_MODEL_PREFLIGHT_CONTRACT_VERSION,
        "request": {
            "command": command,
            "role": role,
            "audit_log": str(audit_log.expanduser()) if audit_log else None,
            "actor": actor,
            "target_type": target_type,
            "target_id": target_id,
        },
        "scope": {
            "name": "external_model",
            "in_scope": in_scope,
            "allowed_commands": sorted(EXTERNAL_MODEL_PREFLIGHT_COMMANDS),
            "reason": "ok" if in_scope else "out_of_scope_command",
        },
        "command_policy": {
            "known": command_policy is not None,
            "command": command_policy["command"] if command_policy else command,
            "operation": command_policy["operation"] if command_policy else None,
            "access_level": command_policy["access_level"] if command_policy else None,
            "audit_required": command_policy["audit_required"] if command_policy else False,
            "future_phase": command_policy["future_phase"] if command_policy else None,
            "notes": command_policy["notes"] if command_policy else "Command is not in the governance enforcement inventory.",
        },
        "permission": permission_payload["decision"],
        "enforcement": {
            **enforcement_payload["enforcement"],
            "preflight_status": status,
            "out_of_scope": not in_scope,
        },
        "outbound_policy": {
            "external_model_calls_enabled_by_default": False,
            "explicit_opt_in_required": in_scope,
            "outbound_data_policy_required": in_scope,
            "privacy_scan_required": in_scope,
            "redaction_or_fail_policy_required": in_scope,
            "evidence_validation_required": in_scope,
            "human_consent_required_for_shared_mode": in_scope,
            "provider_allowlist_required_for_shared_mode": in_scope,
            "raw_transcript_allowed_by_default": False,
            "local_metadata_allowed_by_default": False,
        },
        "audit": {
            "required_before_execution": bool(command_policy["audit_required"]) if command_policy else False,
            "automatic_audit_now": False,
            "preflight_record_written": audit_payload is not None,
            "record": audit_payload["record"] if audit_payload else None,
            "log": audit_payload["log"] if audit_payload else None,
        },
        "execution": {
            "business_command_executed": False,
            "external_call_executed": False,
            "payload_sent": False,
            "model_response_returned": False,
            "provider_metadata_returned": False,
            "server_required": False,
            "cloud_sync": False,
        },
        "diagnostics": {
            "known_command": command_policy is not None,
            "in_scope": in_scope,
            "inventory_source": "threadvault.governance.ENFORCEMENT_GAP_COMMANDS",
            "governance_enabled": config.governance_enabled,
            "v2_retrieval_core_changed": False,
            "external_adapter_implemented": False,
        },
    }


def check_permission(
    config: AppConfig,
    *,
    operation: str,
    role: str,
    audit_log: Path | None = None,
    actor: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
) -> dict[str, Any]:
    operation_policy = _operation_policy(operation)
    role_policy = _role_policy(role)
    required_access = operation_policy["access_level"] if operation_policy else None
    role_access_levels = role_policy["access_levels"] if role_policy else []
    known_operation = operation_policy is not None
    known_role = role_policy is not None
    would_allow = known_operation and known_role and required_access in role_access_levels
    enforced = config.governance_enabled
    allowed = would_allow if enforced else True
    status = "ok" if allowed else "denied"
    reasons = _permission_reasons(
        enforced=enforced,
        known_operation=known_operation,
        known_role=known_role,
        would_allow=would_allow,
        required_access=required_access,
    )
    audit_payload = None
    if audit_log is not None:
        audit_payload = append_audit_record(
            audit_log,
            operation="permission_check",
            actor=actor or role,
            status=status if enforced else "preview",
            target_type=target_type or "operation",
            target_id=target_id or operation,
            metadata={
                "checked_operation": operation,
                "checked_role": role,
                "required_access": required_access or "",
                "governance_enabled": str(config.governance_enabled).lower(),
                "would_allow": str(would_allow).lower(),
                "enforced": str(enforced).lower(),
            },
        )
    return {
        "contract_version": GOVERNANCE_PERMISSION_CHECK_CONTRACT_VERSION,
        "request": {
            "operation": operation,
            "role": role,
            "audit_log": str(audit_log.expanduser()) if audit_log else None,
            "actor": actor,
            "target_type": target_type,
            "target_id": target_id,
        },
        "governance": {
            "enabled": config.governance_enabled,
            "mode": "local_opt_in" if config.governance_enabled else "disabled",
            "permissions_enforced": enforced,
        },
        "decision": {
            "allowed": allowed,
            "would_allow": would_allow,
            "enforced": enforced,
            "status": status,
            "required_access": required_access,
            "role_access_levels": role_access_levels,
            "reasons": reasons,
        },
        "audit": {
            "written": audit_payload is not None,
            "record": audit_payload["record"] if audit_payload else None,
            "log": audit_payload["log"] if audit_payload else None,
        },
        "diagnostics": {
            "known_operation": known_operation,
            "known_role": known_role,
            "server_required": False,
            "external_model_calls": False,
        },
    }


def governance_centralized_audit_store(
    config: AppConfig,
    *,
    action: str,
    store_path: Path | None = None,
    operation: str | None = None,
    actor: str | None = None,
    status: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    normalized_action = action.strip().lower()
    resolved_store = (store_path or config.governance_audit_central_store)
    errors: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    append_payload: dict[str, Any] | None = None
    if normalized_action not in {"append", "list", "verify"}:
        errors.append({"code": "invalid_action", "message": "action must be append, list, or verify.", "path": ["action"]})
    if resolved_store is None:
        errors.append(
            {
                "code": "centralized_audit_store_not_configured",
                "message": "No centralized audit store path was provided and governance.audit.central_store is not configured.",
                "path": ["store"],
            }
        )
    else:
        resolved_store = resolved_store.expanduser()
    if normalized_action == "append":
        for field_name, value in {
            "operation": operation,
            "actor": actor,
            "status": status,
            "target_type": target_type,
            "target_id": target_id,
        }.items():
            if not value:
                errors.append(
                    {
                        "code": f"{field_name}_missing",
                        "message": f"{field_name} is required for append.",
                        "path": [field_name],
                    }
                )
    records, warnings, verification = _read_centralized_audit_store(resolved_store)
    if normalized_action == "append" and resolved_store is not None and not verification["ok"]:
        errors.append(
            {
                "code": "centralized_audit_store_integrity_failed",
                "message": "Existing centralized audit store failed verification; append is blocked.",
                "path": ["store"],
            }
        )
    if not errors and normalized_action == "append" and resolved_store is not None:
        record = _centralized_audit_record(
            config,
            previous_hash=verification["last_hash"],
            operation=operation or "",
            actor=actor or "",
            status=status or "",
            target_type=target_type or "",
            target_id=target_id or "",
            metadata=metadata or {},
        )
        resolved_store.parent.mkdir(parents=True, exist_ok=True)
        with resolved_store.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            handle.write("\n")
        records, warnings, verification = _read_centralized_audit_store(resolved_store)
        append_payload = {"written": True, "record": record}
    else:
        append_payload = {"written": False, "record": None}
    filtered_records = _filter_centralized_audit_records(records, actor=actor if normalized_action == "list" else None, operation=operation)
    limited_records = filtered_records[-limit:] if limit else filtered_records
    if errors:
        blockers.append(
            _centralized_audit_blocker(
                "centralized_audit_store_unavailable",
                "A usable centralized audit store is not available for the requested action.",
                "storage",
            )
        )
    if not verification["ok"]:
        blockers.append(
            _centralized_audit_blocker(
                "centralized_audit_integrity_failed",
                "Centralized audit store hash-chain verification failed.",
                "integrity",
            )
        )
    return {
        "contract_version": GOVERNANCE_CENTRALIZED_AUDIT_STORE_CONTRACT_VERSION,
        "request": {
            "action": normalized_action,
            "store": str(store_path.expanduser()) if store_path else None,
            "configured_store": str(config.governance_audit_central_store) if config.governance_audit_central_store else None,
            "resolved_store": str(resolved_store) if resolved_store else None,
            "operation": operation,
            "actor": actor,
            "status": status,
            "target_type": target_type,
            "target_id": target_id,
            "limit": limit,
        },
        "governance": {
            "enabled": config.governance_enabled,
            "mode": "local_opt_in" if config.governance_enabled else "disabled",
            "centralized_audit_ready": bool(resolved_store is not None and verification["ok"]),
            "team_enforcement_ready": False,
            "server_required": False,
            "server_opt_in": True,
            "cloud_sync": False,
        },
        "store": {
            "type": "local_jsonl_hash_chain",
            "available": resolved_store is not None and not errors and verification["ok"],
            "path": str(resolved_store) if resolved_store else None,
            "exists": bool(resolved_store and resolved_store.exists()),
            "local_file_store": True,
            "shared_persistence": True,
            "server_required": False,
            "cloud_sync": False,
        },
        "append": append_payload,
        "query": {
            "filter_actor": actor if normalized_action == "list" else None,
            "filter_operation": operation,
            "matched_count": len(filtered_records),
            "returned_count": len(limited_records),
            "limit": limit,
            "query_interface_implemented": True,
        },
        "verification": verification,
        "records": limited_records,
        "warnings": warnings,
        "errors": errors,
        "blockers": blockers,
        "diagnostics": {
            "config_path": str(config.source_path) if config.source_path else None,
            "local_first": True,
            "privacy_first": True,
            "server_required": False,
            "server_opt_in": True,
            "cloud_sync": False,
            "append_only_integrity": True,
            "record_hashing": True,
            "signature_or_seal": False,
            "automatic_business_audit": False,
            "v2_retrieval_core_changed": False,
        },
    }


def append_audit_record(
    log_path: Path,
    *,
    operation: str,
    actor: str,
    status: str,
    target_type: str,
    target_id: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved = log_path.expanduser()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "record_version": GOVERNANCE_AUDIT_RECORD_VERSION,
        "record_id": str(uuid4()),
        "timestamp": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "operation": operation,
        "actor": actor,
        "status": status,
        "target": {
            "type": target_type,
            "id": target_id,
        },
        "metadata": metadata or {},
        "local_only": True,
    }
    with resolved.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
        handle.write("\n")
    return {
        "contract_version": GOVERNANCE_AUDIT_APPEND_CONTRACT_VERSION,
        "ok": True,
        "log": _audit_log_payload(resolved),
        "record": record,
        "diagnostics": _audit_diagnostics(record_count=1, warning_count=0),
    }


def list_audit_records(log_path: Path, *, limit: int = 50) -> dict[str, Any]:
    resolved = log_path.expanduser()
    records: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    if resolved.exists():
        with resolved.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                text = line.strip()
                if not text:
                    continue
                try:
                    value = json.loads(text)
                except json.JSONDecodeError as exc:
                    warnings.append({"line_no": line_no, "code": "invalid_audit_json", "message": str(exc)})
                    continue
                if not isinstance(value, dict):
                    warnings.append({"line_no": line_no, "code": "invalid_audit_record", "message": "Audit record must be an object."})
                    continue
                if not _is_audit_record(value):
                    warnings.append({
                        "line_no": line_no,
                        "code": "invalid_audit_record",
                        "message": "Audit record is missing required fields.",
                    })
                    continue
                records.append(value)
    limited_records = records[-limit:] if limit else records
    return {
        "contract_version": GOVERNANCE_AUDIT_LIST_CONTRACT_VERSION,
        "log": _audit_log_payload(resolved),
        "records": limited_records,
        "warnings": warnings,
        "diagnostics": _audit_diagnostics(record_count=len(limited_records), warning_count=len(warnings)),
    }


def _centralized_audit_record(
    config: AppConfig,
    *,
    previous_hash: str | None,
    operation: str,
    actor: str,
    status: str,
    target_type: str,
    target_id: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    actor_record = _configured_actor(config, actor)
    record = {
        "record_version": GOVERNANCE_CENTRALIZED_AUDIT_RECORD_VERSION,
        "record_id": str(uuid4()),
        "timestamp": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "operation": operation,
        "actor": actor,
        "status": status,
        "target": {
            "type": target_type,
            "id": target_id,
        },
        "metadata": metadata,
        "provenance": {
            "actor_source": actor_record.get("source") if actor_record else "unconfigured",
            "configured_actor": actor_record is not None,
            "roles": actor_record.get("roles", []) if actor_record else [],
            "authenticated": False,
            "binding_method": "local_static_config" if actor_record else "manual_actor_label",
        },
        "previous_hash": previous_hash,
        "centralized": True,
        "local_file_store": True,
    }
    record["record_hash"] = _centralized_audit_record_hash(record)
    return record


def _read_centralized_audit_store(path: Path | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    if path is None or not path.exists():
        return records, warnings, _centralized_audit_verification(records, warnings)
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                value = json.loads(text)
            except json.JSONDecodeError as exc:
                warnings.append({"line_no": line_no, "code": "invalid_centralized_audit_json", "message": str(exc)})
                continue
            if not isinstance(value, dict):
                warnings.append(
                    {
                        "line_no": line_no,
                        "code": "invalid_centralized_audit_record",
                        "message": "Centralized audit record must be an object.",
                    }
                )
                continue
            records.append(value)
    return records, warnings, _centralized_audit_verification(records, warnings)


def _centralized_audit_verification(records: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    previous_hash = None
    valid_record_count = 0
    for index, record in enumerate(records):
        if not _is_centralized_audit_record(record):
            errors.append(
                {
                    "index": index,
                    "code": "invalid_centralized_audit_record",
                    "message": "Centralized audit record is missing required fields.",
                }
            )
            continue
        expected_hash = _centralized_audit_record_hash(record)
        if record.get("previous_hash") != previous_hash:
            errors.append(
                {
                    "index": index,
                    "code": "previous_hash_mismatch",
                    "message": "Centralized audit previous_hash does not match the prior record hash.",
                }
            )
        if record.get("record_hash") != expected_hash:
            errors.append(
                {
                    "index": index,
                    "code": "record_hash_mismatch",
                    "message": "Centralized audit record_hash does not match the record payload.",
                }
            )
        previous_hash = record.get("record_hash")
        valid_record_count += 1
    return {
        "ok": not errors and not warnings,
        "record_count": len(records),
        "valid_record_count": valid_record_count,
        "warning_count": len(warnings),
        "errors": errors,
        "append_only": True,
        "hash_chain_valid": not errors,
        "last_hash": previous_hash,
    }


def _is_centralized_audit_record(value: dict[str, Any]) -> bool:
    required = {
        "record_version",
        "record_id",
        "timestamp",
        "operation",
        "actor",
        "status",
        "target",
        "metadata",
        "provenance",
        "previous_hash",
        "record_hash",
        "centralized",
        "local_file_store",
    }
    if not required <= set(value):
        return False
    return (
        value["record_version"] == GOVERNANCE_CENTRALIZED_AUDIT_RECORD_VERSION
        and isinstance(value["target"], dict)
        and {"type", "id"} <= set(value["target"])
    )


def _centralized_audit_record_hash(record: dict[str, Any]) -> str:
    hashable = dict(record)
    hashable.pop("record_hash", None)
    canonical = json.dumps(hashable, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _filter_centralized_audit_records(
    records: list[dict[str, Any]],
    *,
    actor: str | None,
    operation: str | None,
) -> list[dict[str, Any]]:
    filtered = records
    if actor:
        filtered = [record for record in filtered if record.get("actor") == actor]
    if operation:
        filtered = [record for record in filtered if record.get("operation") == operation]
    return filtered


def _audit_log_payload(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "local_only": True,
        "server_required": False,
        "cloud_sync": False,
    }


def _audit_diagnostics(record_count: int, warning_count: int) -> dict[str, Any]:
    return {
        "record_count": record_count,
        "warning_count": warning_count,
        "append_only": True,
        "server_required": False,
        "external_model_calls": False,
    }


def _is_audit_record(value: dict[str, Any]) -> bool:
    required = {
        "record_version",
        "record_id",
        "timestamp",
        "operation",
        "actor",
        "status",
        "target",
        "metadata",
        "local_only",
    }
    if not required <= set(value):
        return False
    return isinstance(value["target"], dict) and {"type", "id"} <= set(value["target"])


def _operation_policy(operation: str) -> dict[str, Any] | None:
    return next((item for item in SENSITIVE_OPERATIONS if item["name"] == operation), None)


def _role_policy(role: str) -> dict[str, Any] | None:
    return next((item for item in ROLES if item["name"] == role), None)


def _command_policy(command: str) -> dict[str, Any] | None:
    normalized = command.strip()
    return next((item for item in ENFORCEMENT_GAP_COMMANDS if item["command"] == normalized), None)


def _is_export_backup_command(command: str) -> bool:
    return command.strip() in EXPORT_BACKUP_PREFLIGHT_COMMANDS


def _is_restore_retention_command(command: str) -> bool:
    return command.strip() in RESTORE_RETENTION_PREFLIGHT_COMMANDS


def _is_raw_read_command(command: str) -> bool:
    return command.strip() in RAW_READ_PREFLIGHT_COMMANDS


def _is_summary_search_command(command: str) -> bool:
    return command.strip() in SUMMARY_SEARCH_PREFLIGHT_COMMANDS


def _is_export_preview_command(command: str) -> bool:
    return command.strip() in EXPORT_PREVIEW_PREFLIGHT_COMMANDS


def _is_external_model_command(command: str) -> bool:
    return command.strip() in EXTERNAL_MODEL_PREFLIGHT_COMMANDS


def _business_command_preflight_category(command: str) -> str:
    if _is_export_backup_command(command):
        return "export_backup"
    if _is_restore_retention_command(command):
        return "restore_retention"
    if _is_raw_read_command(command):
        return "raw_read"
    if _is_summary_search_command(command):
        return "summary_search"
    if _is_export_preview_command(command):
        return "export_preview"
    if _is_external_model_command(command):
        return "external_model"
    return "unknown"


def _business_command_preflight(
    config: AppConfig,
    *,
    command: str,
    role: str,
    audit_log: Path | None,
    actor: str | None,
    target_type: str | None,
    target_id: str | None,
    category: str,
) -> dict[str, Any]:
    kwargs = {
        "command": command,
        "role": role,
        "audit_log": audit_log,
        "actor": actor,
        "target_type": target_type,
        "target_id": target_id,
    }
    if category == "export_backup":
        return governance_export_backup_preflight(config, **kwargs)
    if category == "restore_retention":
        return governance_restore_retention_preflight(config, **kwargs)
    if category == "raw_read":
        return governance_raw_read_preflight(config, **kwargs)
    if category == "summary_search":
        return governance_summary_search_preflight(config, **kwargs)
    if category == "export_preview":
        return governance_export_preview_preflight(config, **kwargs)
    if category == "external_model":
        return governance_external_model_preflight(config, **kwargs)
    return {
        "contract_version": "governance_business_command_preflight.unknown",
        "request": {
            "command": command,
            "role": role,
            "audit_log": str(audit_log.expanduser()) if audit_log else None,
            "actor": actor,
            "target_type": target_type,
            "target_id": target_id,
        },
        "scope": {"known_command": False, "in_scope": False},
        "permission": {
            "enforced": config.governance_enabled,
            "allowed": False,
            "would_allow": False,
        },
        "enforcement": {"preflight_status": "unknown_command"},
        "audit": {"preflight_record_written": False, "record": None, "log": None},
        "execution": {"business_command_executed": False},
    }


def _preflight_status(
    *,
    known_command: bool,
    in_scope: bool,
    would_block_if_enforced: bool,
) -> str:
    if not known_command:
        return "unknown_command"
    if not in_scope:
        return "out_of_scope"
    if would_block_if_enforced:
        return "would_block"
    return "would_allow"


_export_backup_preflight_status = _preflight_status
_restore_retention_preflight_status = _preflight_status


def _readiness_category(
    name: str,
    description: str,
    *,
    commands: list[str],
    recommended_next_phase: str,
    audit_required: bool = True,
) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "commands": commands,
        "audit_required": audit_required,
        "preflight_available": True,
        "dry_run_available": True,
        "automatic_preflight": False,
        "automatic_audit": False,
        "ready_for_team_enforcement": False,
        "recommended_next_phase": recommended_next_phase,
    }


def _server_policy_blocker(code: str, description: str, category: str) -> dict[str, Any]:
    return {
        "code": code,
        "severity": "blocking",
        "category": category,
        "description": description,
        "required_before": "shared_team_enforcement",
    }


def _centralized_audit_blocker(code: str, description: str, category: str) -> dict[str, Any]:
    return {
        "code": code,
        "severity": "blocking",
        "category": category,
        "description": description,
        "required_before": "centralized_audit_retention",
    }


def _v3_acceptance_item(code: str, criterion: str, status: str, evidence: list[str]) -> dict[str, Any]:
    return {
        "code": code,
        "criterion": criterion,
        "status": status,
        "evidence": evidence,
    }


def _v3_milestone(version: str, title: str, status: str, phase_refs: list[str]) -> dict[str, Any]:
    return {
        "version": version,
        "title": title,
        "status": status,
        "phase_refs": phase_refs,
    }


def _v3_completion_blocker(code: str, description: str, category: str) -> dict[str, Any]:
    return {
        "code": code,
        "severity": "blocking",
        "category": category,
        "description": description,
        "required_before": "v3_final_acceptance",
    }


def _identity_actor_blocker(code: str, description: str, category: str) -> dict[str, Any]:
    return {
        "code": code,
        "severity": "blocking",
        "category": category,
        "description": description,
        "required_before": "shared_identity_binding",
    }


def _configured_actor(config: AppConfig, actor_id: str) -> dict[str, Any] | None:
    for actor in config.governance_identity_actors:
        if actor["id"] == actor_id:
            return actor
    return None


def _actor_binding_failure_reason(
    actor_record: dict[str, Any] | None,
    invalid_roles: list[str],
    valid_roles: list[str],
) -> str | None:
    if actor_record is None:
        return "actor_not_configured"
    if invalid_roles:
        return "invalid_role_mapping"
    if not valid_roles:
        return "no_roles_configured"
    return None


def _validate_central_policy_document(document: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if document.get("contract_version") != CENTRAL_POLICY_DOCUMENT_CONTRACT_VERSION:
        errors.append(
            {
                "code": "invalid_contract_version",
                "message": f"contract_version must be {CENTRAL_POLICY_DOCUMENT_CONTRACT_VERSION}",
                "path": ["contract_version"],
            }
        )
    for field in ["policy_id", "version"]:
        if not isinstance(document.get(field), str) or not str(document.get(field)).strip():
            errors.append({"code": f"{field}_missing", "message": f"{field} must be a non-empty string.", "path": [field]})
    provenance = document.get("provenance")
    if not isinstance(provenance, dict):
        errors.append({"code": "provenance_missing", "message": "provenance must be an object.", "path": ["provenance"]})
    else:
        for field in ["author", "source"]:
            if not isinstance(provenance.get(field), str) or not str(provenance.get(field)).strip():
                errors.append(
                    {
                        "code": f"provenance_{field}_missing",
                        "message": f"provenance.{field} must be a non-empty string.",
                        "path": ["provenance", field],
                    }
                )
        for field in ["reviewed_by", "approved_by"]:
            values = provenance.get(field, [])
            if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
                errors.append(
                    {
                        "code": f"provenance_{field}_invalid",
                        "message": f"provenance.{field} must be an array of strings.",
                        "path": ["provenance", field],
                    }
                )
    known_roles = {role["name"] for role in ROLES}
    known_access_levels = {level["name"] for level in ACCESS_LEVELS}
    policy_roles = document.get("roles")
    role_names: set[str] = set()
    if not isinstance(policy_roles, list) or not policy_roles:
        errors.append({"code": "roles_missing", "message": "roles must be a non-empty array.", "path": ["roles"]})
    else:
        for index, item in enumerate(policy_roles):
            if not isinstance(item, dict):
                errors.append({"code": "role_not_object", "message": "Each role must be an object.", "path": ["roles", index]})
                continue
            role_name = item.get("name")
            if not isinstance(role_name, str) or not role_name.strip():
                errors.append(
                    {
                        "code": "role_name_missing",
                        "message": "Role name must be a non-empty string.",
                        "path": ["roles", index, "name"],
                    }
                )
                continue
            role_names.add(role_name)
            if role_name not in known_roles:
                errors.append({"code": "unknown_role", "message": f"Unknown role: {role_name}", "path": ["roles", index, "name"]})
            access_levels = item.get("access_levels")
            if not isinstance(access_levels, list) or any(not isinstance(level, str) for level in access_levels):
                errors.append(
                    {
                        "code": "role_access_levels_invalid",
                        "message": "Role access_levels must be an array of strings.",
                        "path": ["roles", index, "access_levels"],
                    }
                )
            else:
                for level in access_levels:
                    if level not in known_access_levels:
                        errors.append(
                            {
                                "code": "unknown_access_level",
                                "message": f"Unknown access level: {level}",
                                "path": ["roles", index, "access_levels"],
                            }
                        )
    actors = document.get("actors", [])
    if not isinstance(actors, list):
        errors.append({"code": "actors_invalid", "message": "actors must be an array.", "path": ["actors"]})
    else:
        for index, item in enumerate(actors):
            if not isinstance(item, dict):
                errors.append({"code": "actor_not_object", "message": "Each actor must be an object.", "path": ["actors", index]})
                continue
            actor_id = item.get("id")
            if not isinstance(actor_id, str) or not actor_id.strip():
                errors.append(
                    {
                        "code": "actor_id_missing",
                        "message": "Actor id must be a non-empty string.",
                        "path": ["actors", index, "id"],
                    }
                )
            actor_roles = item.get("roles")
            if not isinstance(actor_roles, list) or any(not isinstance(role, str) for role in actor_roles):
                errors.append(
                    {
                        "code": "actor_roles_invalid",
                        "message": "Actor roles must be an array of strings.",
                        "path": ["actors", index, "roles"],
                    }
                )
            else:
                for role in actor_roles:
                    if role not in role_names:
                        errors.append(
                            {
                                "code": "actor_unknown_role",
                                "message": f"Actor references unknown role: {role}",
                                "path": ["actors", index, "roles"],
                            }
                        )
    return errors


def _central_policy_document_warnings(document: dict[str, Any]) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    provenance = document.get("provenance")
    if isinstance(provenance, dict):
        if not provenance.get("reviewed_by"):
            warnings.append(
                {
                    "code": "policy_review_empty",
                    "message": "Policy provenance has no reviewers.",
                    "path": ["provenance", "reviewed_by"],
                }
            )
        if not provenance.get("approved_by"):
            warnings.append(
                {
                    "code": "policy_approval_empty",
                    "message": "Policy provenance has no approvers.",
                    "path": ["provenance", "approved_by"],
                }
            )
    return warnings


def _central_policy_role_map(document: dict[str, Any] | None) -> dict[str, list[str]]:
    if not document:
        return {}
    role_map: dict[str, list[str]] = {}
    for item in document.get("roles", []):
        if isinstance(item, dict) and isinstance(item.get("name"), str) and isinstance(item.get("access_levels"), list):
            role_map[item["name"]] = [level for level in item["access_levels"] if isinstance(level, str)]
    return role_map


def _central_policy_actor_roles(document: dict[str, Any] | None, actor: str | None) -> list[str]:
    if not document or not actor:
        return []
    for item in document.get("actors", []):
        if isinstance(item, dict) and item.get("id") == actor and isinstance(item.get("roles"), list):
            return [role for role in item["roles"] if isinstance(role, str)]
    return []


def _central_policy_access_levels_for_roles(role_map: dict[str, list[str]], roles: list[str]) -> list[str]:
    access_levels: set[str] = set()
    for role in roles:
        access_levels.update(role_map.get(role, []))
    return sorted(access_levels)


def _central_policy_source_hash(document: dict[str, Any]) -> str:
    canonical = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _central_policy_provenance(document: dict[str, Any] | None, source_hash: str | None) -> dict[str, Any]:
    provenance = document.get("provenance") if document else None
    if not isinstance(provenance, dict):
        provenance = {}
    reviewed_by = provenance.get("reviewed_by", [])
    approved_by = provenance.get("approved_by", [])
    return {
        "author": provenance.get("author"),
        "reviewed_by": reviewed_by if isinstance(reviewed_by, list) else [],
        "approved_by": approved_by if isinstance(approved_by, list) else [],
        "source": provenance.get("source"),
        "source_hash": source_hash,
        "author_recorded": isinstance(provenance.get("author"), str) and bool(str(provenance.get("author")).strip()),
        "review_recorded": isinstance(reviewed_by, list) and bool(reviewed_by),
        "approval_recorded": isinstance(approved_by, list) and bool(approved_by),
        "source_hash_recorded": source_hash is not None,
    }


def _central_policy_enforcement_status(
    *,
    policy_valid: bool,
    actor: str | None,
    actor_known: bool,
    operation: str | None,
    operation_known: bool,
    operation_allowed: bool,
) -> str:
    if not policy_valid:
        return "policy_unavailable"
    if actor and not actor_known:
        return "actor_unbound"
    if operation and not operation_known:
        return "unknown_operation"
    if actor and operation and operation_allowed:
        return "would_allow"
    if actor and operation:
        return "would_block"
    return "validated"


def _central_policy_blocker(code: str, description: str, category: str) -> dict[str, Any]:
    return {
        "code": code,
        "severity": "blocking",
        "category": category,
        "description": description,
        "required_before": "central_policy_store",
    }


def _validate_central_backup_policy_document(document: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if document.get("contract_version") != CENTRAL_BACKUP_POLICY_DOCUMENT_CONTRACT_VERSION:
        errors.append(
            {
                "code": "invalid_contract_version",
                "message": f"contract_version must be {CENTRAL_BACKUP_POLICY_DOCUMENT_CONTRACT_VERSION}",
                "path": ["contract_version"],
            }
        )
    for field in ["policy_id", "version"]:
        if not isinstance(document.get(field), str) or not str(document.get(field)).strip():
            errors.append({"code": f"{field}_missing", "message": f"{field} must be a non-empty string.", "path": [field]})
    provenance = document.get("provenance")
    if not isinstance(provenance, dict):
        errors.append({"code": "provenance_missing", "message": "provenance must be an object.", "path": ["provenance"]})
    else:
        for field in ["author", "source"]:
            if not isinstance(provenance.get(field), str) or not str(provenance.get(field)).strip():
                errors.append(
                    {
                        "code": f"provenance_{field}_missing",
                        "message": f"provenance.{field} must be a non-empty string.",
                        "path": ["provenance", field],
                    }
                )
        for field in ["reviewed_by", "approved_by"]:
            values = provenance.get(field, [])
            if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
                errors.append(
                    {
                        "code": f"provenance_{field}_invalid",
                        "message": f"provenance.{field} must be an array of strings.",
                        "path": ["provenance", field],
                    }
                )
    required_objects = ["repository", "backup", "restore", "retention", "legal_hold", "recovery_testing", "migration"]
    for section in required_objects:
        if not isinstance(document.get(section), dict):
            errors.append({"code": f"{section}_missing", "message": f"{section} must be an object.", "path": [section]})
    _require_non_empty_string(errors, document, ["repository", "type"])
    _require_non_empty_string(errors, document, ["repository", "local_path"])
    _require_string_array(errors, document, ["backup", "scope"], allow_empty=False)
    _require_non_empty_string(errors, document, ["backup", "cadence"])
    _require_string_array(errors, document, ["backup", "operator_roles"], allow_empty=False)
    _require_positive_int(errors, document, ["restore", "approvals_required"])
    _require_string_array(errors, document, ["restore", "approver_roles"], allow_empty=False)
    _require_bool(errors, document, ["restore", "dry_run_required"])
    _require_bool(errors, document, ["restore", "pre_restore_backup_required"])
    _require_positive_int(errors, document, ["retention", "keep_latest"])
    _require_bool(errors, document, ["retention", "prune_requires_approval"])
    _require_string_array(errors, document, ["retention", "approver_roles"], allow_empty=False)
    _require_bool(errors, document, ["legal_hold", "enabled"])
    _require_bool(errors, document, ["legal_hold", "bypass_allowed"])
    _require_string_array(errors, document, ["legal_hold", "approver_roles"], allow_empty=False)
    _require_bool(errors, document, ["recovery_testing", "required"])
    _require_non_empty_string(errors, document, ["recovery_testing", "cadence"])
    _require_string_array(errors, document, ["recovery_testing", "operator_roles"], allow_empty=False)
    _require_bool(errors, document, ["migration", "local_history_supported"])
    _require_bool(errors, document, ["migration", "review_required"])
    _require_string_array(errors, document, ["migration", "operator_roles"], allow_empty=False)
    return errors


def _central_backup_policy_warnings(document: dict[str, Any]) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    if _backup_policy_value(document, ["legal_hold", "bypass_allowed"], False) is True:
        warnings.append(
            {
                "code": "legal_hold_bypass_allowed",
                "message": "Legal hold bypass is allowed by policy; review before shared use.",
                "path": ["legal_hold", "bypass_allowed"],
            }
        )
    return warnings


def _central_backup_policy_source_hash(document: dict[str, Any]) -> str:
    canonical = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _central_backup_policy_provenance(document: dict[str, Any] | None, source_hash: str | None) -> dict[str, Any]:
    provenance = document.get("provenance") if document else None
    if not isinstance(provenance, dict):
        provenance = {}
    reviewed_by = provenance.get("reviewed_by", [])
    approved_by = provenance.get("approved_by", [])
    return {
        "author": provenance.get("author"),
        "reviewed_by": reviewed_by if isinstance(reviewed_by, list) else [],
        "approved_by": approved_by if isinstance(approved_by, list) else [],
        "source": provenance.get("source"),
        "source_hash": source_hash,
        "review_recorded": isinstance(reviewed_by, list) and bool(reviewed_by),
        "approval_recorded": isinstance(approved_by, list) and bool(approved_by),
    }


def _central_backup_actor_roles(config: AppConfig, actor: str | None) -> list[str]:
    if not actor:
        return []
    record = _configured_actor(config, actor)
    if not record:
        return []
    return [role for role in record.get("roles", []) if isinstance(role, str)]


def _central_backup_required_roles(document: dict[str, Any] | None, operation_policy: dict[str, Any] | None) -> list[str]:
    if not document or not operation_policy:
        return []
    section = operation_policy["section"]
    role_field = operation_policy["role_field"]
    roles = _backup_policy_value(document, [str(section), str(role_field)], [])
    if isinstance(roles, list):
        return [role for role in roles if isinstance(role, str)]
    return []


def _central_backup_policy_status(
    *,
    policy_valid: bool,
    operation: str | None,
    operation_known: bool,
    actor: str | None,
    actor_known: bool,
    operation_allowed: bool,
) -> str:
    if not policy_valid:
        return "policy_unavailable"
    if operation and not operation_known:
        return "unknown_operation"
    if actor and not actor_known:
        return "actor_unbound"
    if operation and actor and operation_allowed:
        return "would_allow"
    if operation and actor:
        return "would_block"
    if operation:
        return "validated_without_actor"
    return "validated"


def _backup_policy_value(document: dict[str, Any] | None, path: list[str], default: Any = None) -> Any:
    value: Any = document
    for part in path:
        if not isinstance(value, dict) or part not in value:
            return default
        value = value[part]
    return value


def _require_non_empty_string(errors: list[dict[str, Any]], document: dict[str, Any], path: list[str]) -> None:
    value = _backup_policy_value(document, path)
    if not isinstance(value, str) or not value.strip():
        errors.append({"code": f"{'_'.join(path)}_missing", "message": ".".join(path) + " must be a non-empty string.", "path": path})


def _require_string_array(
    errors: list[dict[str, Any]],
    document: dict[str, Any],
    path: list[str],
    *,
    allow_empty: bool,
) -> None:
    value = _backup_policy_value(document, path)
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value) or (not allow_empty and not value):
        errors.append({"code": f"{'_'.join(path)}_invalid", "message": ".".join(path) + " must be an array of strings.", "path": path})


def _require_bool(errors: list[dict[str, Any]], document: dict[str, Any], path: list[str]) -> None:
    value = _backup_policy_value(document, path)
    if not isinstance(value, bool):
        errors.append({"code": f"{'_'.join(path)}_invalid", "message": ".".join(path) + " must be true or false.", "path": path})


def _require_positive_int(errors: list[dict[str, Any]], document: dict[str, Any], path: list[str]) -> None:
    value = _backup_policy_value(document, path)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        errors.append({"code": f"{'_'.join(path)}_invalid", "message": ".".join(path) + " must be an integer >= 1.", "path": path})


def _central_backup_blocker(code: str, description: str, category: str) -> dict[str, Any]:
    return {
        "code": code,
        "severity": "blocking",
        "category": category,
        "description": description,
        "required_before": "centralized_backup_restore_policy",
    }


def _enforcement_reasons(
    *,
    known_command: bool,
    would_block_if_enforced: bool,
    permission_reasons: list[str],
    audit_required: bool,
) -> list[str]:
    reasons: list[str] = []
    if not known_command:
        reasons.append("unknown_command")
    if would_block_if_enforced:
        reasons.append("role_would_be_blocked")
    if audit_required:
        reasons.append("audit_required_for_future_enforcement")
    reasons.append("dry_run_only")
    for reason in permission_reasons:
        if reason not in reasons:
            reasons.append(reason)
    return reasons


def _permission_reasons(
    *,
    enforced: bool,
    known_operation: bool,
    known_role: bool,
    would_allow: bool,
    required_access: str | None,
) -> list[str]:
    reasons: list[str] = []
    if not known_operation:
        reasons.append("unknown_operation")
    if not known_role:
        reasons.append("unknown_role")
    if known_operation and known_role and not would_allow:
        reasons.append(f"role_missing_access:{required_access}")
    if not enforced:
        reasons.append("governance_disabled_not_enforced")
    return reasons
