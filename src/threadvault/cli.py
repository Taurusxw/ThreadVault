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
from .codex_integration import codex_integration_status, install_codex_integration
from .config import default_codex_home, default_db_path
from .importer import sample_codex_home
from .mcp import McpRuntimeConfig, mcp_manifest, serve_mcp
from .privacy import has_high_risk
from .retention import resolve_retention_keep
from .schemas import get_schema, schema_names, validate_payload, write_schema_files
from .store import ArchiveStore, capabilities, robot_guide, robot_schemas
from .summarizer import summary_to_markdown

app = typer.Typer(help="ThreadVault: local-first Codex session archive.")
console = Console()


def _db_option(value: Path | None, config: Path | None = None) -> Path:
    return (value or default_db_path(config)).expanduser()


def _store(db: Path | None, config: Path | None = None) -> ArchiveStore:
    return ArchiveStore(_db_option(db, config))


def _print_json(value) -> None:
    # Machine output must survive legacy Windows/charmap stdout as well as UTF-8 terminals.
    typer.echo(json.dumps(value, ensure_ascii=True, indent=2, default=str))


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
    payload = {"path": str(path), "privacy_findings": [finding.__dict__ for finding in findings]}
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

codex_app = typer.Typer(help="Install and diagnose the complete Codex integration.")
app.add_typer(codex_app, name="codex")

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

storage_app = typer.Typer(help="Hot/cold archive lifecycle and backup utilities.")
app.add_typer(storage_app, name="storage")


@storage_app.command("audit")
def storage_audit_command(
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    cold_root: Annotated[Path | None, typer.Option("--cold-root", help="Cold blob directory.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Measure hot database usage and cold-storage composition."""
    payload = _store(db).storage_audit(cold_root)
    if json_output:
        _print_json(payload)
    else:
        console.print(f"[green]Database:[/green] {payload['db_path']}")
        console.print(f"[green]Hot bytes:[/green] {payload['db_bytes']}")
        console.print(f"[green]Cold blobs:[/green] {payload['cold']['blobs']}")
    if not payload.get("ok"):
        raise typer.Exit(code=2)


@storage_app.command("rebuild")
def storage_rebuild_command(
    target_db: Annotated[Path, typer.Option("--target-db", help="New compact SQLite database path.")],
    db: Annotated[Path | None, typer.Option("--db", help="Source SQLite database path.")] = None,
    cold_root: Annotated[Path | None, typer.Option("--cold-root", help="Cold blob directory for the rebuilt archive.")] = None,
    apply: Annotated[bool, typer.Option("--apply", help="Execute the copy-on-write rebuild.")] = False,
    batch_size: Annotated[int, typer.Option("--batch-size", min=1, max=10000)] = 1000,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Rebuild an archive with the current hot/cold storage policy."""
    payload = _store(db).storage_rebuild(target_db, cold_root, apply=apply, batch_size=batch_size)
    if json_output:
        _print_json(payload)
    else:
        console.print(payload)


@storage_app.command("sync")
def storage_sync_command(
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    codex_home: Annotated[Path | None, typer.Option("--codex-home", help="Codex home containing transcript JSONL files.")] = None,
    apply: Annotated[bool, typer.Option("--apply", help="Import only transcripts missing or newer than the archive.")] = False,
    include_paths: Annotated[bool, typer.Option("--include-paths", help="Include local pending paths in JSON output.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Check source freshness or catch the archive up before backup."""
    payload = _store(db).storage_sync(codex_home=codex_home, apply=apply, include_paths=include_paths)
    if json_output:
        _print_json(payload)
    else:
        if apply and payload["ok"]:
            action = "Archive synchronized"
        else:
            action = "Archive is current" if payload["fresh"] else "Source catch-up required"
        console.print(f"[green]{action}:[/green] pending={payload['pending_files']} source={payload['source_files']}")
    if apply and not payload.get("ok"):
        raise typer.Exit(code=2)


@storage_app.command("verify")
def storage_verify_command(
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    cold_root: Annotated[Path | None, typer.Option("--cold-root", help="Cold blob directory.")] = None,
    deep: Annotated[bool, typer.Option("--deep", help="Decompress and hash every cold blob.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Verify cold blob presence, size, and optionally content hashes."""
    payload = _store(db).storage_verify(cold_root, deep=deep)
    if json_output:
        _print_json(payload)
    else:
        console.print(payload)
    if not payload.get("ok"):
        raise typer.Exit(code=2)


@storage_app.command("event")
def storage_event_command(
    event_id: Annotated[int, typer.Option("--event-id", min=1, help="Event id to hydrate.")],
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    cold_root: Annotated[Path | None, typer.Option("--cold-root", help="Cold blob directory.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Read one event with its original cold payload restored."""
    try:
        payload = _store(db).storage_event(event_id, cold_root)
    except KeyError as exc:
        raise typer.BadParameter(f"Unknown event: {exc.args[0]}") from exc
    if json_output:
        _print_json(payload)
    else:
        console.print(payload)


@storage_app.command("prune")
def storage_prune_command(
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    cold_root: Annotated[Path | None, typer.Option("--cold-root", help="Cold blob directory.")] = None,
    apply: Annotated[bool, typer.Option("--apply", help="Delete unreferenced cold blobs.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Plan or apply garbage collection for unreferenced cold blobs."""
    payload = _store(db).storage_prune(cold_root, apply=apply)
    if json_output:
        _print_json(payload)
    else:
        console.print(payload)


@storage_app.command("backup")
def storage_backup_command(
    out: Annotated[Path, typer.Option("--out", "-o", help="Backup directory.")],
    profile: Annotated[str, typer.Option("--profile", help="core, evidence, or forensic.")] = "core",
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    cold_root: Annotated[Path | None, typer.Option("--cold-root", help="Cold blob directory.")] = None,
    codex_home: Annotated[Path | None, typer.Option("--codex-home", help="Codex home for forensic source JSONL.")] = None,
    force: Annotated[bool, typer.Option("--force", help="Allow replacing a same-name backup.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Create a Core, Evidence, or Forensic storage backup."""
    if profile not in {"core", "evidence", "forensic"}:
        raise typer.BadParameter("--profile must be core, evidence, or forensic.")
    payload = _store(db).storage_backup(
        out,
        profile=profile,
        cold_root=cold_root,
        codex_home=codex_home,
        force=force,
    )
    if json_output:
        _print_json(payload)
    else:
        console.print(payload)
    if not payload.get("ok"):
        raise typer.Exit(code=2)


@storage_app.command("verify-backup")
def storage_backup_verify_command(
    manifest: Annotated[Path, typer.Option("--manifest", help="Storage backup manifest path.")],
    deep: Annotated[bool, typer.Option("--deep", help="Verify cold and forensic content hashes.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Verify a storage-profile backup and its referenced content."""
    payload = _store(None).storage_backup_verify(manifest, deep=deep)
    if json_output:
        _print_json(payload)
    else:
        console.print(payload)
    if not payload.get("ok"):
        raise typer.Exit(code=2)


@storage_app.command("auto")
def storage_auto_command(
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    out: Annotated[Path | None, typer.Option("--out", "-o", help="Smart backup root directory.")] = None,
    cold_root: Annotated[Path | None, typer.Option("--cold-root", help="Cold blob directory.")] = None,
    codex_home: Annotated[Path | None, typer.Option("--codex-home", help="Codex home for monthly forensic backups.")] = None,
    apply: Annotated[bool, typer.Option("--apply", help="Create the due backup and apply bounded retention.")] = False,
    forensic: Annotated[
        bool,
        typer.Option("--forensic/--no-forensic", help="Enable the monthly source-JSONL backup tier."),
    ] = True,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Automatically choose, verify, and retain the appropriate backup tier."""
    payload = _store(db).storage_auto_backup(
        out_root=out,
        cold_root=cold_root,
        codex_home=codex_home,
        apply=apply,
        include_forensic=forensic,
    )
    if json_output:
        _print_json(payload)
    else:
        console.print(payload)
    if not payload.get("ok"):
        raise typer.Exit(code=2)

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
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Run the v2 retrieval query contract."""
    if fields not in {"minimal", "standard", "full"}:
        raise typer.BadParameter("--fields must be minimal, standard, or full.")
    if mode not in {"fts"}:
        raise typer.BadParameter("--mode must be fts.")
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
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Run hybrid FTS/vector retrieval with explanations."""
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
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Emit a safe local client session detail payload."""
    try:
        payload = _store(db).client_session(
            session_id=session,
            event_limit=event_limit,
            max_chars=max_chars,
            local_debug=local_debug,
        )
    except KeyError as exc:
        raise typer.BadParameter(f"Unknown session: {exc.args[0]}") from exc
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
    )
    if json_output:
        _print_json(payload)
        return
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
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Emit safe client warning and privacy detail for a session."""
    try:
        payload = _store(db).client_warnings(
            session_id=session,
            privacy_config_path=privacy_config,
            local_debug=local_debug,
        )
    except KeyError as exc:
        raise typer.BadParameter(f"Unknown session: {exc.args[0]}") from exc
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
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Run the agent-facing retrieval contract."""
    if mode not in {"hybrid", "fts"}:
        raise typer.BadParameter("--mode must be hybrid or fts.")
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
    apply: Annotated[
        bool,
        typer.Option("--apply", help="Immediately import only the transcript named by this hook payload."),
    ] = False,
    diagnostic_json: Annotated[
        bool,
        typer.Option("--diagnostic-json", help="Emit ThreadVault diagnostic JSON instead of hook response."),
    ] = False,
) -> None:
    """Read a Codex Hook payload, enqueue it, and optionally import its transcript."""
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            raise ValueError("Hook payload must be a JSON object.")
        result = _store(db).handle_codex_hook(payload, codex_home=codex_home, apply=apply)
    except Exception as exc:  # noqa: BLE001 - hooks should not break Codex turns.
        result = invalid_hook_payload_result(str(exc))
    _print_json(result if diagnostic_json else result.get("hook_response", hook_continue_response()))


@codex_hook_app.command("config")
def codex_hook_config_command(
    command: Annotated[
        str,
        typer.Option("--command", help="Hook command to place in the generated snippet."),
    ] = "threadvault codex-hook ingest --apply",
    timeout: Annotated[int, typer.Option("--timeout", min=1, help="Hook command timeout in seconds.")] = 30,
    status_message: Annotated[
        str,
        typer.Option("--status-message", help="Codex hook status message."),
    ] = "Archiving this Codex turn in ThreadVault",
    db: Annotated[Path | None, typer.Option("--db", help="Optional database path to include in the command.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Emit a Codex hooks.json Stop hook snippet for automatic single-file import."""
    resolved_command = command
    if db is not None and command == "threadvault codex-hook ingest --apply":
        resolved_command = f'threadvault codex-hook ingest --apply --db "{_db_option(db)}"'
    payload = _store(None).codex_hook_config(resolved_command, timeout=timeout, status_message=status_message)
    if json_output:
        _print_json(payload)
        return
    console.print(json.dumps(payload, ensure_ascii=False, indent=2))


@codex_hook_app.command("install")
def codex_hook_install_command(
    command: Annotated[
        str,
        typer.Option("--command", help="Absolute ThreadVault hook command to install."),
    ] = "threadvault codex-hook ingest --apply",
    timeout: Annotated[int, typer.Option("--timeout", min=1, help="Hook command timeout in seconds.")] = 30,
    status_message: Annotated[
        str,
        typer.Option("--status-message", help="Codex hook status message."),
    ] = "Archiving this Codex turn in ThreadVault",
    codex_home: Annotated[Path | None, typer.Option("--codex-home", help="Codex home containing hooks.json.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="Database path to include in the hook command.")] = None,
    apply: Annotated[bool, typer.Option("--apply", help="Write hooks.json. Defaults to a dry-run plan.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Plan or install the user-level automatic ThreadVault Stop hook."""
    resolved_command = command
    if db is not None and command == "threadvault codex-hook ingest --apply":
        resolved_command = f'threadvault codex-hook ingest --apply --db "{_db_option(db)}"'
    payload = _store(None).install_codex_hook(
        codex_home or default_codex_home(),
        resolved_command,
        timeout=timeout,
        status_message=status_message,
        apply=apply,
    )
    if json_output:
        _print_json(payload)
        return
    verb = "Installed" if apply else "Would install"
    console.print(f"[green]{verb} Codex Stop hook:[/green] {escape(payload['path'])}")
    if payload["trust_required"]:
        console.print("Open /hooks in Codex once to review and trust the new hook.")


@codex_app.command("status")
def codex_status_command(
    codex_home: Annotated[Path | None, typer.Option("--codex-home", help="Codex home containing config.toml and hooks.json.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="ThreadVault SQLite database path.")] = None,
    threadvault_executable: Annotated[
        Path | None,
        typer.Option("--threadvault-executable", help="Override the ThreadVault console executable."),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Report Hook, MCP, observed-ingestion, and source-freshness status."""
    payload = codex_integration_status(
        codex_home or default_codex_home(),
        _db_option(db),
        threadvault_executable=threadvault_executable,
    )
    if json_output:
        _print_json(payload)
        return
    console.print(f"[green]Configured:[/green] {payload['ok']}")
    console.print(f"[green]Healthy:[/green] {payload['healthy']}")
    console.print(f"[green]Pending transcripts:[/green] {payload['source_freshness']['pending_files']}")
    for action in payload["recommended_actions"]:
        console.print(f"- {escape(action)}")


@codex_app.command("install")
def codex_install_command(
    codex_home: Annotated[Path | None, typer.Option("--codex-home", help="Codex home to configure.")] = None,
    db: Annotated[Path | None, typer.Option("--db", help="ThreadVault SQLite database path.")] = None,
    threadvault_executable: Annotated[
        Path | None,
        typer.Option("--threadvault-executable", help="Override the ThreadVault console executable."),
    ] = None,
    codex_executable: Annotated[Path | None, typer.Option("--codex-executable", help="Override the Codex CLI executable.")] = None,
    apply: Annotated[bool, typer.Option("--apply", help="Install the pinned Stop hook and MCP server.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Plan or install the complete local Codex integration in one command."""
    payload = install_codex_integration(
        codex_home or default_codex_home(),
        _db_option(db),
        threadvault_executable=threadvault_executable,
        codex_executable=codex_executable,
        apply=apply,
    )
    if json_output:
        _print_json(payload)
    else:
        verb = "Installed" if apply else "Would install"
        console.print(f"[green]{verb} Codex integration.[/green]")
        console.print(f"Hook: {payload['hook']['action']} · MCP: {payload['mcp']['action']}")
        if payload["hook_trust_required"]:
            console.print("Open /hooks in Codex and trust the ThreadVault Stop hook.")
        if payload["restart_required"]:
            console.print("Restart Codex so the MCP server is loaded.")
    if not payload.get("ok"):
        raise typer.Exit(code=2)


@export_target_app.command("markdown")
def export_target_markdown_command(
    session: Annotated[list[str] | None, typer.Option("--session", help="Session id to include. Repeatable.")] = None,
    project: Annotated[str | None, typer.Option("--project", help="Project cwd to include.")] = None,
    out: Annotated[Path, typer.Option("--out", "-o", help="Target output directory.")] = Path("threadvault-target-export"),
    db: Annotated[Path | None, typer.Option("--db", help="SQLite database path.")] = None,
    privacy_mode: Annotated[str, typer.Option("--privacy-mode", help="warn, redact, or fail.")] = "warn",
    privacy_config: Annotated[Path | None, typer.Option("--privacy-config", help="Optional threadvault.toml privacy config.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Batch export sessions/project to Markdown with a manifest."""
    if not session and not project:
        raise typer.BadParameter("Provide at least one --session or --project.")
    if privacy_mode not in {"warn", "redact", "fail"}:
        raise typer.BadParameter("--privacy-mode must be warn, redact, or fail.")
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
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Batch export sessions/project to an Obsidian-ready Markdown vault."""
    if not session and not project:
        raise typer.BadParameter("Provide at least one --session or --project.")
    if privacy_mode not in {"warn", "redact", "fail"}:
        raise typer.BadParameter("--privacy-mode must be warn, redact, or fail.")
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
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Batch export sessions/project to a Codex Skill candidate folder."""
    if not session and not project:
        raise typer.BadParameter("Provide at least one --session or --project.")
    if privacy_mode not in {"warn", "redact", "fail"}:
        raise typer.BadParameter("--privacy-mode must be warn, redact, or fail.")
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
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Preview or apply backup retention."""
    try:
        resolved_keep, keep_source = resolve_retention_keep(keep, config, "backup_history")
        payload = prune_backup_history(backup_dir, keep=resolved_keep, apply=apply)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    payload["keep_source"] = keep_source
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
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Create a local SQLite backup of the ThreadVault archive."""
    payload = _store(db).backup(out, force=force, write_manifest=not no_manifest)
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
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Restore a ThreadVault backup with explicit safety gates."""
    payload = _store(db).restore(
        backup=backup,
        target_db=target_db,
        apply=apply,
        overwrite=overwrite,
        pre_restore_backup_dir=pre_restore_backup_dir,
        allow_missing_manifest=allow_missing_manifest,
        restore_history=restore_history,
    )
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
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Preview or apply restore history retention."""
    try:
        resolved_keep, keep_source = resolve_retention_keep(keep, config, "restore_history")
        payload = _store(db).restore_history_prune(history, keep=resolved_keep, apply=apply)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    payload["keep_source"] = keep_source
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
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Preview or apply audit report retention."""
    try:
        resolved_keep, keep_source = resolve_retention_keep(keep, config, "audit_history")
        payload = prune_audit_history(report_dir, keep=resolved_keep, apply=apply)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    payload["keep_source"] = keep_source
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
