from __future__ import annotations

from typing import Any

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

CLIENT_TUI_RUNTIME_CONTRACT_VERSION = "client_tui_runtime.v1"


def client_tui_runtime(
    *,
    overview: dict[str, Any],
    export_preview: dict[str, Any] | None = None,
) -> dict[str, Any]:
    query = overview["request"]["query"]
    screen = {
        "title": "ThreadVault Local TUI",
        "sections": _screen_sections(overview, export_preview),
        "session_rows": [_session_row(session) for session in overview["sessions"]],
        "search_rows": [_search_row(result) for result in overview["search"]["results"]],
        "export_rows": _export_rows(export_preview),
    }
    return {
        "contract_version": CLIENT_TUI_RUNTIME_CONTRACT_VERSION,
        "runtime": {
            "name": "threadvault-local-tui",
            "family": "tui",
            "status": "accepted_minimal_runtime",
            "module": "threadvault.client_runtime",
            "server_required": False,
            "cloud_sync": False,
        },
        "request": {
            "query": query,
            "cwd": overview["request"]["cwd"],
            "limit": overview["request"]["limit"],
            "local_debug": overview["request"]["local_debug"],
            "export_preview_requested": export_preview is not None,
            "export_preview_session": (
                export_preview["request"]["sessions"][0]
                if export_preview is not None and export_preview["request"]["sessions"]
                else None
            ),
            "export_preview_profile": export_preview["request"]["profile"] if export_preview is not None else None,
        },
        "screen": screen,
        "overview": overview,
        "export_preview": export_preview,
        "actions": {
            "refresh": "threadvault client tui --json",
            "search": "threadvault client tui --query QUERY --json",
            "open_overview_contract": "threadvault client overview --json",
            "open_agent_retrieval": "threadvault agent retrieve QUERY --json",
            "preview_export": "threadvault client tui --export-preview-session SESSION_ID --out OUT --json",
            "execute_export": export_preview["actions"]["execute"] if export_preview is not None else None,
        },
        "privacy": {
            "local_first": True,
            "raw_paths_included": overview["privacy"]["raw_paths_included"],
            "raw_transcript_included": False,
            "server_required": False,
            "server_opt_in": True,
            "cloud_sync": False,
            "external_model_calls": False,
            "export_preview_writes_files": (
                export_preview["diagnostics"]["writes_files"] if export_preview is not None else False
            ),
        },
        "diagnostics": {
            "mode": "local_tui_runtime",
            "accepted_runtime": True,
            "session_count": overview["diagnostics"]["session_count"],
            "search_result_count": overview["diagnostics"]["search_result_count"],
            "export_preview_included": export_preview is not None,
            "export_preview_planned_file_count": (
                export_preview["diagnostics"]["planned_file_count"] if export_preview is not None else 0
            ),
            "overview_contract_version": overview["contract_version"],
            "export_preview_contract_version": export_preview["contract_version"] if export_preview is not None else None,
            "server_required": False,
            "v2_retrieval_reused": bool(query),
        },
    }


def render_client_tui(payload: dict[str, Any]) -> Group:
    title = Text(payload["screen"]["title"], style="bold cyan")
    summary = Table.grid(expand=False, padding=(0, 1))
    summary.add_column(style="bold")
    summary.add_column()
    summary.add_row("Runtime", payload["runtime"]["status"])
    summary.add_row("Sessions", str(payload["diagnostics"]["session_count"]))
    summary.add_row("Search results", str(payload["diagnostics"]["search_result_count"]))
    summary.add_row("Server required", str(payload["privacy"]["server_required"]))
    summary.add_row("External models", str(payload["privacy"]["external_model_calls"]))

    sessions_table = Table(title="Sessions")
    sessions_table.add_column("Session")
    sessions_table.add_column("Updated")
    sessions_table.add_column("Events", justify="right")
    sessions_table.add_column("Warnings", justify="right")
    for row in payload["screen"]["session_rows"]:
        sessions_table.add_row(row["session_id"], row["updated_at"] or "", str(row["event_count"]), str(row["warning_count"]))

    search_table = Table(title="Search")
    search_table.add_column("Session")
    search_table.add_column("Score")
    search_table.add_column("Snippet")
    for row in payload["screen"]["search_rows"]:
        search_table.add_row(row["session_id"], row["score"], row["snippet"])

    export_table = Table(title="Export Preview")
    export_table.add_column("Kind")
    export_table.add_column("Session")
    export_table.add_column("Path")
    for row in payload["screen"]["export_rows"]:
        export_table.add_row(row["kind"], row["session_id"] or "", row["path"])

    renderables: list[Any] = [Panel(Group(title, summary), title="ThreadVault")]
    if payload["screen"]["session_rows"]:
        renderables.append(sessions_table)
    if payload["request"]["query"] is not None:
        renderables.append(search_table)
    if payload["export_preview"] is not None:
        renderables.append(export_table)
    return Group(*renderables)


def _screen_sections(overview: dict[str, Any], export_preview: dict[str, Any] | None) -> list[dict[str, Any]]:
    sections = [
        {
            "name": "sessions",
            "title": "Sessions",
            "visible": True,
            "count": len(overview["sessions"]),
        },
        {
            "name": "search",
            "title": "Search",
            "visible": overview["request"]["query"] is not None,
            "count": len(overview["search"]["results"]),
        },
        {
            "name": "export_preview",
            "title": "Export Preview",
            "visible": export_preview is not None,
            "count": len(export_preview["planned_files"]) if export_preview is not None else 0,
        },
    ]
    return sections


def _session_row(session: dict[str, Any]) -> dict[str, Any]:
    return {
        "session_id": session["session_id"],
        "cwd": session["cwd"],
        "updated_at": session.get("updated_at") or session.get("first_seen_at"),
        "event_count": session["event_count"],
        "warning_count": session["warning_count"],
    }


def _search_row(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "session_id": result["session_id"],
        "score": str(result.get("score") or result.get("rank") or ""),
        "snippet": str(result.get("snippet") or result.get("text") or "")[:160],
        "evidence_event_ids": result.get("evidence_event_ids", []),
    }


def _export_rows(export_preview: dict[str, Any] | None) -> list[dict[str, Any]]:
    if export_preview is None:
        return []
    return [
        {
            "kind": file["kind"],
            "session_id": file.get("session_id"),
            "path": file["path"],
        }
        for file in export_preview["planned_files"]
    ]
