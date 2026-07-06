from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from .app_config import describe_app_config, diagnose_app_config, init_app_config
from .audit import (
    diff_audit_reports,
    diff_latest_audit_reports,
    latest_audit_report,
    list_audit_reports,
    load_audit_report,
    prune_audit_history,
    write_audit_report,
)
from .backup_history import latest_backup_file, list_backup_files, prune_backup_history, verify_latest_backup
from .client_runtime import render_client_tui
from .codex_hooks import hook_continue_response, invalid_hook_payload_result
from .config import default_db_path
from .importer import sample_codex_home
from .mcp import McpRuntimeConfig, mcp_manifest, serve_mcp
from .privacy import has_high_risk
from .retention import resolve_retention_keep
from .schemas import get_schema, schema_names, validate_payload, write_schema_files
from .shared_server import build_read_only_server
from .store import ArchiveStore, capabilities, robot_guide, robot_schemas
from .summarizer import summary_to_markdown

app = typer.Typer(help="ThreadVault: local-first Codex session archive.")
console = Console()


def _db_option(value: Path | None, config: Path | None = None) -> Path:
    return (value or default_db_path(config)).expanduser()


def _store(db: Path | None, config: Path | None = None) -> ArchiveStore:
    return ArchiveStore(_db_option(db, config))


def _print_json(value) -> None:
    typer.echo(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def _maybe_governance_instrumentation(
    db: Path | None,
    *,
    command: str,
    role: str | None,
    config: Path | None = None,
    audit_log: Path | None = None,
    actor: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
) -> dict | None:
    if role is None:
        return None
    return _store(db).governance_business_command_instrumentation(
        config_path=config,
        command=command,
        role=role,
        audit_log=audit_log,
        actor=actor,
        target_type=target_type,
        target_id=target_id,
    )


def _governance_blocked(instrumentation: dict | None) -> bool:
    return bool(instrumentation and instrumentation["instrumentation"]["blocked"])


def _emit_governance_blocked(command: str, instrumentation: dict, json_output: bool) -> None:
    payload = {
        "ok": False,
        "error": "governance_preflight_blocked",
        "command": command,
        "governance_instrumentation": instrumentation,
    }
    if json_output:
        _print_json(payload)
    else:
        console.print(f"[red]Blocked by governance preflight:[/red] {escape(command)}")
    raise typer.Exit(code=2)


def _mark_governance_executed(instrumentation: dict | None) -> None:
    if instrumentation is None:
        return
    instrumentation["execution"]["business_command_executed"] = True
    preflight = instrumentation.get("preflight")
    if isinstance(preflight, dict) and isinstance(preflight.get("execution"), dict):
        preflight["execution"]["business_command_executed"] = True


def _attach_governance(payload: dict, instrumentation: dict | None) -> dict:
    if instrumentation is not None:
        payload["governance_instrumentation"] = instrumentation
    return payload


@app.callback()
def main() -> None:
    """Archive, search, summarize, and export local Codex JSONL sessions."""


@app.command("init")
def init_command(
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
) -> None:
    """Initialize the local SQLite database."""
    db_path = _db_option(db)
    _store(db).init()
    console.print(f"[green]Initialized database:[/green] {db_path}")


@app.command("import")
def import_command(
    codex_home: Annotated[Path | None, typer.Option("--codex-home", help="Codex home directory.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Import .jsonl sessions from Codex sessions and archived_sessions."""
    stats = _store(db).import_codex(codex_home)
    payload = stats.__dict__
    if json_output:
        _print_json(payload)
        return
    console.print(
        "[green]Import complete[/green] "
        f"discovered={stats.discovered} imported={stats.imported} skipped={stats.skipped} "
        f"failed={stats.failed} events={stats.events} warnings={stats.warnings}"
    )


@app.command("list")
def list_command(
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, max=500)] = 50,
    cwd: Annotated[str | None, typer.Option("--cwd", help="Filter by project cwd.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """List imported sessions."""
    rows = _store(db).list(limit=limit, cwd=cwd)
    if json_output:
        _print_json([row.model_dump() for row in rows])
        return
    table = Table(title="ThreadVault Sessions")
    table.add_column("Session")
    table.add_column("Updated")
    table.add_column("CWD")
    table.add_column("Events", justify="right")
    table.add_column("Warnings", justify="right")
    for row in rows:
        table.add_row(
            escape(row.session_id),
            escape(row.updated_at or row.first_seen_at or ""),
            escape(row.cwd or ""),
            str(row.event_count),
            str(row.warning_count),
        )
    console.print(table)


@app.command("search")
def search_command(
    query: Annotated[str, typer.Argument(help="FTS query.")],
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, max=100)] = 20,
    session: Annotated[str | None, typer.Option("--session", help="Filter by session id.")] = None,
    cwd: Annotated[str | None, typer.Option("--cwd", help="Filter by project cwd.")] = None,
    since: Annotated[str | None, typer.Option("--since", help="Filter events after this timestamp.")] = None,
    until: Annotated[str | None, typer.Option("--until", help="Filter events before this timestamp.")] = None,
    type_filter: Annotated[str | None, typer.Option("--type", help="Filter by top_type or sub_type.")] = None,
    tool: Annotated[str | None, typer.Option("--tool", help="Filter by tool name.")] = None,
    fields: Annotated[str, typer.Option("--fields", help="minimal, standard, or full.")] = "standard",
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Search imported events with SQLite FTS5."""
    if fields not in {"minimal", "standard", "full"}:
        raise typer.BadParameter("--fields must be minimal, standard, or full.")
    rows = _store(db).search(
        query=query,
        limit=limit,
        session_id=session,
        cwd=cwd,
        since=since,
        until=until,
        top_type=type_filter,
        tool=tool,
        fields=fields,
    )
    if json_output:
        _print_json([_search_payload(row, fields) for row in rows])
        return
    table = Table(title=f"Search: {query}")
    table.add_column("Event", justify="right")
    table.add_column("Session")
    table.add_column("Type")
    table.add_column("Snippet")
    for row in rows:
        table.add_row(
            str(row.event_id),
            escape(row.session_id),
            escape(f"{row.top_type}/{row.sub_type or ''}"),
            escape(row.snippet or ""),
        )
    console.print(table)


@app.command("export")
def export_command(
    session: Annotated[str | None, typer.Option("--session", help="Session id to export.")] = None,
    project: Annotated[str | None, typer.Option("--project", help="Project cwd to export index for.")] = None,
    out: Annotated[Path, typer.Option("--out", "-o", help="Output directory.")] = Path("threadvault-export"),
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    format: Annotated[str, typer.Option("--format", help="md, json, jsonl, or csv.")] = "md",
    profile: Annotated[str, typer.Option("--profile", help="full, brief, agent, or review.")] = "full",
    brief: Annotated[bool, typer.Option("--brief", help="Export a concise summary markdown.")] = False,
    include: Annotated[list[str] | None, typer.Option("--include", help="Include top_type/sub_type.")] = None,
    exclude: Annotated[list[str] | None, typer.Option("--exclude", help="Exclude top_type/sub_type.")] = None,
    last_turns: Annotated[int | None, typer.Option("--last-turns", min=1, help="Only export last N turns.")] = None,
    max_chars: Annotated[int | None, typer.Option("--max-chars", min=1, help="Max chars per event text.")] = None,
    max_tool_chars: Annotated[int | None, typer.Option("--max-tool-chars", min=1, help="Max chars per tool output.")] = None,
    no_tool_output: Annotated[bool, typer.Option("--no-tool-output", help="Exclude function_call_output events.")] = False,
    no_reasoning: Annotated[bool, typer.Option("--no-reasoning", help="Exclude reasoning events.")] = False,
    privacy_mode: Annotated[str, typer.Option("--privacy-mode", help="warn, redact, or fail.")] = "warn",
    privacy_config: Annotated[Path | None, typer.Option("--privacy-config", help="Optional threadvault.toml privacy config.")] = None,
    governance_role: Annotated[str | None, typer.Option("--governance-role", help="Role for explicit governance preflight.")] = None,
    governance_config: Annotated[
        Path | None,
        typer.Option("--governance-config", help="Optional threadvault.toml for governance preflight."),
    ] = None,
    governance_audit_log: Annotated[
        Path | None,
        typer.Option("--governance-audit-log", help="Optional local audit JSONL path for governance preflight."),
    ] = None,
    governance_actor: Annotated[str | None, typer.Option("--governance-actor", help="Actor for governance audit metadata.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Export a session or project index to Markdown."""
    if not session and not project:
        raise typer.BadParameter("Provide --session or --project.")
    if format not in {"md", "json", "jsonl", "csv"}:
        raise typer.BadParameter("--format must be md, json, jsonl, or csv.")
    if profile not in {"full", "brief", "agent", "review"}:
        raise typer.BadParameter("--profile must be full, brief, agent, or review.")
    if privacy_mode not in {"warn", "redact", "fail"}:
        raise typer.BadParameter("--privacy-mode must be warn, redact, or fail.")
    if project and format != "md":
        raise typer.BadParameter("Project export currently supports --format md only.")
    governance = _maybe_governance_instrumentation(
        db,
        command="threadvault export",
        role=governance_role,
        config=governance_config,
        audit_log=governance_audit_log,
        actor=governance_actor,
        target_type="session" if session else "project",
        target_id=session or project,
    )
    if _governance_blocked(governance):
        _emit_governance_blocked("threadvault export", governance, json_output)
    store = _store(db)
    try:
        if session:
            path, findings = store.export_session(
                session,
                out,
                fmt=format,
                profile=profile,
                brief=brief,
                include=include,
                exclude=exclude,
                last_turns=last_turns,
                max_chars=max_chars,
                max_tool_chars=max_tool_chars,
                no_tool_output=no_tool_output,
                no_reasoning=no_reasoning,
                privacy_mode=privacy_mode,
                privacy_config_path=privacy_config,
            )
        else:
            assert project is not None
            path, findings = store.export_project(project, out)
    except KeyError as exc:
        raise typer.BadParameter(f"Unknown session: {exc.args[0]}") from exc
    _mark_governance_executed(governance)
    payload = _attach_governance({"path": str(path), "privacy_findings": [finding.__dict__ for finding in findings]}, governance)
    if privacy_mode == "fail" and has_high_risk(findings):
        if json_output:
            _print_json({**payload, "ok": False, "error": "high_risk_privacy_findings"})
        raise typer.Exit(code=2)
    if json_output:
        _print_json(payload)
        return
    console.print(f"[green]Exported:[/green] {path}")
    _print_privacy_findings(findings)


@app.command("summarize")
def summarize_command(
    session: Annotated[str, typer.Option("--session", help="Session id to summarize.")],
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    format: Annotated[str, typer.Option("--format", help="json or markdown.")] = "markdown",
    json_output: Annotated[bool, typer.Option("--json", help="Alias for --format json.")] = False,
) -> None:
    """Generate a local rule-based summary with evidence event ids."""
    try:
        summary = _store(db).summarize(session)
    except KeyError as exc:
        raise typer.BadParameter(f"Unknown session: {exc.args[0]}") from exc
    if json_output:
        format = "json"
    if format == "json":
        _print_json(summary.model_dump())
    elif format == "markdown":
        console.print(summary_to_markdown(summary))
    else:
        raise typer.BadParameter("--format must be json or markdown.")


@app.command("stats")
def stats_command(
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Show archive statistics."""
    payload = _store(db).stats()
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Stats")
    table.add_column("Metric")
    table.add_column("Value")
    for key, value in payload.items():
        table.add_row(escape(str(key)), escape(str(value)))
    console.print(table)


@app.command("capabilities")
def capabilities_command(
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Show supported commands, formats, and feature flags."""
    payload = capabilities()
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Capabilities")
    table.add_column("Key")
    table.add_column("Value")
    for key, value in payload.items():
        table.add_row(escape(str(key)), escape(json.dumps(value, ensure_ascii=False, default=str)))
    console.print(table)


robot_docs_app = typer.Typer(help="Machine-readable docs for agent workflows.")
app.add_typer(robot_docs_app, name="robot-docs")

schemas_app = typer.Typer(help="JSON Schema contract utilities.")
app.add_typer(schemas_app, name="schemas")

audit_history_app = typer.Typer(help="Audit report history utilities.")
app.add_typer(audit_history_app, name="audit-history")

config_app = typer.Typer(help="Local threadvault.toml configuration utilities.")
app.add_typer(config_app, name="config")

backup_history_app = typer.Typer(help="Backup history utilities.")
app.add_typer(backup_history_app, name="backup-history")

restore_history_app = typer.Typer(help="Restore history utilities.")
app.add_typer(restore_history_app, name="restore-history")

ingest_queue_app = typer.Typer(help="Ingestion automation queue utilities.")
app.add_typer(ingest_queue_app, name="ingest-queue")

codex_hook_app = typer.Typer(help="Codex Hook adapter utilities.")
app.add_typer(codex_hook_app, name="codex-hook")

export_target_app = typer.Typer(help="Batch export target utilities.")
app.add_typer(export_target_app, name="export-target")

retrieval_app = typer.Typer(help="v2 retrieval query and diagnostics utilities.")
app.add_typer(retrieval_app, name="retrieval")

summary_pipeline_app = typer.Typer(help="Summary Pipeline chunk selection utilities.")
app.add_typer(summary_pipeline_app, name="summary-pipeline")

vector_app = typer.Typer(help="Config-gated local vector adapter utilities.")
app.add_typer(vector_app, name="vector")

agent_app = typer.Typer(help="Agent-facing retrieval interface utilities.")
app.add_typer(agent_app, name="agent")

client_app = typer.Typer(help="Client-facing manifest and integration utilities.")
app.add_typer(client_app, name="client")

desktop_app = typer.Typer(help="Minimal native desktop app utilities.")
app.add_typer(desktop_app, name="desktop")

mcp_app = typer.Typer(help="Model Context Protocol stdio server utilities.")
app.add_typer(mcp_app, name="mcp")

governance_app = typer.Typer(help="Optional governance discovery utilities.")
app.add_typer(governance_app, name="governance")

governance_audit_app = typer.Typer(help="Local governance audit log utilities.")
governance_app.add_typer(governance_audit_app, name="audit")

governance_permission_app = typer.Typer(help="Governance permission preflight utilities.")
governance_app.add_typer(governance_permission_app, name="permission")

governance_enforcement_app = typer.Typer(help="Governance enforcement planning utilities.")
governance_app.add_typer(governance_enforcement_app, name="enforcement")

governance_policy_app = typer.Typer(help="Governance policy readiness utilities.")
governance_app.add_typer(governance_policy_app, name="policy")

governance_server_app = typer.Typer(help="Governance server readiness utilities.")
governance_app.add_typer(governance_server_app, name="server")

governance_v3_app = typer.Typer(help="v3 completion and acceptance audit utilities.")
governance_app.add_typer(governance_v3_app, name="v3")

governance_identity_app = typer.Typer(help="Governance identity and actor readiness utilities.")
governance_app.add_typer(governance_identity_app, name="identity")

governance_backup_app = typer.Typer(help="Governance backup and restore policy readiness utilities.")
governance_app.add_typer(governance_backup_app, name="backup")

governance_preflight_app = typer.Typer(help="Governance business preflight utilities.")
governance_app.add_typer(governance_preflight_app, name="preflight")

governance_instrumentation_app = typer.Typer(help="Governance business command instrumentation utilities.")
governance_app.add_typer(governance_instrumentation_app, name="instrumentation")


@robot_docs_app.command("guide")
def robot_docs_guide_command(
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = True,
) -> None:
    """Emit an agent-oriented usage guide."""
    payload = robot_guide()
    if json_output:
        _print_json(payload)
    else:
        console.print(payload["purpose"])


@robot_docs_app.command("schemas")
def robot_docs_schemas_command(
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = True,
) -> None:
    """Emit JSON output schemas."""
    payload = robot_schemas()
    if json_output:
        _print_json(payload)
    else:
        console.print(payload)


@retrieval_app.command("query")
def retrieval_query_command(
    query: Annotated[str, typer.Argument(help="Retrieval query text.")],
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, max=100)] = 20,
    session: Annotated[str | None, typer.Option("--session", help="Filter by session id.")] = None,
    cwd: Annotated[str | None, typer.Option("--cwd", help="Filter by project cwd.")] = None,
    since: Annotated[str | None, typer.Option("--since", help="Filter events after this timestamp.")] = None,
    until: Annotated[str | None, typer.Option("--until", help="Filter events before this timestamp.")] = None,
    type_filter: Annotated[str | None, typer.Option("--type", help="Filter by top_type or sub_type.")] = None,
    tool: Annotated[str | None, typer.Option("--tool", help="Filter by tool name.")] = None,
    fields: Annotated[str, typer.Option("--fields", help="minimal, standard, or full.")] = "standard",
    mode: Annotated[str, typer.Option("--mode", help="Retrieval mode. Currently only fts.")] = "fts",
    governance_role: Annotated[str | None, typer.Option("--governance-role", help="Role for explicit governance preflight.")] = None,
    governance_config: Annotated[
        Path | None,
        typer.Option("--governance-config", help="Optional threadvault.toml for governance preflight."),
    ] = None,
    governance_audit_log: Annotated[
        Path | None,
        typer.Option("--governance-audit-log", help="Optional local audit JSONL path for governance preflight."),
    ] = None,
    governance_actor: Annotated[str | None, typer.Option("--governance-actor", help="Actor for governance audit metadata.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Run the v2 retrieval query contract."""
    if fields not in {"minimal", "standard", "full"}:
        raise typer.BadParameter("--fields must be minimal, standard, or full.")
    if mode not in {"fts"}:
        raise typer.BadParameter("--mode must be fts.")
    governance = _maybe_governance_instrumentation(
        db,
        command="threadvault retrieval query",
        role=governance_role,
        config=governance_config,
        audit_log=governance_audit_log,
        actor=governance_actor,
        target_type="query",
        target_id=query,
    )
    if _governance_blocked(governance):
        _emit_governance_blocked("threadvault retrieval query", governance, json_output)
    payload = _store(db).retrieve(
        query=query,
        limit=limit,
        session_id=session,
        cwd=cwd,
        since=since,
        until=until,
        top_type=type_filter,
        tool=tool,
        fields=fields,
        mode=mode,
    )
    _mark_governance_executed(governance)
    _attach_governance(payload, governance)
    if json_output:
        _print_json(payload)
        return
    table = Table(title=f"Retrieval: {query}")
    table.add_column("Event", justify="right")
    table.add_column("Session")
    table.add_column("Type")
    table.add_column("Snippet")
    for row in payload["results"]:
        table.add_row(
            str(row["event_id"]),
            escape(row["session_id"]),
            escape(f"{row['top_type']}/{row.get('sub_type') or ''}"),
            escape(row.get("snippet") or ""),
        )
    console.print(table)
    diagnostics = payload["diagnostics"]
    console.print(
        f"mode={diagnostics['used_mode']} engine={diagnostics['engine']} "
        f"results={diagnostics['result_count']} index_ok={diagnostics['index_status']['ok']}"
    )


@retrieval_app.command("diagnose")
def retrieval_diagnose_command(
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Show v2 retrieval diagnostics without running a query."""
    payload = _store(db).retrieval_diagnostics()
    if json_output:
        _print_json(payload)
        return
    diagnostics = payload["diagnostics"]
    table = Table(title="ThreadVault Retrieval Diagnostics")
    table.add_column("Key")
    table.add_column("Value")
    for key, value in diagnostics.items():
        table.add_row(escape(str(key)), escape(json.dumps(value, ensure_ascii=False, default=str)))
    console.print(table)


@retrieval_app.command("hybrid")
def retrieval_hybrid_command(
    query: Annotated[str, typer.Argument(help="Hybrid retrieval query text.")],
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml for vector capability.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, max=100)] = 20,
    vector_limit: Annotated[int, typer.Option("--vector-limit", min=1, max=50)] = 10,
    session: Annotated[str | None, typer.Option("--session", help="Filter by session id.")] = None,
    cwd: Annotated[str | None, typer.Option("--cwd", help="Filter by project cwd.")] = None,
    since: Annotated[str | None, typer.Option("--since", help="Filter events after this timestamp.")] = None,
    until: Annotated[str | None, typer.Option("--until", help="Filter events before this timestamp.")] = None,
    type_filter: Annotated[str | None, typer.Option("--type", help="Filter by top_type or sub_type.")] = None,
    tool: Annotated[str | None, typer.Option("--tool", help="Filter by tool name.")] = None,
    governance_role: Annotated[str | None, typer.Option("--governance-role", help="Role for explicit governance preflight.")] = None,
    governance_config: Annotated[
        Path | None,
        typer.Option("--governance-config", help="Optional threadvault.toml for governance preflight."),
    ] = None,
    governance_audit_log: Annotated[
        Path | None,
        typer.Option("--governance-audit-log", help="Optional local audit JSONL path for governance preflight."),
    ] = None,
    governance_actor: Annotated[str | None, typer.Option("--governance-actor", help="Actor for governance audit metadata.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Run hybrid FTS/vector retrieval with explanations."""
    governance = _maybe_governance_instrumentation(
        db,
        command="threadvault retrieval hybrid",
        role=governance_role,
        config=governance_config,
        audit_log=governance_audit_log,
        actor=governance_actor,
        target_type="query",
        target_id=query,
    )
    if _governance_blocked(governance):
        _emit_governance_blocked("threadvault retrieval hybrid", governance, json_output)
    payload = _store(db).hybrid_retrieve(
        query=query,
        config_path=config,
        limit=limit,
        vector_limit=vector_limit,
        session_id=session,
        cwd=cwd,
        since=since,
        until=until,
        top_type=type_filter,
        tool=tool,
    )
    _mark_governance_executed(governance)
    _attach_governance(payload, governance)
    if json_output:
        _print_json(payload)
        return
    table = Table(title=f"Hybrid Retrieval: {query}")
    table.add_column("Score")
    table.add_column("Source")
    table.add_column("ID")
    table.add_column("Evidence")
    for row in payload["results"]:
        identifier = row["chunk_id"] or str(row["event_id"])
        table.add_row(
            f"{row['score']:.3f}",
            escape(row["source"]),
            escape(identifier),
            ", ".join(str(event_id) for event_id in row["evidence_event_ids"]),
        )
    console.print(table)
    diagnostics = payload["diagnostics"]
    console.print(
        "capabilities="
        + ",".join(diagnostics["capabilities_used"])
        + f" vector_status={diagnostics['vector']['status']}"
    )


@agent_app.command("manifest")
def agent_manifest_command(
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml for capability discovery.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Emit the agent-facing retrieval interface manifest."""
    payload = _store(None).agent_manifest(config_path=config)
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Agent Interface")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("interface", escape(payload["interface"]["name"]))
    table.add_row("default_mode", escape(payload["interface"]["default_mode"]))
    table.add_row("modes", escape(",".join(payload["interface"]["modes"])))
    table.add_row("schemas", escape(json.dumps(payload["schemas"], ensure_ascii=False)))
    console.print(table)


@client_app.command("manifest")
def client_manifest_command(
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml for capability discovery.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Emit the v3 client-facing integration manifest."""
    payload = _store(None).client_manifest(config_path=config)
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Client Interface")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("interface", escape(payload["interface"]["name"]))
    table.add_row("families", escape(",".join(payload["interface"]["client_families"])))
    table.add_row("server_required", str(payload["defaults"]["server_required"]))
    table.add_row("local_first", str(payload["defaults"]["local_first"]))
    console.print(table)


@client_app.command("overview")
def client_overview_command(
    query: Annotated[str | None, typer.Option("--query", help="Optional search query for the overview.")] = None,
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml for vector capability discovery.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    cwd: Annotated[str | None, typer.Option("--cwd", help="Filter sessions and search results by project cwd.")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, max=100)] = 20,
    local_debug: Annotated[bool, typer.Option("--local-debug", help="Include local debug metadata such as raw paths.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Emit a local client browse/search overview."""
    payload = _store(db).client_overview(
        config_path=config,
        query=query,
        cwd=cwd,
        limit=limit,
        local_debug=local_debug,
    )
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Client Overview")
    table.add_column("Session")
    table.add_column("Updated")
    table.add_column("Events", justify="right")
    table.add_column("Warnings", justify="right")
    for session in payload["sessions"]:
        table.add_row(
            escape(session["session_id"]),
            escape(session.get("updated_at") or session.get("first_seen_at") or ""),
            str(session["event_count"]),
            str(session["warning_count"]),
        )
    console.print(table)
    console.print(
        f"sessions={payload['diagnostics']['session_count']} "
        f"search_results={payload['diagnostics']['search_result_count']}"
    )


@client_app.command("tui")
def client_tui_command(
    query: Annotated[str | None, typer.Option("--query", help="Optional search query for the local TUI runtime.")] = None,
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml for vector capability discovery.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    cwd: Annotated[str | None, typer.Option("--cwd", help="Filter sessions and search results by project cwd.")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, max=100)] = 20,
    export_preview_session: Annotated[
        str | None,
        typer.Option("--export-preview-session", help="Session id to include in the runtime export preview section."),
    ] = None,
    out: Annotated[Path, typer.Option("--out", "-o", help="Future export output directory for preview mode.")] = Path(
        "threadvault-export"
    ),
    profile: Annotated[str, typer.Option("--profile", help="markdown, obsidian, or skill.")] = "markdown",
    local_debug: Annotated[bool, typer.Option("--local-debug", help="Include local debug metadata such as raw paths.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Render the accepted local v3 TUI client runtime."""
    if profile not in {"markdown", "obsidian", "skill"}:
        raise typer.BadParameter("--profile must be markdown, obsidian, or skill.")
    payload = _store(db).client_tui_runtime(
        config_path=config,
        query=query,
        cwd=cwd,
        limit=limit,
        local_debug=local_debug,
        export_preview_session=export_preview_session,
        export_preview_out=out,
        export_preview_profile=profile,
    )
    if json_output:
        _print_json(payload)
        return
    console.print(render_client_tui(payload))


@client_app.command("session")
def client_session_command(
    session: Annotated[str, typer.Option("--session", help="Session id to inspect.")],
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    event_limit: Annotated[int, typer.Option("--event-limit", min=1, max=200)] = 20,
    max_chars: Annotated[int, typer.Option("--max-chars", min=50, max=5000)] = 500,
    local_debug: Annotated[bool, typer.Option("--local-debug", help="Include local debug metadata such as raw paths.")] = False,
    governance_role: Annotated[str | None, typer.Option("--governance-role", help="Role for explicit governance preflight.")] = None,
    governance_config: Annotated[
        Path | None,
        typer.Option("--governance-config", help="Optional threadvault.toml for governance preflight."),
    ] = None,
    governance_audit_log: Annotated[
        Path | None,
        typer.Option("--governance-audit-log", help="Optional local audit JSONL path for governance preflight."),
    ] = None,
    governance_actor: Annotated[str | None, typer.Option("--governance-actor", help="Actor for governance audit metadata.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Emit a safe local client session detail payload."""
    governance = _maybe_governance_instrumentation(
        db,
        command="threadvault client session",
        role=governance_role,
        config=governance_config,
        audit_log=governance_audit_log,
        actor=governance_actor,
        target_type="session",
        target_id=session,
    )
    if _governance_blocked(governance):
        _emit_governance_blocked("threadvault client session", governance, json_output)
    try:
        payload = _store(db).client_session(
            session_id=session,
            event_limit=event_limit,
            max_chars=max_chars,
            local_debug=local_debug,
        )
    except KeyError as exc:
        raise typer.BadParameter(f"Unknown session: {exc.args[0]}") from exc
    _mark_governance_executed(governance)
    _attach_governance(payload, governance)
    if json_output:
        _print_json(payload)
        return
    table = Table(title=f"ThreadVault Client Session: {session}")
    table.add_column("Event", justify="right")
    table.add_column("Type")
    table.add_column("Preview")
    for event in payload["events"]:
        type_label = f"{event['top_type']}/{event.get('sub_type') or ''}"
        table.add_row(str(event["event_id"]), escape(type_label), escape(event["text_preview"]))
    console.print(table)
    console.print(
        f"events={payload['diagnostics']['events_returned']}/{payload['diagnostics']['event_count']} "
        f"topic={payload['summary']['topic']}"
    )


@client_app.command("export-preview")
def client_export_preview_command(
    out: Annotated[Path, typer.Option("--out", "-o", help="Future export output directory.")] = Path("threadvault-export"),
    profile: Annotated[str, typer.Option("--profile", help="markdown, obsidian, or skill.")] = "markdown",
    session: Annotated[list[str] | None, typer.Option("--session", help="Session id to include. Repeat for multiple sessions.")] = None,
    project: Annotated[str | None, typer.Option("--project", help="Project cwd to include.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    privacy_mode: Annotated[str, typer.Option("--privacy-mode", help="warn, redact, or fail.")] = "warn",
    privacy_config: Annotated[Path | None, typer.Option("--privacy-config", help="Optional threadvault.toml privacy config.")] = None,
    skill_name: Annotated[str | None, typer.Option("--skill-name", help="Skill name for skill profile previews.")] = None,
    skill_description: Annotated[
        str | None,
        typer.Option("--skill-description", help="Skill description for skill profile previews."),
    ] = None,
    governance_role: Annotated[str | None, typer.Option("--governance-role", help="Role for explicit governance preflight.")] = None,
    governance_config: Annotated[
        Path | None,
        typer.Option("--governance-config", help="Optional threadvault.toml for governance preflight."),
    ] = None,
    governance_audit_log: Annotated[
        Path | None,
        typer.Option("--governance-audit-log", help="Optional local audit JSONL path for governance preflight."),
    ] = None,
    governance_actor: Annotated[str | None, typer.Option("--governance-actor", help="Actor for governance audit metadata.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Preview a client export without writing files."""
    if profile not in {"markdown", "obsidian", "skill"}:
        raise typer.BadParameter("--profile must be markdown, obsidian, or skill.")
    if privacy_mode not in {"warn", "redact", "fail"}:
        raise typer.BadParameter("--privacy-mode must be warn, redact, or fail.")
    if not session and not project:
        raise typer.BadParameter("Provide --session or --project.")
    payload = _store(db).client_export_preview(
        out_dir=out,
        profile=profile,
        session_ids=session or [],
        project=project,
        privacy_mode=privacy_mode,
        privacy_config_path=privacy_config,
        skill_name=skill_name,
        skill_description=skill_description,
        governance_role=governance_role,
        governance_config_path=governance_config,
        governance_audit_log=governance_audit_log,
        governance_actor=governance_actor,
    )
    if json_output:
        _print_json(payload)
        return
    if payload["diagnostics"].get("governance_blocked"):
        console.print("[red]Export preview blocked by governance preflight.[/red]")
        raise typer.Exit(code=2)
    table = Table(title="ThreadVault Client Export Preview")
    table.add_column("Kind")
    table.add_column("Session")
    table.add_column("Path")
    for file in payload["planned_files"]:
        table.add_row(escape(file["kind"]), escape(file.get("session_id") or ""), escape(file["path"]))
    console.print(table)
    console.print(
        f"planned={payload['diagnostics']['planned_file_count']} "
        f"skipped={payload['diagnostics']['skipped_count']} "
        f"blocked={payload['privacy']['blocked']}"
    )


@client_app.command("warnings")
def client_warnings_command(
    session: Annotated[str, typer.Option("--session", help="Session id to inspect.")],
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    privacy_config: Annotated[Path | None, typer.Option("--privacy-config", help="Optional threadvault.toml privacy config.")] = None,
    local_debug: Annotated[bool, typer.Option("--local-debug", help="Include local debug metadata such as raw paths.")] = False,
    governance_role: Annotated[str | None, typer.Option("--governance-role", help="Role for explicit governance preflight.")] = None,
    governance_config: Annotated[
        Path | None,
        typer.Option("--governance-config", help="Optional threadvault.toml for governance preflight."),
    ] = None,
    governance_audit_log: Annotated[
        Path | None,
        typer.Option("--governance-audit-log", help="Optional local audit JSONL path for governance preflight."),
    ] = None,
    governance_actor: Annotated[str | None, typer.Option("--governance-actor", help="Actor for governance audit metadata.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Emit safe client warning and privacy detail for a session."""
    governance = _maybe_governance_instrumentation(
        db,
        command="threadvault client warnings",
        role=governance_role,
        config=governance_config,
        audit_log=governance_audit_log,
        actor=governance_actor,
        target_type="session",
        target_id=session,
    )
    if _governance_blocked(governance):
        _emit_governance_blocked("threadvault client warnings", governance, json_output)
    try:
        payload = _store(db).client_warnings(
            session_id=session,
            privacy_config_path=privacy_config,
            local_debug=local_debug,
        )
    except KeyError as exc:
        raise typer.BadParameter(f"Unknown session: {exc.args[0]}") from exc
    _mark_governance_executed(governance)
    _attach_governance(payload, governance)
    if json_output:
        _print_json(payload)
        return
    table = Table(title=f"ThreadVault Client Warnings: {session}")
    table.add_column("Code")
    table.add_column("Line", justify="right")
    table.add_column("Message")
    for warning in payload["warnings"]["items"]:
        table.add_row(escape(warning["code"]), str(warning.get("line_no") or ""), escape(warning["message"]))
    console.print(table)
    console.print(
        f"warnings={payload['diagnostics']['warning_count']} "
        f"privacy_findings={payload['diagnostics']['effective_privacy_finding_count']}"
    )


@desktop_app.command("launch")
def desktop_launch_command(
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml config path.")] = None,
    language: Annotated[str, typer.Option("--lang", help="Desktop UI language: zh or en.")] = "zh",
    limit: Annotated[int, typer.Option("--limit", min=1, max=200, help="Max sessions/results to load per refresh.")] = 20,
) -> None:
    """Launch the primary minimal native desktop app."""
    if language not in {"en", "zh"}:
        raise typer.BadParameter("--lang must be en or zh.")
    from .desktop_app import launch_desktop_app
    from .desktop_data import DesktopAppConfig

    launch_desktop_app(DesktopAppConfig(db_path=_db_option(db, config), config_path=config, language=language, limit=limit))


@desktop_app.command("smoke")
def desktop_smoke_command(
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml config path.")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, max=200, help="Max sessions/results to load.")] = 20,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Run a non-window desktop app smoke check."""
    from .desktop_data import DesktopAppConfig, run_desktop_smoke

    payload = run_desktop_smoke(DesktopAppConfig(db_path=_db_option(db, config), config_path=config, limit=limit))
    if json_output:
        _print_json(payload)
        return
    console.print(f"desktop_ok={payload['ok']} toolkit={payload['desktop']['toolkit']}")
    console.print(
        f"sessions={payload['snapshot']['session_count']} "
        f"selected={escape(payload['snapshot']['selected_session_id'])}"
    )


@mcp_app.command("manifest")
def mcp_manifest_command(
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Emit the ThreadVault MCP server manifest."""
    payload = mcp_manifest()
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault MCP Server")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("transport", escape(payload["server"]["transport"]))
    table.add_row("protocol", escape(payload["server"]["protocol_version"]))
    table.add_row("tools", str(len(payload["tools"])))
    console.print(table)


@mcp_app.command("serve")
def mcp_serve_command(
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml for capability discovery.")] = None,
) -> None:
    """Run the ThreadVault MCP stdio server."""
    serve_mcp(McpRuntimeConfig(db_path=_db_option(db, config), config_path=config))


@governance_app.command("status")
def governance_status_command(
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml governance config.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Emit opt-in governance baseline status."""
    payload = _store(db).governance_status(config_path=config)
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Governance Status")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("enabled", str(payload["enabled"]))
    table.add_row("mode", escape(payload["mode"]))
    table.add_row("server_required", str(payload["defaults"]["server_required"]))
    table.add_row("permissions_enforced", str(payload["defaults"]["permissions_enforced"]))
    console.print(table)


@governance_audit_app.command("append")
def governance_audit_append_command(
    log: Annotated[Path, typer.Option("--log", help="Local audit JSONL path.")],
    operation: Annotated[str, typer.Option("--operation", help="Sensitive operation name.")],
    actor: Annotated[str, typer.Option("--actor", help="Local actor identifier.")],
    status: Annotated[str, typer.Option("--status", help="ok, denied, failed, or preview.")],
    target_type: Annotated[str, typer.Option("--target-type", help="Target type, such as session or export.")],
    target_id: Annotated[str, typer.Option("--target-id", help="Target identifier.")],
    metadata: Annotated[list[str] | None, typer.Option("--metadata", help="Metadata key=value. Repeatable.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Append a local governance audit record."""
    payload = _store(db).governance_audit_append(
        log,
        operation=operation,
        actor=actor,
        status=status,
        target_type=target_type,
        target_id=target_id,
        metadata=_parse_metadata(metadata),
    )
    if json_output:
        _print_json(payload)
        return
    console.print(f"[green]Audit record appended:[/green] {payload['record']['record_id']}")


@governance_audit_app.command("list")
def governance_audit_list_command(
    log: Annotated[Path, typer.Option("--log", help="Local audit JSONL path.")],
    limit: Annotated[int, typer.Option("--limit", min=1, max=1000)] = 50,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """List local governance audit records."""
    payload = _store(db).governance_audit_list(log, limit=limit)
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Governance Audit")
    table.add_column("Time")
    table.add_column("Operation")
    table.add_column("Actor")
    table.add_column("Status")
    table.add_column("Target")
    for record in payload["records"]:
        target = record.get("target", {})
        table.add_row(
            escape(record.get("timestamp") or ""),
            escape(record.get("operation") or ""),
            escape(record.get("actor") or ""),
            escape(record.get("status") or ""),
            escape(f"{target.get('type') or ''}:{target.get('id') or ''}"),
        )
    console.print(table)
    console.print(f"records={payload['diagnostics']['record_count']} warnings={payload['diagnostics']['warning_count']}")


@governance_audit_app.command("centralized-readiness")
def governance_audit_centralized_readiness_command(
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml governance config.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Report readiness for future centralized audit retention."""
    payload = _store(db).governance_centralized_audit_readiness(config_path=config)
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Centralized Audit Readiness")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("overall_status", escape(payload["readiness"]["overall_status"]))
    table.add_row("blocking_count", str(payload["readiness"]["blocking_count"]))
    table.add_row("local_audit_available", str(payload["local_audit"]["available"]))
    table.add_row("centralized_audit_store", str(payload["centralized_audit"]["store_implemented"]))
    table.add_row("server_opt_in", str(payload["governance"]["server_opt_in"]))
    console.print(table)


@governance_audit_app.command("centralized-store")
def governance_audit_centralized_store_command(
    action: Annotated[str, typer.Option("--action", help="append, list, or verify.")],
    store: Annotated[Path | None, typer.Option("--store", help="Optional centralized audit JSONL store path.")] = None,
    operation: Annotated[str | None, typer.Option("--operation", help="Sensitive operation name or list filter.")] = None,
    actor: Annotated[str | None, typer.Option("--actor", help="Actor identifier or list filter.")] = None,
    status: Annotated[str | None, typer.Option("--status", help="Audit status for append.")] = None,
    target_type: Annotated[str | None, typer.Option("--target-type", help="Target type for append.")] = None,
    target_id: Annotated[str | None, typer.Option("--target-id", help="Target id for append.")] = None,
    metadata: Annotated[list[str] | None, typer.Option("--metadata", help="Metadata key=value. Repeatable.")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, max=1000)] = 50,
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml governance config.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Append, list, or verify the local centralized audit store."""
    payload = _store(db).governance_centralized_audit_store(
        config_path=config,
        action=action,
        store_path=store,
        operation=operation,
        actor=actor,
        status=status,
        target_type=target_type,
        target_id=target_id,
        metadata=_parse_metadata(metadata),
        limit=limit,
    )
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Centralized Audit Store")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("action", escape(payload["request"]["action"]))
    table.add_row("store_available", str(payload["store"]["available"]))
    table.add_row("verification_ok", str(payload["verification"]["ok"]))
    table.add_row("record_count", str(payload["verification"]["record_count"]))
    table.add_row("returned_count", str(payload["query"]["returned_count"]))
    table.add_row("server_required", str(payload["governance"]["server_required"]))
    console.print(table)


@governance_permission_app.command("check")
def governance_permission_check_command(
    operation: Annotated[str, typer.Option("--operation", help="Sensitive operation name.")],
    role: Annotated[str, typer.Option("--role", help="Governance role name.")],
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml governance config.")] = None,
    audit_log: Annotated[Path | None, typer.Option("--audit-log", help="Optional local audit JSONL path.")] = None,
    actor: Annotated[str | None, typer.Option("--actor", help="Actor for optional audit logging.")] = None,
    target_type: Annotated[str | None, typer.Option("--target-type", help="Target type for optional audit logging.")] = None,
    target_id: Annotated[str | None, typer.Option("--target-id", help="Target id for optional audit logging.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Preflight a governance permission decision."""
    payload = _store(db).governance_permission_check(
        config_path=config,
        operation=operation,
        role=role,
        audit_log=audit_log,
        actor=actor,
        target_type=target_type,
        target_id=target_id,
    )
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Governance Permission Check")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("operation", escape(operation))
    table.add_row("role", escape(role))
    table.add_row("allowed", str(payload["decision"]["allowed"]))
    table.add_row("would_allow", str(payload["decision"]["would_allow"]))
    table.add_row("enforced", str(payload["decision"]["enforced"]))
    console.print(table)


@governance_enforcement_app.command("gaps")
def governance_enforcement_gaps_command(
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml governance config.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Emit the governance enforcement gap audit."""
    payload = _store(db).governance_enforcement_gaps(config_path=config)
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Governance Enforcement Gaps")
    table.add_column("Command")
    table.add_column("Access")
    table.add_column("Future Phase")
    for item in payload["commands"]:
        table.add_row(escape(item["command"]), escape(item["access_level"]), escape(item["future_phase"]))
    console.print(table)
    console.print(
        f"commands={payload['summary']['command_count']} "
        f"audit_required={payload['summary']['audit_required_count']}"
    )


@governance_enforcement_app.command("check")
def governance_enforcement_check_command(
    command: Annotated[str, typer.Option("--command", help="ThreadVault command to dry-run against governance policy.")],
    role: Annotated[str, typer.Option("--role", help="Governance role name.")],
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml governance config.")] = None,
    audit_log: Annotated[Path | None, typer.Option("--audit-log", help="Optional local audit JSONL path.")] = None,
    actor: Annotated[str | None, typer.Option("--actor", help="Actor for optional audit logging.")] = None,
    target_type: Annotated[str | None, typer.Option("--target-type", help="Target type for optional audit logging.")] = None,
    target_id: Annotated[str | None, typer.Option("--target-id", help="Target id for optional audit logging.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Dry-run future governance enforcement for one command and role."""
    payload = _store(db).governance_enforcement_check(
        config_path=config,
        command=command,
        role=role,
        audit_log=audit_log,
        actor=actor,
        target_type=target_type,
        target_id=target_id,
    )
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Governance Enforcement Dry Run")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("command", escape(command))
    table.add_row("role", escape(role))
    table.add_row("known_command", str(payload["command_policy"]["known"]))
    table.add_row("access_level", escape(str(payload["command_policy"]["access_level"] or "")))
    table.add_row("would_allow", str(payload["permission"]["would_allow"]))
    table.add_row("would_block_if_enforced", str(payload["enforcement"]["would_block_if_enforced"]))
    table.add_row("status", escape(payload["enforcement"]["status"]))
    console.print(table)


@governance_policy_app.command("readiness")
def governance_policy_readiness_command(
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml governance config.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Report readiness for future team governance policy enforcement."""
    payload = _store(db).governance_policy_readiness(config_path=config)
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Governance Policy Readiness")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("overall_status", escape(payload["readiness"]["overall_status"]))
    table.add_row("team_enforcement_ready", str(payload["governance"]["team_enforcement_ready"]))
    table.add_row("blocking_count", str(payload["readiness"]["blocking_count"]))
    table.add_row("local_first", str(payload["diagnostics"]["local_first"]))
    table.add_row("server_required", str(payload["governance"]["server_required"]))
    console.print(table)


@governance_policy_app.command("central-readiness")
def governance_central_policy_readiness_command(
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml governance config.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Report readiness for centralized policy storage and versioning."""
    payload = _store(db).governance_central_policy_readiness(config_path=config)
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Central Policy Readiness")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("overall_status", escape(payload["readiness"]["overall_status"]))
    table.add_row("central_policy_ready", str(payload["governance"]["central_policy_ready"]))
    table.add_row("blocking_count", str(payload["readiness"]["blocking_count"]))
    table.add_row("local_static_policy", str(payload["fallback"]["local_static_policy_available"]))
    table.add_row("server_opt_in", str(payload["governance"]["server_opt_in"]))
    console.print(table)


@governance_policy_app.command("central-store")
def governance_central_policy_store_command(
    policy: Annotated[Path | None, typer.Option("--policy", help="Optional local central policy JSON document.")] = None,
    actor: Annotated[str | None, typer.Option("--actor", help="Optional actor id to resolve against central policy.")] = None,
    operation: Annotated[
        str | None,
        typer.Option("--operation", help="Optional governance operation to resolve, such as export_archive."),
    ] = None,
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml governance config.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Validate and resolve a local central policy document."""
    payload = _store(db).governance_central_policy_store(
        config_path=config,
        policy_path=policy,
        actor=actor,
        operation=operation,
    )
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Central Policy Store")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("policy_valid", str(payload["policy"]["valid"]))
    table.add_row("store_available", str(payload["store"]["available"]))
    table.add_row("actor", escape(str(payload["actor_resolution"]["requested"] or "")))
    table.add_row("operation", escape(str(payload["operation_resolution"]["requested"] or "")))
    table.add_row("would_allow", str(payload["enforcement"]["would_allow"]))
    table.add_row("status", escape(payload["enforcement"]["status"]))
    table.add_row("server_required", str(payload["governance"]["server_required"]))
    console.print(table)


@governance_server_app.command("policy-readiness")
def governance_server_policy_readiness_command(
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml governance config.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Report readiness for optional server/team policy enforcement."""
    payload = _store(db).governance_server_policy_readiness(config_path=config)
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Governance Server Policy Readiness")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("overall_status", escape(payload["readiness"]["overall_status"]))
    table.add_row("safe_to_enable_server_mode", str(payload["readiness"]["safe_to_enable_server_mode"]))
    table.add_row("blocking_count", str(payload["readiness"]["blocking_count"]))
    table.add_row("server_opt_in", str(payload["governance"]["server_opt_in"]))
    table.add_row("server_required", str(payload["governance"]["server_required"]))
    console.print(table)


@governance_server_app.command("read-only-manifest")
def governance_read_only_server_manifest_command(
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml governance config.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Emit the opt-in read-only shared/server prototype manifest."""
    payload = _store(db).governance_read_only_server_manifest(config_path=config)
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Read-Only Server Prototype")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("implemented", str(payload["runtime"]["implemented"]))
    table.add_row("prototype", str(payload["runtime"]["prototype"]))
    table.add_row("route_count", str(payload["diagnostics"]["route_count"]))
    table.add_row("server_required", str(payload["governance"]["server_required"]))
    table.add_row("server_opt_in", str(payload["governance"]["server_opt_in"]))
    console.print(table)


@governance_server_app.command("read-only-smoke")
def governance_read_only_server_smoke_command(
    query: Annotated[str, typer.Option("--query", help="Query used for the agent retrieval smoke route.")] = "pytest",
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml governance config.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Exercise read-only server routes in process without binding a socket."""
    payload = _store(db).governance_read_only_server_smoke(config_path=config, query=query)
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Read-Only Server Smoke")
    table.add_column("Route")
    table.add_column("OK")
    table.add_column("Schema")
    for check in payload["checks"]:
        table.add_row(escape(check["path"]), str(check["ok"]), escape(check["schema"]))
    console.print(table)
    if not payload["ok"]:
        raise typer.Exit(code=1)


@governance_server_app.command("serve-read-only")
def governance_serve_read_only_command(
    enable: Annotated[bool, typer.Option("--enable", help="Required explicit opt-in before binding a local server.")] = False,
    host: Annotated[str, typer.Option("--host", help="Bind host. Loopback is the intended prototype default.")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port", min=1, max=65535, help="Bind port.")] = 8765,
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml governance config.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
) -> None:
    """Start the opt-in read-only shared/server prototype."""
    if not enable:
        raise typer.BadParameter("serve-read-only requires explicit --enable before binding a socket.")
    server = build_read_only_server(_store(db), host=host, port=port, config_path=config)
    console.print(f"[green]ThreadVault read-only server:[/green] http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        console.print("[yellow]Stopping read-only server.[/yellow]")
    finally:
        server.server_close()


@governance_v3_app.command("gap-audit")
def governance_v3_gap_audit_command(
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml governance config.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Report remaining gaps before v3 final acceptance."""
    payload = _store(db).governance_v3_completion_gap_audit(config_path=config)
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault v3 Completion Gap Audit")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("overall_status", escape(payload["completion"]["overall_status"]))
    table.add_row("v3_complete", str(payload["completion"]["v3_complete"]))
    table.add_row("accepted_phase_count", str(payload["completion"]["accepted_phase_count"]))
    table.add_row("remaining_gap_count", str(payload["completion"]["remaining_gap_count"]))
    table.add_row("blocking_count", str(payload["completion"]["blocking_count"]))
    table.add_row("server_opt_in", str(payload["governance"]["server_opt_in"]))
    console.print(table)


@governance_v3_app.command("acceptance-smoke")
def governance_v3_acceptance_smoke_command(
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml governance config.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    query: Annotated[str, typer.Option("--query", help="Query used for retrieval/client/server smoke checks.")] = "pytest",
    session: Annotated[str, typer.Option("--session", help="Session id used for client/export smoke checks.")] = "sess-current",
    work_dir: Annotated[Path | None, typer.Option("--work-dir", help="Directory for temporary smoke artifacts.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Run the final v3 acceptance smoke."""
    payload = _store(db).governance_v3_acceptance_smoke(
        config_path=config,
        query=query,
        session_id=session,
        work_dir=work_dir,
    )
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault v3 Acceptance Smoke")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("status", escape(payload["status"]))
    table.add_row("ok", str(payload["ok"]))
    table.add_row("checks", str(payload["summary"]["required_check_count"]))
    table.add_row("failed", str(payload["summary"]["failed_check_count"]))
    table.add_row("server_required", str(payload["governance"]["server_required"]))
    table.add_row("cloud_sync", str(payload["governance"]["cloud_sync"]))
    console.print(table)
    if not payload["ok"]:
        raise typer.Exit(code=1)


@governance_identity_app.command("actor-readiness")
def governance_identity_actor_readiness_command(
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml governance config.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Report readiness for identity providers and actor binding."""
    payload = _store(db).governance_identity_actor_readiness(config_path=config)
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Identity Actor Readiness")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("overall_status", escape(payload["readiness"]["overall_status"]))
    table.add_row("identity_binding_ready", str(payload["governance"]["identity_binding_ready"]))
    table.add_row("blocking_count", str(payload["readiness"]["blocking_count"]))
    table.add_row("manual_actor_labels", str(payload["local_fallback"]["manual_actor_labels_available"]))
    table.add_row("server_opt_in", str(payload["governance"]["server_opt_in"]))
    console.print(table)


@governance_identity_app.command("bind")
def governance_identity_actor_binding_command(
    actor: Annotated[str, typer.Option("--actor", help="Actor id to resolve from local identity config.")],
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml governance config.")] = None,
    command: Annotated[str | None, typer.Option("--command", help="Command being attributed to the actor.")] = None,
    operation: Annotated[str | None, typer.Option("--operation", help="Sensitive operation being attributed.")] = None,
    target_type: Annotated[str | None, typer.Option("--target-type", help="Target type for request attribution.")] = None,
    target_id: Annotated[str | None, typer.Option("--target-id", help="Target id for request attribution.")] = None,
    client_id: Annotated[str | None, typer.Option("--client-id", help="Client/runtime id for request attribution.")] = None,
    audit_log: Annotated[Path | None, typer.Option("--audit-log", help="Optional local audit JSONL path.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Resolve an actor against local static identity config."""
    payload = _store(db).governance_identity_actor_binding(
        config_path=config,
        actor=actor,
        command=command,
        operation=operation,
        target_type=target_type,
        target_id=target_id,
        client_id=client_id,
        audit_log=audit_log,
    )
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Identity Actor Binding")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("actor", escape(actor))
    table.add_row("bound", str(payload["binding"]["bound"]))
    table.add_row("status", escape(payload["binding"]["status"]))
    table.add_row("roles", escape(",".join(payload["role_mapping"]["roles"])))
    table.add_row("audit_written", str(payload["audit"]["written"]))
    console.print(table)


@governance_backup_app.command("central-readiness")
def governance_central_backup_readiness_command(
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml governance config.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Report readiness for centralized backup/restore policy."""
    payload = _store(db).governance_central_backup_readiness(config_path=config)
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Central Backup Readiness")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("overall_status", escape(payload["readiness"]["overall_status"]))
    table.add_row("central_backup_ready", str(payload["governance"]["central_backup_ready"]))
    table.add_row("shared_restore_ready", str(payload["governance"]["shared_restore_ready"]))
    table.add_row("blocking_count", str(payload["readiness"]["blocking_count"]))
    table.add_row("local_backup_restore", str(payload["local_backup"]["sufficient_for_local_use"]))
    table.add_row("server_opt_in", str(payload["governance"]["server_opt_in"]))
    console.print(table)


@governance_backup_app.command("policy")
def governance_central_backup_policy_command(
    policy: Annotated[Path | None, typer.Option("--policy", help="Optional local centralized backup policy JSON path.")] = None,
    operation: Annotated[
        str | None,
        typer.Option("--operation", help="Optional operation to preview: backup_archive, restore_backup, delete_or_prune."),
    ] = None,
    actor: Annotated[str | None, typer.Option("--actor", help="Optional actor id to resolve through local identity config.")] = None,
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml governance config.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Validate centralized backup/restore policy and preview decisions."""
    payload = _store(db).governance_central_backup_policy(
        config_path=config,
        policy_path=policy,
        operation=operation,
        actor=actor,
    )
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Central Backup Policy")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("policy_valid", str(payload["policy"]["valid"]))
    table.add_row("operation", escape(str(payload["operation_resolution"]["requested"])))
    table.add_row("allowed", str(payload["operation_resolution"]["allowed"]))
    table.add_row("status", escape(payload["enforcement"]["status"]))
    table.add_row("server_opt_in", str(payload["governance"]["server_opt_in"]))
    console.print(table)


@governance_preflight_app.command("export-backup")
def governance_export_backup_preflight_command(
    command: Annotated[str, typer.Option("--command", help="Export or backup command to preflight.")],
    role: Annotated[str, typer.Option("--role", help="Governance role name.")],
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml governance config.")] = None,
    audit_log: Annotated[Path | None, typer.Option("--audit-log", help="Optional local audit JSONL path.")] = None,
    actor: Annotated[str | None, typer.Option("--actor", help="Actor for optional audit logging.")] = None,
    target_type: Annotated[str | None, typer.Option("--target-type", help="Target type for optional audit logging.")] = None,
    target_id: Annotated[str | None, typer.Option("--target-id", help="Target id for optional audit logging.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Preflight export/backup governance without executing the business command."""
    payload = _store(db).governance_export_backup_preflight(
        config_path=config,
        command=command,
        role=role,
        audit_log=audit_log,
        actor=actor,
        target_type=target_type,
        target_id=target_id,
    )
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Export/Backup Governance Preflight")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("command", escape(command))
    table.add_row("role", escape(role))
    table.add_row("in_scope", str(payload["scope"]["in_scope"]))
    table.add_row("would_allow", str(payload["permission"]["would_allow"]))
    table.add_row("preflight_status", escape(payload["enforcement"]["preflight_status"]))
    table.add_row("business_command_executed", str(payload["execution"]["business_command_executed"]))
    console.print(table)


@governance_preflight_app.command("restore-retention")
def governance_restore_retention_preflight_command(
    command: Annotated[str, typer.Option("--command", help="Restore or retention command to preflight.")],
    role: Annotated[str, typer.Option("--role", help="Governance role name.")],
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml governance config.")] = None,
    audit_log: Annotated[Path | None, typer.Option("--audit-log", help="Optional local audit JSONL path.")] = None,
    actor: Annotated[str | None, typer.Option("--actor", help="Actor for optional audit logging.")] = None,
    target_type: Annotated[str | None, typer.Option("--target-type", help="Target type for optional audit logging.")] = None,
    target_id: Annotated[str | None, typer.Option("--target-id", help="Target id for optional audit logging.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Preflight restore/retention governance without executing the business command."""
    payload = _store(db).governance_restore_retention_preflight(
        config_path=config,
        command=command,
        role=role,
        audit_log=audit_log,
        actor=actor,
        target_type=target_type,
        target_id=target_id,
    )
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Restore/Retention Governance Preflight")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("command", escape(command))
    table.add_row("role", escape(role))
    table.add_row("in_scope", str(payload["scope"]["in_scope"]))
    table.add_row("would_allow", str(payload["permission"]["would_allow"]))
    table.add_row("preflight_status", escape(payload["enforcement"]["preflight_status"]))
    table.add_row("business_command_executed", str(payload["execution"]["business_command_executed"]))
    console.print(table)


@governance_preflight_app.command("raw-read")
def governance_raw_read_preflight_command(
    command: Annotated[str, typer.Option("--command", help="Raw-read command to preflight.")],
    role: Annotated[str, typer.Option("--role", help="Governance role name.")],
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml governance config.")] = None,
    audit_log: Annotated[Path | None, typer.Option("--audit-log", help="Optional local audit JSONL path.")] = None,
    actor: Annotated[str | None, typer.Option("--actor", help="Actor for optional audit logging.")] = None,
    target_type: Annotated[str | None, typer.Option("--target-type", help="Target type for optional audit logging.")] = None,
    target_id: Annotated[str | None, typer.Option("--target-id", help="Target id for optional audit logging.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Preflight raw-read governance without executing the business command."""
    payload = _store(db).governance_raw_read_preflight(
        config_path=config,
        command=command,
        role=role,
        audit_log=audit_log,
        actor=actor,
        target_type=target_type,
        target_id=target_id,
    )
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Raw Read Governance Preflight")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("command", escape(command))
    table.add_row("role", escape(role))
    table.add_row("in_scope", str(payload["scope"]["in_scope"]))
    table.add_row("would_allow", str(payload["permission"]["would_allow"]))
    table.add_row("preflight_status", escape(payload["enforcement"]["preflight_status"]))
    table.add_row("business_command_executed", str(payload["execution"]["business_command_executed"]))
    console.print(table)


@governance_preflight_app.command("summary-search")
def governance_summary_search_preflight_command(
    command: Annotated[str, typer.Option("--command", help="Summary/search command to preflight.")],
    role: Annotated[str, typer.Option("--role", help="Governance role name.")],
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml governance config.")] = None,
    audit_log: Annotated[Path | None, typer.Option("--audit-log", help="Optional local audit JSONL path.")] = None,
    actor: Annotated[str | None, typer.Option("--actor", help="Actor for optional audit logging.")] = None,
    target_type: Annotated[str | None, typer.Option("--target-type", help="Target type for optional audit logging.")] = None,
    target_id: Annotated[str | None, typer.Option("--target-id", help="Target id for optional audit logging.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Preflight summary/search governance without executing the business command."""
    payload = _store(db).governance_summary_search_preflight(
        config_path=config,
        command=command,
        role=role,
        audit_log=audit_log,
        actor=actor,
        target_type=target_type,
        target_id=target_id,
    )
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Summary/Search Governance Preflight")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("command", escape(command))
    table.add_row("role", escape(role))
    table.add_row("in_scope", str(payload["scope"]["in_scope"]))
    table.add_row("would_allow", str(payload["permission"]["would_allow"]))
    table.add_row("preflight_status", escape(payload["enforcement"]["preflight_status"]))
    table.add_row("business_command_executed", str(payload["execution"]["business_command_executed"]))
    console.print(table)


@governance_preflight_app.command("export-preview")
def governance_export_preview_preflight_command(
    command: Annotated[str, typer.Option("--command", help="Client export-preview command to preflight.")],
    role: Annotated[str, typer.Option("--role", help="Governance role name.")],
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml governance config.")] = None,
    audit_log: Annotated[Path | None, typer.Option("--audit-log", help="Optional local audit JSONL path.")] = None,
    actor: Annotated[str | None, typer.Option("--actor", help="Actor for optional audit logging.")] = None,
    target_type: Annotated[str | None, typer.Option("--target-type", help="Target type for optional audit logging.")] = None,
    target_id: Annotated[str | None, typer.Option("--target-id", help="Target id for optional audit logging.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Preflight client export-preview governance without executing the business command."""
    payload = _store(db).governance_export_preview_preflight(
        config_path=config,
        command=command,
        role=role,
        audit_log=audit_log,
        actor=actor,
        target_type=target_type,
        target_id=target_id,
    )
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Export Preview Governance Preflight")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("command", escape(command))
    table.add_row("role", escape(role))
    table.add_row("in_scope", str(payload["scope"]["in_scope"]))
    table.add_row("would_allow", str(payload["permission"]["would_allow"]))
    table.add_row("preflight_status", escape(payload["enforcement"]["preflight_status"]))
    table.add_row("business_command_executed", str(payload["execution"]["business_command_executed"]))
    console.print(table)


@governance_preflight_app.command("external-model")
def governance_external_model_preflight_command(
    command: Annotated[str, typer.Option("--command", help="External model command surface to preflight.")],
    role: Annotated[str, typer.Option("--role", help="Governance role name.")],
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml governance config.")] = None,
    audit_log: Annotated[Path | None, typer.Option("--audit-log", help="Optional local audit JSONL path.")] = None,
    actor: Annotated[str | None, typer.Option("--actor", help="Actor for optional audit logging.")] = None,
    target_type: Annotated[str | None, typer.Option("--target-type", help="Target type for optional audit logging.")] = None,
    target_id: Annotated[str | None, typer.Option("--target-id", help="Target id for optional audit logging.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Preflight external-model governance without sending any outbound payload."""
    payload = _store(db).governance_external_model_preflight(
        config_path=config,
        command=command,
        role=role,
        audit_log=audit_log,
        actor=actor,
        target_type=target_type,
        target_id=target_id,
    )
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault External Model Governance Preflight")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("command", escape(command))
    table.add_row("role", escape(role))
    table.add_row("in_scope", str(payload["scope"]["in_scope"]))
    table.add_row("would_allow", str(payload["permission"]["would_allow"]))
    table.add_row("preflight_status", escape(payload["enforcement"]["preflight_status"]))
    table.add_row("external_call_executed", str(payload["execution"]["external_call_executed"]))
    console.print(table)


@governance_instrumentation_app.command("business-command")
def governance_business_command_instrumentation_command(
    command: Annotated[str, typer.Option("--command", help="ThreadVault business command to instrument.")],
    role: Annotated[str, typer.Option("--role", help="Governance role name.")],
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml governance config.")] = None,
    audit_log: Annotated[Path | None, typer.Option("--audit-log", help="Optional local audit JSONL path.")] = None,
    actor: Annotated[str | None, typer.Option("--actor", help="Actor for optional audit logging.")] = None,
    target_type: Annotated[str | None, typer.Option("--target-type", help="Target type for optional audit logging.")] = None,
    target_id: Annotated[str | None, typer.Option("--target-id", help="Target id for optional audit logging.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Normalize governance preflight and audit evidence for a business command."""
    payload = _store(db).governance_business_command_instrumentation(
        config_path=config,
        command=command,
        role=role,
        audit_log=audit_log,
        actor=actor,
        target_type=target_type,
        target_id=target_id,
    )
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Business Command Governance Instrumentation")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("command", escape(command))
    table.add_row("role", escape(role))
    table.add_row("category", escape(payload["command_policy"]["category"]))
    table.add_row("instrumented", str(payload["instrumentation"]["instrumented"]))
    table.add_row("blocked", str(payload["instrumentation"]["blocked"]))
    table.add_row("should_execute", str(payload["instrumentation"]["business_command_should_execute"]))
    table.add_row("audit_written", str((payload.get("audit") or {}).get("preflight_record_written", False)))
    console.print(table)


@agent_app.command("retrieve")
def agent_retrieve_command(
    query: Annotated[str, typer.Argument(help="Agent retrieval query text.")],
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml for vector capability.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    mode: Annotated[str, typer.Option("--mode", help="hybrid or fts.")] = "hybrid",
    limit: Annotated[int, typer.Option("--limit", min=1, max=100)] = 20,
    vector_limit: Annotated[int, typer.Option("--vector-limit", min=1, max=50)] = 10,
    session: Annotated[str | None, typer.Option("--session", help="Filter by session id.")] = None,
    cwd: Annotated[str | None, typer.Option("--cwd", help="Filter by project cwd.")] = None,
    since: Annotated[str | None, typer.Option("--since", help="Filter events after this timestamp.")] = None,
    until: Annotated[str | None, typer.Option("--until", help="Filter events before this timestamp.")] = None,
    type_filter: Annotated[str | None, typer.Option("--type", help="Filter by top_type or sub_type.")] = None,
    tool: Annotated[str | None, typer.Option("--tool", help="Filter by tool name.")] = None,
    local_debug: Annotated[bool, typer.Option("--local-debug", help="Include local debug metadata such as file paths.")] = False,
    governance_role: Annotated[str | None, typer.Option("--governance-role", help="Role for explicit governance preflight.")] = None,
    governance_config: Annotated[
        Path | None,
        typer.Option("--governance-config", help="Optional threadvault.toml for governance preflight."),
    ] = None,
    governance_audit_log: Annotated[
        Path | None,
        typer.Option("--governance-audit-log", help="Optional local audit JSONL path for governance preflight."),
    ] = None,
    governance_actor: Annotated[str | None, typer.Option("--governance-actor", help="Actor for governance audit metadata.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Run the agent-facing retrieval contract."""
    if mode not in {"hybrid", "fts"}:
        raise typer.BadParameter("--mode must be hybrid or fts.")
    governance = _maybe_governance_instrumentation(
        db,
        command="threadvault agent retrieve",
        role=governance_role,
        config=governance_config,
        audit_log=governance_audit_log,
        actor=governance_actor,
        target_type="query",
        target_id=query,
    )
    if _governance_blocked(governance):
        _emit_governance_blocked("threadvault agent retrieve", governance, json_output)
    payload = _store(db).agent_retrieve(
        query=query,
        config_path=config,
        mode=mode,
        limit=limit,
        vector_limit=vector_limit,
        session_id=session,
        cwd=cwd,
        since=since,
        until=until,
        top_type=type_filter,
        tool=tool,
        local_debug=local_debug,
    )
    _mark_governance_executed(governance)
    _attach_governance(payload, governance)
    if json_output:
        _print_json(payload)
        return
    table = Table(title=f"Agent Retrieval: {query}")
    table.add_column("Score")
    table.add_column("Source")
    table.add_column("ID")
    table.add_column("Evidence")
    for row in payload["results"]:
        identifier = row["chunk_id"] or str(row["event_id"])
        table.add_row(
            f"{row['score']:.3f}",
            escape(row["source"]),
            escape(identifier),
            ", ".join(str(event_id) for event_id in row["evidence_event_ids"]),
        )
    console.print(table)
    diagnostics = payload["diagnostics"]
    console.print(
        f"mode={diagnostics['used_mode']} capabilities="
        + ",".join(diagnostics["capabilities_used"])
        + f" results={diagnostics['result_count']}"
    )


@summary_pipeline_app.command("chunks")
def summary_pipeline_chunks_command(
    session: Annotated[list[str] | None, typer.Option("--session", help="Session id to include. Repeat for multiple sessions.")] = None,
    project: Annotated[str | None, typer.Option("--project", help="Project cwd to include.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    max_chunks_per_session: Annotated[int, typer.Option("--max-chunks-per-session", min=1, max=100)] = 12,
    max_chars: Annotated[int, typer.Option("--max-chars", min=100, max=20000)] = 1200,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Build summary/evidence chunks for future retrieval adapters."""
    session_ids = session or []
    if not session_ids and not project:
        raise typer.BadParameter("Provide --session or --project.")
    payload = _store(db).summary_chunks(
        session_ids=session_ids,
        project=project,
        max_chunks_per_session=max_chunks_per_session,
        max_chars=max_chars,
    )
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Summary Chunks")
    table.add_column("Chunk")
    table.add_column("Type")
    table.add_column("Session")
    table.add_column("Evidence")
    for chunk in payload["chunks"]:
        table.add_row(
            escape(chunk["chunk_id"]),
            escape(chunk["chunk_type"]),
            escape(chunk["session_id"]),
            ", ".join(str(event_id) for event_id in chunk["evidence_event_ids"]),
        )
    console.print(table)
    diagnostics = payload["diagnostics"]
    console.print(
        f"sessions={diagnostics['selected_sessions_count']} chunks={diagnostics['chunks_count']} "
        f"embedding_generated={diagnostics['embedding_generated']}"
    )


@vector_app.command("index")
def vector_index_command(
    session: Annotated[list[str] | None, typer.Option("--session", help="Session id to index. Repeat for multiple sessions.")] = None,
    project: Annotated[str | None, typer.Option("--project", help="Project cwd to index.")] = None,
    config: Annotated[Path | None, typer.Option("--config", help="threadvault.toml with retrieval.vector.enabled = true.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    max_chunks_per_session: Annotated[int, typer.Option("--max-chunks-per-session", min=1, max=100)] = 12,
    max_chars: Annotated[int, typer.Option("--max-chars", min=100, max=20000)] = 1200,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Build the local vector index from Summary Pipeline chunks."""
    session_ids = session or []
    if not session_ids and not project:
        raise typer.BadParameter("Provide --session or --project.")
    try:
        payload = _store(db).vector_index(
            session_ids=session_ids,
            project=project,
            config_path=config,
            max_chunks_per_session=max_chunks_per_session,
            max_chars=max_chars,
        )
    except (PermissionError, ValueError) as exc:
        _handle_vector_error(exc, json_output)
        return
    if json_output:
        _print_json(payload)
        return
    console.print(
        f"indexed={payload['indexed']['chunks']} total={payload['indexed']['total_chunks']} "
        f"adapter={payload['adapter']} dimensions={payload['dimensions']}"
    )


@vector_app.command("query")
def vector_query_command(
    query: Annotated[str, typer.Argument(help="Vector query text.")],
    config: Annotated[Path | None, typer.Option("--config", help="threadvault.toml with retrieval.vector.enabled = true.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, max=50)] = 10,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Query the local vector index."""
    try:
        payload = _store(db).vector_query(query=query, config_path=config, limit=limit)
    except (PermissionError, ValueError) as exc:
        _handle_vector_error(exc, json_output)
        return
    if json_output:
        _print_json(payload)
        return
    table = Table(title=f"Vector Query: {query}")
    table.add_column("Score")
    table.add_column("Chunk")
    table.add_column("Session")
    table.add_column("Type")
    for row in payload["results"]:
        table.add_row(f"{row['score']:.3f}", escape(row["chunk_id"]), escape(row["session_id"]), escape(row["chunk_type"]))
    console.print(table)


@vector_app.command("status")
def vector_status_command(
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Show local vector adapter/index status."""
    payload = _store(db).vector_status(config_path=config)
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Vector Status")
    table.add_column("Key")
    table.add_column("Value")
    for key, value in payload.items():
        table.add_row(escape(str(key)), escape(json.dumps(value, ensure_ascii=False, default=str)))
    console.print(table)


@schemas_app.command("list")
def schemas_list_command(
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = False,
) -> None:
    """List named ThreadVault JSON schemas."""
    payload = {"schemas": schema_names()}
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Schemas")
    table.add_column("Name")
    for name in payload["schemas"]:
        table.add_row(escape(name))
    console.print(table)


@schemas_app.command("show")
def schemas_show_command(
    name: Annotated[str, typer.Argument(help="Schema name.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = True,
) -> None:
    """Show one named JSON schema."""
    try:
        payload = get_schema(name)
    except KeyError as exc:
        raise typer.BadParameter(f"Unknown schema: {exc.args[0]}") from exc
    if json_output:
        _print_json(payload)
        return
    console.print(json.dumps(payload, ensure_ascii=False, indent=2))


@schemas_app.command("write")
def schemas_write_command(
    out: Annotated[Path, typer.Option("--out", "-o", help="Output directory.")] = Path("docs/schemas"),
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = False,
) -> None:
    """Write schema JSON files to a directory."""
    paths = write_schema_files(out)
    payload = {"out": str(out), "files": [str(path) for path in paths]}
    if json_output:
        _print_json(payload)
        return
    console.print(f"[green]Wrote schemas:[/green] {out}")


@config_app.command("show")
def config_show_command(
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml path.")] = None,
    include_values: Annotated[bool, typer.Option("--include-values", help="Include raw allowlist values in local output.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Show safe local ThreadVault config summary."""
    try:
        payload = describe_app_config(config, include_values=include_values)
    except Exception as exc:  # noqa: BLE001 - config show should return machine-readable diagnostics.
        diagnostic = diagnose_app_config(config)
        if json_output:
            _print_json(diagnostic)
            raise typer.Exit(code=1) from exc
        raise typer.BadParameter(str(exc)) from exc
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Config")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row("resolved_path", escape(payload["resolved_path"]))
    table.add_row("exists", str(payload["exists"]))
    table.add_row("loaded", str(payload["loaded"]))
    table.add_row("sections", escape(", ".join(payload["sections"])))
    table.add_row("privacy.allowlist_count", str(payload["privacy"]["allowlist_count"]))
    table.add_row("audit_history.keep", escape(str(payload["audit_history"]["keep"])))
    table.add_row("backup_history.keep", escape(str(payload["backup_history"]["keep"])))
    table.add_row("restore_history.keep", escape(str(payload["restore_history"]["keep"])))
    console.print(table)


@config_app.command("doctor")
def config_doctor_command(
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml path.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Diagnose local ThreadVault config health."""
    payload = diagnose_app_config(config)
    if json_output:
        _print_json(payload)
    else:
        table = Table(title="ThreadVault Config Doctor")
        table.add_column("Key")
        table.add_column("Value")
        table.add_row("ok", str(payload["ok"]))
        table.add_row("resolved_path", escape(payload["resolved_path"]))
        table.add_row("errors", str(len(payload["errors"])))
        table.add_row("warnings", str(len(payload["warnings"])))
        console.print(table)
    if not payload["ok"]:
        raise typer.Exit(code=1)


@config_app.command("init")
def config_init_command(
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml path.")] = None,
    force: Annotated[bool, typer.Option("--force", help="Overwrite an existing config file.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Create a starter local ThreadVault config file."""
    payload = init_app_config(config, force=force)
    if json_output:
        _print_json(payload)
    elif payload["ok"]:
        action = "Overwrote" if payload["overwritten"] else "Created"
        console.print(f"[green]{action} config:[/green] {payload['resolved_path']}")
    else:
        console.print(f"[yellow]Config already exists:[/yellow] {payload['resolved_path']}")
    if not payload["ok"]:
        raise typer.Exit(code=1)


@ingest_queue_app.command("enqueue")
def ingest_queue_enqueue_command(
    source: Annotated[str, typer.Option("--source", help="Trigger source, such as hook or manual.")] = "manual",
    codex_home: Annotated[Path | None, typer.Option("--codex-home", help="Codex home directory to import when processed.")] = None,
    reason: Annotated[str, typer.Option("--reason", help="Reason for the ingestion request.")] = "scan",
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Enqueue lightweight ingestion work for later processing."""
    payload = _store(db).enqueue_ingestion(source=source, codex_home=codex_home, reason=reason)
    if json_output:
        _print_json(payload)
        return
    request = payload["request"]
    if payload["enqueued"]:
        console.print(f"[green]Queued ingestion request:[/green] {request['request_id']}")
    else:
        console.print(f"[yellow]Matching active ingestion request already exists:[/yellow] {request['request_id']}")


@ingest_queue_app.command("list")
def ingest_queue_list_command(
    status: Annotated[str | None, typer.Option("--status", help="Filter by pending, processing, completed, failed, or skipped.")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, max=500)] = 50,
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """List ingestion automation queue requests."""
    try:
        payload = _store(db).list_ingestion_queue(status=status, limit=limit)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Ingestion Queue")
    table.add_column("Request", justify="right")
    table.add_column("Status")
    table.add_column("Source")
    table.add_column("Reason")
    table.add_column("Codex Home")
    for request in payload["requests"]:
        table.add_row(
            str(request["request_id"]),
            escape(request["status"]),
            escape(request["source"]),
            escape(request["reason"]),
            escape(request["codex_home"] or ""),
        )
    console.print(table)


@ingest_queue_app.command("process")
def ingest_queue_process_command(
    codex_home: Annotated[Path | None, typer.Option("--codex-home", help="Override Codex home for all processed requests.")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, max=100)] = 10,
    apply: Annotated[bool, typer.Option("--apply", help="Actually run imports. Defaults to dry-run.")] = False,
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Dry-run or process pending ingestion automation requests."""
    payload = _store(db).process_ingestion_queue(codex_home=codex_home, limit=limit, apply=apply)
    if json_output:
        _print_json(payload)
        return
    action = "Processed" if apply else "Would process"
    console.print(f"[green]{action} ingestion requests:[/green] {payload['processed'] if apply else len(payload['requests'])}")


@codex_hook_app.command("ingest")
def codex_hook_ingest_command(
    codex_home: Annotated[Path | None, typer.Option("--codex-home", help="Override Codex home for the queued request.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    diagnostic_json: Annotated[
        bool,
        typer.Option("--diagnostic-json", help="Emit ThreadVault diagnostic JSON instead of hook response."),
    ] = False,
) -> None:
    """Read a Codex Hook JSON payload from stdin and enqueue ingestion work."""
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            raise ValueError("Hook payload must be a JSON object.")
        result = _store(db).handle_codex_hook(payload, codex_home=codex_home)
    except Exception as exc:  # noqa: BLE001 - hooks should not break Codex turns.
        result = invalid_hook_payload_result(str(exc))
    _print_json(result if diagnostic_json else result.get("hook_response", hook_continue_response()))


@codex_hook_app.command("config")
def codex_hook_config_command(
    command: Annotated[
        str,
        typer.Option("--command", help="Hook command to place in the generated snippet."),
    ] = "threadvault codex-hook ingest",
    timeout: Annotated[int, typer.Option("--timeout", min=1, help="Hook command timeout in seconds.")] = 10,
    status_message: Annotated[str, typer.Option("--status-message", help="Codex hook status message.")] = "Queueing ThreadVault ingestion",
    db: Annotated[Path | None, typer.Option("--db", help="Optional database path to include in the command.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Emit a sample Codex hooks.json Stop hook snippet."""
    resolved_command = command
    if db is not None and command == "threadvault codex-hook ingest":
        resolved_command = f'threadvault codex-hook ingest --db "{_db_option(db)}"'
    payload = _store(None).codex_hook_config(resolved_command, timeout=timeout, status_message=status_message)
    if json_output:
        _print_json(payload)
        return
    console.print(json.dumps(payload, ensure_ascii=False, indent=2))


@export_target_app.command("markdown")
def export_target_markdown_command(
    session: Annotated[list[str] | None, typer.Option("--session", help="Session id to include. Repeatable.")] = None,
    project: Annotated[str | None, typer.Option("--project", help="Project cwd to include.")] = None,
    out: Annotated[Path, typer.Option("--out", "-o", help="Target output directory.")] = Path("threadvault-target-export"),
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    privacy_mode: Annotated[str, typer.Option("--privacy-mode", help="warn, redact, or fail.")] = "warn",
    privacy_config: Annotated[Path | None, typer.Option("--privacy-config", help="Optional threadvault.toml privacy config.")] = None,
    governance_role: Annotated[str | None, typer.Option("--governance-role", help="Role for explicit governance preflight.")] = None,
    governance_config: Annotated[
        Path | None,
        typer.Option("--governance-config", help="Optional threadvault.toml for governance preflight."),
    ] = None,
    governance_audit_log: Annotated[
        Path | None,
        typer.Option("--governance-audit-log", help="Optional local audit JSONL path for governance preflight."),
    ] = None,
    governance_actor: Annotated[str | None, typer.Option("--governance-actor", help="Actor for governance audit metadata.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Batch export sessions/project to Markdown with a manifest."""
    if not session and not project:
        raise typer.BadParameter("Provide at least one --session or --project.")
    if privacy_mode not in {"warn", "redact", "fail"}:
        raise typer.BadParameter("--privacy-mode must be warn, redact, or fail.")
    governance = _maybe_governance_instrumentation(
        db,
        command="threadvault export-target markdown",
        role=governance_role,
        config=governance_config,
        audit_log=governance_audit_log,
        actor=governance_actor,
        target_type="export_target",
        target_id=str(out),
    )
    if _governance_blocked(governance):
        _emit_governance_blocked("threadvault export-target markdown", governance, json_output)
    try:
        payload = _store(db).export_target(
            out,
            profile="markdown",
            session_ids=session or [],
            project=project,
            privacy_mode=privacy_mode,
            privacy_config_path=privacy_config,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    _mark_governance_executed(governance)
    _attach_governance(payload, governance)
    if json_output:
        _print_json(payload)
        return
    console.print(
        "[green]Export target complete:[/green] "
        f"files={len(payload['files'])} skipped={len(payload['skipped'])} manifest={out / 'threadvault-export-manifest.json'}"
    )


@export_target_app.command("obsidian")
def export_target_obsidian_command(
    session: Annotated[list[str] | None, typer.Option("--session", help="Session id to include. Repeatable.")] = None,
    project: Annotated[str | None, typer.Option("--project", help="Project cwd to include.")] = None,
    out: Annotated[Path, typer.Option("--out", "-o", help="Target output directory.")] = Path("threadvault-obsidian-vault"),
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    privacy_mode: Annotated[str, typer.Option("--privacy-mode", help="warn, redact, or fail.")] = "warn",
    privacy_config: Annotated[Path | None, typer.Option("--privacy-config", help="Optional threadvault.toml privacy config.")] = None,
    governance_role: Annotated[str | None, typer.Option("--governance-role", help="Role for explicit governance preflight.")] = None,
    governance_config: Annotated[
        Path | None,
        typer.Option("--governance-config", help="Optional threadvault.toml for governance preflight."),
    ] = None,
    governance_audit_log: Annotated[
        Path | None,
        typer.Option("--governance-audit-log", help="Optional local audit JSONL path for governance preflight."),
    ] = None,
    governance_actor: Annotated[str | None, typer.Option("--governance-actor", help="Actor for governance audit metadata.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Batch export sessions/project to an Obsidian-ready Markdown vault."""
    if not session and not project:
        raise typer.BadParameter("Provide at least one --session or --project.")
    if privacy_mode not in {"warn", "redact", "fail"}:
        raise typer.BadParameter("--privacy-mode must be warn, redact, or fail.")
    governance = _maybe_governance_instrumentation(
        db,
        command="threadvault export-target obsidian",
        role=governance_role,
        config=governance_config,
        audit_log=governance_audit_log,
        actor=governance_actor,
        target_type="export_target",
        target_id=str(out),
    )
    if _governance_blocked(governance):
        _emit_governance_blocked("threadvault export-target obsidian", governance, json_output)
    try:
        payload = _store(db).export_target(
            out,
            profile="obsidian",
            session_ids=session or [],
            project=project,
            privacy_mode=privacy_mode,
            privacy_config_path=privacy_config,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    _mark_governance_executed(governance)
    _attach_governance(payload, governance)
    if json_output:
        _print_json(payload)
        return
    console.print(
        "[green]Obsidian vault export complete:[/green] "
        f"files={len(payload['files'])} skipped={len(payload['skipped'])} manifest={out / 'threadvault-export-manifest.json'}"
    )


@export_target_app.command("skill")
def export_target_skill_command(
    session: Annotated[list[str] | None, typer.Option("--session", help="Session id to include. Repeatable.")] = None,
    project: Annotated[str | None, typer.Option("--project", help="Project cwd to include.")] = None,
    out: Annotated[Path, typer.Option("--out", "-o", help="Target output directory.")] = Path("threadvault-skill-candidate"),
    skill_name: Annotated[str | None, typer.Option("--skill-name", help="Generated Skill name.")] = None,
    skill_description: Annotated[str | None, typer.Option("--skill-description", help="Generated Skill description.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    privacy_mode: Annotated[str, typer.Option("--privacy-mode", help="warn, redact, or fail.")] = "warn",
    privacy_config: Annotated[Path | None, typer.Option("--privacy-config", help="Optional threadvault.toml privacy config.")] = None,
    governance_role: Annotated[str | None, typer.Option("--governance-role", help="Role for explicit governance preflight.")] = None,
    governance_config: Annotated[
        Path | None,
        typer.Option("--governance-config", help="Optional threadvault.toml for governance preflight."),
    ] = None,
    governance_audit_log: Annotated[
        Path | None,
        typer.Option("--governance-audit-log", help="Optional local audit JSONL path for governance preflight."),
    ] = None,
    governance_actor: Annotated[str | None, typer.Option("--governance-actor", help="Actor for governance audit metadata.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Batch export sessions/project to a Codex Skill candidate folder."""
    if not session and not project:
        raise typer.BadParameter("Provide at least one --session or --project.")
    if privacy_mode not in {"warn", "redact", "fail"}:
        raise typer.BadParameter("--privacy-mode must be warn, redact, or fail.")
    governance = _maybe_governance_instrumentation(
        db,
        command="threadvault export-target skill",
        role=governance_role,
        config=governance_config,
        audit_log=governance_audit_log,
        actor=governance_actor,
        target_type="export_target",
        target_id=str(out),
    )
    if _governance_blocked(governance):
        _emit_governance_blocked("threadvault export-target skill", governance, json_output)
    try:
        payload = _store(db).export_target(
            out,
            profile="skill",
            session_ids=session or [],
            project=project,
            privacy_mode=privacy_mode,
            privacy_config_path=privacy_config,
            skill_name=skill_name,
            skill_description=skill_description,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    _mark_governance_executed(governance)
    _attach_governance(payload, governance)
    if json_output:
        _print_json(payload)
        return
    console.print(
        "[green]Skill candidate export complete:[/green] "
        f"files={len(payload['files'])} skipped={len(payload['skipped'])} manifest={out / 'threadvault-export-manifest.json'}"
    )


@backup_history_app.command("list")
def backup_history_list_command(
    backup_dir: Annotated[Path, typer.Option("--dir", help="Backup directory.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """List valid ThreadVault backups in a directory."""
    payload = list_backup_files(backup_dir)
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Backup History")
    table.add_column("Path")
    table.add_column("Bytes", justify="right")
    table.add_column("Sessions", justify="right")
    for backup in payload["backups"]:
        table.add_row(escape(backup["path"]), str(backup["bytes"]), str(backup["stats"].get("sessions", "")))
    console.print(table)


@backup_history_app.command("latest")
def backup_history_latest_command(
    backup_dir: Annotated[Path, typer.Option("--dir", help="Backup directory.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Show the latest valid ThreadVault backup in a directory."""
    payload = latest_backup_file(backup_dir)
    if json_output:
        _print_json(payload)
        return
    if payload["latest"] is None:
        console.print("[yellow]No valid backups found.[/yellow]")
        raise typer.Exit(code=1)
    console.print(json.dumps(payload["latest"], ensure_ascii=False, indent=2))


@backup_history_app.command("verify-latest")
def backup_history_verify_latest_command(
    backup_dir: Annotated[Path, typer.Option("--dir", help="Backup directory.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Verify the latest valid ThreadVault backup in a directory."""
    payload = verify_latest_backup(backup_dir)
    if json_output:
        _print_json(payload)
    elif payload["ok"]:
        console.print(f"[green]Latest backup verified:[/green] {payload['latest']['path']}")
    else:
        console.print("[red]No valid backup could be verified.[/red]")
    if not payload["ok"]:
        raise typer.Exit(code=1)


@backup_history_app.command("prune")
def backup_history_prune_command(
    backup_dir: Annotated[Path, typer.Option("--dir", help="Backup directory.")],
    keep: Annotated[int | None, typer.Option("--keep", min=1, help="Number of latest valid backups to keep.")] = None,
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml config with [backup_history].keep.")] = None,
    apply: Annotated[bool, typer.Option("--apply", help="Actually delete old backups. Defaults to dry-run.")] = False,
    governance_role: Annotated[str | None, typer.Option("--governance-role", help="Role for explicit governance preflight.")] = None,
    governance_config: Annotated[
        Path | None,
        typer.Option("--governance-config", help="Optional threadvault.toml for governance preflight."),
    ] = None,
    governance_audit_log: Annotated[
        Path | None,
        typer.Option("--governance-audit-log", help="Optional local audit JSONL path for governance preflight."),
    ] = None,
    governance_actor: Annotated[str | None, typer.Option("--governance-actor", help="Actor for governance audit metadata.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Preview or apply backup retention."""
    governance = _maybe_governance_instrumentation(
        None,
        command="threadvault backup-history prune",
        role=governance_role,
        config=governance_config,
        audit_log=governance_audit_log,
        actor=governance_actor,
        target_type="backup_history",
        target_id=str(backup_dir),
    )
    if _governance_blocked(governance):
        _emit_governance_blocked("threadvault backup-history prune", governance, json_output)
    try:
        resolved_keep, keep_source = resolve_retention_keep(keep, config, "backup_history")
        payload = prune_backup_history(backup_dir, keep=resolved_keep, apply=apply)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    payload["keep_source"] = keep_source
    _mark_governance_executed(governance)
    _attach_governance(payload, governance)
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Backup Prune")
    table.add_column("Action")
    table.add_column("Count", justify="right")
    table.add_row("kept", str(len(payload["kept"])))
    table.add_row("deletable", str(len(payload["deletable"])))
    table.add_row("deleted", str(len(payload["deleted"])))
    console.print(table)

@app.command("validate-json")
def validate_json_command(
    schema: Annotated[str, typer.Option("--schema", help="Schema name.")],
    input_path: Annotated[Path, typer.Option("--input", "-i", help="JSON payload file.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = False,
) -> None:
    """Validate a JSON payload against a ThreadVault schema."""
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    try:
        result = validate_payload(schema, payload)
    except KeyError as exc:
        raise typer.BadParameter(f"Unknown schema: {exc.args[0]}") from exc
    if json_output:
        _print_json(result)
    elif result["ok"]:
        console.print("[green]JSON payload is valid.[/green]")
    else:
        table = Table(title="Validation Errors")
        table.add_column("Path")
        table.add_column("Message")
        for error in result["errors"]:
            table.add_row(".".join(str(part) for part in error["path"]), escape(error["message"]))
        console.print(table)
    if not result["ok"]:
        raise typer.Exit(code=1)


@app.command("reindex")
def reindex_command(
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    fts_only: Annotated[bool, typer.Option("--fts-only", help="Rebuild only FTS index.")] = True,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Rebuild derived indexes."""
    try:
        payload = _store(db).reindex(fts_only=fts_only)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    if json_output:
        _print_json(payload)
        return
    console.print(f"[green]Reindexed FTS:[/green] events={payload['events']} events_fts={payload['events_fts']}")


@app.command("vacuum")
def vacuum_command(
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Run SQLite VACUUM on the archive database."""
    payload = _store(db).vacuum()
    if json_output:
        _print_json(payload)
        return
    console.print(f"[green]Vacuum complete:[/green] {payload['db_path']}")


@app.command("backup")
def backup_command(
    out: Annotated[Path, typer.Option("--out", "-o", help="Backup output file or directory.")],
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    force: Annotated[bool, typer.Option("--force", help="Overwrite an existing backup file.")] = False,
    no_manifest: Annotated[bool, typer.Option("--no-manifest", help="Do not write a sidecar manifest file.")] = False,
    governance_role: Annotated[str | None, typer.Option("--governance-role", help="Role for explicit governance preflight.")] = None,
    governance_config: Annotated[
        Path | None,
        typer.Option("--governance-config", help="Optional threadvault.toml for governance preflight."),
    ] = None,
    governance_audit_log: Annotated[
        Path | None,
        typer.Option("--governance-audit-log", help="Optional local audit JSONL path for governance preflight."),
    ] = None,
    governance_actor: Annotated[str | None, typer.Option("--governance-actor", help="Actor for governance audit metadata.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Create a local SQLite backup of the ThreadVault archive."""
    governance = _maybe_governance_instrumentation(
        db,
        command="threadvault backup",
        role=governance_role,
        config=governance_config,
        audit_log=governance_audit_log,
        actor=governance_actor,
        target_type="backup",
        target_id=str(out),
    )
    if _governance_blocked(governance):
        _emit_governance_blocked("threadvault backup", governance, json_output)
    payload = _store(db).backup(out, force=force, write_manifest=not no_manifest)
    _mark_governance_executed(governance)
    _attach_governance(payload, governance)
    if json_output:
        _print_json(payload)
    elif payload["ok"]:
        console.print(f"[green]Backup written:[/green] {payload['destination']}")
    else:
        console.print(f"[yellow]Backup already exists:[/yellow] {payload['destination']}")
    if not payload["ok"]:
        raise typer.Exit(code=1)


@app.command("backup-verify")
def backup_verify_command(
    backup: Annotated[Path, typer.Option("--backup", help="Backup database file to verify.")],
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    manifest: Annotated[bool, typer.Option("--manifest", help="Also verify the sidecar manifest.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Verify a local ThreadVault SQLite backup."""
    payload = _store(db).verify_backup(backup, manifest=manifest)
    if json_output:
        _print_json(payload)
    elif payload["ok"]:
        console.print(f"[green]Backup verified:[/green] {payload['backup']}")
    else:
        console.print(f"[red]Backup verification failed:[/red] {payload['backup']}")
    if not payload["ok"]:
        raise typer.Exit(code=1)


@app.command("backup-manifest")
def backup_manifest_command(
    backup: Annotated[Path, typer.Option("--backup", help="Backup database file whose manifest should be verified.")],
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Verify a local ThreadVault backup sidecar manifest."""
    payload = _store(db).verify_backup_manifest(backup)
    if json_output:
        _print_json(payload)
    elif payload["ok"]:
        console.print(f"[green]Backup manifest verified:[/green] {payload['manifest']}")
    else:
        console.print(f"[red]Backup manifest verification failed:[/red] {payload['manifest']}")
    if not payload["ok"]:
        raise typer.Exit(code=1)


@app.command("restore-plan")
def restore_plan_command(
    backup: Annotated[Path, typer.Option("--backup", help="Backup database file to evaluate.")],
    target_db: Annotated[Path, typer.Option("--target-db", help="Future restore destination database path.")],
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Build a read-only restore preflight plan without writing files."""
    payload = _store(db).restore_plan(backup, target_db)
    if json_output:
        _print_json(payload)
    elif payload["ok"]:
        console.print(f"[green]Restore plan looks usable:[/green] {payload['target_db']}")
    else:
        console.print(f"[red]Restore plan has blocking issues:[/red] {payload['target_db']}")
    if not payload["ok"]:
        raise typer.Exit(code=1)


@app.command("restore")
def restore_command(
    backup: Annotated[Path, typer.Option("--backup", help="Backup database file to restore.")],
    target_db: Annotated[Path, typer.Option("--target-db", help="Restore destination database path.")],
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    apply: Annotated[bool, typer.Option("--apply", help="Actually restore the backup. Defaults to dry-run.")] = False,
    overwrite: Annotated[bool, typer.Option("--overwrite", help="Allow replacing an existing target database.")] = False,
    pre_restore_backup_dir: Annotated[
        Path | None,
        typer.Option("--pre-restore-backup-dir", help="Directory for backing up an existing target before overwrite."),
    ] = None,
    allow_missing_manifest: Annotated[
        bool,
        typer.Option("--allow-missing-manifest", help="Allow applying a legacy backup without a manifest."),
    ] = False,
    restore_history: Annotated[Path | None, typer.Option("--restore-history", help="Optional restore history JSONL path.")] = None,
    governance_role: Annotated[str | None, typer.Option("--governance-role", help="Role for explicit governance preflight.")] = None,
    governance_config: Annotated[
        Path | None,
        typer.Option("--governance-config", help="Optional threadvault.toml for governance preflight."),
    ] = None,
    governance_audit_log: Annotated[
        Path | None,
        typer.Option("--governance-audit-log", help="Optional local audit JSONL path for governance preflight."),
    ] = None,
    governance_actor: Annotated[str | None, typer.Option("--governance-actor", help="Actor for governance audit metadata.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Restore a ThreadVault backup with explicit safety gates."""
    governance = _maybe_governance_instrumentation(
        db,
        command="threadvault restore",
        role=governance_role,
        config=governance_config,
        audit_log=governance_audit_log,
        actor=governance_actor,
        target_type="restore",
        target_id=str(target_db),
    )
    if _governance_blocked(governance):
        _emit_governance_blocked("threadvault restore", governance, json_output)
    payload = _store(db).restore(
        backup=backup,
        target_db=target_db,
        apply=apply,
        overwrite=overwrite,
        pre_restore_backup_dir=pre_restore_backup_dir,
        allow_missing_manifest=allow_missing_manifest,
        restore_history=restore_history,
    )
    _mark_governance_executed(governance)
    _attach_governance(payload, governance)
    if json_output:
        _print_json(payload)
    elif payload["ok"]:
        console.print(f"[green]Restore {payload['mode']}:[/green] {payload['target_db']}")
    else:
        console.print(f"[red]Restore blocked:[/red] {payload['target_db']}")
    if not payload["ok"]:
        raise typer.Exit(code=1)


@restore_history_app.command("list")
def restore_history_list_command(
    history: Annotated[Path | None, typer.Option("--history", help="Restore history JSONL path.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """List local restore history records."""
    payload = _store(db).restore_history_list(history)
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Restore History")
    table.add_column("Restored")
    table.add_column("Target")
    table.add_column("Backup")
    for record in payload["records"]:
        table.add_row(str(record.get("restored_at") or ""), escape(record.get("target_db") or ""), escape(record.get("backup") or ""))
    console.print(table)


@restore_history_app.command("latest")
def restore_history_latest_command(
    history: Annotated[Path | None, typer.Option("--history", help="Restore history JSONL path.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Show the latest local restore history record."""
    payload = _store(db).restore_history_latest(history)
    if json_output:
        _print_json(payload)
        return
    latest = payload.get("latest")
    if latest is None:
        console.print("[yellow]No restore history records found.[/yellow]")
        raise typer.Exit(code=1)
    console.print(json.dumps(latest, ensure_ascii=False, indent=2))


@restore_history_app.command("prune")
def restore_history_prune_command(
    history: Annotated[Path | None, typer.Option("--history", help="Restore history JSONL path.")] = None,
    keep: Annotated[int | None, typer.Option("--keep", min=1, help="Number of latest valid restore records to keep.")] = None,
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml config with [restore_history].keep.")] = None,
    apply: Annotated[bool, typer.Option("--apply", help="Rewrite the history file. Defaults to dry-run.")] = False,
    db: Annotated[Path | None, typer.Option("--db", help="Unused; kept for command shape consistency.")] = None,
    governance_role: Annotated[str | None, typer.Option("--governance-role", help="Role for explicit governance preflight.")] = None,
    governance_config: Annotated[
        Path | None,
        typer.Option("--governance-config", help="Optional threadvault.toml for governance preflight."),
    ] = None,
    governance_audit_log: Annotated[
        Path | None,
        typer.Option("--governance-audit-log", help="Optional local audit JSONL path for governance preflight."),
    ] = None,
    governance_actor: Annotated[str | None, typer.Option("--governance-actor", help="Actor for governance audit metadata.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Preview or apply restore history retention."""
    governance = _maybe_governance_instrumentation(
        db,
        command="threadvault restore-history prune",
        role=governance_role,
        config=governance_config,
        audit_log=governance_audit_log,
        actor=governance_actor,
        target_type="restore_history",
        target_id=str(history) if history else None,
    )
    if _governance_blocked(governance):
        _emit_governance_blocked("threadvault restore-history prune", governance, json_output)
    try:
        resolved_keep, keep_source = resolve_retention_keep(keep, config, "restore_history")
        payload = _store(db).restore_history_prune(history, keep=resolved_keep, apply=apply)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    payload["keep_source"] = keep_source
    _mark_governance_executed(governance)
    _attach_governance(payload, governance)
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Restore History Prune")
    table.add_column("Action")
    table.add_column("Count", justify="right")
    table.add_row("kept", str(len(payload["kept"])))
    table.add_row("deletable", str(len(payload["deletable"])))
    table.add_row("warnings", str(len(payload["warnings"])))
    console.print(table)

@app.command("doctor")
def doctor_command(
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    codex_home: Annotated[Path | None, typer.Option("--codex-home", help="Codex home directory.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Run local diagnostics for database, FTS, and Codex session discovery."""
    payload = _store(db).doctor(codex_home=codex_home)
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Doctor")
    table.add_column("Check")
    table.add_column("OK")
    table.add_column("Message")
    for check in payload["checks"]:
        table.add_row(escape(check["name"]), "yes" if check["ok"] else "no", escape(check["message"]))
    console.print(table)
    console.print(f"Codex home: {payload['codex_home']}")
    console.print(f"JSONL files: {payload['jsonl_files']}")


@app.command("warnings")
def warnings_command(
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, max=500)] = 50,
    session: Annotated[str | None, typer.Option("--session", help="Filter by session id.")] = None,
    code: Annotated[str | None, typer.Option("--code", help="Filter by warning code.")] = None,
    path: Annotated[str | None, typer.Option("--path", help="Filter by raw path.")] = None,
    summary: Annotated[bool, typer.Option("--summary", help="Summarize warnings by code.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """List parse warnings."""
    store = _store(db)
    if summary:
        payload = store.warning_summary()
        if json_output:
            _print_json(payload)
            return
        table = Table(title="ThreadVault Warning Summary")
        table.add_column("Code")
        table.add_column("Count", justify="right")
        for item in payload:
            table.add_row(escape(item["code"]), str(item["count"]))
        console.print(table)
        return
    rows = store.warnings(limit=limit, session_id=session, code=code, raw_path=path)
    payload = [dict(row) for row in rows]
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Parse Warnings")
    table.add_column("ID", justify="right")
    table.add_column("Session")
    table.add_column("Code")
    table.add_column("Line", justify="right")
    table.add_column("Message")
    for row in rows:
        table.add_row(
            str(row["warning_id"]),
            escape(row["session_id"] or ""),
            escape(row["code"]),
            str(row["line_no"] or ""),
            escape(row["message"]),
        )
    console.print(table)


@app.command("ingest-sample")
def ingest_sample_command(
    codex_home: Annotated[Path | None, typer.Option("--codex-home", help="Codex home directory.")] = None,
    limit: Annotated[int | None, typer.Option("--limit", min=1, help="Maximum JSONL files to sample.")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Parse only; do not write database.")] = True,
    include_paths: Annotated[
        bool,
        typer.Option("--include-paths", help="Include raw paths and session IDs in local debug output."),
    ] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Sample Codex JSONL parse health without importing raw content."""
    if not dry_run:
        raise typer.BadParameter("v0.4 ingest-sample only supports --dry-run.")
    payload = sample_codex_home(codex_home=codex_home, limit=limit, include_paths=include_paths)
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Ingest Sample")
    table.add_column("Metric")
    table.add_column("Value")
    for key in ("files", "parseable_files", "parseable_ratio", "events", "warnings"):
        table.add_row(key, str(payload[key]))
    console.print(table)


@app.command("audit-corpus")
def audit_corpus_command(
    codex_home: Annotated[Path | None, typer.Option("--codex-home", help="Codex home directory.")] = None,
    limit: Annotated[int | None, typer.Option("--limit", min=1, help="Maximum JSONL files to sample.")] = None,
    out: Annotated[Path | None, typer.Option("--out", "-o", help="Write timestamped audit report to this directory.")] = None,
    include_paths: Annotated[
        bool,
        typer.Option("--include-paths", help="Include raw paths and session IDs in local debug output."),
    ] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Audit Codex corpus parse health without emitting raw transcript content."""
    payload = sample_codex_home(codex_home=codex_home, limit=limit, include_paths=include_paths)
    if out is not None:
        path = write_audit_report(payload, out)
        payload = {**payload, "report_path": str(path)}
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Corpus Audit")
    table.add_column("Metric")
    table.add_column("Value")
    for key in ("files", "parseable_files", "parseable_ratio", "events", "warnings"):
        table.add_row(key, str(payload[key]))
    console.print(payload["privacy_note"])
    console.print(table)
    if out is not None:
        console.print(f"[green]Report:[/green] {payload['report_path']}")


@app.command("audit-diff")
def audit_diff_command(
    before: Annotated[Path, typer.Option("--before", help="Earlier audit report JSON.")],
    after: Annotated[Path, typer.Option("--after", help="Later audit report JSON.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Compare two anonymous corpus audit reports."""
    payload = diff_audit_reports(load_audit_report(before), load_audit_report(after))
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Audit Diff")
    table.add_column("Metric")
    table.add_column("Delta")
    for key in ("files_delta", "events_delta", "warnings_delta", "parseable_ratio_delta"):
        table.add_row(key, str(payload[key]))
    console.print(table)


@audit_history_app.command("list")
def audit_history_list_command(
    report_dir: Annotated[Path, typer.Option("--dir", help="Audit report directory.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """List valid ThreadVault audit reports in a directory."""
    payload = list_audit_reports(report_dir)
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Audit History")
    table.add_column("Generated")
    table.add_column("Warnings", justify="right")
    table.add_column("Path")
    for report in payload["reports"]:
        table.add_row(str(report.get("generated_at") or ""), str(report.get("warnings") or ""), escape(report["path"]))
    console.print(table)


@audit_history_app.command("latest")
def audit_history_latest_command(
    report_dir: Annotated[Path, typer.Option("--dir", help="Audit report directory.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Show the latest valid ThreadVault audit report in a directory."""
    payload = latest_audit_report(report_dir)
    if json_output:
        _print_json(payload)
        return
    latest = payload.get("latest")
    if latest is None:
        console.print("[yellow]No audit reports found.[/yellow]")
        raise typer.Exit(code=1)
    console.print(json.dumps(latest, ensure_ascii=False, indent=2))


@audit_history_app.command("diff-latest")
def audit_history_diff_latest_command(
    report_dir: Annotated[Path, typer.Option("--dir", help="Audit report directory.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Compare the latest two valid ThreadVault audit reports."""
    payload = diff_latest_audit_reports(report_dir)
    if json_output:
        _print_json(payload)
    elif payload["ok"]:
        table = Table(title="ThreadVault Latest Audit Diff")
        table.add_column("Metric")
        table.add_column("Delta")
        for key in ("files_delta", "events_delta", "warnings_delta", "parseable_ratio_delta"):
            table.add_row(key, str(payload["diff"][key]))
        console.print(table)
    else:
        console.print("[yellow]At least two valid reports are required.[/yellow]")
    if not payload["ok"]:
        raise typer.Exit(code=1)


@audit_history_app.command("prune")
def audit_history_prune_command(
    report_dir: Annotated[Path, typer.Option("--dir", help="Audit report directory.")],
    keep: Annotated[int | None, typer.Option("--keep", min=1, help="Number of latest valid reports to keep.")] = None,
    config: Annotated[Path | None, typer.Option("--config", help="Optional threadvault.toml config with [audit_history].keep.")] = None,
    apply: Annotated[bool, typer.Option("--apply", help="Actually delete old reports. Defaults to dry-run.")] = False,
    governance_role: Annotated[str | None, typer.Option("--governance-role", help="Role for explicit governance preflight.")] = None,
    governance_config: Annotated[
        Path | None,
        typer.Option("--governance-config", help="Optional threadvault.toml for governance preflight."),
    ] = None,
    governance_audit_log: Annotated[
        Path | None,
        typer.Option("--governance-audit-log", help="Optional local audit JSONL path for governance preflight."),
    ] = None,
    governance_actor: Annotated[str | None, typer.Option("--governance-actor", help="Actor for governance audit metadata.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Preview or apply audit report retention."""
    governance = _maybe_governance_instrumentation(
        None,
        command="threadvault audit-history prune",
        role=governance_role,
        config=governance_config,
        audit_log=governance_audit_log,
        actor=governance_actor,
        target_type="audit_history",
        target_id=str(report_dir),
    )
    if _governance_blocked(governance):
        _emit_governance_blocked("threadvault audit-history prune", governance, json_output)
    try:
        resolved_keep, keep_source = resolve_retention_keep(keep, config, "audit_history")
        payload = prune_audit_history(report_dir, keep=resolved_keep, apply=apply)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    payload["keep_source"] = keep_source
    _mark_governance_executed(governance)
    _attach_governance(payload, governance)
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Audit Prune")
    table.add_column("Action")
    table.add_column("Count", justify="right")
    table.add_row("kept", str(len(payload["kept"])))
    table.add_row("deletable", str(len(payload["deletable"])))
    table.add_row("deleted", str(len(payload["deleted"])))
    console.print(table)

@app.command("privacy-scan")
def privacy_scan_command(
    session: Annotated[str, typer.Option("--session", help="Session id to scan.")],
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    privacy_config: Annotated[Path | None, typer.Option("--privacy-config", help="Optional threadvault.toml privacy config.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Scan a session for sensitive content without exporting it."""
    try:
        payload = _store(db).privacy_scan(session, privacy_config_path=privacy_config)
    except KeyError as exc:
        raise typer.BadParameter(f"Unknown session: {exc.args[0]}") from exc
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Privacy Scan")
    table.add_column("Kind")
    table.add_column("Severity")
    table.add_column("Excerpt")
    for finding in payload["findings"][:50]:
        table.add_row(escape(finding["kind"]), escape(finding["severity"]), escape(finding["excerpt"]))
    console.print(table)


@app.command("self-test")
def self_test_command(
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Run local ThreadVault checks without scanning real Codex transcripts."""
    payload = _store(db).self_test()
    if json_output:
        _print_json(payload)
        return
    table = Table(title="ThreadVault Self Test")
    table.add_column("Check")
    table.add_column("OK")
    for check in payload["checks"]:
        table.add_row(escape(check["name"]), "yes" if check["ok"] else "no")
    console.print(table)
    if not payload["ok"]:
        raise typer.Exit(code=1)


def _search_payload(row, fields: str) -> dict:
    if fields == "minimal":
        return {"event_id": row.event_id, "session_id": row.session_id}
    payload = row.model_dump()
    if fields == "standard":
        payload.pop("rank", None)
    return payload


def _handle_vector_error(exc: Exception, json_output: bool) -> None:
    code = "vector_disabled" if isinstance(exc, PermissionError) else "vector_error"
    if json_output:
        _print_json({"ok": False, "code": code, "error": str(exc)})
        raise typer.Exit(code=1) from exc
    raise typer.BadParameter(str(exc)) from exc


def _parse_metadata(items: list[str] | None) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            raise typer.BadParameter("--metadata values must use key=value.")
        key, value = item.split("=", 1)
        if not key:
            raise typer.BadParameter("--metadata keys must not be empty.")
        metadata[key] = value
    return metadata


def _print_privacy_findings(findings) -> None:
    if not findings:
        return
    table = Table(title="Privacy warnings")
    table.add_column("Kind")
    table.add_column("Excerpt")
    for finding in findings[:20]:
        table.add_row(escape(finding.kind), escape(finding.excerpt))
    console.print("[yellow]Potential sensitive content found. Nothing was removed automatically.[/yellow]")
    console.print(table)
