from __future__ import annotations

import platform
import sys
from pathlib import Path
from typing import Any

from .agent_interface import (
    AGENT_INTERFACE_CONTRACT_VERSION,
    AGENT_RETRIEVAL_CONTRACT_VERSION,
    AgentRetrievalRequest,
    agent_manifest,
    agent_retrieve,
)
from .app_config import load_app_config
from .backup_manifest import verify_backup_manifest, write_backup_manifest
from .client_interface import (
    CLIENT_EXPORT_PREVIEW_CONTRACT_VERSION,
    CLIENT_INTERFACE_CONTRACT_VERSION,
    CLIENT_OVERVIEW_CONTRACT_VERSION,
    CLIENT_SESSION_CONTRACT_VERSION,
    CLIENT_WARNINGS_CONTRACT_VERSION,
    blocked_client_export_preview,
    client_export_preview,
    client_manifest,
    client_overview,
    client_session_detail,
    client_warnings_detail,
)
from .client_runtime import CLIENT_TUI_RUNTIME_CONTRACT_VERSION, client_tui_runtime
from .codex_hooks import build_codex_hook_config, handle_codex_hook_payload
from .config import default_codex_home, discover_session_dirs
from .database import (
    SCHEMA_VERSION,
    backup_database,
    connect,
    get_events_filtered,
    get_project_sessions,
    get_session,
    init_db,
    list_sessions,
    list_warnings,
    reindex_fts,
    verify_database_backup,
    warning_summary,
)
from .database import (
    doctor as database_doctor,
)
from .database import (
    stats as database_stats,
)
from .database import (
    vacuum as database_vacuum,
)
from .export_targets import ExportTargetRequest, export_target, preview_export_target
from .exporter import export_project_markdown, export_session
from .governance import (
    AUDIT_APPEND_COMMAND,
    AUDIT_LIST_COMMAND,
    BUSINESS_COMMAND_INSTRUMENTATION_COMMAND,
    CENTRAL_BACKUP_POLICY_COMMAND,
    CENTRAL_BACKUP_READINESS_COMMAND,
    CENTRAL_POLICY_READINESS_COMMAND,
    CENTRAL_POLICY_STORE_COMMAND,
    CENTRALIZED_AUDIT_READINESS_COMMAND,
    CENTRALIZED_AUDIT_STORE_COMMAND,
    ENFORCEMENT_CHECK_COMMAND,
    ENFORCEMENT_GAPS_COMMAND,
    EXPORT_BACKUP_PREFLIGHT_COMMAND,
    EXPORT_PREVIEW_PREFLIGHT_COMMAND,
    EXTERNAL_MODEL_PREFLIGHT_COMMAND,
    GOVERNANCE_AUDIT_APPEND_CONTRACT_VERSION,
    GOVERNANCE_AUDIT_LIST_CONTRACT_VERSION,
    GOVERNANCE_BUSINESS_COMMAND_INSTRUMENTATION_CONTRACT_VERSION,
    GOVERNANCE_CENTRAL_BACKUP_POLICY_CONTRACT_VERSION,
    GOVERNANCE_CENTRAL_BACKUP_READINESS_CONTRACT_VERSION,
    GOVERNANCE_CENTRAL_POLICY_READINESS_CONTRACT_VERSION,
    GOVERNANCE_CENTRAL_POLICY_STORE_CONTRACT_VERSION,
    GOVERNANCE_CENTRALIZED_AUDIT_READINESS_CONTRACT_VERSION,
    GOVERNANCE_CENTRALIZED_AUDIT_STORE_CONTRACT_VERSION,
    GOVERNANCE_ENFORCEMENT_CHECK_CONTRACT_VERSION,
    GOVERNANCE_ENFORCEMENT_GAPS_CONTRACT_VERSION,
    GOVERNANCE_EXPORT_BACKUP_PREFLIGHT_CONTRACT_VERSION,
    GOVERNANCE_EXPORT_PREVIEW_PREFLIGHT_CONTRACT_VERSION,
    GOVERNANCE_EXTERNAL_MODEL_PREFLIGHT_CONTRACT_VERSION,
    GOVERNANCE_IDENTITY_ACTOR_BINDING_CONTRACT_VERSION,
    GOVERNANCE_IDENTITY_ACTOR_READINESS_CONTRACT_VERSION,
    GOVERNANCE_PERMISSION_CHECK_CONTRACT_VERSION,
    GOVERNANCE_POLICY_READINESS_CONTRACT_VERSION,
    GOVERNANCE_RAW_READ_PREFLIGHT_CONTRACT_VERSION,
    GOVERNANCE_RESTORE_RETENTION_PREFLIGHT_CONTRACT_VERSION,
    GOVERNANCE_SERVER_POLICY_READINESS_CONTRACT_VERSION,
    GOVERNANCE_STATUS_CONTRACT_VERSION,
    GOVERNANCE_SUMMARY_SEARCH_PREFLIGHT_CONTRACT_VERSION,
    GOVERNANCE_V3_ACCEPTANCE_SMOKE_CONTRACT_VERSION,
    GOVERNANCE_V3_COMPLETION_GAP_AUDIT_CONTRACT_VERSION,
    IDENTITY_ACTOR_BINDING_COMMAND,
    IDENTITY_ACTOR_READINESS_COMMAND,
    PERMISSION_CHECK_COMMAND,
    POLICY_READINESS_COMMAND,
    RAW_READ_PREFLIGHT_COMMAND,
    RESTORE_RETENTION_PREFLIGHT_COMMAND,
    SERVER_POLICY_READINESS_COMMAND,
    SUMMARY_SEARCH_PREFLIGHT_COMMAND,
    V3_ACCEPTANCE_SMOKE_COMMAND,
    V3_COMPLETION_GAP_AUDIT_COMMAND,
    append_audit_record,
    check_permission,
    governance_business_command_instrumentation,
    governance_central_backup_policy,
    governance_central_backup_readiness,
    governance_central_policy_readiness,
    governance_central_policy_store,
    governance_centralized_audit_readiness,
    governance_centralized_audit_store,
    governance_enforcement_check,
    governance_enforcement_gaps,
    governance_export_backup_preflight,
    governance_export_preview_preflight,
    governance_external_model_preflight,
    governance_identity_actor_binding,
    governance_identity_actor_readiness,
    governance_policy_readiness,
    governance_raw_read_preflight,
    governance_restore_retention_preflight,
    governance_server_policy_readiness,
    governance_status,
    governance_summary_search_preflight,
    governance_v3_completion_gap_audit,
    list_audit_records,
)
from .hybrid_retrieval import HYBRID_RETRIEVAL_CONTRACT_VERSION, HybridRetrievalRequest, hybrid_retrieve
from .importer import import_codex_home, sample_codex_home
from .ingestion import IngestionRequest, enqueue_ingestion, list_ingestion_queue, process_ingestion_queue
from .mcp_contracts import MCP_MANIFEST_CONTRACT_VERSION, MCP_PROTOCOL_VERSION
from .models import SearchResult, SessionRow, Summary
from .privacy import RULES_VERSION, effective_findings, scan_sensitive_text
from .restore import restore_backup
from .restore_history import latest_restore_history, list_restore_history, prune_restore_history
from .restore_plan import build_restore_plan
from .retrieval import RETRIEVAL_CONTRACT_VERSION, RETRIEVAL_MODES, RetrievalQuery, build_retrieval_diagnostics, retrieve, retrieve_response
from .schemas import CONTRACT_VERSION, contract_schemas
from .shared_server import (
    READ_ONLY_SERVER_MANIFEST_COMMAND,
    READ_ONLY_SERVER_MANIFEST_CONTRACT_VERSION,
    READ_ONLY_SERVER_SMOKE_COMMAND,
    READ_ONLY_SERVER_SMOKE_CONTRACT_VERSION,
    read_only_server_smoke,
    shared_server_manifest,
)
from .state import inspect_state
from .summarizer import build_summary
from .summary_pipeline import SUMMARY_CHUNKS_CONTRACT_VERSION, SummaryChunkRequest, build_summary_chunks
from .vector_adapter import (
    DEFAULT_VECTOR_DIMENSIONS,
    LOCAL_VECTOR_ADAPTER,
    VECTOR_CONTRACT_VERSION,
    VectorIndexRequest,
    build_vector_index,
    query_vector_index,
    vector_index_status,
)

PERSONAL_UI_HEALTH_CONTRACT_VERSION = "personal_ui_health.v1"
PERSONAL_UI_ACTION_CONTRACT_VERSION = "personal_ui_action.v1"
PERSONAL_UI_SMOKE_CONTRACT_VERSION = "personal_ui_smoke.v1"
PERSONAL_UI_SERVE_COMMAND = "threadvault ui serve --host 127.0.0.1 --port 8766 --open"
PERSONAL_UI_SMOKE_COMMAND = "threadvault ui smoke --json"


class ArchiveStore:
    """Small interface over ThreadVault's SQLite implementation."""

    def __init__(self, db_path: Path):
        self.db_path = db_path.expanduser()

    def init(self) -> None:
        with connect(self.db_path) as conn:
            init_db(conn)

    def import_codex(self, codex_home: Path | None = None):
        with connect(self.db_path) as conn:
            init_db(conn)
            return import_codex_home(conn, codex_home)

    def enqueue_ingestion(self, source: str = "manual", codex_home: Path | None = None, reason: str = "scan") -> dict[str, Any]:
        with connect(self.db_path) as conn:
            init_db(conn)
            return enqueue_ingestion(conn, IngestionRequest(source=source, codex_home=codex_home, reason=reason))

    def list_ingestion_queue(self, status: str | None = None, limit: int = 50) -> dict[str, Any]:
        with connect(self.db_path) as conn:
            init_db(conn)
            return list_ingestion_queue(conn, status=status, limit=limit)

    def process_ingestion_queue(self, codex_home: Path | None = None, limit: int = 10, apply: bool = False) -> dict[str, Any]:
        with connect(self.db_path) as conn:
            init_db(conn)
            return process_ingestion_queue(conn, codex_home=codex_home, limit=limit, apply=apply)

    def handle_codex_hook(self, payload: dict[str, Any], codex_home: Path | None = None) -> dict[str, Any]:
        with connect(self.db_path) as conn:
            init_db(conn)
            return handle_codex_hook_payload(conn, payload, codex_home=codex_home)

    def codex_hook_config(self, command: str, timeout: int = 10, status_message: str = "Queueing ThreadVault ingestion") -> dict[str, Any]:
        return build_codex_hook_config(command, timeout=timeout, status_message=status_message)

    def list(self, limit: int = 50, cwd: str | None = None) -> list[SessionRow]:
        with connect(self.db_path) as conn:
            return list_sessions(conn, limit=limit, cwd=cwd)

    def search(
        self,
        query: str,
        limit: int = 20,
        session_id: str | None = None,
        cwd: str | None = None,
        since: str | None = None,
        until: str | None = None,
        top_type: str | None = None,
        tool: str | None = None,
        fields: str = "standard",
    ) -> list[SearchResult]:
        with connect(self.db_path) as conn:
            return retrieve(
                conn,
                RetrievalQuery(
                    text=query,
                    limit=limit,
                    session_id=session_id,
                    cwd=cwd,
                    since=since,
                    until=until,
                    top_type=top_type,
                    tool=tool,
                    fields=fields,
                ),
            )

    def retrieve(
        self,
        query: str,
        limit: int = 20,
        session_id: str | None = None,
        cwd: str | None = None,
        since: str | None = None,
        until: str | None = None,
        top_type: str | None = None,
        tool: str | None = None,
        fields: str = "standard",
        mode: str = "fts",
    ) -> dict[str, Any]:
        with connect(self.db_path) as conn:
            response = retrieve_response(
                conn,
                RetrievalQuery(
                    text=query,
                    limit=limit,
                    session_id=session_id,
                    cwd=cwd,
                    since=since,
                    until=until,
                    top_type=top_type,
                    tool=tool,
                    fields=fields,
                    mode=mode,
                ),
            )
            return response.to_payload()

    def retrieval_diagnostics(self) -> dict[str, Any]:
        with connect(self.db_path) as conn:
            init_db(conn)
            diagnostics = build_retrieval_diagnostics(conn)
        return {
            "contract_version": RETRIEVAL_CONTRACT_VERSION,
            "diagnostics": diagnostics.to_payload(),
        }

    def hybrid_retrieve(
        self,
        query: str,
        config_path: Path | None = None,
        limit: int = 20,
        vector_limit: int = 10,
        session_id: str | None = None,
        cwd: str | None = None,
        since: str | None = None,
        until: str | None = None,
        top_type: str | None = None,
        tool: str | None = None,
    ) -> dict[str, Any]:
        with connect(self.db_path) as conn:
            init_db(conn)
            return hybrid_retrieve(
                conn,
                HybridRetrievalRequest(
                    text=query,
                    limit=limit,
                    vector_limit=vector_limit,
                    session_id=session_id,
                    cwd=cwd,
                    since=since,
                    until=until,
                    top_type=top_type,
                    tool=tool,
                ),
                load_app_config(config_path),
            )

    def agent_manifest(self, config_path: Path | None = None) -> dict[str, Any]:
        return agent_manifest(load_app_config(config_path))

    def client_manifest(self, config_path: Path | None = None) -> dict[str, Any]:
        return client_manifest(load_app_config(config_path), capabilities(), robot_guide())

    def governance_status(self, config_path: Path | None = None) -> dict[str, Any]:
        return governance_status(load_app_config(config_path))

    def governance_audit_append(
        self,
        log_path: Path,
        *,
        operation: str,
        actor: str,
        status: str,
        target_type: str,
        target_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return append_audit_record(
            log_path,
            operation=operation,
            actor=actor,
            status=status,
            target_type=target_type,
            target_id=target_id,
            metadata=metadata,
        )

    def governance_audit_list(self, log_path: Path, limit: int = 50) -> dict[str, Any]:
        return list_audit_records(log_path, limit=limit)

    def governance_centralized_audit_store(
        self,
        config_path: Path | None = None,
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
        return governance_centralized_audit_store(
            load_app_config(config_path),
            action=action,
            store_path=store_path,
            operation=operation,
            actor=actor,
            status=status,
            target_type=target_type,
            target_id=target_id,
            metadata=metadata,
            limit=limit,
        )

    def governance_permission_check(
        self,
        config_path: Path | None = None,
        *,
        operation: str,
        role: str,
        audit_log: Path | None = None,
        actor: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
    ) -> dict[str, Any]:
        return check_permission(
            load_app_config(config_path),
            operation=operation,
            role=role,
            audit_log=audit_log,
            actor=actor,
            target_type=target_type,
            target_id=target_id,
        )

    def governance_enforcement_gaps(self, config_path: Path | None = None) -> dict[str, Any]:
        return governance_enforcement_gaps(load_app_config(config_path))

    def governance_enforcement_check(
        self,
        config_path: Path | None = None,
        *,
        command: str,
        role: str,
        audit_log: Path | None = None,
        actor: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
    ) -> dict[str, Any]:
        return governance_enforcement_check(
            load_app_config(config_path),
            command=command,
            role=role,
            audit_log=audit_log,
            actor=actor,
            target_type=target_type,
            target_id=target_id,
        )

    def governance_business_command_instrumentation(
        self,
        config_path: Path | None = None,
        *,
        command: str,
        role: str,
        audit_log: Path | None = None,
        actor: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
    ) -> dict[str, Any]:
        return governance_business_command_instrumentation(
            load_app_config(config_path),
            command=command,
            role=role,
            audit_log=audit_log,
            actor=actor,
            target_type=target_type,
            target_id=target_id,
        )

    def governance_policy_readiness(self, config_path: Path | None = None) -> dict[str, Any]:
        return governance_policy_readiness(load_app_config(config_path))

    def governance_server_policy_readiness(self, config_path: Path | None = None) -> dict[str, Any]:
        return governance_server_policy_readiness(load_app_config(config_path))

    def governance_read_only_server_manifest(self, config_path: Path | None = None) -> dict[str, Any]:
        return shared_server_manifest(load_app_config(config_path), db_path=self.db_path)

    def governance_read_only_server_smoke(self, config_path: Path | None = None, query: str = "pytest") -> dict[str, Any]:
        return read_only_server_smoke(self, config_path=config_path, query=query)

    def governance_centralized_audit_readiness(self, config_path: Path | None = None) -> dict[str, Any]:
        return governance_centralized_audit_readiness(load_app_config(config_path))

    def governance_v3_completion_gap_audit(self, config_path: Path | None = None) -> dict[str, Any]:
        return governance_v3_completion_gap_audit(load_app_config(config_path))

    def governance_v3_acceptance_smoke(
        self,
        config_path: Path | None = None,
        *,
        query: str = "pytest",
        session_id: str = "sess-current",
        work_dir: Path | None = None,
    ) -> dict[str, Any]:
        smoke_dir = (work_dir or self.db_path.parent / "threadvault-v3-smoke").expanduser()
        smoke_dir.mkdir(parents=True, exist_ok=True)
        governance_config = config_path or smoke_dir / "threadvault-governance.toml"
        if config_path is None:
            governance_config.write_text("[governance]\nenabled = true\n", encoding="utf-8")
        audit_log = smoke_dir / "governance-smoke-audit.jsonl"
        backup_out = smoke_dir / "reader-blocked-backup.db"

        checks: list[dict[str, Any]] = []

        def add_check(code: str, category: str, ok: bool, evidence: dict[str, Any], message: str, required: bool = True) -> None:
            checks.append(
                {
                    "code": code,
                    "category": category,
                    "ok": ok,
                    "required": required,
                    "message": message,
                    "evidence": evidence,
                }
            )

        gap_audit = self.governance_v3_completion_gap_audit()
        capabilities_payload = capabilities()
        guide = robot_guide()
        schemas = robot_schemas()

        add_check(
            "local_first_defaults",
            "boundary",
            bool(
                gap_audit["governance"]["server_required"] is False
                and gap_audit["governance"]["server_opt_in"] is True
                and gap_audit["governance"]["cloud_sync"] is False
                and capabilities_payload["feature_flags"]["local_first"] is True
                and capabilities_payload["feature_flags"]["cloud_sync"] is False
            ),
            {
                "server_required": gap_audit["governance"]["server_required"],
                "server_opt_in": gap_audit["governance"]["server_opt_in"],
                "cloud_sync": gap_audit["governance"]["cloud_sync"],
            },
            "CLI and governance defaults remain local-first and server/cloud opt-in.",
        )

        retrieval = self.retrieve(query=query, limit=5)
        hybrid = self.hybrid_retrieve(query=query, limit=5)
        agent = self.agent_retrieve(query=query, limit=5)
        vector = self.vector_status()
        add_check(
            "accepted_v2_retrieval_reused",
            "v2_retrieval",
            bool(
                retrieval["results"]
                and retrieval["diagnostics"]["used_mode"] == "fts"
                and hybrid["results"]
                and hybrid["diagnostics"]["capabilities_used"] == ["fts", "hybrid"]
                and agent["results"]
                and agent["privacy"]["raw_paths_included"] is False
                and vector["config"]["enabled"] is False
            ),
            {
                "retrieval_results": len(retrieval["results"]),
                "hybrid_capabilities": hybrid["diagnostics"]["capabilities_used"],
                "agent_raw_paths_included": agent["privacy"]["raw_paths_included"],
                "vector_enabled_by_default": vector["config"]["enabled"],
            },
            "Accepted v2 retrieval, hybrid, vector default, and agent interface still work.",
        )

        manifest = self.client_manifest()
        overview = self.client_overview(query=query, limit=5)
        tui = self.client_tui_runtime(query=query, limit=5, export_preview_session=session_id, export_preview_out=smoke_dir / "preview")
        add_check(
            "richer_client_runtime",
            "client",
            bool(
                manifest["defaults"]["server_required"] is False
                and overview["sessions"]
                and overview["search"]["results"]
                and tui["runtime"]["status"] == "accepted_minimal_runtime"
                and tui["export_preview"] is not None
                and tui["privacy"]["export_preview_writes_files"] is False
            ),
            {
                "sessions": len(overview["sessions"]),
                "search_results": len(overview["search"]["results"]),
                "tui_status": tui["runtime"]["status"],
                "export_preview_writes_files": tui["privacy"]["export_preview_writes_files"],
            },
            "Richer local client can browse, search, and preview exports without writing files.",
        )

        read_only = self.governance_read_only_server_smoke(query=query)
        add_check(
            "optional_read_only_server",
            "server",
            bool(
                read_only["ok"]
                and read_only["governance"]["server_required"] is False
                and read_only["governance"]["server_opt_in"] is True
                and read_only["summary"]["failed_route_count"] == 0
            ),
            {
                "ok": read_only["ok"],
                "checked_route_count": read_only["summary"]["checked_route_count"],
                "server_required": read_only["governance"]["server_required"],
                "server_opt_in": read_only["governance"]["server_opt_in"],
            },
            "Optional read-only server prototype passes in-process smoke without becoming required.",
        )

        raw_block = self.governance_business_command_instrumentation(
            config_path=governance_config,
            command="threadvault client session",
            role="reader",
            actor="reader@example",
            target_type="session",
            target_id=session_id,
        )
        search_allow = self.governance_business_command_instrumentation(
            config_path=governance_config,
            command="threadvault retrieval query",
            role="reader",
            actor="reader@example",
            target_type="query",
            target_id=query,
        )
        backup_block = self.governance_business_command_instrumentation(
            config_path=governance_config,
            command="threadvault backup",
            role="reader",
            actor="reader@example",
            audit_log=audit_log,
            target_type="backup",
            target_id=str(backup_out),
        )
        add_check(
            "governance_access_separation_and_instrumentation",
            "governance",
            bool(
                raw_block["instrumentation"]["blocked"]
                and not search_allow["instrumentation"]["blocked"]
                and backup_block["instrumentation"]["blocked"]
                and backup_block["audit"]["preflight_record_written"] is True
                and not backup_out.exists()
            ),
            {
                "raw_read_blocked_for_reader": raw_block["instrumentation"]["blocked"],
                "summary_search_allowed_for_reader": not search_allow["instrumentation"]["blocked"],
                "backup_blocked_for_reader": backup_block["instrumentation"]["blocked"],
                "audit_written": backup_block["audit"]["preflight_record_written"],
                "blocked_backup_exists": backup_out.exists(),
            },
            "Governance separates raw read from summary/search and blocks denied side effects before execution.",
        )

        add_check(
            "governance_runtime_discovery",
            "governance",
            bool(
                self.governance_identity_actor_readiness()["identity_provider"]["implemented"]
                and self.governance_central_policy_readiness()["central_policy"]["store_implemented"]
                and self.governance_centralized_audit_readiness()["centralized_audit"]["store_implemented"]
                and self.governance_central_backup_readiness()["policy"]["backup_policy_implemented"]
                and self.governance_server_policy_readiness()["outbound_policy"]["default_external_calls_enabled"] is False
            ),
            {
                "identity_actor_binding": self.governance_identity_actor_readiness()["actor_binding"]["implemented"],
                "central_policy_store": self.governance_central_policy_readiness()["central_policy"]["store_implemented"],
                "centralized_audit_store": self.governance_centralized_audit_readiness()["centralized_audit"]["store_implemented"],
                "central_backup_policy": self.governance_central_backup_readiness()["policy"]["backup_policy_implemented"],
                "external_calls_enabled_by_default": self.governance_server_policy_readiness()["outbound_policy"][
                    "default_external_calls_enabled"
                ],
            },
            "Governance runtimes are discoverable and external model calls stay disabled by default.",
        )

        phase_docs = [
            Path("docs/progress/archive/legacy-v3/README.md"),
            Path("docs/progress/archive/legacy-v3/phases/phase-33-v3-final-acceptance-smoke/plan.md"),
            Path("docs/progress/archive/legacy-v3/phases/phase-33-v3-final-acceptance-smoke/design-notes.md"),
            Path("docs/progress/archive/legacy-v3/phases/phase-33-v3-final-acceptance-smoke/acceptance.md"),
        ]
        add_check(
            "discovery_schema_and_docs",
            "contracts",
            bool(
                "governance v3 acceptance-smoke" in capabilities_payload["json_outputs"]
                and capabilities_payload["feature_flags"]["governance_v3_acceptance_smoke"] is True
                and guide["governance"]["v3_acceptance_smoke_schema"] == "governance_v3_acceptance_smoke"
                and "governance_v3_acceptance_smoke" in schemas
                and all(path.exists() for path in phase_docs)
                and not Path("deep-research-report.md").exists()
            ),
            {
                "json_output_registered": "governance v3 acceptance-smoke" in capabilities_payload["json_outputs"],
                "schema_registered": "governance_v3_acceptance_smoke" in schemas,
                "phase_docs_present": all(path.exists() for path in phase_docs),
                "deep_research_report_absent": not Path("deep-research-report.md").exists(),
            },
            "Discovery, schema summaries, phase docs, and retired root report invariant are present.",
        )

        required_checks = [check for check in checks if check["required"]]
        failed_checks = [check for check in required_checks if not check["ok"]]
        criteria = [
            {
                "code": "local_cli_without_server",
                "status": "satisfied" if checks[0]["ok"] else "failed",
                "evidence": ["local_first_defaults", "accepted_v2_retrieval_reused"],
            },
            {
                "code": "richer_client_browse_search_export",
                "status": "satisfied" if checks[2]["ok"] else "failed",
                "evidence": ["richer_client_runtime"],
            },
            {
                "code": "shared_access_separation",
                "status": "satisfied" if checks[3]["ok"] and checks[4]["ok"] else "failed",
                "evidence": ["optional_read_only_server", "governance_access_separation_and_instrumentation"],
            },
            {
                "code": "audit_records_for_sensitive_operations",
                "status": "satisfied" if checks[4]["ok"] and checks[5]["ok"] else "failed",
                "evidence": ["governance_access_separation_and_instrumentation", "governance_runtime_discovery"],
            },
            {
                "code": "external_model_cloud_explicit",
                "status": "satisfied" if checks[0]["ok"] and checks[5]["ok"] else "failed",
                "evidence": ["local_first_defaults", "governance_runtime_discovery"],
            },
        ]
        ok = not failed_checks and all(item["status"] == "satisfied" for item in criteria)
        return {
            "contract_version": GOVERNANCE_V3_ACCEPTANCE_SMOKE_CONTRACT_VERSION,
            "status": "accepted" if ok else "failed",
            "ok": ok,
            "governance": {
                "server_required": False,
                "server_opt_in": True,
                "cloud_sync": False,
                "team_capabilities_opt_in": True,
                "production_shared_enforcement_claimed": False,
            },
            "checks": checks,
            "summary": {
                "required_check_count": len(required_checks),
                "passed_check_count": len(required_checks) - len(failed_checks),
                "failed_check_count": len(failed_checks),
                "criteria_count": len(criteria),
                "criteria_satisfied_count": len([item for item in criteria if item["status"] == "satisfied"]),
            },
            "criteria": criteria,
            "gap_audit": {
                "current": {
                    "accepted_phase_count": gap_audit["completion"]["accepted_phase_count"],
                    "current_phase": gap_audit["completion"]["current_phase"],
                    "blocking_count": gap_audit["completion"]["blocking_count"],
                    "v3_complete": gap_audit["completion"]["v3_complete"],
                }
            },
            "diagnostics": {
                "db_path": str(self.db_path),
                "work_dir": str(smoke_dir),
                "config_path": str(governance_config),
                "query": query,
                "session_id": session_id,
                "local_first": True,
                "privacy_first": True,
                "server_required": False,
                "server_opt_in": True,
                "cloud_sync": False,
                "v2_retrieval_core_changed": False,
                "deep_research_report_retired": not Path("deep-research-report.md").exists(),
            },
        }

    def governance_identity_actor_readiness(self, config_path: Path | None = None) -> dict[str, Any]:
        return governance_identity_actor_readiness(load_app_config(config_path))

    def governance_identity_actor_binding(
        self,
        config_path: Path | None = None,
        *,
        actor: str,
        command: str | None = None,
        operation: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        client_id: str | None = None,
        audit_log: Path | None = None,
    ) -> dict[str, Any]:
        return governance_identity_actor_binding(
            load_app_config(config_path),
            actor=actor,
            command=command,
            operation=operation,
            target_type=target_type,
            target_id=target_id,
            client_id=client_id,
            audit_log=audit_log,
        )

    def governance_central_policy_readiness(self, config_path: Path | None = None) -> dict[str, Any]:
        return governance_central_policy_readiness(load_app_config(config_path))

    def governance_central_policy_store(
        self,
        config_path: Path | None = None,
        *,
        policy_path: Path | None = None,
        actor: str | None = None,
        operation: str | None = None,
    ) -> dict[str, Any]:
        return governance_central_policy_store(
            load_app_config(config_path),
            policy_path=policy_path,
            actor=actor,
            operation=operation,
        )

    def governance_central_backup_readiness(self, config_path: Path | None = None) -> dict[str, Any]:
        return governance_central_backup_readiness(load_app_config(config_path))

    def governance_central_backup_policy(
        self,
        config_path: Path | None = None,
        *,
        policy_path: Path | None = None,
        operation: str | None = None,
        actor: str | None = None,
    ) -> dict[str, Any]:
        return governance_central_backup_policy(
            load_app_config(config_path),
            policy_path=policy_path,
            operation=operation,
            actor=actor,
        )

    def governance_export_backup_preflight(
        self,
        config_path: Path | None = None,
        *,
        command: str,
        role: str,
        audit_log: Path | None = None,
        actor: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
    ) -> dict[str, Any]:
        return governance_export_backup_preflight(
            load_app_config(config_path),
            command=command,
            role=role,
            audit_log=audit_log,
            actor=actor,
            target_type=target_type,
            target_id=target_id,
        )

    def governance_restore_retention_preflight(
        self,
        config_path: Path | None = None,
        *,
        command: str,
        role: str,
        audit_log: Path | None = None,
        actor: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
    ) -> dict[str, Any]:
        return governance_restore_retention_preflight(
            load_app_config(config_path),
            command=command,
            role=role,
            audit_log=audit_log,
            actor=actor,
            target_type=target_type,
            target_id=target_id,
        )

    def governance_raw_read_preflight(
        self,
        config_path: Path | None = None,
        *,
        command: str,
        role: str,
        audit_log: Path | None = None,
        actor: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
    ) -> dict[str, Any]:
        return governance_raw_read_preflight(
            load_app_config(config_path),
            command=command,
            role=role,
            audit_log=audit_log,
            actor=actor,
            target_type=target_type,
            target_id=target_id,
        )

    def governance_summary_search_preflight(
        self,
        config_path: Path | None = None,
        *,
        command: str,
        role: str,
        audit_log: Path | None = None,
        actor: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
    ) -> dict[str, Any]:
        return governance_summary_search_preflight(
            load_app_config(config_path),
            command=command,
            role=role,
            audit_log=audit_log,
            actor=actor,
            target_type=target_type,
            target_id=target_id,
        )

    def governance_export_preview_preflight(
        self,
        config_path: Path | None = None,
        *,
        command: str,
        role: str,
        audit_log: Path | None = None,
        actor: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
    ) -> dict[str, Any]:
        return governance_export_preview_preflight(
            load_app_config(config_path),
            command=command,
            role=role,
            audit_log=audit_log,
            actor=actor,
            target_type=target_type,
            target_id=target_id,
        )

    def governance_external_model_preflight(
        self,
        config_path: Path | None = None,
        *,
        command: str,
        role: str,
        audit_log: Path | None = None,
        actor: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
    ) -> dict[str, Any]:
        return governance_external_model_preflight(
            load_app_config(config_path),
            command=command,
            role=role,
            audit_log=audit_log,
            actor=actor,
            target_type=target_type,
            target_id=target_id,
        )

    def client_overview(
        self,
        config_path: Path | None = None,
        query: str | None = None,
        cwd: str | None = None,
        limit: int = 20,
        local_debug: bool = False,
    ) -> dict[str, Any]:
        with connect(self.db_path) as conn:
            init_db(conn)
            sessions = list_sessions(conn, limit=limit, cwd=cwd)
            return client_overview(
                conn,
                sessions=sessions,
                config=load_app_config(config_path),
                query=query,
                cwd=cwd,
                limit=limit,
                local_debug=local_debug,
            )

    def client_session(
        self,
        session_id: str,
        event_limit: int = 20,
        max_chars: int = 500,
        local_debug: bool = False,
    ) -> dict[str, Any]:
        with connect(self.db_path) as conn:
            init_db(conn)
            session = get_session(conn, session_id)
            if session is None:
                raise KeyError(session_id)
            events = get_events_filtered(conn, session_id)
            warning_count = len(list_warnings(conn, session_id=session_id, limit=100000))
            summary = build_summary(session, events)
            session_payload = dict(session)
            session_payload["event_count"] = len(events)
            session_payload["warning_count"] = warning_count
            return client_session_detail(
                session=session_payload,
                summary=summary,
                events=events,
                event_limit=event_limit,
                max_chars=max_chars,
                local_debug=local_debug,
            )

    def client_export_preview(
        self,
        out_dir: Path,
        profile: str = "markdown",
        session_ids: list[str] | None = None,
        project: str | None = None,
        privacy_mode: str = "warn",
        privacy_config_path: Path | None = None,
        skill_name: str | None = None,
        skill_description: str | None = None,
        governance_role: str | None = None,
        governance_config_path: Path | None = None,
        governance_audit_log: Path | None = None,
        governance_actor: str | None = None,
    ) -> dict[str, Any]:
        request = ExportTargetRequest(
            out_dir=out_dir,
            profile=profile,
            session_ids=session_ids or [],
            project=project,
            privacy_mode=privacy_mode,
            privacy_config_path=privacy_config_path,
            skill_name=skill_name,
            skill_description=skill_description,
        )
        execute_command = _export_preview_execute_command(request)
        governance_instrumentation = None
        if governance_role is not None:
            preflight = governance_export_preview_preflight(
                load_app_config(governance_config_path),
                command="threadvault client export-preview",
                role=governance_role,
                audit_log=governance_audit_log,
                actor=governance_actor,
                target_type="client_export_preview",
                target_id=project or ",".join(session_ids or []) or str(out_dir),
            )
            blocked = bool(preflight["permission"]["enforced"] and not preflight["permission"]["allowed"])
            governance_instrumentation = {
                "enabled": True,
                "blocked": blocked,
                "reason": "preflight_blocked" if blocked else "preflight_allowed",
                "role": governance_role,
                "actor": governance_actor,
                "audit_log": str(governance_audit_log.expanduser()) if governance_audit_log else None,
                "preflight": preflight,
            }
            if blocked:
                return blocked_client_export_preview(
                    profile=profile,
                    out_dir=out_dir,
                    session_ids=session_ids or [],
                    project=project,
                    privacy_mode=privacy_mode,
                    execute_command=execute_command,
                    governance_instrumentation=governance_instrumentation,
                )
        with connect(self.db_path) as conn:
            init_db(conn)
            preview = preview_export_target(conn, request)
        if governance_instrumentation is not None:
            governance_instrumentation["preflight"]["execution"]["preview_generated"] = True
            governance_instrumentation["preflight"]["execution"]["manifest_returned"] = True
        return client_export_preview(preview, execute_command, governance_instrumentation=governance_instrumentation)

    def client_warnings(
        self,
        session_id: str,
        privacy_config_path: Path | None = None,
        local_debug: bool = False,
    ) -> dict[str, Any]:
        with connect(self.db_path) as conn:
            init_db(conn)
            session = get_session(conn, session_id)
            if session is None:
                raise KeyError(session_id)
            warnings = list_warnings(conn, session_id=session_id, limit=100000)
            session_payload = dict(session)
            session_payload["warning_count"] = len(warnings)
        return client_warnings_detail(
            session=session_payload,
            warnings=warnings,
            privacy_scan=self.privacy_scan(session_id, privacy_config_path=privacy_config_path),
            local_debug=local_debug,
        )

    def client_tui_runtime(
        self,
        config_path: Path | None = None,
        query: str | None = None,
        cwd: str | None = None,
        limit: int = 20,
        local_debug: bool = False,
        export_preview_session: str | None = None,
        export_preview_out: Path | None = None,
        export_preview_profile: str = "markdown",
    ) -> dict[str, Any]:
        overview = self.client_overview(
            config_path=config_path,
            query=query,
            cwd=cwd,
            limit=limit,
            local_debug=local_debug,
        )
        export_preview = None
        if export_preview_session is not None:
            export_preview = self.client_export_preview(
                out_dir=export_preview_out or Path("threadvault-export"),
                profile=export_preview_profile,
                session_ids=[export_preview_session],
            )
        return client_tui_runtime(overview=overview, export_preview=export_preview)

    def agent_retrieve(
        self,
        query: str,
        config_path: Path | None = None,
        mode: str = "hybrid",
        limit: int = 20,
        vector_limit: int = 10,
        session_id: str | None = None,
        cwd: str | None = None,
        since: str | None = None,
        until: str | None = None,
        top_type: str | None = None,
        tool: str | None = None,
        local_debug: bool = False,
    ) -> dict[str, Any]:
        with connect(self.db_path) as conn:
            init_db(conn)
            return agent_retrieve(
                conn,
                AgentRetrievalRequest(
                    text=query,
                    mode=mode,
                    limit=limit,
                    vector_limit=vector_limit,
                    session_id=session_id,
                    cwd=cwd,
                    since=since,
                    until=until,
                    top_type=top_type,
                    tool=tool,
                    local_debug=local_debug,
                ),
                load_app_config(config_path),
            )

    def warnings(self, limit: int = 50, session_id: str | None = None, code: str | None = None, raw_path: str | None = None):
        with connect(self.db_path) as conn:
            return list_warnings(conn, limit=limit, session_id=session_id, code=code, raw_path=raw_path)

    def warning_summary(self) -> list[dict[str, Any]]:
        with connect(self.db_path) as conn:
            init_db(conn)
            return warning_summary(conn)

    def stats(self) -> dict[str, Any]:
        with connect(self.db_path) as conn:
            init_db(conn)
            return database_stats(conn)

    def doctor(self, codex_home: Path | None = None) -> dict[str, Any]:
        home = (codex_home or default_codex_home()).expanduser()
        with connect(self.db_path) as conn:
            init_db(conn)
            result = database_doctor(conn)
        session_dirs = discover_session_dirs(home)
        readable_files = []
        missing_dirs = []
        for session_dir in session_dirs:
            if not session_dir.exists():
                missing_dirs.append(str(session_dir))
                continue
            readable_files.extend(str(path) for path in session_dir.rglob("*.jsonl") if path.is_file())
        state = inspect_state(home)
        result.update({
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "db_path": str(self.db_path),
            "codex_home": str(home),
            "session_dirs": [str(path) for path in session_dirs],
            "missing_session_dirs": missing_dirs,
            "jsonl_files": len(readable_files),
            "codex_state": state,
        })
        return result

    def summarize(self, session_id: str) -> Summary:
        with connect(self.db_path) as conn:
            session = get_session(conn, session_id)
            if session is None:
                raise KeyError(session_id)
            events = get_events_filtered(conn, session_id)
            return build_summary(session, events)

    def summary_chunks(
        self,
        session_ids: list[str] | None = None,
        project: str | None = None,
        max_chunks_per_session: int = 12,
        max_chars: int = 1200,
    ) -> dict[str, Any]:
        with connect(self.db_path) as conn:
            init_db(conn)
            return build_summary_chunks(
                conn,
                SummaryChunkRequest(
                    session_ids=session_ids or [],
                    project=project,
                    max_chunks_per_session=max_chunks_per_session,
                    max_chars=max_chars,
                ),
            )

    def vector_index(
        self,
        session_ids: list[str] | None = None,
        project: str | None = None,
        config_path: Path | None = None,
        max_chunks_per_session: int = 12,
        max_chars: int = 1200,
    ) -> dict[str, Any]:
        with connect(self.db_path) as conn:
            init_db(conn)
            return build_vector_index(
                conn,
                VectorIndexRequest(
                    session_ids=session_ids or [],
                    project=project,
                    max_chunks_per_session=max_chunks_per_session,
                    max_chars=max_chars,
                ),
                load_app_config(config_path),
            )

    def vector_query(self, query: str, config_path: Path | None = None, limit: int = 10) -> dict[str, Any]:
        with connect(self.db_path) as conn:
            init_db(conn)
            return query_vector_index(conn, query=query, config=load_app_config(config_path), limit=limit)

    def vector_status(self, config_path: Path | None = None) -> dict[str, Any]:
        with connect(self.db_path) as conn:
            init_db(conn)
            return vector_index_status(conn, load_app_config(config_path))

    def export_session(
        self,
        session_id: str,
        out_dir: Path,
        fmt: str = "md",
        profile: str = "full",
        brief: bool = False,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        last_turns: int | None = None,
        max_chars: int | None = None,
        max_tool_chars: int | None = None,
        no_tool_output: bool = False,
        no_reasoning: bool = False,
        privacy_mode: str = "warn",
        privacy_config_path: Path | None = None,
    ):
        include, exclude, last_turns, max_chars, max_tool_chars, no_tool_output, no_reasoning, brief = apply_export_profile(
            profile=profile,
            include=include,
            exclude=exclude,
            last_turns=last_turns,
            max_chars=max_chars,
            max_tool_chars=max_tool_chars,
            no_tool_output=no_tool_output,
            no_reasoning=no_reasoning,
            brief=brief,
        )
        with connect(self.db_path) as conn:
            session = get_session(conn, session_id)
            if session is None:
                raise KeyError(session_id)
            events = get_events_filtered(
                conn,
                session_id,
                include=include,
                exclude=exclude,
                last_turns=last_turns,
                no_tool_output=no_tool_output,
                no_reasoning=no_reasoning,
            )
            return export_session(
                session,
                events,
                out_dir,
                fmt=fmt,
                brief=brief,
                max_chars=max_chars,
                max_tool_chars=max_tool_chars,
                privacy_mode=privacy_mode,
                privacy_config=load_app_config(privacy_config_path),
            )

    def export_project(self, cwd: str, out_dir: Path):
        with connect(self.db_path) as conn:
            sessions = get_project_sessions(conn, cwd)
            summaries = []
            for session in sessions:
                events = get_events_filtered(conn, session["session_id"])
                summaries.append(build_summary(session, events))
            return export_project_markdown(cwd, sessions, out_dir, summaries=summaries)

    def export_target(
        self,
        out_dir: Path,
        profile: str = "markdown",
        session_ids: list[str] | None = None,
        project: str | None = None,
        privacy_mode: str = "warn",
        privacy_config_path: Path | None = None,
        skill_name: str | None = None,
        skill_description: str | None = None,
    ) -> dict[str, Any]:
        with connect(self.db_path) as conn:
            init_db(conn)
            return export_target(
                conn,
                ExportTargetRequest(
                    out_dir=out_dir,
                    profile=profile,
                    session_ids=session_ids or [],
                    project=project,
                    privacy_mode=privacy_mode,
                    privacy_config_path=privacy_config_path,
                    skill_name=skill_name,
                    skill_description=skill_description,
                ),
            )

    def reindex(self, fts_only: bool = True) -> dict[str, Any]:
        with connect(self.db_path) as conn:
            init_db(conn)
            if not fts_only:
                raise ValueError("Only --fts-only is supported in v0.3.")
            return reindex_fts(conn)

    def vacuum(self) -> dict[str, Any]:
        with connect(self.db_path) as conn:
            init_db(conn)
            database_vacuum(conn)
        return {"ok": True, "db_path": str(self.db_path)}

    def backup(self, out: Path, force: bool = False, write_manifest: bool = True) -> dict[str, Any]:
        payload = backup_database(self.db_path, out, force=force)
        payload["manifest"] = None
        if payload["ok"] and write_manifest:
            payload["manifest"] = write_backup_manifest(payload)
        return payload

    def verify_backup(self, backup: Path, manifest: bool = False) -> dict[str, Any]:
        payload = verify_database_backup(backup)
        payload["manifest"] = verify_backup_manifest(backup) if manifest else None
        if manifest and payload["manifest"] and not payload["manifest"]["ok"]:
            payload["ok"] = False
            payload["errors"].append({"code": "backup_manifest_failed", "message": "Backup manifest verification failed."})
        return payload

    def verify_backup_manifest(self, backup: Path) -> dict[str, Any]:
        return verify_backup_manifest(backup)

    def restore_plan(self, backup: Path, target_db: Path) -> dict[str, Any]:
        return build_restore_plan(backup, target_db)

    def restore(
        self,
        backup: Path,
        target_db: Path,
        apply: bool = False,
        overwrite: bool = False,
        pre_restore_backup_dir: Path | None = None,
        allow_missing_manifest: bool = False,
        restore_history: Path | None = None,
    ) -> dict[str, Any]:
        return restore_backup(
            backup=backup,
            target_db=target_db,
            apply=apply,
            overwrite=overwrite,
            pre_restore_backup_dir=pre_restore_backup_dir,
            allow_missing_manifest=allow_missing_manifest,
            restore_history=restore_history,
        )

    def restore_history_list(self, history: Path | None = None) -> dict[str, Any]:
        return list_restore_history(history)

    def restore_history_latest(self, history: Path | None = None) -> dict[str, Any]:
        return latest_restore_history(history)

    def restore_history_prune(self, history: Path | None = None, keep: int = 10, apply: bool = False) -> dict[str, Any]:
        return prune_restore_history(history, keep=keep, apply=apply)

    def ingest_sample(self, codex_home: Path | None = None, limit: int | None = None, include_paths: bool = False) -> dict[str, Any]:
        return sample_codex_home(codex_home=codex_home, limit=limit, include_paths=include_paths)

    def privacy_scan(self, session_id: str, privacy_config_path: Path | None = None) -> dict[str, Any]:
        with connect(self.db_path) as conn:
            session = get_session(conn, session_id)
            if session is None:
                raise KeyError(session_id)
            events = get_events_filtered(conn, session_id)
        text = "\n".join(str(event["text_content"] or "") for event in events)
        config = load_app_config(privacy_config_path)
        findings = scan_sensitive_text(text, allowlist=config.allowlist)
        effective = effective_findings(findings)
        by_severity: dict[str, int] = {}
        by_kind: dict[str, int] = {}
        for finding in effective:
            by_severity[finding.severity] = by_severity.get(finding.severity, 0) + 1
            by_kind[finding.kind] = by_kind.get(finding.kind, 0) + 1
        return {
            "session_id": session_id,
            "rules_version": RULES_VERSION,
            "config_path": str(config.source_path) if config.source_path else None,
            "findings": [finding.__dict__ for finding in findings],
            "summary": {
                "total": len(findings),
                "allowlisted_count": len(findings) - len(effective),
                "effective_findings_count": len(effective),
                "by_severity": by_severity,
                "by_kind": by_kind,
            },
        }

    def self_test(self) -> dict[str, Any]:
        checks: list[dict[str, Any]] = []
        with connect(self.db_path) as conn:
            init_db(conn)
            doctor_result = database_doctor(conn)
        checks.append({"name": "database_schema", "ok": doctor_result["ok"]})
        checks.append({
            "name": "sqlite_fts5",
            "ok": any(check["name"] == "sqlite_fts5" and check["ok"] for check in doctor_result["checks"]),
        })
        try:
            from .parser import parse_session_file

            fixture = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "codex_home" / "sessions" / "current.jsonl"
            parsed = parse_session_file(fixture) if fixture.exists() else None
            checks.append({"name": "fixture_parser", "ok": bool(parsed and parsed.events)})
        except Exception:
            checks.append({"name": "fixture_parser", "ok": False})
        return {"ok": all(check["ok"] for check in checks), "checks": checks, "db_path": str(self.db_path)}


def capabilities() -> dict[str, Any]:
    return {
        "name": "threadvault",
        "contract_version": CONTRACT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "stability_policy": (
            "JSON output fields are append-only within the v0.x contract unless a command is explicitly marked experimental."
        ),
        "commands": [
            "init",
            "import",
            "list",
            "search",
            "export",
            "summarize",
            "stats",
            "doctor",
            "warnings",
            "privacy-scan",
            "ingest-sample",
            "capabilities",
            "robot-docs",
            "reindex",
            "vacuum",
            "backup",
            "backup-verify",
            "backup-manifest",
            "restore-plan",
            "restore",
            "restore-history",
            "backup-history",
            "self-test",
            "schemas",
            "validate-json",
            "audit-corpus",
            "audit-diff",
            "audit-history",
            "config",
            "ingest-queue",
            "codex-hook",
            "export-target",
            "retrieval",
            "summary-pipeline",
            "vector",
            "agent",
            "client",
            "ui",
            "mcp",
            "governance",
        ],
        "json_outputs": [
            "import",
            "list",
            "search",
            "summarize",
            "stats",
            "doctor",
            "warnings",
            "privacy-scan",
            "ingest-sample",
            "capabilities",
            "robot-docs guide",
            "robot-docs schemas",
            "reindex",
            "vacuum",
            "backup",
            "backup-verify",
            "backup-manifest",
            "restore-plan",
            "restore",
            "restore-history list",
            "restore-history latest",
            "restore-history prune",
            "backup-history list",
            "backup-history latest",
            "backup-history verify-latest",
            "backup-history prune",
            "self-test",
            "schemas list",
            "schemas show",
            "schemas write",
            "validate-json",
            "audit-corpus",
            "audit-diff",
            "audit-history list",
            "audit-history latest",
            "audit-history diff-latest",
            "audit-history prune",
            "config show",
            "config doctor",
            "config init",
            "ingest-queue enqueue",
            "ingest-queue list",
            "ingest-queue process",
            "codex-hook ingest",
            "codex-hook config",
            "export-target markdown",
            "export-target obsidian",
            "export-target skill",
            "retrieval query",
            "retrieval diagnose",
            "retrieval hybrid",
            "summary-pipeline chunks",
            "vector index",
            "vector query",
            "vector status",
            "agent manifest",
            "agent retrieve",
            "client manifest",
            "client overview",
            "client tui",
            "client session",
            "client export-preview",
            "client warnings",
            "ui smoke",
            "mcp manifest",
            "mcp serve",
            "governance status",
            "governance audit append",
            "governance audit list",
            "governance permission check",
            "governance enforcement gaps",
            "governance enforcement check",
            "governance instrumentation business-command",
            "governance policy readiness",
            "governance server policy-readiness",
            "governance server read-only-manifest",
            "governance server read-only-smoke",
            "governance audit centralized-readiness",
            "governance audit centralized-store",
            "governance v3 gap-audit",
            "governance v3 acceptance-smoke",
            "governance identity actor-readiness",
            "governance identity bind",
            "governance policy central-readiness",
            "governance policy central-store",
            "governance backup central-readiness",
            "governance backup policy",
            "governance preflight export-backup",
            "governance preflight restore-retention",
            "governance preflight raw-read",
            "governance preflight summary-search",
            "governance preflight export-preview",
            "governance preflight external-model",
        ],
        "export_formats": ["md", "json", "jsonl", "csv"],
        "export_profiles": ["full", "brief", "agent", "review"],
        "privacy_modes": ["warn", "redact", "fail"],
        "retrieval_modes": RETRIEVAL_MODES,
        "search_fields": ["minimal", "standard", "full"],
        "feature_flags": {
            "local_first": True,
            "sqlite_fts5": True,
            "codex_state_readonly_enrichment": True,
            "privacy_allowlist": True,
            "ingestion_queue": True,
            "codex_hook_adapter": True,
            "export_target_manifest": True,
            "obsidian_vault_target": True,
            "codex_skill_target": True,
            "retrieval_module": True,
            "retrieval_diagnostics": True,
            "hybrid_retrieval": True,
            "agent_retrieval_interface": True,
            "client_interface_manifest": True,
            "client_overview": True,
            "client_tui_runtime": True,
            "client_session": True,
            "client_export_preview": True,
            "client_export_preview_governance_instrumentation": True,
            "client_warnings": True,
            "personal_web_ui": True,
            "personal_ui_server": True,
            "personal_ui_action_registry": True,
            "personal_ui_acceptance_smoke": True,
            "personal_ui_desktop_wrapper": False,
            "personal_ui_team_mode": False,
            "personal_ui_cloud_sync": False,
            "mcp_stdio_server": True,
            "mcp_read_only_tools": True,
            "mcp_export_preview": True,
            "governance_baseline": True,
            "governance_audit_log": True,
            "governance_permission_preflight": True,
            "governance_enforcement_gap_audit": True,
            "governance_enforcement_dry_run": True,
            "governance_business_command_instrumentation": True,
            "governance_policy_readiness": True,
            "governance_server_policy_readiness": True,
            "governance_read_only_server_manifest": True,
            "governance_read_only_server_smoke": True,
            "governance_centralized_audit_readiness": True,
            "governance_centralized_audit_store": True,
            "governance_v3_completion_gap_audit": True,
            "governance_v3_acceptance_smoke": True,
            "governance_identity_actor_readiness": True,
            "governance_identity_actor_binding": True,
            "governance_central_policy_readiness": True,
            "governance_central_policy_store": True,
            "governance_central_backup_readiness": True,
            "governance_central_backup_policy": True,
            "governance_export_backup_preflight": True,
            "governance_restore_retention_preflight": True,
            "governance_raw_read_preflight": True,
            "governance_summary_search_preflight": True,
            "governance_export_preview_preflight": True,
            "governance_external_model_preflight": True,
            "summary_evidence_chunks": True,
            "local_vector_adapter": True,
            "local_vector_enabled_by_default": False,
            "external_llm_summary": False,
            "cloud_sync": False,
        },
    }


def robot_guide() -> dict[str, Any]:
    return {
        "purpose": "Machine-readable ThreadVault usage guide for agents.",
        "json_contract": "Commands with --json emit only JSON on stdout.",
        "recommended_commands": [
            "threadvault capabilities --json",
            "threadvault schemas list --json",
            "threadvault schemas show search_minimal --json",
            "threadvault audit-corpus --codex-home CODEX_HOME --json",
            "threadvault doctor --json",
            "threadvault search QUERY --json --fields minimal",
            "threadvault validate-json --schema search_minimal --input payload.json --json",
            "threadvault export --session SESSION_ID --format json --json",
            "threadvault ingest-queue enqueue --source hook --reason session-stop --json",
            "threadvault ingest-queue process --apply --json",
            "threadvault codex-hook config --json",
            "threadvault export-target markdown --session SESSION_ID --out OUT --json",
            "threadvault export-target obsidian --project CWD --out OUT --json",
            "threadvault export-target skill --project CWD --out OUT --skill-name NAME --json",
            "threadvault retrieval query QUERY --json",
            "threadvault retrieval diagnose --json",
            "threadvault retrieval hybrid QUERY --json",
            "threadvault summary-pipeline chunks --session SESSION_ID --json",
            "threadvault vector status --json",
            "threadvault vector index --session SESSION_ID --config threadvault.toml --json",
            "threadvault vector query QUERY --config threadvault.toml --json",
            "threadvault agent manifest --json",
            "threadvault agent retrieve QUERY --json",
            "threadvault client manifest --json",
            "threadvault client overview --json",
            "threadvault client overview --query QUERY --json",
            "threadvault client tui --json",
            "threadvault client tui --query QUERY --json",
            "threadvault client tui --export-preview-session SESSION_ID --out OUT --json",
            "threadvault client session --session SESSION_ID --json",
            "threadvault client export-preview --session SESSION_ID --out OUT --json",
            "threadvault client export-preview --session SESSION_ID --out OUT --governance-role reviewer --json",
            "threadvault client warnings --session SESSION_ID --json",
            "threadvault mcp manifest --json",
            "threadvault mcp serve",
            PERSONAL_UI_SERVE_COMMAND,
            PERSONAL_UI_SMOKE_COMMAND,
            "threadvault governance status --json",
            AUDIT_APPEND_COMMAND,
            AUDIT_LIST_COMMAND,
            PERMISSION_CHECK_COMMAND,
            ENFORCEMENT_GAPS_COMMAND,
            ENFORCEMENT_CHECK_COMMAND,
            BUSINESS_COMMAND_INSTRUMENTATION_COMMAND,
            POLICY_READINESS_COMMAND,
            SERVER_POLICY_READINESS_COMMAND,
            READ_ONLY_SERVER_MANIFEST_COMMAND,
            READ_ONLY_SERVER_SMOKE_COMMAND,
            CENTRALIZED_AUDIT_READINESS_COMMAND,
            CENTRALIZED_AUDIT_STORE_COMMAND,
            V3_COMPLETION_GAP_AUDIT_COMMAND,
            V3_ACCEPTANCE_SMOKE_COMMAND,
            IDENTITY_ACTOR_READINESS_COMMAND,
            IDENTITY_ACTOR_BINDING_COMMAND,
            CENTRAL_POLICY_READINESS_COMMAND,
            CENTRAL_POLICY_STORE_COMMAND,
            CENTRAL_BACKUP_READINESS_COMMAND,
            CENTRAL_BACKUP_POLICY_COMMAND,
            EXPORT_BACKUP_PREFLIGHT_COMMAND,
            RESTORE_RETENTION_PREFLIGHT_COMMAND,
            RAW_READ_PREFLIGHT_COMMAND,
            SUMMARY_SEARCH_PREFLIGHT_COMMAND,
            EXPORT_PREVIEW_PREFLIGHT_COMMAND,
            EXTERNAL_MODEL_PREFLIGHT_COMMAND,
        ],
        "governance": {
            "module": "threadvault.governance",
            "status_contract_version": GOVERNANCE_STATUS_CONTRACT_VERSION,
            "schema": "governance_status",
            "audit_append_contract_version": GOVERNANCE_AUDIT_APPEND_CONTRACT_VERSION,
            "audit_list_contract_version": GOVERNANCE_AUDIT_LIST_CONTRACT_VERSION,
            "audit_schemas": ["governance_audit_append", "governance_audit_list"],
            "permission_check_contract_version": GOVERNANCE_PERMISSION_CHECK_CONTRACT_VERSION,
            "permission_schema": "governance_permission_check",
            "enforcement_gaps_contract_version": GOVERNANCE_ENFORCEMENT_GAPS_CONTRACT_VERSION,
            "enforcement_gaps_schema": "governance_enforcement_gaps",
            "enforcement_check_contract_version": GOVERNANCE_ENFORCEMENT_CHECK_CONTRACT_VERSION,
            "enforcement_check_schema": "governance_enforcement_check",
            "business_command_instrumentation_contract_version": GOVERNANCE_BUSINESS_COMMAND_INSTRUMENTATION_CONTRACT_VERSION,
            "business_command_instrumentation_schema": "governance_business_command_instrumentation",
            "policy_readiness_contract_version": GOVERNANCE_POLICY_READINESS_CONTRACT_VERSION,
            "policy_readiness_schema": "governance_policy_readiness",
            "server_policy_readiness_contract_version": GOVERNANCE_SERVER_POLICY_READINESS_CONTRACT_VERSION,
            "server_policy_readiness_schema": "governance_server_policy_readiness",
            "read_only_server_manifest_contract_version": READ_ONLY_SERVER_MANIFEST_CONTRACT_VERSION,
            "read_only_server_manifest_schema": "governance_read_only_server_manifest",
            "read_only_server_smoke_contract_version": READ_ONLY_SERVER_SMOKE_CONTRACT_VERSION,
            "read_only_server_smoke_schema": "governance_read_only_server_smoke",
            "centralized_audit_readiness_contract_version": (
                GOVERNANCE_CENTRALIZED_AUDIT_READINESS_CONTRACT_VERSION
            ),
            "centralized_audit_readiness_schema": "governance_centralized_audit_readiness",
            "centralized_audit_store_contract_version": GOVERNANCE_CENTRALIZED_AUDIT_STORE_CONTRACT_VERSION,
            "centralized_audit_store_schema": "governance_centralized_audit_store",
            "v3_completion_gap_audit_contract_version": GOVERNANCE_V3_COMPLETION_GAP_AUDIT_CONTRACT_VERSION,
            "v3_completion_gap_audit_schema": "governance_v3_completion_gap_audit",
            "v3_acceptance_smoke_contract_version": GOVERNANCE_V3_ACCEPTANCE_SMOKE_CONTRACT_VERSION,
            "v3_acceptance_smoke_schema": "governance_v3_acceptance_smoke",
            "identity_actor_readiness_contract_version": GOVERNANCE_IDENTITY_ACTOR_READINESS_CONTRACT_VERSION,
            "identity_actor_readiness_schema": "governance_identity_actor_readiness",
            "identity_actor_binding_contract_version": GOVERNANCE_IDENTITY_ACTOR_BINDING_CONTRACT_VERSION,
            "identity_actor_binding_schema": "governance_identity_actor_binding",
            "central_policy_readiness_contract_version": GOVERNANCE_CENTRAL_POLICY_READINESS_CONTRACT_VERSION,
            "central_policy_readiness_schema": "governance_central_policy_readiness",
            "central_policy_store_contract_version": GOVERNANCE_CENTRAL_POLICY_STORE_CONTRACT_VERSION,
            "central_policy_store_schema": "governance_central_policy_store",
            "central_backup_readiness_contract_version": GOVERNANCE_CENTRAL_BACKUP_READINESS_CONTRACT_VERSION,
            "central_backup_readiness_schema": "governance_central_backup_readiness",
            "central_backup_policy_contract_version": GOVERNANCE_CENTRAL_BACKUP_POLICY_CONTRACT_VERSION,
            "central_backup_policy_schema": "governance_central_backup_policy",
            "export_backup_preflight_contract_version": GOVERNANCE_EXPORT_BACKUP_PREFLIGHT_CONTRACT_VERSION,
            "export_backup_preflight_schema": "governance_export_backup_preflight",
            "restore_retention_preflight_contract_version": GOVERNANCE_RESTORE_RETENTION_PREFLIGHT_CONTRACT_VERSION,
            "restore_retention_preflight_schema": "governance_restore_retention_preflight",
            "raw_read_preflight_contract_version": GOVERNANCE_RAW_READ_PREFLIGHT_CONTRACT_VERSION,
            "raw_read_preflight_schema": "governance_raw_read_preflight",
            "summary_search_preflight_contract_version": GOVERNANCE_SUMMARY_SEARCH_PREFLIGHT_CONTRACT_VERSION,
            "summary_search_preflight_schema": "governance_summary_search_preflight",
            "export_preview_preflight_contract_version": GOVERNANCE_EXPORT_PREVIEW_PREFLIGHT_CONTRACT_VERSION,
            "export_preview_preflight_schema": "governance_export_preview_preflight",
            "external_model_preflight_contract_version": GOVERNANCE_EXTERNAL_MODEL_PREFLIGHT_CONTRACT_VERSION,
            "external_model_preflight_schema": "governance_external_model_preflight",
            "enabled_by_default": False,
            "server_required": False,
            "server_opt_in": True,
            "permissions_enforced": False,
            "audit_log_implemented": True,
        },
        "client_interface": {
            "module": "threadvault.client_interface",
            "manifest_contract_version": CLIENT_INTERFACE_CONTRACT_VERSION,
            "overview_contract_version": CLIENT_OVERVIEW_CONTRACT_VERSION,
            "tui_runtime_contract_version": CLIENT_TUI_RUNTIME_CONTRACT_VERSION,
            "session_contract_version": CLIENT_SESSION_CONTRACT_VERSION,
            "export_preview_contract_version": CLIENT_EXPORT_PREVIEW_CONTRACT_VERSION,
            "warnings_contract_version": CLIENT_WARNINGS_CONTRACT_VERSION,
            "schemas": [
                "client_interface_manifest",
                "client_overview",
                "client_tui_runtime",
                "client_session",
                "client_export_preview",
                "client_warnings",
            ],
            "client_families": ["desktop", "ide", "web", "tui", "server"],
            "accepted_runtimes": ["threadvault-local-tui"],
            "server_required": False,
            "server_opt_in": True,
            "instrumented_commands": ["threadvault client export-preview"],
        },
        "personal_ui": {
            "module": "threadvault.personal_ui",
            "serve_command": PERSONAL_UI_SERVE_COMMAND,
            "health_contract_version": PERSONAL_UI_HEALTH_CONTRACT_VERSION,
            "health_schema": "personal_ui_health",
            "action_contract_version": PERSONAL_UI_ACTION_CONTRACT_VERSION,
            "action_schema": "personal_ui_action",
            "smoke_command": PERSONAL_UI_SMOKE_COMMAND,
            "smoke_contract_version": PERSONAL_UI_SMOKE_CONTRACT_VERSION,
            "smoke_schema": "personal_ui_smoke",
            "action_registry": "POST /api/action",
            "action_registry_status": "implemented",
            "dangerous_actions_require_confirm": ["restore_apply", "vacuum", "reindex", "schema_write"],
            "export_actions_require_preview": [
                "export_session",
                "export_target_markdown",
                "export_target_obsidian",
                "export_target_skill",
            ],
            "default_host": "127.0.0.1",
            "default_port": 8766,
            "server_required": False,
            "cloud_sync": False,
            "team_mode": False,
            "external_model_calls": False,
        },
        "agent_interface": {
            "module": "threadvault.agent_interface",
            "manifest_contract_version": AGENT_INTERFACE_CONTRACT_VERSION,
            "retrieval_contract_version": AGENT_RETRIEVAL_CONTRACT_VERSION,
            "schemas": ["agent_interface_manifest", "agent_retrieval"],
            "default_mode": "hybrid",
            "modes": ["hybrid", "fts"],
            "mcp_runtime_included": True,
            "local_debug_opt_in": True,
        },
        "mcp_interface": {
            "module": "threadvault.mcp",
            "manifest_contract_version": MCP_MANIFEST_CONTRACT_VERSION,
            "schema": "mcp_manifest",
            "protocol_version": MCP_PROTOCOL_VERSION,
            "transport": "stdio",
            "serve_command": "threadvault mcp serve",
            "manifest_command": "threadvault mcp manifest --json",
            "tools": [
                "threadvault_capabilities",
                "threadvault_stats",
                "threadvault_doctor",
                "threadvault_retrieve",
                "threadvault_session",
                "threadvault_export_preview",
            ],
            "writes_files": False,
            "external_model_calls": False,
            "raw_paths_default": False,
        },
        "retrieval": {
            "module": "threadvault.retrieval",
            "modes": RETRIEVAL_MODES,
            "default_mode": "fts",
            "contract_version": RETRIEVAL_CONTRACT_VERSION,
            "schemas": ["retrieval_query", "retrieval_diagnostics", "hybrid_retrieval"],
            "hybrid_contract_version": HYBRID_RETRIEVAL_CONTRACT_VERSION,
            "hybrid_degrades_to_fts": True,
        },
        "summary_pipeline": {
            "module": "threadvault.summary_pipeline",
            "contract_version": SUMMARY_CHUNKS_CONTRACT_VERSION,
            "schemas": ["summary_chunks"],
            "default_chunk_types": ["session_summary", "turn_summary", "evidence"],
            "embedding_generated": False,
        },
        "vector": {
            "module": "threadvault.vector_adapter",
            "contract_version": VECTOR_CONTRACT_VERSION,
            "schemas": ["vector_index", "vector_query", "vector_status"],
            "adapter": LOCAL_VECTOR_ADAPTER,
            "default_dimensions": DEFAULT_VECTOR_DIMENSIONS,
            "enabled_by_default": False,
            "source_schema": "summary_chunks",
        },
        "minimal_search_fields": ["event_id", "session_id"],
        "standard_search_fields": [
            "event_id",
            "session_id",
            "timestamp",
            "top_type",
            "sub_type",
            "role",
            "tool_name",
            "file_path",
            "snippet",
        ],
    }


def robot_schemas() -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "search_minimal": {"event_id": "integer", "session_id": "string"},
        "search_standard": {
            "event_id": "integer",
            "session_id": "string",
            "timestamp": "string|null",
            "top_type": "string",
            "sub_type": "string|null",
            "role": "string|null",
            "tool_name": "string|null",
            "file_path": "string|null",
            "snippet": "string|null",
        },
        "capabilities": {
            "name": "string",
            "contract_version": "string",
            "schema_version": "integer",
            "stability_policy": "string",
            "commands": "string[]",
            "json_outputs": "string[]",
            "export_formats": "string[]",
            "export_profiles": "string[]",
            "privacy_modes": "string[]",
            "retrieval_modes": "string[]",
            "search_fields": "string[]",
            "feature_flags": "object",
        },
        "ingestion_enqueue": {
            "ok": "boolean",
            "enqueued": "boolean",
            "request": "object",
        },
        "ingestion_queue_list": {
            "requests": "object[]",
            "count": "integer",
        },
        "ingestion_process": {
            "ok": "boolean",
            "apply": "boolean",
            "processed": "integer",
            "requests": "object[]",
        },
        "codex_hook_ingest": {
            "ok": "boolean",
            "hook_event_name": "string|null",
            "codex_home": "string|null",
            "enqueue": "object|null",
            "hook_response": "object",
        },
        "codex_hook_config": {
            "hooks": "object",
        },
        "export_target_manifest": {
            "manifest_version": "string",
            "target_profile": "string",
            "files": "object[]",
            "skipped": "object[]",
            "privacy": "object",
            "evidence": "object",
        },
        "retrieval_query": {
            "contract_version": "string",
            "query": "object",
            "diagnostics": "object",
            "results": "object[]",
        },
        "retrieval_diagnostics": {
            "contract_version": "string",
            "diagnostics": "object",
        },
        "hybrid_retrieval": {
            "contract_version": "string",
            "query": "object",
            "results": "object[]",
            "diagnostics": "object",
        },
        "agent_interface_manifest": {
            "contract_version": "string",
            "interface": "object",
            "capabilities": "object",
            "schemas": "object",
            "recommended_commands": "string[]",
            "privacy": "object",
            "defaults": "object",
        },
        "agent_retrieval": {
            "contract_version": "string",
            "request": "object",
            "results": "object[]",
            "diagnostics": "object",
            "privacy": "object",
        },
        "mcp_manifest": {
            "contract_version": "string",
            "server": "object",
            "tools": "object[]",
            "privacy": "object",
            "integration_guidance": "object",
        },
        "client_interface_manifest": {
            "contract_version": "string",
            "interface": "object",
            "client_families": "object[]",
            "entrypoints": "object",
            "schemas": "object",
            "defaults": "object",
            "integration_policy": "object",
            "governance": "object",
        },
        "client_overview": {
            "contract_version": "string",
            "request": "object",
            "sessions": "object[]",
            "search": "object",
            "actions": "object",
            "privacy": "object",
            "diagnostics": "object",
        },
        "client_tui_runtime": {
            "contract_version": "string",
            "runtime": "object",
            "request": "object",
            "screen": "object",
            "overview": "object",
            "export_preview": "object|null",
            "actions": "object",
            "privacy": "object",
            "diagnostics": "object",
        },
        "client_session": {
            "contract_version": "string",
            "request": "object",
            "session": "object",
            "summary": "object",
            "events": "object[]",
            "actions": "object",
            "privacy": "object",
            "diagnostics": "object",
        },
        "client_export_preview": {
            "contract_version": "string",
            "request": "object",
            "selection": "object",
            "planned_files": "object[]",
            "skipped": "object[]",
            "privacy": "object",
            "evidence": "object",
            "actions": "object",
            "governance_instrumentation": "object",
            "diagnostics": "object",
        },
        "client_warnings": {
            "contract_version": "string",
            "request": "object",
            "session": "object",
            "warnings": "object",
            "privacy": "object",
            "actions": "object",
            "diagnostics": "object",
        },
        "personal_ui_health": {
            "contract_version": "string",
            "ok": "boolean",
            "status": "string",
            "server": "object",
            "defaults": "object",
            "paths": "object",
        },
        "personal_ui_action": {
            "contract_version": "string",
            "ok": "boolean",
            "action": "string|null",
            "status": "string",
            "confirm": "boolean",
            "message": "string|null",
            "result": "object|null",
            "safety": "object",
            "available_actions": "string[]",
        },
        "personal_ui_smoke": {
            "contract_version": "string",
            "status": "string",
            "ok": "boolean",
            "server": "object",
            "checks": "object[]",
            "summary": "object",
            "criteria": "object[]",
            "boundaries": "object",
            "diagnostics": "object",
        },
        "governance_status": {
            "contract_version": "string",
            "enabled": "boolean",
            "mode": "string",
            "access_levels": "object[]",
            "roles": "object[]",
            "sensitive_operations": "object[]",
            "audit_requirements": "object",
            "defaults": "object",
            "diagnostics": "object",
        },
        "governance_audit_append": {
            "contract_version": "string",
            "ok": "boolean",
            "log": "object",
            "record": "object",
            "diagnostics": "object",
        },
        "governance_audit_list": {
            "contract_version": "string",
            "log": "object",
            "records": "object[]",
            "warnings": "object[]",
            "diagnostics": "object",
        },
        "governance_permission_check": {
            "contract_version": "string",
            "request": "object",
            "governance": "object",
            "decision": "object",
            "audit": "object",
            "diagnostics": "object",
        },
        "governance_enforcement_gaps": {
            "contract_version": "string",
            "governance": "object",
            "commands": "object[]",
            "summary": "object",
            "recommendations": "string[]",
            "diagnostics": "object",
        },
        "governance_enforcement_check": {
            "contract_version": "string",
            "request": "object",
            "command_policy": "object",
            "permission": "object",
            "enforcement": "object",
            "audit": "object",
            "diagnostics": "object",
        },
        "governance_business_command_instrumentation": {
            "contract_version": "string",
            "request": "object",
            "governance": "object",
            "command_policy": "object",
            "instrumentation": "object",
            "preflight": "object",
            "audit": "object",
            "execution": "object",
            "diagnostics": "object",
        },
        "governance_policy_readiness": {
            "contract_version": "string",
            "governance": "object",
            "readiness": "object",
            "capabilities": "object",
            "command_categories": "object[]",
            "blockers": "object[]",
            "recommended_next_phases": "string[]",
            "diagnostics": "object",
        },
        "governance_server_policy_readiness": {
            "contract_version": "string",
            "governance": "object",
            "readiness": "object",
            "server": "object",
            "policy": "object",
            "identity": "object",
            "instrumentation": "object",
            "audit": "object",
            "backup_restore": "object",
            "outbound_policy": "object",
            "blockers": "object[]",
            "recommended_next_phases": "string[]",
            "diagnostics": "object",
        },
        "governance_read_only_server_manifest": {
            "contract_version": "string",
            "governance": "object",
            "runtime": "object",
            "routes": "object[]",
            "read_only": "object",
            "security": "object",
            "integration": "object",
            "commands": "object",
            "diagnostics": "object",
        },
        "governance_read_only_server_smoke": {
            "contract_version": "string",
            "ok": "boolean",
            "request": "object",
            "checks": "object[]",
            "summary": "object",
            "governance": "object",
            "diagnostics": "object",
        },
        "governance_centralized_audit_readiness": {
            "contract_version": "string",
            "governance": "object",
            "readiness": "object",
            "local_audit": "object",
            "centralized_audit": "object",
            "identity": "object",
            "integrity": "object",
            "retention": "object",
            "review": "object",
            "backup_export": "object",
            "instrumentation": "object",
            "blockers": "object[]",
            "recommended_next_phases": "string[]",
            "diagnostics": "object",
        },
        "governance_centralized_audit_store": {
            "contract_version": "string",
            "request": "object",
            "governance": "object",
            "store": "object",
            "append": "object",
            "query": "object",
            "verification": "object",
            "records": "object[]",
            "warnings": "object[]",
            "errors": "object[]",
            "blockers": "object[]",
            "diagnostics": "object",
        },
        "governance_v3_completion_gap_audit": {
            "contract_version": "string",
            "governance": "object",
            "completion": "object",
            "milestones": "object[]",
            "acceptance_criteria": "object[]",
            "implemented_capabilities": "string[]",
            "remaining_gaps": "object[]",
            "blockers": "object[]",
            "recommended_next_phases": "string[]",
            "diagnostics": "object",
        },
        "governance_v3_acceptance_smoke": {
            "contract_version": "string",
            "status": "string",
            "ok": "boolean",
            "governance": "object",
            "checks": "object[]",
            "summary": "object",
            "criteria": "object[]",
            "gap_audit": "object",
            "diagnostics": "object",
        },
        "governance_identity_actor_readiness": {
            "contract_version": "string",
            "governance": "object",
            "readiness": "object",
            "identity_provider": "object",
            "actor_binding": "object",
            "role_mapping": "object",
            "request_attribution": "object",
            "audit_provenance": "object",
            "local_fallback": "object",
            "blockers": "object[]",
            "recommended_next_phases": "string[]",
            "diagnostics": "object",
        },
        "governance_identity_actor_binding": {
            "contract_version": "string",
            "request": "object",
            "governance": "object",
            "identity_provider": "object",
            "actor": "object",
            "binding": "object",
            "role_mapping": "object",
            "request_attribution": "object",
            "audit": "object",
            "diagnostics": "object",
        },
        "governance_central_policy_readiness": {
            "contract_version": "string",
            "governance": "object",
            "readiness": "object",
            "local_policy": "object",
            "central_policy": "object",
            "adapter": "object",
            "versioning": "object",
            "provenance": "object",
            "migration": "object",
            "identity_dependency": "object",
            "fallback": "object",
            "blockers": "object[]",
            "recommended_next_phases": "string[]",
            "diagnostics": "object",
        },
        "governance_central_policy_store": {
            "contract_version": "string",
            "request": "object",
            "governance": "object",
            "store": "object",
            "policy": "object",
            "validation": "object",
            "provenance": "object",
            "actor_resolution": "object",
            "operation_resolution": "object",
            "enforcement": "object",
            "blockers": "object[]",
            "diagnostics": "object",
        },
        "governance_central_backup_readiness": {
            "contract_version": "string",
            "governance": "object",
            "readiness": "object",
            "local_backup": "object",
            "central_backup": "object",
            "policy": "object",
            "restore": "object",
            "retention": "object",
            "audit": "object",
            "dependencies": "object",
            "recovery_testing": "object",
            "blockers": "object[]",
            "recommended_next_phases": "string[]",
            "diagnostics": "object",
        },
        "governance_central_backup_policy": {
            "contract_version": "string",
            "governance": "object",
            "request": "object",
            "store": "object",
            "policy": "object",
            "validation": "object",
            "provenance": "object",
            "repository": "object",
            "backup": "object",
            "restore": "object",
            "retention": "object",
            "legal_hold": "object",
            "recovery_testing": "object",
            "migration": "object",
            "operation_resolution": "object",
            "audit": "object",
            "enforcement": "object",
            "blockers": "object[]",
            "diagnostics": "object",
        },
        "governance_export_backup_preflight": {
            "contract_version": "string",
            "request": "object",
            "scope": "object",
            "command_policy": "object",
            "permission": "object",
            "enforcement": "object",
            "privacy": "object",
            "audit": "object",
            "execution": "object",
            "diagnostics": "object",
        },
        "governance_restore_retention_preflight": {
            "contract_version": "string",
            "request": "object",
            "scope": "object",
            "command_policy": "object",
            "permission": "object",
            "enforcement": "object",
            "recovery": "object",
            "audit": "object",
            "execution": "object",
            "diagnostics": "object",
        },
        "governance_raw_read_preflight": {
            "contract_version": "string",
            "request": "object",
            "scope": "object",
            "command_policy": "object",
            "permission": "object",
            "enforcement": "object",
            "privacy": "object",
            "audit": "object",
            "execution": "object",
            "diagnostics": "object",
        },
        "governance_summary_search_preflight": {
            "contract_version": "string",
            "request": "object",
            "scope": "object",
            "command_policy": "object",
            "permission": "object",
            "enforcement": "object",
            "privacy": "object",
            "audit": "object",
            "execution": "object",
            "diagnostics": "object",
        },
        "governance_export_preview_preflight": {
            "contract_version": "string",
            "request": "object",
            "scope": "object",
            "command_policy": "object",
            "permission": "object",
            "enforcement": "object",
            "privacy": "object",
            "audit": "object",
            "execution": "object",
            "diagnostics": "object",
        },
        "governance_external_model_preflight": {
            "contract_version": "string",
            "request": "object",
            "scope": "object",
            "command_policy": "object",
            "permission": "object",
            "enforcement": "object",
            "outbound_policy": "object",
            "audit": "object",
            "execution": "object",
            "diagnostics": "object",
        },
        "summary_chunks": {
            "contract_version": "string",
            "selection": "object",
            "chunks": "object[]",
            "skipped": "object[]",
            "diagnostics": "object",
        },
        "vector_index": {
            "contract_version": "string",
            "ok": "boolean",
            "adapter": "string",
            "dimensions": "integer",
            "source": "object",
            "indexed": "object",
            "diagnostics": "object",
        },
        "vector_query": {
            "contract_version": "string",
            "query": "object",
            "results": "object[]",
            "diagnostics": "object",
        },
        "vector_status": {
            "contract_version": "string",
            "ok": "boolean",
            "config": "object",
            "index": "object",
            "diagnostics": "object",
        },
        "schemas": contract_schemas(),
    }


def apply_export_profile(
    profile: str,
    include: list[str] | None,
    exclude: list[str] | None,
    last_turns: int | None,
    max_chars: int | None,
    max_tool_chars: int | None,
    no_tool_output: bool,
    no_reasoning: bool,
    brief: bool,
):
    if profile == "full":
        return include, exclude, last_turns, max_chars, max_tool_chars, no_tool_output, no_reasoning, brief
    if profile == "brief":
        return include, exclude, last_turns, max_chars, max_tool_chars, no_tool_output, no_reasoning, True
    if profile == "agent":
        merged_exclude = list(exclude or [])
        if "reasoning" not in merged_exclude:
            merged_exclude.append("reasoning")
        return include, merged_exclude, last_turns, max_chars or 4000, max_tool_chars or 1000, True, True, brief
    if profile == "review":
        return include, exclude, last_turns, max_chars or 8000, max_tool_chars or 2000, no_tool_output, True, brief
    raise ValueError(f"Unsupported export profile: {profile}")


def _export_preview_execute_command(request: ExportTargetRequest) -> str:
    parts = ["threadvault", "export-target", request.profile]
    for session_id in request.session_ids:
        parts.extend(["--session", session_id])
    if request.project:
        parts.extend(["--project", request.project])
    parts.extend(["--out", str(request.out_dir), "--privacy-mode", request.privacy_mode, "--json"])
    if request.skill_name:
        parts.extend(["--skill-name", request.skill_name])
    if request.skill_description:
        parts.extend(["--skill-description", request.skill_description])
    return " ".join(parts)
