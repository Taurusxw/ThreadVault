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
from .archive_lifecycle import (
    STORAGE_PROFILES,
    backup_storage_profile,
    hydrate_event_rows,
    prune_cold_storage,
    read_cold_event,
    rebuild_archive,
    storage_audit,
    verify_cold_storage,
    verify_storage_backup,
)
from .backup_manifest import verify_backup_manifest, write_backup_manifest
from .client_interface import (
    CLIENT_EXPORT_PREVIEW_CONTRACT_VERSION,
    CLIENT_INTERFACE_CONTRACT_VERSION,
    CLIENT_OVERVIEW_CONTRACT_VERSION,
    CLIENT_SESSION_CONTRACT_VERSION,
    CLIENT_WARNINGS_CONTRACT_VERSION,
    client_export_preview,
    client_manifest,
    client_overview,
    client_session_detail,
    client_warnings_detail,
)
from .client_runtime import CLIENT_TUI_RUNTIME_CONTRACT_VERSION, client_tui_runtime
from .codex_hooks import build_codex_hook_config, handle_codex_hook_payload, install_codex_hook
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
from .smart_backup import run_smart_backup
from .source_sync import sync_codex_sources
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

PRIMARY_LOCAL_INTERFACE = "native_desktop"
PRIMARY_LOCAL_INTERFACE_COMMAND = "threadvault desktop launch"
PRIMARY_LOCAL_INTERFACE_SMOKE_COMMAND = "threadvault desktop smoke --json"
MAJOR_RELEASE_TARGET = "2.0.0"


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

    def handle_codex_hook(
        self,
        payload: dict[str, Any],
        codex_home: Path | None = None,
        *,
        apply: bool = False,
    ) -> dict[str, Any]:
        with connect(self.db_path) as conn:
            init_db(conn)
            return handle_codex_hook_payload(conn, payload, codex_home=codex_home, apply=apply)

    def codex_hook_config(
        self,
        command: str,
        timeout: int = 30,
        status_message: str = "Archiving this Codex turn in ThreadVault",
    ) -> dict[str, Any]:
        return build_codex_hook_config(command, timeout=timeout, status_message=status_message)

    def install_codex_hook(
        self,
        codex_home: Path,
        command: str,
        *,
        timeout: int = 30,
        status_message: str = "Archiving this Codex turn in ThreadVault",
        apply: bool = False,
    ) -> dict[str, Any]:
        return install_codex_hook(
            codex_home,
            command,
            timeout=timeout,
            status_message=status_message,
            apply=apply,
        )

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
        with connect(self.db_path) as conn:
            init_db(conn)
            preview = preview_export_target(conn, request)
        return client_export_preview(preview, execute_command)

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
            events = hydrate_event_rows(conn, self.db_path, events)
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

    def storage_audit(self, cold_root: Path | None = None) -> dict[str, Any]:
        with connect(self.db_path) as conn:
            init_db(conn)
        return storage_audit(self.db_path, cold_root=cold_root)

    def storage_rebuild(
        self,
        target_db: Path,
        cold_root: Path | None = None,
        *,
        apply: bool = False,
        batch_size: int = 1000,
    ) -> dict[str, Any]:
        return rebuild_archive(
            self.db_path,
            target_db,
            cold_root=cold_root,
            apply=apply,
            batch_size=batch_size,
        )

    def storage_verify(self, cold_root: Path | None = None, *, deep: bool = False) -> dict[str, Any]:
        return verify_cold_storage(self.db_path, cold_root=cold_root, deep=deep)

    def storage_sync(
        self,
        *,
        codex_home: Path | None = None,
        apply: bool = False,
        include_paths: bool = False,
    ) -> dict[str, Any]:
        return sync_codex_sources(
            self.db_path,
            codex_home=codex_home,
            apply=apply,
            include_paths=include_paths,
        )

    def storage_prune(self, cold_root: Path | None = None, *, apply: bool = False) -> dict[str, Any]:
        return prune_cold_storage(self.db_path, cold_root=cold_root, apply=apply)

    def storage_event(self, event_id: int, cold_root: Path | None = None) -> dict[str, Any]:
        return read_cold_event(self.db_path, event_id, cold_root=cold_root)

    def storage_backup(
        self,
        out_dir: Path,
        *,
        profile: str = "core",
        cold_root: Path | None = None,
        codex_home: Path | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        return backup_storage_profile(
            self.db_path,
            out_dir,
            profile=profile,
            cold_root=cold_root,
            codex_home=codex_home,
            force=force,
        )

    def storage_backup_verify(self, manifest: Path, *, deep: bool = False) -> dict[str, Any]:
        return verify_storage_backup(manifest, deep=deep)

    def storage_auto_backup(
        self,
        *,
        out_root: Path | None = None,
        cold_root: Path | None = None,
        codex_home: Path | None = None,
        apply: bool = False,
        include_forensic: bool = True,
    ) -> dict[str, Any]:
        return run_smart_backup(
            self.db_path,
            out_root=out_root,
            cold_root=cold_root,
            codex_home=codex_home,
            apply=apply,
            include_forensic=include_forensic,
        )

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
            events = hydrate_event_rows(conn, self.db_path, events)
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
            "JSON output fields are append-only within the 2.x contract unless a command is explicitly marked experimental."
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
            "codex",
            "export-target",
            "retrieval",
            "summary-pipeline",
            "vector",
            "agent",
            "client",
            "desktop",
            "mcp",
            "storage",
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
            "codex-hook install",
            "codex status",
            "codex install",
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
            "desktop smoke",
            "mcp manifest",
            "mcp serve",
            "storage audit",
            "storage sync",
            "storage rebuild",
            "storage verify",
            "storage event",
            "storage prune",
            "storage backup",
            "storage verify-backup",
            "storage auto",
        ],
        "export_formats": ["md", "json", "jsonl", "csv"],
        "export_profiles": ["full", "brief", "agent", "review"],
        "privacy_modes": ["warn", "redact", "fail"],
        "retrieval_modes": RETRIEVAL_MODES,
        "search_fields": ["minimal", "standard", "full"],
        "interface_policy": {
            "primary_local_interface": PRIMARY_LOCAL_INTERFACE,
            "primary_command": PRIMARY_LOCAL_INTERFACE_COMMAND,
            "primary_smoke_command": PRIMARY_LOCAL_INTERFACE_SMOKE_COMMAND,
            "major_release_target": MAJOR_RELEASE_TARGET,
            "browser_required_for_primary": False,
            "server_required_for_primary": False,
            "frontend_build_pipeline_for_primary": False,
        },
        "feature_flags": {
            "local_first": True,
            "sqlite_fts5": True,
            "codex_state_readonly_enrichment": True,
            "privacy_allowlist": True,
            "ingestion_queue": True,
            "codex_hook_adapter": True,
            "codex_one_command_integration": True,
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
            "client_warnings": True,
            "native_desktop_app": True,
            "native_desktop_primary": True,
            "desktop_smart_backup_center": True,
            "desktop_confirmed_export": True,
            "mcp_stdio_server": True,
            "mcp_read_only_tools": True,
            "mcp_export_preview": True,
            "hot_cold_storage": True,
            "content_addressed_cold_blobs": True,
            "storage_backup_profiles": list(STORAGE_PROFILES),
            "smart_backup": True,
            "source_freshness_guard": True,
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
            "threadvault codex-hook install --db DB --json",
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
            "threadvault client warnings --session SESSION_ID --json",
            "threadvault mcp manifest --json",
            "threadvault mcp serve",
            "threadvault storage audit --json",
            "threadvault storage rebuild --target-db TARGET --json",
            "threadvault storage verify --json",
            "threadvault storage prune --json",
            "threadvault storage backup --profile core --out OUT --json",
            "threadvault storage auto --apply --json",
            PRIMARY_LOCAL_INTERFACE_COMMAND,
            PRIMARY_LOCAL_INTERFACE_SMOKE_COMMAND,
        ],
        "interface_policy": {
            "primary_local_interface": PRIMARY_LOCAL_INTERFACE,
            "primary_command": PRIMARY_LOCAL_INTERFACE_COMMAND,
            "primary_smoke_command": PRIMARY_LOCAL_INTERFACE_SMOKE_COMMAND,
            "major_release_target": MAJOR_RELEASE_TARGET,
            "browser_required_for_primary": False,
            "server_required_for_primary": False,
            "frontend_build_pipeline_for_primary": False,
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
            "client_families": ["desktop", "ide", "tui"],
            "accepted_runtimes": ["threadvault-local-tui"],
            "server_required": False,
        },
        "desktop_app": {
            "module": "threadvault.desktop_app",
            "data_module": "threadvault.desktop_data",
            "status": "primary_local_interface",
            "recommended_for_daily_use": True,
            "launch_command": PRIMARY_LOCAL_INTERFACE_COMMAND,
            "smoke_command": PRIMARY_LOCAL_INTERFACE_SMOKE_COMMAND,
            "contract_version": "desktop_app.v2",
            "smoke_contract_version": "desktop_smoke.v2",
            "toolkit": "tkinter",
            "major_release_target": MAJOR_RELEASE_TARGET,
            "server_required": False,
            "browser_required": False,
            "frontend_build_pipeline": False,
            "cloud_sync": False,
            "background_worker_threads": True,
            "store_interface": [
                "client_overview",
                "client_session",
                "client_export_preview",
                "export_target",
                "client_warnings",
                "stats",
                "doctor",
                "backup",
                "storage_auto_backup",
                "verify_backup",
                "restore_plan",
                "restore",
                "reindex",
                "vacuum",
                "schema_names",
                "write_schema_files",
                "robot_guide",
                "robot_schemas",
            ],
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
            "interface_policy": "object",
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
            "process": "object|null",
            "hook_response": "object",
        },
        "codex_hook_config": {
            "hooks": "object",
        },
        "codex_hook_install": {
            "ok": "boolean",
            "apply": "boolean",
            "path": "string",
            "action": "string",
            "config": "object",
            "trust_required": "boolean",
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
