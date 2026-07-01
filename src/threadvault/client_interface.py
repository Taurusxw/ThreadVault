from __future__ import annotations

import sqlite3
from typing import Any

from .agent_interface import AgentRetrievalRequest, agent_retrieve
from .app_config import AppConfig
from .governance import governance_status

CLIENT_INTERFACE_CONTRACT_VERSION = "client_interface.v1"
CLIENT_OVERVIEW_CONTRACT_VERSION = "client_overview.v1"
CLIENT_SESSION_CONTRACT_VERSION = "client_session.v1"
CLIENT_EXPORT_PREVIEW_CONTRACT_VERSION = "client_export_preview.v1"
CLIENT_WARNINGS_CONTRACT_VERSION = "client_warnings.v1"
CLIENT_FAMILIES = ["desktop", "ide", "web", "tui", "server"]


def client_manifest(config: AppConfig, capabilities_payload: dict[str, Any], robot_guide_payload: dict[str, Any]) -> dict[str, Any]:
    feature_flags = capabilities_payload["feature_flags"]
    return {
        "contract_version": CLIENT_INTERFACE_CONTRACT_VERSION,
        "interface": {
            "name": "threadvault-client-manifest",
            "version": "v1",
            "module": "threadvault.client_interface",
            "client_families": CLIENT_FAMILIES,
        },
        "client_families": [
            _family(
                "desktop",
                status="planned",
                server_required=False,
                recommended_entrypoints=["threadvault client manifest --json", "threadvault agent retrieve QUERY --json"],
            ),
            _family(
                "ide",
                status="planned",
                server_required=False,
                recommended_entrypoints=[
                    "threadvault client manifest --json",
                    "threadvault export-target markdown --project CWD --out OUT --json",
                    "threadvault agent retrieve QUERY --cwd CWD --json",
                ],
            ),
            _family(
                "web",
                status="planned",
                server_required=False,
                recommended_entrypoints=["threadvault client manifest --json", "threadvault agent retrieve QUERY --json"],
            ),
            _family(
                "tui",
                status="accepted_minimal_runtime",
                server_required=False,
                recommended_entrypoints=[
                    "threadvault client tui --json",
                    "threadvault client tui --query QUERY --json",
                    "threadvault client tui --export-preview-session SESSION_ID --out OUT --json",
                ],
            ),
            _family(
                "server",
                status="deferred",
                server_required=False,
                opt_in=True,
                recommended_entrypoints=["threadvault client manifest --json", "threadvault capabilities --json"],
            ),
        ],
        "entrypoints": {
            "discovery": [
                "threadvault client manifest --json",
                "threadvault client overview --json",
                "threadvault client tui --json",
                "threadvault client session --session SESSION_ID --json",
                "threadvault client export-preview --session SESSION_ID --out OUT --json",
                "threadvault client warnings --session SESSION_ID --json",
                "threadvault capabilities --json",
                "threadvault robot-docs guide --json",
            ],
            "retrieval": [
                "threadvault client overview --query QUERY --json",
                "threadvault client tui --query QUERY --json",
                "threadvault agent retrieve QUERY --json",
                "threadvault retrieval hybrid QUERY --json",
            ],
            "export": [
                "threadvault client tui --export-preview-session SESSION_ID --out OUT --json",
                "threadvault client export-preview --session SESSION_ID --out OUT --json",
                "threadvault client warnings --session SESSION_ID --json",
                "threadvault export-target markdown --session SESSION_ID --out OUT --json",
                "threadvault export-target obsidian --project CWD --out OUT --json",
                "threadvault export-target skill --project CWD --out OUT --skill-name NAME --json",
            ],
            "vector": [
                "threadvault vector status --json",
                "threadvault vector index --session SESSION_ID --config threadvault.toml --json",
            ],
            "schemas": ["threadvault schemas list --json", "threadvault schemas show client_interface_manifest --json"],
        },
        "schemas": {
            "manifest": "client_interface_manifest",
            "overview": "client_overview",
            "tui_runtime": "client_tui_runtime",
            "session": "client_session",
            "export_preview": "client_export_preview",
            "warnings": "client_warnings",
            "agent": robot_guide_payload["agent_interface"]["schemas"],
            "retrieval": robot_guide_payload["retrieval"]["schemas"],
            "summary": robot_guide_payload["summary_pipeline"]["schemas"],
            "vector": robot_guide_payload["vector"]["schemas"],
            "export": ["export_target_manifest"],
            "governance": "governance_status",
        },
        "defaults": {
            "local_first": feature_flags["local_first"],
            "server_required": False,
            "server_available": False,
            "server_opt_in": True,
            "cloud_sync": feature_flags["cloud_sync"],
            "external_model_calls": feature_flags["external_llm_summary"],
            "raw_paths_in_default_output": False,
            "vector_enabled_by_default": feature_flags["local_vector_enabled_by_default"],
            "local_vector_enabled": config.vector_enabled,
        },
        "integration_policy": {
            "reuse_existing_interfaces": True,
            "do_not_reparse_codex_transcripts": True,
            "do_not_bypass_privacy_scan_for_export": True,
            "prefer_agent_retrieval_for_search": True,
            "local_debug_metadata_opt_in": True,
        },
        "governance": governance_status(config),
    }


def _family(
    name: str,
    status: str,
    server_required: bool,
    recommended_entrypoints: list[str],
    opt_in: bool = False,
) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "server_required": server_required,
        "opt_in": opt_in,
        "recommended_entrypoints": recommended_entrypoints,
    }


def client_overview(
    conn: sqlite3.Connection,
    *,
    sessions: list[Any],
    config: AppConfig,
    query: str | None = None,
    cwd: str | None = None,
    limit: int = 20,
    local_debug: bool = False,
) -> dict[str, Any]:
    search_payload = None
    if query:
        search_payload = agent_retrieve(
            conn,
            AgentRetrievalRequest(text=query, limit=limit, cwd=cwd, local_debug=local_debug),
            config,
        )
    return {
        "contract_version": CLIENT_OVERVIEW_CONTRACT_VERSION,
        "request": {
            "query": query,
            "cwd": cwd,
            "limit": limit,
            "local_debug": local_debug,
        },
        "sessions": [_session_payload(session, local_debug=local_debug) for session in sessions],
        "search": _search_payload(search_payload),
        "actions": {
            "refresh": "threadvault client overview --json",
            "search": "threadvault client overview --query QUERY --json",
            "export_markdown": "threadvault export-target markdown --session SESSION_ID --out OUT --json",
            "open_agent_retrieval": "threadvault agent retrieve QUERY --json",
        },
        "privacy": {
            "local_first": True,
            "raw_paths_included": local_debug,
            "local_debug": local_debug,
            "external_model_calls": False,
        },
        "diagnostics": {
            "mode": "browse_search_overview",
            "session_count": len(sessions),
            "search_result_count": len(search_payload["results"]) if search_payload else 0,
            "vector_enabled": config.vector_enabled,
            "server_required": False,
        },
    }


def client_session_detail(
    *,
    session: Any,
    summary: Any,
    events: list[dict[str, Any]],
    event_limit: int = 20,
    max_chars: int = 500,
    local_debug: bool = False,
) -> dict[str, Any]:
    visible_events = events[:event_limit]
    return {
        "contract_version": CLIENT_SESSION_CONTRACT_VERSION,
        "request": {
            "session_id": session["session_id"],
            "event_limit": event_limit,
            "max_chars": max_chars,
            "local_debug": local_debug,
        },
        "session": _session_detail_payload(session, local_debug=local_debug),
        "summary": _summary_payload(summary),
        "events": [_event_preview(event, max_chars=max_chars, local_debug=local_debug) for event in visible_events],
        "actions": {
            "overview": "threadvault client overview --json",
            "search_within_session": f"threadvault agent retrieve QUERY --session {session['session_id']} --json",
            "export_markdown": f"threadvault export-target markdown --session {session['session_id']} --out OUT --json",
            "export_json": f"threadvault export --session {session['session_id']} --format json --out OUT --json",
        },
        "privacy": {
            "local_first": True,
            "raw_paths_included": local_debug,
            "event_file_paths_included": local_debug,
            "raw_transcript_included": False,
            "external_model_calls": False,
        },
        "diagnostics": {
            "mode": "session_detail",
            "event_count": session["event_count"],
            "events_returned": len(visible_events),
            "events_truncated": max(session["event_count"] - len(visible_events), 0),
            "summary_evidence_count": len(summary.evidence_event_ids),
            "server_required": False,
        },
    }


def client_export_preview(
    preview: dict[str, Any],
    execute_command: str,
    governance_instrumentation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "contract_version": CLIENT_EXPORT_PREVIEW_CONTRACT_VERSION,
        "request": {
            "profile": preview["target_profile"],
            "root": preview["root"],
            "sessions": preview["selection"]["sessions"],
            "project": preview["selection"]["project"],
            "privacy_mode": preview["privacy"]["mode"],
        },
        "selection": preview["selection"],
        "planned_files": preview["files"],
        "skipped": preview["skipped"],
        "privacy": {
            **preview["privacy"],
            "blocked": any(item.get("reason") == "high_risk_privacy_findings" for item in preview["skipped"]),
        },
        "evidence": preview["evidence"],
        "actions": {
            "execute": execute_command,
            "manifest_name": "threadvault-export-manifest.json",
        },
        "governance_instrumentation": governance_instrumentation or _governance_instrumentation_disabled(),
        "diagnostics": {
            **preview["diagnostics"],
            "server_required": False,
            "external_model_calls": False,
            "governance_instrumented": bool(governance_instrumentation and governance_instrumentation["enabled"]),
            "governance_blocked": bool(governance_instrumentation and governance_instrumentation["blocked"]),
        },
    }


def blocked_client_export_preview(
    *,
    profile: str,
    out_dir: Any,
    session_ids: list[str],
    project: str | None,
    privacy_mode: str,
    execute_command: str,
    governance_instrumentation: dict[str, Any],
) -> dict[str, Any]:
    root = str(out_dir.expanduser()) if hasattr(out_dir, "expanduser") else str(out_dir)
    return {
        "contract_version": CLIENT_EXPORT_PREVIEW_CONTRACT_VERSION,
        "request": {
            "profile": profile,
            "root": root,
            "sessions": session_ids,
            "project": project,
            "privacy_mode": privacy_mode,
        },
        "selection": {
            "sessions": session_ids,
            "project": project,
            "selected_session_ids": [],
        },
        "planned_files": [],
        "skipped": [
            {
                "kind": "governance",
                "reason": "governance_preflight_blocked",
                "preflight_status": governance_instrumentation["preflight"]["enforcement"]["preflight_status"],
            }
        ],
        "privacy": {
            "mode": privacy_mode,
            "findings_count": 0,
            "effective_findings_count": 0,
            "blocked": False,
        },
        "evidence": {
            "event_ids": [],
            "sessions_with_evidence": [],
        },
        "actions": {
            "execute": execute_command,
            "manifest_name": "threadvault-export-manifest.json",
        },
        "governance_instrumentation": governance_instrumentation,
        "diagnostics": {
            "preview": False,
            "writes_files": False,
            "manifest_written": False,
            "planned_file_count": 0,
            "skipped_count": 1,
            "server_required": False,
            "external_model_calls": False,
            "governance_instrumented": True,
            "governance_blocked": True,
        },
    }


def _governance_instrumentation_disabled() -> dict[str, Any]:
    return {
        "enabled": False,
        "blocked": False,
        "reason": "not_requested",
        "role": None,
        "actor": None,
        "audit_log": None,
        "preflight": None,
    }


def client_warnings_detail(
    *,
    session: Any,
    warnings: list[Any],
    privacy_scan: dict[str, Any],
    local_debug: bool = False,
) -> dict[str, Any]:
    privacy_summary = privacy_scan["summary"]
    return {
        "contract_version": CLIENT_WARNINGS_CONTRACT_VERSION,
        "request": {
            "session_id": session["session_id"],
            "local_debug": local_debug,
        },
        "session": _session_warning_payload(session, local_debug=local_debug),
        "warnings": {
            "items": [_warning_payload(warning, local_debug=local_debug) for warning in warnings],
            "summary": _warning_summary(warnings),
            "count": len(warnings),
        },
        "privacy": {
            "rules_version": privacy_scan["rules_version"],
            "config_path": privacy_scan.get("config_path") if local_debug else None,
            "findings": [_privacy_finding_payload(finding, local_debug=local_debug) for finding in privacy_scan["findings"]],
            "summary": privacy_summary,
            "has_effective_findings": privacy_summary["effective_findings_count"] > 0,
            "raw_paths_included": local_debug,
            "raw_transcript_included": False,
            "external_model_calls": False,
        },
        "actions": {
            "session_detail": f"threadvault client session --session {session['session_id']} --json",
            "privacy_scan": f"threadvault privacy-scan --session {session['session_id']} --json",
            "export_preview": f"threadvault client export-preview --session {session['session_id']} --out OUT --json",
            "config_show": "threadvault config show --json",
        },
        "diagnostics": {
            "mode": "warning_detail",
            "warning_count": len(warnings),
            "privacy_finding_count": privacy_summary["total"],
            "effective_privacy_finding_count": privacy_summary["effective_findings_count"],
            "server_required": False,
            "local_debug": local_debug,
        },
    }


def _session_payload(session: Any, local_debug: bool) -> dict[str, Any]:
    payload = {
        "session_id": session.session_id,
        "cwd": session.cwd,
        "source_kind": session.source_kind,
        "first_seen_at": session.first_seen_at,
        "updated_at": session.updated_at,
        "event_count": session.event_count,
        "warning_count": session.warning_count,
    }
    if local_debug:
        payload["raw_path"] = session.raw_path
    return payload


def _session_detail_payload(session: Any, local_debug: bool) -> dict[str, Any]:
    payload = {
        "session_id": session["session_id"],
        "parent_session_id": session["parent_session_id"],
        "cwd": session["cwd"],
        "source_kind": session["source_kind"],
        "model_provider": session["model_provider"],
        "first_seen_at": session["first_seen_at"],
        "updated_at": session["updated_at"],
        "archived": bool(session["archived"]),
        "event_count": session["event_count"],
        "warning_count": session["warning_count"],
    }
    if local_debug:
        payload["raw_path"] = session["raw_path"]
    return payload


def _session_warning_payload(session: Any, local_debug: bool) -> dict[str, Any]:
    payload = {
        "session_id": session["session_id"],
        "cwd": session["cwd"],
        "source_kind": session["source_kind"],
        "first_seen_at": session["first_seen_at"],
        "updated_at": session["updated_at"],
        "warning_count": session["warning_count"],
    }
    if local_debug:
        payload["raw_path"] = session["raw_path"]
    return payload


def _warning_payload(warning: Any, local_debug: bool) -> dict[str, Any]:
    payload = {
        "warning_id": warning["warning_id"],
        "session_id": warning["session_id"],
        "line_no": warning["line_no"],
        "code": warning["code"],
        "message": warning["message"],
        "created_at": warning["created_at"],
    }
    if local_debug:
        payload["raw_path"] = warning["raw_path"]
        payload["raw_excerpt"] = warning["raw_excerpt"]
    return payload


def _warning_summary(warnings: list[Any]) -> dict[str, Any]:
    by_code: dict[str, int] = {}
    for warning in warnings:
        code = warning["code"]
        by_code[code] = by_code.get(code, 0) + 1
    return {"by_code": by_code}


def _privacy_finding_payload(finding: dict[str, Any], local_debug: bool) -> dict[str, Any]:
    payload = {
        "kind": finding["kind"],
        "severity": finding["severity"],
        "allowlisted": finding["allowlisted"],
        "excerpt": finding["excerpt"],
    }
    if finding["kind"] in {"windows_abs_path", "posix_abs_path"} and not local_debug:
        payload["excerpt"] = "[local path omitted]"
    if local_debug:
        payload["start"] = finding["start"]
        payload["end"] = finding["end"]
    return payload


def _summary_payload(summary: Any) -> dict[str, Any]:
    return {
        "session_id": summary.session_id,
        "topic": summary.topic,
        "user_goal": summary.user_goal,
        "key_steps": summary.key_steps,
        "key_commands": summary.key_commands,
        "files": summary.files,
        "problems": summary.problems,
        "next_steps": summary.next_steps,
        "evidence_event_ids": summary.evidence_event_ids,
        "evidence_coverage": summary.evidence_coverage,
        "missing_evidence_warnings": summary.missing_evidence_warnings,
    }


def _event_preview(event: dict[str, Any], max_chars: int, local_debug: bool) -> dict[str, Any]:
    text = str(_row_value(event, "text_content") or "")
    truncated = len(text) > max_chars
    payload = {
        "event_id": _row_value(event, "event_id"),
        "turn_id": _row_value(event, "turn_id"),
        "turn_index": _row_value(event, "turn_index"),
        "timestamp": _row_value(event, "timestamp"),
        "top_type": _row_value(event, "top_type"),
        "sub_type": _row_value(event, "sub_type"),
        "role": _row_value(event, "role"),
        "tool_name": _row_value(event, "tool_name"),
        "text_preview": text[:max_chars],
        "truncated": truncated,
    }
    if local_debug:
        payload["file_path"] = _row_value(event, "file_path")
        payload["line_no"] = _row_value(event, "line_no")
    return payload


def _row_value(row: Any, key: str) -> Any:
    return row[key]


def _search_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    if payload is None:
        return {
            "query": None,
            "results": [],
            "diagnostics": {
                "used_mode": None,
                "capabilities_used": [],
                "result_count": 0,
            },
        }
    return {
        "query": payload["request"]["text"],
        "results": payload["results"],
        "diagnostics": payload["diagnostics"],
    }
