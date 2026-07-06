from __future__ import annotations

import json
import threading
import time
import webbrowser
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .app_config import describe_app_config, diagnose_app_config, init_app_config, load_app_config
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
from .config import default_db_path
from .importer import sample_codex_home
from .schemas import get_schema, schema_names, validate_payload, write_schema_files
from .store import ArchiveStore, capabilities, robot_guide, robot_schemas

PERSONAL_UI_HEALTH_CONTRACT_VERSION = "personal_ui_health.v1"
PERSONAL_UI_ACTION_CONTRACT_VERSION = "personal_ui_action.v1"
PERSONAL_UI_SMOKE_CONTRACT_VERSION = "personal_ui_smoke.v1"
PERSONAL_UI_SERVE_COMMAND = "threadvault ui serve --host 127.0.0.1 --port 8766 --open"
PERSONAL_UI_SMOKE_COMMAND = "threadvault ui smoke --json"
PERSONAL_UI_EXPORT_DIR = "threadvault-ui-output"


@dataclass(frozen=True)
class PersonalUIServerConfig:
    host: str = "127.0.0.1"
    port: int = 8766
    db_path: Path | None = None
    config_path: Path | None = None
    language: str = "en"
    exit_on_close: bool = False
    close_timeout_seconds: float = 8.0

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def open_url(self) -> str:
        if self.language == "zh":
            return f"{self.url}/zh"
        return self.url


@dataclass(frozen=True)
class PersonalUIActionSpec:
    name: str
    label: str
    dangerous_action: bool = False
    confirm_required: bool = False
    preview_required: bool = False
    dry_run_default: bool = True
    implemented: bool = True
    deferred_reason: str | None = None


DANGEROUS_CONFIRM_ACTIONS = frozenset({"restore_apply", "vacuum", "reindex", "schema_write"})
EXPORT_WRITE_ACTIONS = frozenset({"export_session", "export_target_markdown", "export_target_obsidian", "export_target_skill"})
PRUNE_ACTIONS = frozenset({"backup_history_prune", "restore_history_prune", "audit_history_prune"})

ACTION_REGISTRY: dict[str, PersonalUIActionSpec] = {
    "init": PersonalUIActionSpec("init", "Initialize database", dry_run_default=False),
    "import": PersonalUIActionSpec("import", "Import Codex sessions", dry_run_default=False),
    "ingest_queue_enqueue": PersonalUIActionSpec("ingest_queue_enqueue", "Enqueue ingestion", dry_run_default=False),
    "ingest_queue_list": PersonalUIActionSpec("ingest_queue_list", "List ingestion queue"),
    "ingest_queue_process": PersonalUIActionSpec("ingest_queue_process", "Process ingestion queue"),
    "sessions_list": PersonalUIActionSpec("sessions_list", "List sessions"),
    "client_overview": PersonalUIActionSpec("client_overview", "Client overview"),
    "client_session": PersonalUIActionSpec("client_session", "Client session"),
    "client_export_preview": PersonalUIActionSpec("client_export_preview", "Client export preview"),
    "client_warnings": PersonalUIActionSpec("client_warnings", "Client warnings"),
    "search": PersonalUIActionSpec("search", "Search"),
    "retrieval_query": PersonalUIActionSpec("retrieval_query", "Retrieval query"),
    "hybrid_retrieval": PersonalUIActionSpec("hybrid_retrieval", "Hybrid retrieval"),
    "agent_retrieve": PersonalUIActionSpec("agent_retrieve", "Agent retrieve"),
    "summary_chunks": PersonalUIActionSpec("summary_chunks", "Summary chunks"),
    "summarize": PersonalUIActionSpec("summarize", "Summarize"),
    "vector_status": PersonalUIActionSpec("vector_status", "Vector status"),
    "vector_index": PersonalUIActionSpec("vector_index", "Vector index"),
    "vector_query": PersonalUIActionSpec("vector_query", "Vector query"),
    "privacy_scan": PersonalUIActionSpec("privacy_scan", "Privacy scan"),
    "warnings": PersonalUIActionSpec("warnings", "Warnings"),
    "warnings_summary": PersonalUIActionSpec("warnings_summary", "Warnings summary"),
    "export_preview": PersonalUIActionSpec("export_preview", "Export preview"),
    "export_session": PersonalUIActionSpec("export_session", "Export session", preview_required=True, dry_run_default=False),
    "export_target_markdown": PersonalUIActionSpec(
        "export_target_markdown",
        "Export target markdown",
        preview_required=True,
        dry_run_default=False,
    ),
    "export_target_obsidian": PersonalUIActionSpec(
        "export_target_obsidian",
        "Export target obsidian",
        preview_required=True,
        dry_run_default=False,
    ),
    "export_target_skill": PersonalUIActionSpec("export_target_skill", "Export target skill", preview_required=True, dry_run_default=False),
    "config_init": PersonalUIActionSpec("config_init", "Config init", dry_run_default=False),
    "config_show": PersonalUIActionSpec("config_show", "Config show"),
    "config_doctor": PersonalUIActionSpec("config_doctor", "Config doctor"),
    "stats": PersonalUIActionSpec("stats", "Stats"),
    "doctor": PersonalUIActionSpec("doctor", "Doctor"),
    "self_test": PersonalUIActionSpec("self_test", "Self-test"),
    "reindex": PersonalUIActionSpec("reindex", "Reindex", dangerous_action=True, confirm_required=True, dry_run_default=False),
    "vacuum": PersonalUIActionSpec("vacuum", "Vacuum", dangerous_action=True, confirm_required=True, dry_run_default=False),
    "backup": PersonalUIActionSpec("backup", "Backup", dry_run_default=False),
    "backup_verify": PersonalUIActionSpec("backup_verify", "Backup verify"),
    "backup_history": PersonalUIActionSpec("backup_history", "Backup history"),
    "backup_history_latest": PersonalUIActionSpec("backup_history_latest", "Latest backup"),
    "backup_history_verify_latest": PersonalUIActionSpec("backup_history_verify_latest", "Verify latest backup"),
    "backup_history_prune": PersonalUIActionSpec("backup_history_prune", "Prune backup history", dangerous_action=True),
    "restore_plan": PersonalUIActionSpec("restore_plan", "Restore plan"),
    "restore_apply": PersonalUIActionSpec(
        "restore_apply",
        "Restore apply",
        dangerous_action=True,
        confirm_required=True,
        dry_run_default=False,
    ),
    "restore_history": PersonalUIActionSpec("restore_history", "Restore history"),
    "restore_history_latest": PersonalUIActionSpec("restore_history_latest", "Latest restore"),
    "restore_history_prune": PersonalUIActionSpec("restore_history_prune", "Prune restore history", dangerous_action=True),
    "audit_corpus": PersonalUIActionSpec("audit_corpus", "Audit corpus"),
    "audit_history": PersonalUIActionSpec("audit_history", "Audit history"),
    "audit_history_latest": PersonalUIActionSpec("audit_history_latest", "Latest audit"),
    "audit_history_diff_latest": PersonalUIActionSpec("audit_history_diff_latest", "Diff latest audit"),
    "audit_history_prune": PersonalUIActionSpec("audit_history_prune", "Prune audit history", dangerous_action=True),
    "audit_diff": PersonalUIActionSpec("audit_diff", "Audit diff"),
    "schemas_list": PersonalUIActionSpec("schemas_list", "Schemas list"),
    "schema_list": PersonalUIActionSpec("schema_list", "Schemas list"),
    "schemas_show": PersonalUIActionSpec("schemas_show", "Schemas show"),
    "schema_show": PersonalUIActionSpec("schema_show", "Schemas show"),
    "validate_json": PersonalUIActionSpec("validate_json", "Validate JSON"),
    "schemas_write": PersonalUIActionSpec(
        "schemas_write",
        "Schemas write",
        dangerous_action=True,
        confirm_required=True,
        dry_run_default=False,
    ),
    "schema_write": PersonalUIActionSpec(
        "schema_write",
        "Schemas write",
        dangerous_action=True,
        confirm_required=True,
        dry_run_default=False,
    ),
    "capabilities": PersonalUIActionSpec("capabilities", "Capabilities"),
    "robot_docs_guide": PersonalUIActionSpec("robot_docs_guide", "Robot docs guide"),
    "robot_docs_schemas": PersonalUIActionSpec("robot_docs_schemas", "Robot docs schemas"),
    "governance_status": PersonalUIActionSpec("governance_status", "Governance status"),
    "governance_v3_gap_audit": PersonalUIActionSpec("governance_v3_gap_audit", "v3 gap audit"),
    "governance_v3_acceptance_smoke": PersonalUIActionSpec("governance_v3_acceptance_smoke", "v3 acceptance smoke"),
    "governance_preflight": PersonalUIActionSpec("governance_preflight", "Governance preflight"),
    "governance_instrumentation": PersonalUIActionSpec("governance_instrumentation", "Governance instrumentation"),
    "governance_external_model_preflight": PersonalUIActionSpec("governance_external_model_preflight", "External model preflight"),
}


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ThreadVault Personal UI</title>
  <link rel="stylesheet" href="/assets/app.css?v=20260702-paths">
</head>
<body>
  <aside class="nav" aria-label="Primary">
    <div class="brand">
      <strong>ThreadVault</strong>
      <span>Personal Web UI</span>
    </div>
    <button class="nav-button is-active" data-view="archive" type="button">Archive</button>
    <button class="nav-button" data-view="search" type="button">Search</button>
    <button class="nav-button" data-view="session" type="button">Session</button>
    <button class="nav-button" data-view="export" type="button">Export</button>
    <button class="nav-button" data-view="privacy" type="button">Privacy</button>
    <button class="nav-button" data-view="maintenance" type="button">Maintenance</button>
    <button class="nav-button" data-view="backup" type="button">Backup / Restore</button>
    <button class="nav-button" data-view="config" type="button">Config</button>
    <button class="nav-button" data-view="schemas" type="button">Schemas</button>
    <button class="nav-button" data-view="governance" type="button">Governance</button>
  </aside>
  <main class="workspace">
    <header class="topbar">
      <div class="status-block">
        <span id="status-dot" class="status-dot"></span>
        <span id="status">Starting...</span>
        <span id="db-path" class="muted"></span>
        <span id="export-path" class="muted"></span>
      </div>
      <div id="activity" class="activity" aria-live="polite" hidden>
        <div class="activity-main">
          <span class="spinner" aria-hidden="true"></span>
          <strong id="activity-title">Working</strong>
        </div>
        <ol id="activity-steps"></ol>
      </div>
      <div class="mode-switch" aria-label="Interface mode">
        <button id="mode-basic" class="mode-button" data-ui-mode="basic" type="button">Basic Mode</button>
        <button id="mode-pro" class="mode-button" data-ui-mode="pro" type="button">Pro Mode</button>
      </div>
      <form id="global-search" class="search-form">
        <input id="query" type="search" placeholder="Search archive" autocomplete="off">
        <select id="search-mode" aria-label="Search mode">
          <option value="hybrid">Hybrid</option>
          <option value="fts">Retrieval</option>
          <option value="agent">Agent</option>
        </select>
        <button type="submit">Search</button>
      </form>
      <button id="refresh" class="secondary" type="button">Refresh</button>
    </header>
    <section id="content" class="content" aria-live="polite">
      <div class="section-heading">
        <h1>Archive</h1>
        <p>Loading local archive overview.</p>
      </div>
    </section>
  </main>
  <aside class="json-panel" aria-label="Raw JSON output">
    <div class="panel-heading">
      <h2>JSON Output</h2>
      <button id="clear-json" class="secondary" type="button">Clear</button>
    </div>
    <pre id="json">{}</pre>
  </aside>
  <script src="/assets/app.js?v=20260702-paths"></script>
</body>
</html>
"""


APP_CSS = """
:root {
  color-scheme: light;
  --ink: #1f2328;
  --muted: #667085;
  --line: #d7dde5;
  --surface: #f5f6f8;
  --panel: #ffffff;
  --accent: #0f766e;
  --accent-ink: #ffffff;
  --warn: #9a3412;
  --danger: #b42318;
  --ok: #15803d;
  --shadow: 0 1px 2px rgba(16, 24, 40, 0.08);
}
* { box-sizing: border-box; }
html {
  height: 100%;
}
body {
  margin: 0;
  height: 100vh;
  display: grid;
  grid-template-columns: 220px minmax(420px, 1fr) minmax(320px, 34vw);
  font-family: "Segoe UI", system-ui, sans-serif;
  color: var(--ink);
  background: var(--panel);
  overflow: hidden;
}
body.mode-basic {
  grid-template-columns: minmax(420px, 1fr);
}
body.mode-basic .nav,
body.mode-basic .json-panel {
  display: none;
}
body.mode-basic .content {
  align-content: start;
}
.nav {
  background: #eef2f6;
  border-right: 1px solid var(--line);
  padding: 16px;
  overflow: auto;
}
.brand {
  display: grid;
  gap: 2px;
  margin-bottom: 16px;
}
.brand strong { font-size: 18px; }
.brand span, .muted { color: var(--muted); font-size: 12px; }
.nav-button, button, select, input, textarea {
  font: inherit;
}
.nav-button, .topbar button, .action-button {
  width: 100%;
  margin-top: 10px;
  padding: 9px 10px;
  border: 1px solid var(--line);
  background: var(--panel);
  color: var(--ink);
  text-align: left;
  border-radius: 6px;
  cursor: pointer;
}
.nav-button.is-active {
  border-color: var(--accent);
  color: var(--accent);
  box-shadow: inset 3px 0 0 var(--accent);
}
.topbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 10px;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--line);
  background: var(--panel);
  position: sticky;
  top: 0;
  z-index: 2;
}
.status-block {
  display: flex;
  align-items: center;
  gap: 8px;
  grid-column: 1 / -1;
  min-width: 0;
  overflow: hidden;
}
.status-block span { overflow-wrap: anywhere; }
#db-path,
#export-path {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--warn);
  flex: 0 0 auto;
}
.status-dot.ok { background: var(--ok); }
.status-dot.fail { background: var(--danger); }
.activity {
  grid-column: 1 / -1;
  display: grid;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid #b7d9d4;
  border-radius: 8px;
  background: #f0fdfa;
}
.activity[hidden] { display: none; }
.activity-main {
  display: flex;
  align-items: center;
  gap: 8px;
}
.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid #99f6e4;
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex: 0 0 auto;
}
.activity.is-done .spinner {
  position: relative;
  border-color: var(--ok);
  background: var(--ok);
  animation: none;
}
.activity.is-done .spinner::after {
  content: "";
  position: absolute;
  left: 4px;
  top: 1px;
  width: 4px;
  height: 8px;
  border: solid #fff;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}
.activity.is-failed .spinner {
  border-color: var(--danger);
  border-top-color: var(--danger);
  animation: none;
}
.activity ol {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.activity li, .workflow-step {
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 4px 9px;
  background: var(--panel);
  color: var(--muted);
  font-size: 12px;
}
.activity li.is-active, .workflow-step.is-active {
  border-color: var(--accent);
  color: var(--accent);
  background: #ecfdf5;
}
.activity li.is-done, .workflow-step.is-done {
  border-color: #bbf7d0;
  color: var(--ok);
  background: #f0fdf4;
}
.workflow-status {
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  color: var(--ink);
  line-height: 1.45;
}
.workflow-status.is-waiting {
  border-color: #fde68a;
  background: #fffbeb;
}
.workflow-status.is-ready {
  border-color: #99f6e4;
  background: #f0fdfa;
}
.workflow-status.is-done {
  border-color: #bbf7d0;
  background: #f0fdf4;
}
.primary-write-action {
  width: auto;
  justify-self: start;
  margin-top: 0;
  padding: 9px 12px;
  border: 1px solid var(--accent);
  border-radius: 6px;
  background: var(--accent);
  color: var(--accent-ink);
  cursor: pointer;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.mode-switch {
  display: inline-grid;
  grid-template-columns: repeat(2, minmax(88px, auto));
  gap: 4px;
  padding: 3px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
}
.mode-switch .mode-button {
  width: auto;
  margin: 0;
  padding: 7px 10px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--muted);
  text-align: center;
}
.mode-switch .mode-button.is-active {
  background: var(--panel);
  color: var(--accent);
  box-shadow: var(--shadow);
}
.search-form {
  display: grid;
  grid-template-columns: minmax(120px, 1fr) 108px minmax(72px, auto);
  gap: 8px;
  min-width: 0;
}
.topbar button, .search-form button {
  width: auto;
  margin: 0;
  text-align: center;
  background: var(--accent);
  color: var(--accent-ink);
  border-color: var(--accent);
}
button.secondary {
  background: var(--panel);
  color: var(--ink);
  border-color: var(--line);
}
button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
button.is-disabled {
  opacity: 0.72;
  cursor: help;
  border-style: dashed;
  background: var(--surface);
  color: var(--muted);
}
button.is-running {
  position: relative;
  color: transparent !important;
}
button.is-running::after {
  content: attr(data-busy-label);
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: var(--accent-ink);
}
button.secondary.is-running::after,
.action-button.is-running::after {
  color: var(--accent);
}
input, select, textarea {
  padding: 9px 10px;
  border: 1px solid var(--line);
  border-radius: 6px;
  min-width: 0;
  background: var(--panel);
}
.input-wide {
  font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
  min-width: 28ch;
}
textarea {
  width: 100%;
  min-height: 96px;
  resize: vertical;
}
.workspace {
  min-width: 0;
  min-height: 0;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  overflow: hidden;
  background: #fbfcfd;
}
.content {
  padding: 18px;
  display: grid;
  gap: 16px;
  min-height: 0;
  overflow: auto;
}
.section-heading h1 { margin: 0 0 4px; font-size: 24px; }
.section-heading p { margin: 0; color: var(--muted); }
.basic-hero {
  display: grid;
  gap: 18px;
  align-content: start;
  max-width: 1080px;
}
.basic-hero .section-heading h1 {
  font-size: 32px;
}
.quick-actions {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}
.quick-action {
  display: grid;
  gap: 10px;
  align-content: start;
  min-height: 172px;
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel);
  box-shadow: var(--shadow);
}
.quick-action h2 {
  margin: 0;
  font-size: 18px;
}
.quick-action p {
  margin: 0;
  color: var(--muted);
  line-height: 1.5;
}
.quick-action button {
  width: auto;
  margin-top: auto;
  justify-self: start;
  padding: 9px 12px;
  border: 1px solid var(--accent);
  border-radius: 6px;
  background: var(--accent);
  color: var(--accent-ink);
  cursor: pointer;
}
.quick-action .toolbar {
  grid-template-columns: minmax(0, 1fr) auto;
}
.basic-search-results {
  display: grid;
  gap: 10px;
}
.result-card {
  display: grid;
  gap: 6px;
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel);
}
.result-card p {
  margin: 0;
  color: var(--muted);
  line-height: 1.45;
}
.toolbar, .form-grid, .button-row {
  display: grid;
  gap: 10px;
}
.toolbar { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.form-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.button-row { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.panel, details {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  box-shadow: var(--shadow);
  padding: 14px;
}
.panel h2, details h2 { margin: 0 0 10px; font-size: 17px; }
.panel h3 { margin: 14px 0 8px; font-size: 14px; }
.hint, .danger-note { color: var(--muted); font-size: 13px; line-height: 1.45; }
.danger-note { color: var(--danger); }
.summary-note {
  color: var(--muted);
  line-height: 1.55;
  margin: 0 0 10px;
}
.workflow {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.pill-row { display: flex; flex-wrap: wrap; gap: 6px; }
.pill {
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 3px 8px;
  background: var(--surface);
  font-size: 12px;
}
.table-wrap { overflow: auto; border: 1px solid var(--line); border-radius: 8px; background: var(--panel); }
table { width: 100%; border-collapse: collapse; min-width: 680px; }
th, td { padding: 9px 10px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
th { background: var(--surface); font-size: 12px; color: var(--muted); }
tr:last-child td { border-bottom: 0; }
.link-button {
  border: 0;
  background: transparent;
  color: var(--accent);
  padding: 0;
  margin: 0;
  cursor: pointer;
  text-align: left;
}
.json-panel {
  background: #111827;
  color: #e5e7eb;
  border-left: 1px solid #0b1220;
  padding: 14px;
  min-height: 0;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  overflow: hidden;
}
.panel-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
}
.panel-heading h2 { margin: 0; font-size: 16px; }
.json-panel button.secondary {
  color: #e5e7eb;
  background: #1f2937;
  border-color: #374151;
}
pre { white-space: pre-wrap; overflow-wrap: anywhere; font-size: 12px; line-height: 1.45; }
.json-panel pre {
  min-height: 0;
  margin: 0;
  overflow: auto;
}
@media (max-width: 900px) {
  body {
    height: auto;
    min-height: 100vh;
    grid-template-columns: 1fr;
    overflow: auto;
  }
  .nav {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    border: 0;
    border-bottom: 1px solid var(--line);
  }
  .brand { grid-column: 1 / -1; margin-bottom: 0; }
  .nav-button { margin-top: 0; }
  .workspace {
    display: block;
    min-height: auto;
    overflow: visible;
  }
  .content { overflow: visible; }
  .topbar, .search-form, .toolbar, .form-grid, .button-row { grid-template-columns: 1fr; }
  .mode-switch, .quick-actions { grid-template-columns: 1fr; }
  body.mode-basic { grid-template-columns: 1fr; }
  .json-panel {
    display: block;
    border-left: 0;
    min-height: 280px;
    overflow: visible;
  }
  .json-panel pre { max-height: 60vh; }
  table { min-width: 560px; }
}
"""


APP_JS = """
const UI_MODE_KEY = "threadvault.uiMode";

const state = {
  activeView: "home",
  uiMode: "basic",
  health: null,
  overview: null,
  selectedSession: null,
  exportControls: {
    session: "",
    profile: "markdown",
    privacyMode: "warn",
  },
  exportPreview: null,
  exportResult: null,
  activeTask: null,
};

const uiText = {
  requestFailed: "Request failed",
  requiresConfirm: "requires confirm=true.",
  applyRequiresConfirm: "apply requires confirm=true.",
  confirmPromptSuffix: " requires confirmation. Continue?",
  statusConnector: " on ",
  statusOk: "ok",
  bootError: "error",
  exportPreviewMissing: "Generate a matching preview before writing files.",
  exportPreviewReady: "Preview ready",
  exportPreviewStale: "Export preview reset after input change.",
  exportWritten: "Export written",
  exportStepChoose: "1. Choose session and format",
  exportStepPreview: "2. Generate preview",
  exportStepWrite: "3. Write files",
  exportNeedsPreview: "Next step: generate a preview. Write buttons explain why they are locked if clicked.",
  exportReadyToWrite: "Next step: review the preview, then click the enabled write button.",
  exportComplete: "Export complete. The output path is shown below.",
  exportLocked: "Locked until the preview matches this write action.",
  actionCancelled: "Action cancelled.",
  noRecentSession: "No imported sessions are available yet.",
  basicSkillPrompt: "Open or search a session first, then generate a Codex Skill export preview.",
  working: "Working",
  done: "Done",
  failed: "Failed",
  busyLabel: "Running...",
  openingViewPrefix: "Opening",
  switchingModePrefix: "Switching to",
  privacyModes: {
    warn: "Warn only",
    redact: "Redact automatically",
    fail: "Block on high risk",
  },
};

const actionLabels = {
  reindex: "Reindex",
  vacuum: "Vacuum",
  restore_apply: "Restore apply",
  schema_write: "Schema write",
  schemas_write: "Schemas write",
  backup_history_prune: "Backup history prune",
  restore_history_prune: "Restore history prune",
  audit_history_prune: "Audit history prune",
};

const roleLabels = {
  assistant: "助手",
  developer: "开发者",
  system: "系统",
  tool: "工具",
  user: "用户",
};

const actionProgress = {
  client_export_preview: {
    title: "Generating export preview",
    steps: ["Read session", "Scan privacy", "Plan files"],
  },
  export_session: {
    title: "Writing session export",
    steps: ["Check preview", "Write file", "Report path"],
  },
  export_target_markdown: {
    title: "Writing Markdown export",
    steps: ["Check preview", "Write files", "Report path"],
  },
  export_target_obsidian: {
    title: "Writing Obsidian export",
    steps: ["Check preview", "Write vault", "Report path"],
  },
  export_target_skill: {
    title: "Writing Skill export",
    steps: ["Check preview", "Write skill files", "Report path"],
  },
};

const views = {
  archive: {
    title: "Archive",
    summary: "Browse local Codex sessions, filter by project/cwd, and open session detail.",
  },
  search: {
    title: "Search",
    summary: "Run standard search, retrieval query, hybrid retrieval, and agent retrieve flows.",
  },
  session: {
    title: "Session",
    summary: "Inspect summary, event previews, evidence event ids, warnings, and export entrypoints.",
  },
  export: {
    title: "Export",
    summary: "Preview export targets before write actions are enabled in the action registry.",
  },
  privacy: {
    title: "Privacy",
    summary: "Inspect privacy scan and parser warning surfaces without bypassing existing rules.",
  },
  maintenance: {
    title: "Maintenance",
    summary: "Review stats, doctor, self-test, reindex, and vacuum controls.",
  },
  backup: {
    title: "Backup / Restore",
    summary: "Prepare backup, verify, history, restore plan, and restore controls.",
  },
  config: {
    title: "Config",
    summary: "Expose config init, show, and doctor workflows for Phase 04 action wiring.",
  },
  schemas: {
    title: "Schemas",
    summary: "List, show, validate, and write JSON schema contracts.",
  },
  governance: {
    title: "Governance",
    summary: "Show personal defaults and advanced v3 governance diagnostics.",
  },
};

function byId(id) {
  return document.getElementById(id);
}

function getStoredMode() {
  const stored = window.localStorage.getItem(UI_MODE_KEY);
  return stored === "pro" ? "pro" : "basic";
}

function setStoredMode(mode) {
  window.localStorage.setItem(UI_MODE_KEY, mode === "pro" ? "pro" : "basic");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setJson(payload) {
  byId("json").textContent = JSON.stringify(payload, null, 2);
}

function setStatus(label, ok) {
  byId("status").textContent = label;
  byId("status-dot").className = ok === false ? "status-dot fail" : "status-dot ok";
}

function pathLabel(label, value) {
  return value ? `${label}: ${value}` : "";
}

function setActivity(title, steps, activeIndex, done) {
  const node = byId("activity");
  const titleNode = byId("activity-title");
  const stepsNode = byId("activity-steps");
  if (!node || !titleNode || !stepsNode) return;
  if (!title) {
    node.hidden = true;
    node.classList.remove("is-running", "is-done", "is-failed");
    titleNode.textContent = uiText.working;
    stepsNode.innerHTML = "";
    return;
  }
  node.hidden = false;
  const failed = String(title).startsWith(`${uiText.failed}:`);
  node.classList.toggle("is-done", Boolean(done));
  node.classList.toggle("is-failed", failed);
  node.classList.toggle("is-running", !done && !failed);
  titleNode.textContent = title;
  stepsNode.innerHTML = (steps || []).map((step, index) => {
    const cls = done || index < activeIndex ? "is-done" : index === activeIndex ? "is-active" : "";
    return `<li class="${cls}">${escapeHtml(step)}</li>`;
  }).join("");
}

function setButtonBusy(button, busy) {
  if (!button) return;
  if (busy) {
    button.dataset.wasDisabled = button.disabled ? "true" : "false";
    button.dataset.busyLabel = uiText.busyLabel;
    button.disabled = true;
    button.classList.add("is-running");
    button.setAttribute("aria-busy", "true");
    return;
  }
  button.classList.remove("is-running");
  button.removeAttribute("aria-busy");
  if (button.dataset.wasDisabled !== "true") button.disabled = false;
  delete button.dataset.wasDisabled;
  delete button.dataset.busyLabel;
}

async function runWithFeedback(task, work) {
  const steps = task.steps || [task.title || uiText.working];
  const title = task.title || uiText.working;
  const startedAt = Date.now();
  state.activeTask = task;
  setStatus(title, true);
  setActivity(title, steps, 0, false);
  setButtonBusy(task.button, true);
  try {
    const result = await work();
    setActivity(uiText.done, steps, steps.length, true);
    setStatus(task.success || uiText.done, true);
    return result;
  } catch (error) {
    setActivity(`${uiText.failed}: ${error.message}`, steps, 0, false);
    setStatus(error.message, false);
    throw error;
  } finally {
    const remaining = Math.max(0, 280 - (Date.now() - startedAt));
    if (remaining) await new Promise((resolve) => setTimeout(resolve, remaining));
    setButtonBusy(task.button, false);
    state.activeTask = null;
  }
}

function applyMode(mode) {
  state.uiMode = mode === "pro" ? "pro" : "basic";
  document.body.classList.toggle("mode-basic", state.uiMode === "basic");
  document.body.classList.toggle("mode-pro", state.uiMode === "pro");
  document.querySelectorAll(".mode-button").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.uiMode === state.uiMode);
  });
}

function actionLabel(action) {
  return actionLabels[action] || action;
}

function roleLabel(role) {
  return roleLabels[role] || role;
}

function formatTimestamp(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const pad = (part) => String(part).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function eventPreview(event) {
  return event.text_preview || event.text || event.preview || event.content || "";
}

function cleanSummary(summary) {
  const raw = summary.title || summary.topic || "";
  if (!raw) return "No summary loaded.";
  const compact = String(raw).trim();
  if (compact.startsWith("<environment_context>") || compact.includes("<cwd>") || compact.includes("<shell>")) {
    return [
      "This summary starts with raw environment context, so the main UI folded it into a short note.",
      "Inspect the JSON panel for the original text.",
    ].join(" ");
  }
  return compact;
}

function statusLabel(status) {
  return status === "ok" ? uiText.statusOk : status;
}

function apiErrorMessage(payload) {
  const action = payload.action || "";
  if (payload.status === "confirm_required" && action) {
    if (payload.message === `${action} requires confirm=true.`) {
      return `${actionLabel(action)} ${uiText.requiresConfirm}`;
    }
    if (payload.message === `${action} apply requires confirm=true.`) {
      return `${actionLabel(action)} ${uiText.applyRequiresConfirm}`;
    }
  }
  return payload.message || payload.error || uiText.requestFailed;
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  const payload = await response.json();
  setJson(payload);
  if (!response.ok || payload.ok === false) {
    throw new Error(apiErrorMessage(payload));
  }
  return payload;
}

async function postAction(action, params, confirm) {
  return fetchJson("/api/action", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, params: params || {}, confirm: Boolean(confirm) }),
  });
}

function heading(viewName) {
  const view = views[viewName];
  return `
    <div class="section-heading">
      <h1>${view.title}</h1>
      <p>${view.summary}</p>
    </div>
  `;
}

function placeholderButton(label, action, dangerText, disabled) {
  const disabledAttr = disabled ? ` aria-disabled="true" disabled data-disabled-reason="${escapeHtml(dangerText)}"` : "";
  const disabledClass = disabled ? " is-disabled" : "";
  return `
    <button class="action-button${disabledClass}" type="button" data-action="${action}"${disabledAttr}>
      ${label}
    </button>
    <p class="hint">${dangerText}</p>
  `;
}

function valueOf(id) {
  const node = byId(id);
  return node ? node.value : "";
}

function selectedExportControls() {
  return {
    session: valueOf("export-session") || state.exportControls.session || state.selectedSession || "",
    profile: valueOf("export-profile") || state.exportControls.profile || "markdown",
    privacyMode: valueOf("privacy-mode") || state.exportControls.privacyMode || "warn",
  };
}

function syncExportControls() {
  state.exportControls = selectedExportControls();
  return state.exportControls;
}

function exportActionForProfile(profile) {
  if (profile === "obsidian") return "export_target_obsidian";
  if (profile === "skill") return "export_target_skill";
  if (profile === "session") return "export_session";
  return "export_target_markdown";
}

function previewProfileForExport(profile) {
  return profile === "session" ? "markdown" : profile;
}

function exportPreviewKey(action, controls) {
  return JSON.stringify({
    action,
    session: controls.session || "",
    profile: controls.profile || "markdown",
    privacyMode: controls.privacyMode || "warn",
  });
}

function currentExportPreviewKey(action) {
  return exportPreviewKey(action, selectedExportControls());
}

function hasMatchingExportPreview(action) {
  return Boolean(state.exportPreview && state.exportPreview.key === currentExportPreviewKey(action));
}

function exportPrivacySummary(result) {
  const privacy = result && result.privacy ? result.privacy : {};
  const effective = privacy.effective_findings_count ?? privacy.findings_count ?? 0;
  const highRisk = privacy.high_risk_findings_count ?? privacy.high_count ?? 0;
  return { effective, highRisk, blocked: Boolean(privacy.blocked) };
}

function exportOutputPaths(result) {
  if (!result) return [];
  if (Array.isArray(result)) {
    return result
      .map((item) => (typeof item === "string" ? item : item && item.path ? item.path : null))
      .filter(Boolean);
  }
  if (Array.isArray(result.files)) return result.files.map((item) => item.path || item).filter(Boolean);
  if (Array.isArray(result.planned_files)) return result.planned_files.map((item) => item.path || item).filter(Boolean);
  if (result.path) return [result.path];
  if (result.target_path) return [result.target_path];
  if (result.root) return [result.root];
  return [];
}

function exportModeLabel(profile) {
  if (profile === "session") return "Session export";
  if (profile === "obsidian") return "Obsidian";
  if (profile === "skill") return "Skill";
  return "Markdown";
}

function exportWriteLabel(profile) {
  if (profile === "session") return "Export session";
  if (profile === "obsidian") return "Export obsidian";
  if (profile === "skill") return "Export skill";
  return "Export markdown";
}

function renderExportSummary() {
  const preview = state.exportPreview;
  const result = state.exportResult;
  if (!preview && !result) {
    return `<p class="summary-note">${uiText.exportPreviewMissing}</p>`;
  }
  const latest = result || preview;
  const privacy = exportPrivacySummary(latest.payload?.result || latest.payload || {});
  const paths = exportOutputPaths(latest.payload?.result || latest.payload || {});
  const status = result ? uiText.exportWritten : uiText.exportPreviewReady;
  return `
    <p class="summary-note">
      ${status}: ${exportModeLabel(latest.controls.profile)} ·
      ${uiText.privacyModes[latest.controls.privacyMode] || latest.controls.privacyMode}
    </p>
    <div class="pill-row">
      <span class="pill">Session ${escapeHtml(latest.controls.session || "-")}</span>
      <span class="pill">Privacy findings ${escapeHtml(privacy.effective)}</span>
      <span class="pill">High risk ${escapeHtml(privacy.highRisk)}</span>
      <span class="pill">${privacy.blocked ? "Blocked" : "Allowed"}</span>
    </div>
    <p class="hint">${paths.length ? escapeHtml(paths.join(", ")) : "No output path reported in this response."}</p>
  `;
}

function renderExportWorkflow() {
  const hasPreview = Boolean(state.exportPreview);
  const hasResult = Boolean(state.exportResult);
  return `
    <div class="workflow" aria-label="Export workflow">
      <span class="workflow-step is-done">${uiText.exportStepChoose}</span>
      <span class="workflow-step ${hasPreview || hasResult ? "is-done" : "is-active"}">${uiText.exportStepPreview}</span>
      <span class="workflow-step ${hasResult ? "is-done" : hasPreview ? "is-active" : ""}">${uiText.exportStepWrite}</span>
    </div>
  `;
}

function renderExportStage() {
  const currentAction = exportActionForProfile((state.exportControls || {}).profile || "markdown");
  const readyToWrite = hasMatchingExportPreview(currentAction);
  const message = state.exportResult
    ? uiText.exportComplete
    : readyToWrite
      ? uiText.exportReadyToWrite
      : uiText.exportNeedsPreview;
  const cls = state.exportResult ? "is-done" : readyToWrite ? "is-ready" : "is-waiting";
  return `<div class="workflow-status ${cls}" role="status">${message}</div>`;
}

function renderExportPrimaryAction() {
  if (state.exportResult) return "";
  const controls = state.exportControls || {};
  const profile = controls.profile || "markdown";
  const currentAction = exportActionForProfile(profile);
  if (!hasMatchingExportPreview(currentAction)) return "";
  return `
    <button class="primary-write-action" type="button" data-action="${currentAction}">
      ${exportWriteLabel(profile)}
    </button>
  `;
}

function paramsForAction(action) {
  const exportControls = selectedExportControls();
  const session = exportControls.session || state.selectedSession || "";
  const profile = exportControls.profile || "markdown";
  const privacyMode = exportControls.privacyMode || "warn";
  const schemaJson = valueOf("schema-json");
  const base = { session, privacy_mode: privacyMode };
  const out = state.health?.paths?.default_export_dir || "threadvault-ui-output";
  const commonQuery = byId("query") ? byId("query").value || "pytest" : "pytest";
  const simple = {
    stats: {},
    doctor: {},
    self_test: {},
    reindex: {},
    vacuum: {},
    backup: { out: "threadvault-ui-backups" },
    backup_history: { dir: "threadvault-ui-backups" },
    restore_history: {},
    config_show: {},
    config_doctor: {},
    schemas_list: {},
    governance_status: {},
    governance_v3_gap_audit: {},
    governance_v3_acceptance_smoke: { query: commonQuery, session: session || "sess-current" },
    governance_preflight: {
      kind: "summary_search",
      command: "threadvault retrieval query",
      role: "reader",
      target_type: "query",
      target_id: commonQuery,
    },
    governance_instrumentation: { command: "threadvault retrieval query", role: "reader", target_type: "query", target_id: commonQuery },
    vector_status: {},
    warnings_summary: {},
    capabilities: {},
    robot_docs_guide: {},
    robot_docs_schemas: {},
  };
  if (action in simple) return simple[action];
  if (action === "privacy_scan" || action === "client_warnings" || action === "summarize" || action === "summary_chunks") {
    return { session };
  }
  if (action === "validate_json") {
    return { schema: "personal_ui_action", payload: schemaJson || "{}" };
  }
  if (action === "schema_write" || action === "schemas_write") {
    return { out: "docs/schemas" };
  }
  if (action === "export_session") {
    const params = { ...base, out, format: "md", profile: "full" };
    if (hasMatchingExportPreview(action)) params.preview_accepted = true;
    return params;
  }
  if (action === "export_target_markdown" || action === "export_target_obsidian" || action === "export_target_skill") {
    const targetProfile = action.replace("export_target_", "");
    const params = { ...base, out, profile: targetProfile };
    if (hasMatchingExportPreview(action)) params.preview_accepted = true;
    return params;
  }
  return {};
}

function requiresConfirm(action) {
  return ["restore_apply", "vacuum", "reindex", "schema_write", "schemas_write"].includes(action);
}

function renderSessionTable(sessions) {
  if (!sessions || sessions.length === 0) {
    return `<div class="panel"><p class="hint">No sessions match the current filters.</p></div>`;
  }
  const rows = sessions.map((session) => `
    <tr>
      <td>
        <button class="link-button" type="button" data-open-session="${escapeHtml(session.session_id)}">
          ${escapeHtml(session.session_id)}
        </button>
      </td>
      <td>${escapeHtml(session.cwd || session.project || "")}</td>
      <td>${escapeHtml(session.updated_at || session.created_at || "")}</td>
      <td>${escapeHtml(session.event_count)}</td>
      <td>${escapeHtml(session.warning_count || 0)}</td>
    </tr>
  `).join("");
  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Session</th>
            <th>Project / CWD</th>
            <th>Updated</th>
            <th>Events</th>
            <th>Warnings</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

function recentSession() {
  const sessions = state.overview && Array.isArray(state.overview.sessions) ? state.overview.sessions : [];
  return sessions.length ? sessions[0] : null;
}

async function loadOverview(extraQuery) {
  const suffix = extraQuery ? "?" + extraQuery : "?limit=20";
  const payload = await fetchJson("/api/client/overview" + suffix);
  state.overview = payload;
  return payload;
}

async function renderArchive() {
  const overview = state.overview || await loadOverview();
  const sessions = overview.sessions || [];
  byId("content").innerHTML = `
    ${heading("archive")}
    <div class="panel">
      <h2>Archive Filters</h2>
      <form id="archive-filter" class="toolbar">
        <input name="query" placeholder="Query">
        <input name="cwd" placeholder="Project or cwd">
        <input name="limit" type="number" min="1" max="200" value="20">
        <button type="submit">Apply</button>
      </form>
    </div>
    ${renderSessionTable(sessions)}
  `;
}

function renderBasicSearchResults(payload) {
  const results = payload && payload.results ? payload.results : [];
  if (!results.length) {
    return `<div class="panel"><p class="hint">No matching old records yet.</p></div>`;
  }
  return `
    <div class="basic-search-results">
      ${results.map((result) => `
        <article class="result-card">
          <button class="link-button" type="button" data-open-session="${escapeHtml(result.session_id || "")}">
            ${escapeHtml(result.session_id || "Unknown session")}
          </button>
          <p>${escapeHtml(result.snippet || result.text || result.summary || "")}</p>
        </article>
      `).join("")}
    </div>
  `;
}

function renderHome(payload) {
  const latest = recentSession();
  const latestLabel = latest ? latest.updated_at || latest.created_at || latest.session_id : uiText.noRecentSession;
  byId("content").innerHTML = `
    <div class="basic-hero">
      <div class="section-heading">
        <h1>Start with what you need</h1>
        <p>ThreadVault keeps the advanced controls available, but Basic Mode focuses on the three daily moves.</p>
      </div>
      <div class="quick-actions">
        <section class="quick-action">
          <h2>Search old records</h2>
          <p>Find previous Codex work by keyword, error text, project name, or decision.</p>
          <form id="basic-search" class="toolbar">
            <input name="q" placeholder="Search old records" value="${escapeHtml(byId("query").value || "")}">
            <button type="submit">Search</button>
          </form>
        </section>
        <section class="quick-action">
          <h2>Open latest session</h2>
          <p>${escapeHtml(latestLabel)}</p>
          <button id="open-latest-session" type="button"${latest ? "" : " disabled"}>Open latest</button>
        </section>
        <section class="quick-action">
          <h2>Export for Codex reuse</h2>
          <p>Generate a Codex Skill preview from the current or latest session, then write it after review.</p>
          <button id="basic-skill-preview" type="button"${latest || state.selectedSession ? "" : " disabled"}>Prepare Skill export</button>
        </section>
      </div>
      ${payload ? renderBasicSearchResults(payload) : ""}
    </div>
  `;
}

function renderSearch(payload) {
  const results = payload && payload.results ? payload.results : [];
  const rows = results.map((result) => `
    <tr>
      <td>${escapeHtml(result.session_id || "")}</td>
      <td>${escapeHtml(result.source || result.mode || "")}</td>
      <td>${escapeHtml(result.score || "")}</td>
      <td>${escapeHtml((result.evidence_event_ids || []).join(", "))}</td>
      <td>${escapeHtml(result.snippet || result.text || result.summary || "")}</td>
    </tr>
  `).join("");
  byId("content").innerHTML = `
    ${heading("search")}
    <div class="panel">
      <h2>Retrieval Controls</h2>
      <div class="pill-row">
        <span class="pill">Standard search</span>
        <span class="pill">Retrieval query</span>
        <span class="pill">Hybrid retrieval</span>
        <span class="pill">Agent retrieve</span>
      </div>
      <form id="view-search" class="toolbar">
        <input name="q" placeholder="Search query" value="${escapeHtml(byId("query").value || "pytest")}">
        <select name="mode">
          <option value="fts">Retrieval query</option>
          <option value="hybrid" selected>Hybrid retrieval</option>
          <option value="agent">Agent retrieve</option>
        </select>
        <input name="limit" type="number" min="1" max="100" value="20">
        <button type="submit">Run</button>
      </form>
      <p class="hint">Standard archive search remains available through existing CLI; this web route uses agent retrieval.</p>
      <div class="button-row">
        ${placeholderButton("Summary chunks", "summary_chunks", "Select stable summary/evidence chunks for a session or project.")}
        ${placeholderButton("Vector status", "vector_status", "Read-only vector index and config status.")}
        ${placeholderButton("Vector query", "vector_query", "Query the local vector adapter when configured.")}
      </div>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Session</th>
            <th>Source</th>
            <th>Score</th>
            <th>Evidence Event IDs</th>
            <th>Preview</th>
          </tr>
        </thead>
        <tbody>${rows || `<tr><td colspan="5">Run a query to populate results.</td></tr>`}</tbody>
      </table>
    </div>
  `;
}

async function openSession(sessionId) {
  state.selectedSession = sessionId;
  const payload = await fetchJson(`/api/client/session?session=${encodeURIComponent(sessionId)}&event_limit=12`);
  renderSession(payload);
}

function renderSession(payload) {
  const session = payload ? payload.session || {} : {};
  const summary = payload ? payload.summary || {} : {};
  const events = payload ? payload.events || [] : [];
  const evidenceIds = summary.evidence_event_ids || payload?.evidence_event_ids || [];
  const summaryText = cleanSummary(summary);
  const eventRows = events.map((event) => `
    <tr>
      <td>${escapeHtml(event.event_id || event.id || "")}</td>
      <td>${escapeHtml(roleLabel(event.role || event.type || ""))}</td>
      <td>${escapeHtml(formatTimestamp(event.created_at || event.timestamp || ""))}</td>
      <td>${escapeHtml(eventPreview(event))}</td>
    </tr>
  `).join("");
  byId("content").innerHTML = `
    ${heading("session")}
    <div class="panel">
      <h2>Session Lookup</h2>
      <form id="session-lookup" class="toolbar">
        <input
          class="input-wide"
          name="session"
          placeholder="Session ID"
          value="${escapeHtml(session.session_id || state.selectedSession || "")}"
        >
        <button type="submit">Open Session</button>
        <button type="button" id="load-warnings" class="secondary">Warnings</button>
        <button type="button" id="session-export-preview" class="secondary">Export Preview</button>
      </form>
    </div>
    <div class="panel">
      <h2>Summary</h2>
      <p class="summary-note">${escapeHtml(summaryText)}</p>
      <div class="pill-row">${evidenceIds.map((id) => `<span class="pill">${escapeHtml(id)}</span>`).join("")}</div>
    </div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Event ID</th><th>Type</th><th>Created</th><th>Preview</th></tr></thead>
        <tbody>${eventRows || `<tr><td colspan="4">Open a session to view events.</td></tr>`}</tbody>
      </table>
    </div>
  `;
}

function renderExport() {
  const controls = state.exportControls || {};
  const session = controls.session || state.selectedSession || "";
  const profile = controls.profile || "markdown";
  const privacyMode = controls.privacyMode || "warn";
  const writeActions = {
    export_session: hasMatchingExportPreview("export_session"),
    export_target_markdown: hasMatchingExportPreview("export_target_markdown"),
    export_target_obsidian: hasMatchingExportPreview("export_target_obsidian"),
    export_target_skill: hasMatchingExportPreview("export_target_skill"),
  };
  byId("content").innerHTML = `
    ${heading("export")}
    <div class="panel">
      <h2>Export Preview</h2>
      ${renderExportWorkflow()}
      ${renderExportStage()}
      <div class="form-grid">
        <input class="input-wide" id="export-session" placeholder="Session ID" value="${escapeHtml(session)}">
        <select id="export-profile">
          <option value="markdown"${profile === "markdown" ? " selected" : ""}>Markdown</option>
          <option value="obsidian"${profile === "obsidian" ? " selected" : ""}>Obsidian</option>
          <option value="skill"${profile === "skill" ? " selected" : ""}>Skill</option>
          <option value="session"${profile === "session" ? " selected" : ""}>Session export</option>
        </select>
        <select id="privacy-mode">
          <option value="warn"${privacyMode === "warn" ? " selected" : ""}>Privacy warn</option>
          <option value="redact"${privacyMode === "redact" ? " selected" : ""}>Privacy redact</option>
          <option value="fail"${privacyMode === "fail" ? " selected" : ""}>Privacy fail</option>
        </select>
        <button id="preview-export" type="button">Generate Preview</button>
      </div>
      <div id="export-summary">${renderExportSummary()}</div>
      ${renderExportPrimaryAction()}
      <p class="hint">Changing session, profile, or privacy mode invalidates the current preview.</p>
    </div>
    <div class="panel">
      <h2>Write Actions</h2>
      ${placeholderButton(
        "Export session",
        "export_session",
        writeActions.export_session ? uiText.exportReadyToWrite : "Preview must match the session export selection before writing.",
        !writeActions.export_session,
      )}
      ${placeholderButton(
        "Export markdown",
        "export_target_markdown",
        writeActions.export_target_markdown ? uiText.exportReadyToWrite : "Preview must match Markdown before writing files.",
        !writeActions.export_target_markdown,
      )}
      ${placeholderButton(
        "Export obsidian",
        "export_target_obsidian",
        writeActions.export_target_obsidian ? uiText.exportReadyToWrite : "Preview must match Obsidian before writing files.",
        !writeActions.export_target_obsidian,
      )}
      ${placeholderButton(
        "Export skill",
        "export_target_skill",
        writeActions.export_target_skill ? uiText.exportReadyToWrite : "Preview must match Skill before writing files.",
        !writeActions.export_target_skill,
      )}
    </div>
  `;
}

function renderPrivacy() {
  byId("content").innerHTML = `
    ${heading("privacy")}
    <div class="panel">
      <h2>Privacy Scan</h2>
      <form id="privacy-form" class="toolbar">
        <input name="session" placeholder="Session ID" value="${escapeHtml(state.selectedSession || "")}">
        <button type="submit">Load Warnings</button>
        <button class="secondary" type="button" data-action="privacy_scan">Privacy Scan</button>
        <button class="secondary" type="button" data-action="warnings">Warnings</button>
        <button class="secondary" type="button" data-action="warnings_summary">Warnings Summary</button>
      </form>
      <p class="hint">Privacy scan and allowlist behavior reuse existing ThreadVault privacy rules.</p>
    </div>
  `;
}

function renderMaintenance() {
  byId("content").innerHTML = `
    ${heading("maintenance")}
    <div class="button-row">
      ${placeholderButton("Stats", "stats", "Read-only database statistics.")}
      ${placeholderButton("Doctor", "doctor", "Read-only health diagnostics.")}
      ${placeholderButton("Self-test", "self_test", "Read-only local self-test.")}
      ${placeholderButton("Reindex", "reindex", "Requires confirm=true before Phase 04 execution.")}
      ${placeholderButton("Vacuum", "vacuum", "Requires confirm=true before Phase 04 execution.")}
    </div>
  `;
}

function renderBackup() {
  byId("content").innerHTML = `
    ${heading("backup")}
    <div class="button-row">
      ${placeholderButton("Backup", "backup", "Backup may execute directly but must display its target path.")}
      ${placeholderButton("Backup verify", "backup_verify", "Read-only backup verification.")}
      ${placeholderButton("Backup history", "backup_history", "Read-only history list.")}
      ${placeholderButton("Restore plan", "restore_plan", "Restore must start with a plan.")}
      ${placeholderButton("Restore apply", "restore_apply", "Requires confirm=true and a restore plan.")}
      ${placeholderButton("Restore history", "restore_history", "Read-only restore history.")}
      ${placeholderButton("Backup history prune", "backup_history_prune", "Dry-run by default; apply requires confirmation.")}
      ${placeholderButton("Restore history prune", "restore_history_prune", "Dry-run by default; apply requires confirmation.")}
    </div>
  `;
}

function renderConfig() {
  byId("content").innerHTML = `
    ${heading("config")}
    <div class="button-row">
      ${placeholderButton("Config init", "config_init", "Writes local config only after Phase 04 action wiring.")}
      ${placeholderButton("Config show", "config_show", "Read-only config inspection.")}
      ${placeholderButton("Config doctor", "config_doctor", "Read-only config diagnostics.")}
    </div>
  `;
}

function renderSchemas() {
  byId("content").innerHTML = `
    ${heading("schemas")}
    <div class="button-row">
      ${placeholderButton("Schemas list", "schemas_list", "Read-only schema registry listing.")}
      ${placeholderButton("Schemas show", "schemas_show", "Read-only schema detail.")}
      ${placeholderButton("Validate JSON", "validate_json", "Validates pasted JSON against a selected schema.")}
      ${placeholderButton("Schema write", "schema_write", "Requires confirm=true before writing artifacts.")}
      ${placeholderButton("Capabilities", "capabilities", "Read-only public capability discovery.")}
      ${placeholderButton("Robot docs guide", "robot_docs_guide", "Read-only agent usage guide.")}
      ${placeholderButton("Robot docs schemas", "robot_docs_schemas", "Read-only schema guide.")}
    </div>
    <textarea id="schema-json" placeholder="Paste JSON payload for validation"></textarea>
  `;
}

function renderGovernance() {
  byId("content").innerHTML = `
    ${heading("governance")}
    <div class="panel">
      <h2>Personal Defaults</h2>
      <div class="pill-row">
        <span class="pill">local-first</span>
        <span class="pill">privacy-first</span>
        <span class="pill">no cloud sync</span>
        <span class="pill">no team enforcement by default</span>
      </div>
    </div>
    <details open>
      <summary>Advanced Diagnostics</summary>
      <div class="button-row">
        ${placeholderButton("Governance status", "governance_status", "Read-only personal governance status.")}
        ${placeholderButton("v3 gap audit", "governance_v3_gap_audit", "Read-only accepted v3 completion audit.")}
        ${placeholderButton("v3 acceptance smoke", "governance_v3_acceptance_smoke", "Read-only v3 acceptance smoke.")}
        ${placeholderButton("Governance preflight", "governance_preflight", "Read-only permission preflight diagnostics.")}
        ${placeholderButton("Instrumentation diagnostics", "governance_instrumentation", "Read-only instrumentation diagnostics.")}
        ${placeholderButton(
          "External model preflight",
          "governance_external_model_preflight",
          "Read-only diagnostic; external model calls remain disabled by default.",
        )}
      </div>
    </details>
  `;
}

async function renderActiveView(payload) {
  if (state.uiMode === "basic" && state.activeView === "home") return renderHome(payload);
  if (state.activeView === "archive") return renderArchive();
  if (state.activeView === "search") return renderSearch(payload);
  if (state.activeView === "session") return renderSession(payload);
  if (state.activeView === "export") return renderExport();
  if (state.activeView === "privacy") return renderPrivacy();
  if (state.activeView === "maintenance") return renderMaintenance();
  if (state.activeView === "backup") return renderBackup();
  if (state.activeView === "config") return renderConfig();
  if (state.activeView === "schemas") return renderSchemas();
  return renderGovernance();
}

async function runRetrieve(query, mode, limit) {
  const routeMode = mode === "agent" ? "hybrid" : mode;
  const payload = await fetchJson(
    `/api/retrieve?q=${encodeURIComponent(query)}&mode=${encodeURIComponent(routeMode)}&limit=${encodeURIComponent(limit || 20)}`,
  );
  if (state.uiMode === "basic") {
    state.activeView = "home";
    renderHome(payload);
  } else {
    state.activeView = "search";
    activateNav("search");
    renderSearch(payload);
  }
}

function activateNav(viewName) {
  state.activeView = viewName;
  document.querySelectorAll(".nav-button").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.view === viewName);
  });
}

async function switchMode(mode) {
  applyMode(mode);
  setStoredMode(state.uiMode);
  if (state.uiMode === "basic") {
    state.activeView = "home";
    await renderHome();
    return;
  }
  state.activeView = "archive";
  activateNav("archive");
  await renderArchive();
}

async function openLatestSession() {
  const latest = recentSession();
  if (!latest || !latest.session_id) {
    setStatus(uiText.noRecentSession, false);
    return;
  }
  state.activeView = "session";
  activateNav("session");
  await openSession(latest.session_id);
}

async function prepareBasicSkillExport() {
  const latest = recentSession();
  const session = state.selectedSession || (latest && latest.session_id) || "";
  if (!session) {
    setStatus(uiText.basicSkillPrompt, false);
    return;
  }
  state.selectedSession = session;
  state.exportControls = {
    session,
    profile: "skill",
    privacyMode: "warn",
  };
  state.exportPreview = null;
  state.exportResult = null;
  await generateExportPreview();
}

async function generateExportPreview() {
  const controls = syncExportControls();
  const action = exportActionForProfile(controls.profile);
  const payload = await postAction("client_export_preview", {
    session: controls.session,
    out: state.health?.paths?.default_export_dir || "threadvault-ui-output",
    profile: previewProfileForExport(controls.profile),
    privacy_mode: controls.privacyMode,
  }, false);
  state.exportPreview = {
    key: exportPreviewKey(action, controls),
    action,
    controls: { ...controls },
    payload,
  };
  state.exportResult = null;
  renderExport();
  setStatus(uiText.exportPreviewReady, true);
}

function progressForAction(action) {
  return actionProgress[action] || {
    title: actionLabel(action),
    steps: ["Send request", "Run action", "Show result"],
  };
}

function bindEvents() {
  applyMode(getStoredMode());

  document.querySelectorAll(".nav-button").forEach((button) => {
    button.addEventListener("click", async () => {
      activateNav(button.dataset.view);
      await runWithFeedback(
        {
          title: `${uiText.openingViewPrefix} ${button.textContent.trim()}`,
          steps: ["Switch view", "Load content"],
          button,
        },
        () => renderActiveView(),
      ).catch(() => {});
    });
  });

  document.querySelectorAll(".mode-button").forEach((button) => {
    button.addEventListener("click", async () => {
      await runWithFeedback(
        {
          title: `${uiText.switchingModePrefix} ${button.textContent.trim()}`,
          steps: ["Save mode", "Render view"],
          button,
        },
        () => switchMode(button.dataset.uiMode),
      ).catch(() => {});
    });
  });

  byId("global-search").addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = event.submitter instanceof HTMLButtonElement ? event.submitter : null;
    await runWithFeedback(
      { title: "Searching archive", steps: ["Send query", "Rank matches", "Render results"], button },
      () => runRetrieve(byId("query").value || "pytest", byId("search-mode").value, 20),
    ).catch(() => {});
  });

  byId("refresh").addEventListener("click", async () => {
    await runWithFeedback(
      { title: "Refreshing current view", steps: ["Clear cached overview", "Reload view"], button: byId("refresh") },
      async () => {
        state.overview = null;
        await renderActiveView();
      },
    ).catch(() => {});
  });

  byId("clear-json").addEventListener("click", () => setJson({}));

  byId("content").addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    const sessionId = target.dataset.openSession;
    if (sessionId) {
      await runWithFeedback(
        { title: "Opening session", steps: ["Load session", "Build summary", "Render events"], button: target },
        async () => {
          activateNav("session");
          await openSession(sessionId);
        },
      ).catch(() => {});
      return;
    }
    if (target.id === "load-warnings") {
      const input = target.closest("form")?.querySelector('input[name="session"]');
      const session = input instanceof HTMLInputElement ? input.value : state.selectedSession;
      if (session) {
        await runWithFeedback(
          { title: "Loading warnings", steps: ["Read session", "Collect warnings", "Show JSON"], button: target },
          () => fetchJson(`/api/client/warnings?session=${encodeURIComponent(session)}`),
        ).catch(() => {});
      }
      return;
    }
    if (target.id === "session-export-preview") {
      const input = target.closest("form")?.querySelector('input[name="session"]');
      const session = input instanceof HTMLInputElement ? input.value : state.selectedSession;
      state.exportControls = {
        session: session || "",
        profile: "session",
        privacyMode: "warn",
      };
      state.exportPreview = null;
      state.exportResult = null;
      activateNav("export");
      renderExport();
      return;
    }
    if (target.id === "preview-export") {
      await runWithFeedback(
        { ...progressForAction("client_export_preview"), button: target, success: uiText.exportPreviewReady },
        () => generateExportPreview(),
      ).catch(() => {});
      return;
    }
    if (target.id === "open-latest-session") {
      await runWithFeedback(
        { title: "Opening latest session", steps: ["Find latest", "Load session", "Render details"], button: target },
        () => openLatestSession(),
      ).catch(() => {});
      return;
    }
    if (target.id === "basic-skill-preview") {
      await runWithFeedback(
        { ...progressForAction("client_export_preview"), button: target, success: uiText.exportPreviewReady },
        () => prepareBasicSkillExport(),
      ).catch(() => {});
      return;
    }
    if (target.dataset.action) {
      if (target.getAttribute("aria-disabled") === "true") {
        const reason = target.dataset.disabledReason || uiText.exportLocked;
        setStatus(reason, false);
        setActivity(reason, [uiText.exportStepChoose, uiText.exportStepPreview, uiText.exportStepWrite], 1, false);
        return;
      }
      const action = target.dataset.action;
      const confirmAction = requiresConfirm(action) ? window.confirm(actionLabel(action) + uiText.confirmPromptSuffix) : false;
      if (requiresConfirm(action) && !confirmAction) {
        setStatus(uiText.actionCancelled, true);
        return;
      }
      const payload = await runWithFeedback(
        { ...progressForAction(action), button: target },
        () => postAction(action, paramsForAction(action), confirmAction),
      ).catch(() => null);
      if (payload && ["export_session", "export_target_markdown", "export_target_obsidian", "export_target_skill"].includes(action)) {
        state.exportResult = {
          action,
          controls: { ...selectedExportControls() },
          payload,
        };
        renderExport();
        setStatus(uiText.exportWritten, true);
      }
    }
  });

  byId("content").addEventListener("change", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLInputElement) && !(target instanceof HTMLSelectElement)) return;
    if (!["export-session", "export-profile", "privacy-mode"].includes(target.id)) return;
    syncExportControls();
    state.exportPreview = null;
    state.exportResult = null;
    renderExport();
    setStatus(uiText.exportPreviewStale, true);
  });

  byId("content").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.target;
    if (!(form instanceof HTMLFormElement)) return;
    const data = new FormData(form);
    if (form.id === "archive-filter") {
      await runWithFeedback(
        {
          title: "Applying archive filters",
          steps: ["Build filters", "Load matching sessions", "Render table"],
          button: event.submitter instanceof HTMLButtonElement ? event.submitter : null,
        },
        async () => {
          const params = new URLSearchParams();
          for (const [key, value] of data.entries()) {
            if (value) params.set(key, value);
          }
          const payload = await loadOverview(params.toString());
          state.overview = payload;
          await renderArchive();
        },
      ).catch(() => {});
    }
    if (form.id === "basic-search") {
      await runWithFeedback(
        {
          title: "Searching old records",
          steps: ["Send query", "Find matching sessions", "Show cards"],
          button: event.submitter instanceof HTMLButtonElement ? event.submitter : null,
        },
        () => runRetrieve(data.get("q") || byId("query").value || "pytest", "hybrid", 10),
      ).catch(() => {});
    }
    if (form.id === "view-search") {
      await runWithFeedback(
        {
          title: "Running retrieval",
          steps: ["Send query", "Rank evidence", "Render results"],
          button: event.submitter instanceof HTMLButtonElement ? event.submitter : null,
        },
        () => runRetrieve(data.get("q") || "pytest", data.get("mode") || "hybrid", data.get("limit") || 20),
      ).catch(() => {});
    }
    if (form.id === "session-lookup") {
      await runWithFeedback(
        {
          title: "Opening session",
          steps: ["Load session", "Build summary", "Render events"],
          button: event.submitter instanceof HTMLButtonElement ? event.submitter : null,
        },
        () => openSession(data.get("session")),
      ).catch(() => {});
    }
    if (form.id === "privacy-form") {
      const session = data.get("session");
      if (session) {
        await runWithFeedback(
          {
            title: "Loading privacy warnings",
            steps: ["Read session", "Collect findings", "Show JSON"],
            button: event.submitter instanceof HTMLButtonElement ? event.submitter : null,
          },
          () => fetchJson(`/api/client/warnings?session=${encodeURIComponent(session)}`),
        ).catch(() => {});
      }
    }
  });
}

async function boot() {
  bindEvents();
  startHeartbeat();
  const health = await fetchJson("/api/health");
  state.health = health;
  setStatus(`${statusLabel(health.status)}${uiText.statusConnector}${health.server.host}:${health.server.port}`, true);
  byId("db-path").textContent = pathLabel("Index DB", health.paths && health.paths.db_path);
  byId("export-path").textContent = pathLabel("Export folder", health.paths && health.paths.default_export_dir);
  const overview = await loadOverview();
  state.overview = overview;
  if (state.uiMode === "basic") {
    state.activeView = "home";
    await renderHome();
  } else {
    state.activeView = "archive";
    activateNav("archive");
    await renderArchive();
  }
}

boot().catch((error) => {
  setStatus(uiText.bootError, false);
  setJson({ ok: false, error: String(error) });
});

function startHeartbeat() {
  const ping = () => {
    fetch("/api/ui-heartbeat", {
      method: "POST",
      cache: "no-store",
      keepalive: true,
    }).catch(() => {});
  };
  ping();
  window.setInterval(ping, 2000);
}
"""


INDEX_HTML_ZH = (
    INDEX_HTML.replace('lang="en"', 'lang="zh-CN"')
    .replace("<title>ThreadVault Personal UI</title>", "<title>ThreadVault 个人界面</title>")
    .replace("<span>Personal Web UI</span>", "<span>个人 Web 控制台</span>")
    .replace('aria-label="Primary"', 'aria-label="主导航"')
    .replace('aria-label="Interface mode"', 'aria-label="界面模式"')
    .replace(">Basic Mode</button>", ">普通模式</button>")
    .replace(">Pro Mode</button>", ">专业模式</button>")
    .replace('>Archive</button>', '>归档</button>')
    .replace('>Search</button>', '>搜索</button>')
    .replace('>Session</button>', '>会话</button>')
    .replace('>Export</button>', '>导出</button>')
    .replace('>Privacy</button>', '>隐私</button>')
    .replace('>Maintenance</button>', '>维护</button>')
    .replace('>Backup / Restore</button>', '>备份 / 恢复</button>')
    .replace('>Config</button>', '>配置</button>')
    .replace('>Schemas</button>', '>结构定义</button>')
    .replace('>Governance</button>', '>治理</button>')
    .replace('placeholder="Search archive"', 'placeholder="搜索归档"')
    .replace('aria-label="Search mode"', 'aria-label="搜索模式"')
    .replace('>Hybrid</option>', '>混合</option>')
    .replace('>Retrieval</option>', '>检索</option>')
    .replace('>Agent</option>', '>Agent</option>')
    .replace('>Refresh</button>', '>刷新</button>')
    .replace("<h1>Archive</h1>", "<h1>归档</h1>")
    .replace("<p>Loading local archive overview.</p>", "<p>正在加载本地归档概览。</p>")
    .replace('aria-label="Raw JSON output"', 'aria-label="原始 JSON 输出"')
    .replace("<h2>JSON Output</h2>", "<h2>JSON 输出</h2>")
    .replace(">Clear</button>", ">清空</button>")
    .replace('/assets/app.js?v=20260702-paths', '/assets/app.zh.js?v=20260702-paths')
)


APP_JS_ZH = (
    APP_JS.replace('"Archive"', '"归档"')
    .replace('"Request failed"', '"请求失败"')
    .replace('"requires confirm=true."', '"需要确认参数。"')
    .replace('"apply requires confirm=true."', '"实际执行需要确认。"')
    .replace('" requires confirmation. Continue?"', '" 需要确认。继续？"')
    .replace('" on "', '" 于 "')
    .replace('"ok"', '"正常"')
    .replace('"error"', '"错误"')
    .replace('"Working"', '"正在执行"')
    .replace('"Done"', '"完成"')
    .replace('"Failed"', '"失败"')
    .replace('"Running..."', '"运行中..."')
    .replace('"Opening"', '"正在打开"')
    .replace('"Switching to"', '"正在切换到"')
    .replace("Index DB", "索引库")
    .replace("Export folder", "导出目录")
    .replace("Generating export preview", "正在生成导出预览")
    .replace("Writing session export", "正在写入会话导出")
    .replace("Writing Markdown export", "正在写入 Markdown 导出")
    .replace("Writing Obsidian export", "正在写入 Obsidian 导出")
    .replace("Writing Skill export", "正在写入技能包导出")
    .replace("Read session", "读取会话")
    .replace("Scan privacy", "扫描隐私")
    .replace("Plan files", "规划文件")
    .replace("Check preview", "检查预览")
    .replace("Write files", "写入文件")
    .replace("Write file", "写入文件")
    .replace("Write vault", "写入知识库")
    .replace("Write skill files", "写入技能包文件")
    .replace("Report path", "报告路径")
    .replace("Send request", "发送请求")
    .replace("Run action", "执行操作")
    .replace("Show result", "显示结果")
    .replace("Save mode", "保存模式")
    .replace("Render view", "渲染视图")
    .replace("Searching archive", "正在搜索归档")
    .replace("Searching old records", "正在搜索旧记录")
    .replace("Send query", "发送查询")
    .replace("Rank matches", "排序匹配")
    .replace("Find matching sessions", "查找匹配会话")
    .replace("Show cards", "显示卡片")
    .replace("Render results", "渲染结果")
    .replace("Refreshing current view", "正在刷新当前视图")
    .replace("Clear cached overview", "清空缓存概览")
    .replace("Reload view", "重新加载视图")
    .replace("Opening session", "正在打开会话")
    .replace("Opening latest session", "正在打开最近会话")
    .replace("Load session", "加载会话")
    .replace("Build summary", "生成摘要")
    .replace("Render events", "渲染事件")
    .replace("Loading warnings", "正在加载警告")
    .replace("Loading privacy warnings", "正在加载隐私警告")
    .replace("Collect warnings", "收集警告")
    .replace("Collect findings", "收集发现")
    .replace("Show JSON", "显示 JSON")
    .replace("Find latest", "查找最近会话")
    .replace("Render details", "渲染详情")
    .replace("Applying archive filters", "正在应用归档筛选")
    .replace("Build filters", "构建筛选条件")
    .replace("Load matching sessions", "加载匹配会话")
    .replace("Render table", "渲染表格")
    .replace("Running retrieval", "正在运行检索")
    .replace("Rank evidence", "排序证据")
    .replace("Switch view", "切换视图")
    .replace("Load content", "加载内容")
    .replace("1. Choose session and format", "1. 选择会话和格式")
    .replace("2. Generate preview", "2. 生成预览")
    .replace("3. Write files", "3. 写入文件")
    .replace(
        "Next step: generate a preview. Write buttons explain why they are locked if clicked.",
        "下一步：先生成预览。若写入按钮还被锁定，点击后会说明原因。",
    )
    .replace(
        "Next step: review the preview, then click the enabled write button.",
        "下一步：检查预览，然后点击已解锁的写入按钮。",
    )
    .replace("Export complete. The output path is shown below.", "导出完成。输出路径显示在下方。")
    .replace("Locked until the preview matches this write action.", "预览匹配该写入操作后才会解锁。")
    .replace('reindex: "Reindex"', 'reindex: "重建索引"')
    .replace('vacuum: "Vacuum"', 'vacuum: "数据库清理"')
    .replace('restore_apply: "Restore apply"', 'restore_apply: "执行恢复"')
    .replace('schema_write: "Schema write"', 'schema_write: "写入结构定义"')
    .replace('schemas_write: "Schemas write"', 'schemas_write: "写入结构定义"')
    .replace('backup_history_prune: "Backup history prune"', 'backup_history_prune: "清理备份历史"')
    .replace('restore_history_prune: "Restore history prune"', 'restore_history_prune: "清理恢复历史"')
    .replace('audit_history_prune: "Audit history prune"', 'audit_history_prune: "清理审计历史"')
    .replace(
        '"Browse local Codex sessions, filter by project/cwd, and open session detail."',
        '"浏览本地 Codex 会话，按项目或 cwd 筛选，并打开会话详情。"',
    )
    .replace('"Search"', '"搜索"')
    .replace(
        '"Run standard search, retrieval query, hybrid retrieval, and agent retrieve flows."',
        '"运行标准搜索、检索查询、混合检索和智能体检索流程。"',
    )
    .replace('"Session"', '"会话"')
    .replace(
        '"Inspect summary, event previews, evidence event ids, warnings, and export entrypoints."',
        '"查看摘要、事件预览、证据事件 ID、警告和导出入口。"',
    )
    .replace('"Export"', '"导出"')
    .replace(
        '"Preview export targets before write actions are enabled in the action registry."',
        '"在执行写入前预览导出目标。"',
    )
    .replace('"Privacy"', '"隐私"')
    .replace(
        '"Inspect privacy scan and parser warning surfaces without bypassing existing rules."',
        '"查看隐私扫描和解析警告，不绕过现有规则。"',
    )
    .replace('"Maintenance"', '"维护"')
    .replace(
        '"Review stats, doctor, self-test, reindex, and vacuum controls."',
        '"查看统计、诊断、自检、重建索引和数据库清理控制。"',
    )
    .replace('"Backup / Restore"', '"备份 / 恢复"')
    .replace(
        '"Prepare backup, verify, history, restore plan, and restore controls."',
        '"准备备份、验证、历史、恢复计划和恢复控制。"',
    )
    .replace('"Config"', '"配置"')
    .replace(
        '"Expose config init, show, and doctor workflows for Phase 04 action wiring."',
        '"提供配置初始化、查看和诊断工作流。"',
    )
    .replace('"Schemas"', '"结构定义"')
    .replace(
        '"List, show, validate, and write JSON schema contracts."',
        '"列出、查看、验证和写入 JSON 结构定义合同。"',
    )
    .replace('"Governance"', '"治理"')
    .replace(
        '"Show personal defaults and advanced v3 governance diagnostics."',
        '"显示个人默认值和高级 v3 治理诊断。"',
    )
    .replace("Starting...", "启动中...")
    .replace("Start with what you need", "从你要做的事开始")
    .replace(
        "ThreadVault keeps the advanced controls available, but Basic Mode focuses on the three daily moves.",
        "ThreadVault 保留专业控制台，但普通模式只聚焦三个日常动作。",
    )
    .replace("Search old records", "搜索旧记录")
    .replace(
        "Find previous Codex work by keyword, error text, project name, or decision.",
        "按关键词、报错、项目名或决策查找以前的 Codex 工作。",
    )
    .replace('placeholder="Search old records"', 'placeholder="搜索旧记录"')
    .replace(">Search</button>", ">搜索</button>")
    .replace("Open latest session", "打开最近会话")
    .replace("Open latest", "打开最近")
    .replace("Export for Codex reuse", "导出给 Codex 继续用")
    .replace(
        "Generate a Codex Skill preview from the current or latest session, then write it after review.",
        "从当前或最近会话生成 Codex 技能包预览，确认后再写入文件。",
    )
    .replace("Prepare Skill export", "准备技能包导出")
    .replace("No matching old records yet.", "暂时没有匹配的旧记录。")
    .replace("default database", "默认数据库")
    .replace("Archive Filters", "归档筛选")
    .replace('placeholder="Query"', 'placeholder="查询"')
    .replace('placeholder="Project or cwd"', 'placeholder="项目或 cwd"')
    .replace(">Apply</button>", ">应用</button>")
    .replace("No sessions match the current filters.", "没有会话匹配当前筛选条件。")
    .replace("<th>Session</th>", "<th>会话</th>")
    .replace("<th>Project / CWD</th>", "<th>项目 / CWD</th>")
    .replace("<th>Updated</th>", "<th>更新时间</th>")
    .replace("<th>Events</th>", "<th>事件</th>")
    .replace("<th>Warnings</th>", "<th>警告</th>")
    .replace("Retrieval Controls", "检索控制")
    .replace("Standard search", "标准搜索")
    .replace("Retrieval query", "检索查询")
    .replace("Hybrid retrieval", "混合检索")
    .replace("Agent retrieve", "智能体检索")
    .replace('placeholder="Search query"', 'placeholder="搜索查询"')
    .replace(">Run</button>", ">运行</button>")
    .replace(
        "Standard archive search remains available through existing CLI; this web route uses agent retrieval.",
        "标准归档搜索仍可通过命令行使用；当前 Web 路由使用智能体检索。",
    )
    .replace("Summary chunks", "摘要块")
    .replace("Vector status", "向量状态")
    .replace("Vector query", "向量查询")
    .replace("Select stable summary/evidence chunks for a session or project.", "为会话或项目选择稳定的摘要/证据块。")
    .replace("Read-only vector index and config status.", "只读查看向量索引和配置状态。")
    .replace("Query the local vector adapter when configured.", "在已配置时查询本地向量适配器。")
    .replace("<th>Source</th>", "<th>来源</th>")
    .replace("<th>Score</th>", "<th>分数</th>")
    .replace("<th>Evidence Event IDs</th>", "<th>证据事件 ID</th>")
    .replace("<th>Preview</th>", "<th>预览</th>")
    .replace("Run a query to populate results.", "运行查询后显示结果。")
    .replace("Session Lookup", "会话查询")
    .replace('placeholder="Session ID"', 'placeholder="会话 ID"')
    .replace(">Open Session</button>", ">打开会话</button>")
    .replace(">Export Preview</button>", ">导出预览</button>")
    .replace("Summary", "摘要")
    .replace("No summary loaded.", "尚未加载摘要。")
    .replace(
        "This summary starts with raw environment context, so the main UI folded it into a short note. "
        "Inspect the JSON panel for the original text.",
        "该摘要以原始环境上下文开头，主界面已折叠为简短说明；原文可在右侧 JSON 面板查看。",
    )
    .replace("Evidence Event IDs", "证据事件 ID")
    .replace("Event Preview", "事件预览")
    .replace("Event ID", "事件 ID")
    .replace("<th>Type</th>", "<th>类型</th>")
    .replace("<th>Created</th>", "<th>创建时间</th>")
    .replace("Open a session to view events.", "打开会话后查看事件。")
    .replace("Markdown", "Markdown")
    .replace("Obsidian", "Obsidian")
    .replace("Skill", "技能包")
    .replace("Session export", "会话导出")
    .replace("Privacy warn", "隐私警告")
    .replace("Privacy redact", "隐私脱敏")
    .replace("Privacy fail", "隐私失败")
    .replace("Preview Required", "需要预览")
    .replace("Generate Preview", "生成预览")
    .replace("Generate a matching preview before writing files.", "写入文件前请先生成匹配的预览。")
    .replace("Export workflow", "导出流程")
    .replace("Preview ready", "预览已生成")
    .replace("Export preview reset after input change.", "导出预览已因输入变更而失效。")
    .replace("Export written", "导出已写入")
    .replace("Action cancelled.", "操作已取消。")
    .replace("No imported sessions are available yet.", "还没有可用的已导入会话。")
    .replace(
        "Open or search a session first, then generate a Codex Skill export preview.",
        "请先打开或搜索一个会话，然后生成 Codex 技能包导出预览。",
    )
    .replace(
        "Open or search a session first, then generate a Codex 技能包 export preview.",
        "请先打开或搜索一个会话，然后生成 Codex 技能包导出预览。",
    )
    .replace("Warn only", "仅警告")
    .replace("Redact automatically", "自动脱敏")
    .replace("Block on high risk", "发现高风险则阻止")
    .replace(
        "Phase 03 exposes the workflow. Phase 04 will wire export actions after preview is available.",
        "当前提供预览工作流；预览可用后再接入导出写入操作。",
    )
    .replace(
        "Changing session, profile, or privacy mode invalidates the current preview.",
        "会话、导出类型或隐私模式变化后，当前预览会立即失效。",
    )
    .replace("Privacy findings", "隐私发现")
    .replace("High risk", "高风险")
    .replace("Session ${escapeHtml(latest.controls.session || \"-\")}", "会话 ${escapeHtml(latest.controls.session || \"-\")}")
    .replace("Blocked", "已阻止")
    .replace("Allowed", "允许")
    .replace("No output path reported in this response.", "本次响应未报告输出路径。")
    .replace("Write Actions", "写入操作")
    .replace("Export session", "导出会话")
    .replace("Export markdown", "导出 Markdown")
    .replace("Export obsidian", "导出 Obsidian")
    .replace("Export skill", "导出技能包")
    .replace("Export Session", "导出会话")
    .replace("Export target markdown", "导出 Markdown 目标")
    .replace("Export target obsidian", "导出 Obsidian 目标")
    .replace("Export target skill", "导出技能包目标")
    .replace("Export actions require reviewing preview output first.", "导出写入操作需要先查看预览结果。")
    .replace("Privacy Scan", "隐私扫描")
    .replace("Load Warnings", "加载警告")
    .replace("Warnings Summary", "警告汇总")
    .replace(
        "Privacy scan and allowlist behavior reuse existing ThreadVault privacy rules.",
        "隐私扫描和白名单行为复用现有 ThreadVault 隐私规则。",
    )
    .replace("Parser Warnings", "解析警告")
    .replace("Stats", "统计")
    .replace("Doctor", "诊断")
    .replace("Self-test", "自检")
    .replace("Reindex", "重建索引")
    .replace("Read-only database statistics.", "只读查看数据库统计。")
    .replace("Read-only health diagnostics.", "只读查看健康诊断。")
    .replace("Read-only local self-test.", "只读运行本地自检。")
    .replace("Vacuum", "数据库清理")
    .replace("Backup verify", "备份验证")
    .replace("Backup history latest", "最新备份")
    .replace("Backup history verify latest", "验证最新备份")
    .replace("Backup history prune", "清理备份历史")
    .replace("Backup history", "备份历史")
    .replace('placeholderButton("Backup", "backup"', 'placeholderButton("备份", "backup"')
    .replace("Restore history latest", "最新恢复")
    .replace("Restore history prune", "清理恢复历史")
    .replace("Restore history", "恢复历史")
    .replace("Restore apply", "执行恢复")
    .replace("Restore plan", "恢复计划")
    .replace("Read-only backup verification.", "只读执行备份验证。")
    .replace("Read-only history list.", "只读查看历史列表。")
    .replace("Restore must start with a plan.", "恢复必须先从计划开始。")
    .replace("Read-only restore history.", "只读查看恢复历史。")
    .replace("Dry-run by default; apply requires confirmation.", "默认模拟运行；实际执行需要确认。")
    .replace("Config init", "初始化配置")
    .replace("Config show", "查看配置")
    .replace("Config doctor", "配置诊断")
    .replace("Writes local config only after Phase 04 action wiring.", "仅在操作接入后写入本地配置。")
    .replace("Read-only config inspection.", "只读查看配置。")
    .replace("Read-only config diagnostics.", "只读查看配置诊断。")
    .replace("Schemas list", "结构定义列表")
    .replace("Schemas show", "查看结构定义")
    .replace("Validate JSON", "验证 JSON")
    .replace("Schema write", "写入结构定义")
    .replace("Capabilities", "能力清单")
    .replace("Robot docs guide", "机器人文档指南")
    .replace("Robot docs schemas", "机器人结构定义文档")
    .replace("Read-only schema registry listing.", "只读查看结构定义注册表。")
    .replace("Read-only schema detail.", "只读查看结构定义详情。")
    .replace("Validates pasted JSON against a selected schema.", "按选定结构定义验证粘贴的 JSON。")
    .replace("Read-only public capability discovery.", "只读查看公开能力清单。")
    .replace("Read-only agent usage guide.", "只读查看智能体使用指南。")
    .replace("Read-only schema guide.", "只读查看结构定义指南。")
    .replace('placeholder="Paste JSON payload for validation"', 'placeholder="粘贴要验证的 JSON 内容"')
    .replace("Personal Defaults", "个人默认值")
    .replace("local-first", "本地优先")
    .replace("privacy-first", "隐私优先")
    .replace("no cloud sync", "无云同步")
    .replace("no team enforcement by default", "默认无团队强制策略")
    .replace("Advanced Diagnostics", "高级诊断")
    .replace("Governance status", "治理状态")
    .replace("v3 gap audit", "v3 差距审计")
    .replace("v3 acceptance smoke", "v3 验收冒烟")
    .replace("Governance preflight", "治理预检")
    .replace("Instrumentation diagnostics", "埋点诊断")
    .replace("External model preflight", "外部模型预检")
    .replace("Read-only personal governance status.", "只读查看个人治理状态。")
    .replace("Read-only accepted v3 completion audit.", "只读查看已验收的 v3 完成度审计。")
    .replace("Read-only v3 acceptance smoke.", "只读运行 v3 验收冒烟。")
    .replace("Read-only permission preflight diagnostics.", "只读查看权限预检诊断。")
    .replace("Read-only instrumentation diagnostics.", "只读查看埋点诊断。")
    .replace("Read-only diagnostic; external model calls remain disabled by default.", "只读诊断；外部模型调用默认保持禁用。")
    .replace("status === \"正常\"", "status === \"ok\"")
    .replace("Warnings Summary", "警告汇总")
    .replace("Warnings 摘要", "警告汇总")
    .replace(">Warnings</button>", ">警告</button>")
    .replace("Export Preview", "导出预览")
    .replace("Read-only v3 验收冒烟.", "只读运行 v3 验收冒烟。")
    .replace("Preview must be accepted before writing a session export.", "写入会话导出前必须先接受预览。")
    .replace("Preview must be generated before writing files.", "写入文件前必须先生成预览。")
    .replace("Preview must match the session export selection before writing.", "预览必须匹配会话导出选择后才能写入。")
    .replace("Preview must match Markdown before writing files.", "预览必须匹配 Markdown 后才能写入文件。")
    .replace("Preview must match Obsidian before writing files.", "预览必须匹配 Obsidian 后才能写入文件。")
    .replace("Preview must match Skill before writing files.", "预览必须匹配技能包后才能写入文件。")
    .replace("Preview must match 技能包 before writing files.", "预览必须匹配技能包后才能写入文件。")
    .replace("Requires confirm=true before Phase 04 execution.", "执行前需要确认参数。")
    .replace("Backup may execute directly but must display its target path.", "备份可直接执行，但必须显示目标路径。")
    .replace("Requires confirm=true and a restore plan.", "需要确认参数和恢复计划。")
    .replace("Requires confirm=true before writing artifacts.", "写入产物前需要确认参数。")
    .replace("clean摘要", "cleanSummary")
    .replace("renderExport摘要", "renderExportSummary")
    .replace("exportPrivacy摘要", "exportPrivacySummary")
    .replace("prepareBasic技能包Export", "prepareBasicSkillExport")
    .replace("basic技能包Prompt", "basicSkillPrompt")
)


def build_health_payload(config: PersonalUIServerConfig) -> dict[str, Any]:
    app_config = load_app_config(config.config_path)
    db_path = config.db_path or default_db_path(config.config_path)
    return {
        "contract_version": PERSONAL_UI_HEALTH_CONTRACT_VERSION,
        "ok": True,
        "status": "ok",
        "server": {
            "host": config.host,
            "port": config.port,
            "url": config.url,
            "loopback_default": config.host == "127.0.0.1",
            "public_network_default": False,
            "authentication_required": False,
        },
        "defaults": {
            "local_first": True,
            "privacy_first": True,
            "cloud_sync": False,
            "external_model_calls": False,
            "team_enforcement": False,
            "react_vite_node_required": False,
        },
        "paths": {
            "db_path": str(db_path),
            "default_export_dir": str(Path(PERSONAL_UI_EXPORT_DIR).resolve()),
            "config_path": str(app_config.source_path) if app_config.source_path else None,
        },
    }


def handle_api_get(store: ArchiveStore, target: str, config: PersonalUIServerConfig) -> dict[str, Any]:
    parsed = urlparse(target)
    params = parse_qs(parsed.query)
    path = parsed.path.rstrip("/") or "/"
    try:
        if path == "/api/health":
            return _response(HTTPStatus.OK, "personal_ui_health", build_health_payload(config))
        if path == "/api/capabilities":
            return _response(HTTPStatus.OK, "capabilities", capabilities())
        if path == "/api/client/overview":
            return _response(
                HTTPStatus.OK,
                "client_overview",
                store.client_overview(
                    config_path=config.config_path,
                    query=_first(params, "query") or _first(params, "q"),
                    cwd=_first(params, "cwd"),
                    limit=_int_param(params, "limit", 20),
                    local_debug=False,
                ),
            )
        if path == "/api/client/session":
            session_id = _first(params, "session")
            if not session_id:
                return _response(HTTPStatus.BAD_REQUEST, "error", _error("session_required", "Provide session."))
            return _response(
                HTTPStatus.OK,
                "client_session",
                store.client_session(
                    session_id=session_id,
                    event_limit=_int_param(params, "event_limit", 20),
                    max_chars=_int_param(params, "max_chars", 500),
                    local_debug=False,
                ),
            )
        if path == "/api/client/warnings":
            session_id = _first(params, "session")
            if not session_id:
                return _response(HTTPStatus.BAD_REQUEST, "error", _error("session_required", "Provide session."))
            return _response(HTTPStatus.OK, "client_warnings", store.client_warnings(session_id=session_id, local_debug=False))
        if path == "/api/retrieve":
            query = _first(params, "q") or _first(params, "query")
            if not query:
                return _response(HTTPStatus.BAD_REQUEST, "error", _error("query_required", "Provide q or query."))
            return _response(
                HTTPStatus.OK,
                "agent_retrieval",
                store.agent_retrieve(
                    query=query,
                    config_path=config.config_path,
                    mode=_first(params, "mode") or "hybrid",
                    limit=_int_param(params, "limit", 20),
                    vector_limit=_int_param(params, "vector_limit", 10),
                    session_id=_first(params, "session"),
                    cwd=_first(params, "cwd"),
                    local_debug=False,
                ),
            )
        return _response(HTTPStatus.NOT_FOUND, "error", _error("route_not_found", f"No route for {path}.", path=path))
    except KeyError as exc:
        return _response(HTTPStatus.NOT_FOUND, "error", _error("not_found", str(exc.args[0])))
    except Exception as exc:
        return _response(HTTPStatus.INTERNAL_SERVER_ERROR, "error", _error("handler_error", str(exc)))


def handle_api_action(store: ArchiveStore, body: dict[str, Any], config: PersonalUIServerConfig) -> dict[str, Any]:
    action = body.get("action")
    confirm = bool(body.get("confirm"))
    if not isinstance(action, str) or not action:
        return _response(HTTPStatus.BAD_REQUEST, "personal_ui_action", _action_payload(None, False, "action_required", confirm))
    spec = ACTION_REGISTRY.get(action)
    if spec is None:
        return _response(
            HTTPStatus.BAD_REQUEST,
            "personal_ui_action",
            _action_payload(action, False, "unknown_action", confirm, message=f"Unknown action: {action}"),
        )
    params = body.get("params") if isinstance(body.get("params"), dict) else {}
    if spec.confirm_required and not confirm:
        return _response(
            HTTPStatus.FORBIDDEN,
            "personal_ui_action",
            _action_payload(action, False, "confirm_required", confirm, spec=spec, message=f"{action} requires confirm=true."),
        )
    if action in PRUNE_ACTIONS and bool(params.get("apply")) and not confirm:
        return _response(
            HTTPStatus.FORBIDDEN,
            "personal_ui_action",
            _action_payload(action, False, "confirm_required", confirm, spec=spec, message=f"{action} apply requires confirm=true."),
        )
    if spec.preview_required and not _truthy(params.get("preview_accepted")):
        return _response(
            HTTPStatus.FORBIDDEN,
            "personal_ui_action",
            _action_payload(
                action,
                False,
                "preview_required",
                confirm,
                spec=spec,
                message=f"{action} requires preview_accepted=true after reviewing an export preview.",
            ),
        )
    if not spec.implemented:
        return _response(
            HTTPStatus.NOT_IMPLEMENTED,
            "personal_ui_action",
            _action_payload(action, False, "deferred", confirm, spec=spec, message=spec.deferred_reason),
        )
    try:
        result = _execute_action(store, action, params, config)
    except KeyError as exc:
        return _response(
            HTTPStatus.NOT_FOUND,
            "personal_ui_action",
            _action_payload(action, False, "not_found", confirm, spec=spec, message=str(exc.args[0])),
        )
    except ValueError as exc:
        return _response(
            HTTPStatus.BAD_REQUEST,
            "personal_ui_action",
            _action_payload(action, False, "invalid_params", confirm, spec=spec, message=str(exc)),
        )
    except Exception as exc:
        return _response(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "personal_ui_action",
            _action_payload(action, False, "handler_error", confirm, spec=spec, message=str(exc)),
        )
    return _response(
        HTTPStatus.OK,
        "personal_ui_action",
        _action_payload(action, True, "ok", confirm, spec=spec, result=result),
    )


def _execute_action(store: ArchiveStore, action: str, params: dict[str, Any], config: PersonalUIServerConfig) -> Any:
    if action == "init":
        store.init()
        return {"ok": True, "db_path": str(store.db_path)}
    if action == "import":
        return store.import_codex(_path(params.get("codex_home")))
    if action == "ingest_queue_enqueue":
        return store.enqueue_ingestion(
            source=_str(params.get("source"), "manual"),
            codex_home=_path(params.get("codex_home")),
            reason=_str(params.get("reason"), "scan"),
        )
    if action == "ingest_queue_list":
        return store.list_ingestion_queue(status=_optional_str(params.get("status")), limit=_int_value(params.get("limit"), 50))
    if action == "ingest_queue_process":
        return store.process_ingestion_queue(
            codex_home=_path(params.get("codex_home")),
            limit=_int_value(params.get("limit"), 10),
            apply=_truthy(params.get("apply")),
        )
    if action == "sessions_list":
        return {
            "sessions": [
                dict(row)
                for row in store.list(limit=_int_value(params.get("limit"), 50), cwd=_optional_str(params.get("cwd")))
            ]
        }
    if action == "client_overview":
        return store.client_overview(
            config_path=config.config_path,
            query=_optional_str(params.get("query")),
            cwd=_optional_str(params.get("cwd")),
            limit=_int_value(params.get("limit"), 20),
            local_debug=False,
        )
    if action == "client_session":
        return store.client_session(
            session_id=_required_str(params, "session"),
            event_limit=_int_value(params.get("event_limit"), 20),
            max_chars=_int_value(params.get("max_chars"), 500),
            local_debug=False,
        )
    if action == "client_export_preview" or action == "export_preview":
        return store.client_export_preview(
            out_dir=_path(params.get("out")) or _default_work_dir("threadvault-export-preview"),
            profile=_str(params.get("profile"), "markdown"),
            session_ids=_string_list(params.get("session") or params.get("sessions")),
            project=_optional_str(params.get("project")),
            privacy_mode=_privacy_mode(params.get("privacy_mode")),
            privacy_config_path=_path(params.get("privacy_config")),
        )
    if action == "client_warnings":
        return store.client_warnings(session_id=_required_str(params, "session"), privacy_config_path=_path(params.get("privacy_config")))
    if action == "search":
        return {
            "results": [
                _row_payload(item)
                for item in store.search(
                    query=_required_query(params),
                    limit=_int_value(params.get("limit"), 20),
                    session_id=_optional_str(params.get("session")),
                    cwd=_optional_str(params.get("cwd")),
                    fields=_str(params.get("fields"), "standard"),
                )
            ]
        }
    if action == "retrieval_query":
        return store.retrieve(
            query=_required_query(params),
            limit=_int_value(params.get("limit"), 20),
            session_id=_optional_str(params.get("session")),
            cwd=_optional_str(params.get("cwd")),
        )
    if action == "hybrid_retrieval":
        return store.hybrid_retrieve(
            query=_required_query(params),
            config_path=config.config_path,
            limit=_int_value(params.get("limit"), 20),
            vector_limit=_int_value(params.get("vector_limit"), 10),
            session_id=_optional_str(params.get("session")),
            cwd=_optional_str(params.get("cwd")),
        )
    if action == "agent_retrieve":
        return store.agent_retrieve(
            query=_required_query(params),
            config_path=config.config_path,
            mode=_str(params.get("mode"), "hybrid"),
            limit=_int_value(params.get("limit"), 20),
            vector_limit=_int_value(params.get("vector_limit"), 10),
            session_id=_optional_str(params.get("session")),
            cwd=_optional_str(params.get("cwd")),
            local_debug=False,
        )
    if action == "summary_chunks":
        return store.summary_chunks(
            session_ids=_string_list(params.get("session") or params.get("sessions")),
            project=_optional_str(params.get("project")),
            max_chunks_per_session=_int_value(params.get("max_chunks_per_session"), 12),
            max_chars=_int_value(params.get("max_chars"), 1200),
        )
    if action == "summarize":
        return _object_payload(store.summarize(_required_str(params, "session")))
    if action == "vector_status":
        return store.vector_status(config_path=config.config_path)
    if action == "vector_index":
        return store.vector_index(
            session_ids=_string_list(params.get("session") or params.get("sessions")),
            project=_optional_str(params.get("project")),
            config_path=config.config_path,
            max_chunks_per_session=_int_value(params.get("max_chunks_per_session"), 12),
            max_chars=_int_value(params.get("max_chars"), 1200),
        )
    if action == "vector_query":
        return store.vector_query(query=_required_query(params), config_path=config.config_path, limit=_int_value(params.get("limit"), 10))
    if action == "privacy_scan":
        return store.privacy_scan(session_id=_required_str(params, "session"), privacy_config_path=_path(params.get("privacy_config")))
    if action == "warnings":
        return {"warnings": store.warnings(limit=_int_value(params.get("limit"), 50), session_id=_optional_str(params.get("session")))}
    if action == "warnings_summary":
        return {"summary": store.warning_summary()}
    if action == "export_session":
        path, findings = store.export_session(
            session_id=_required_str(params, "session"),
            out_dir=_path(params.get("out")) or _default_work_dir("threadvault-session-export"),
            fmt=_str(params.get("format"), "md"),
            profile=_str(params.get("profile"), "full"),
            privacy_mode=_privacy_mode(params.get("privacy_mode")),
            privacy_config_path=_path(params.get("privacy_config")),
        )
        return {"path": str(path), "privacy": _privacy_summary_from_findings(findings)}
    if action in {"export_target_markdown", "export_target_obsidian", "export_target_skill"}:
        profile = action.removeprefix("export_target_")
        return store.export_target(
            _path(params.get("out")) or _default_work_dir(f"threadvault-{profile}-export"),
            profile=profile,
            session_ids=_string_list(params.get("session") or params.get("sessions")),
            project=_optional_str(params.get("project")),
            privacy_mode=_privacy_mode(params.get("privacy_mode")),
            privacy_config_path=_path(params.get("privacy_config")),
            skill_name=_optional_str(params.get("skill_name")),
            skill_description=_optional_str(params.get("skill_description")),
        )
    if action == "config_init":
        return init_app_config(_path(params.get("config")) or config.config_path, force=_truthy(params.get("force")))
    if action == "config_show":
        return describe_app_config(_path(params.get("config")) or config.config_path, include_values=False)
    if action == "config_doctor":
        return diagnose_app_config(_path(params.get("config")) or config.config_path)
    if action == "stats":
        return store.stats()
    if action == "doctor":
        return store.doctor(codex_home=_path(params.get("codex_home")))
    if action == "self_test":
        return store.self_test()
    if action == "reindex":
        return store.reindex(fts_only=True)
    if action == "vacuum":
        return store.vacuum()
    if action == "backup":
        out = _path(params.get("out")) or _default_work_dir("threadvault-backups")
        payload = store.backup(out, force=_truthy(params.get("force")), write_manifest=True)
        return {**payload, "target_path": payload.get("path") or payload.get("backup_path") or str(out)}
    if action == "backup_verify":
        return store.verify_backup(_required_path(params, "backup"), manifest=_truthy(params.get("manifest")))
    if action == "backup_history":
        return list_backup_files(_path(params.get("dir")) or _default_work_dir("threadvault-backups"))
    if action == "backup_history_latest":
        return latest_backup_file(_path(params.get("dir")) or _default_work_dir("threadvault-backups"))
    if action == "backup_history_verify_latest":
        return verify_latest_backup(_path(params.get("dir")) or _default_work_dir("threadvault-backups"))
    if action == "backup_history_prune":
        return prune_backup_history(
            _path(params.get("dir")) or _default_work_dir("threadvault-backups"),
            keep=_int_value(params.get("keep"), 10),
            apply=_truthy(params.get("apply")),
        )
    if action == "restore_plan":
        return store.restore_plan(
            backup=_required_path(params, "backup"),
            target_db=_path(params.get("target_db")) or default_db_path(config.config_path),
        )
    if action == "restore_apply":
        return store.restore(
            backup=_required_path(params, "backup"),
            target_db=_path(params.get("target_db")) or default_db_path(config.config_path),
            apply=True,
            overwrite=_truthy(params.get("overwrite")),
            pre_restore_backup_dir=_path(params.get("pre_restore_backup_dir")),
            allow_missing_manifest=_truthy(params.get("allow_missing_manifest")),
            restore_history=_path(params.get("restore_history")),
        )
    if action == "restore_history":
        return store.restore_history_list(history=_path(params.get("history")))
    if action == "restore_history_latest":
        return store.restore_history_latest(history=_path(params.get("history")))
    if action == "restore_history_prune":
        return store.restore_history_prune(
            history=_path(params.get("history")),
            keep=_int_value(params.get("keep"), 10),
            apply=_truthy(params.get("apply")),
        )
    if action == "audit_corpus":
        payload = sample_codex_home(
            codex_home=_path(params.get("codex_home")),
            limit=_optional_int(params.get("limit")),
            include_paths=_truthy(params.get("include_paths")),
        )
        if params.get("out"):
            path = write_audit_report(payload, _required_path(params, "out"))
            payload = {**payload, "report_path": str(path)}
        return payload
    if action == "audit_history":
        return list_audit_reports(_required_path(params, "dir"))
    if action == "audit_history_latest":
        return latest_audit_report(_required_path(params, "dir"))
    if action == "audit_history_diff_latest":
        return diff_latest_audit_reports(_required_path(params, "dir"))
    if action == "audit_history_prune":
        return prune_audit_history(
            _required_path(params, "dir"),
            keep=_int_value(params.get("keep"), 10),
            apply=_truthy(params.get("apply")),
        )
    if action == "audit_diff":
        return diff_audit_reports(load_audit_report(_required_path(params, "before")), load_audit_report(_required_path(params, "after")))
    if action in {"schemas_list", "schema_list"}:
        return {"schemas": schema_names()}
    if action in {"schemas_show", "schema_show"}:
        return get_schema(_required_str(params, "name"))
    if action == "validate_json":
        payload = params.get("payload")
        if isinstance(payload, str):
            payload = json.loads(payload)
        return validate_payload(_required_str(params, "schema"), payload)
    if action in {"schemas_write", "schema_write"}:
        out = _path(params.get("out")) or Path("docs/schemas")
        paths = write_schema_files(out)
        return {"out": str(out), "files": [str(path) for path in paths]}
    if action == "capabilities":
        return capabilities()
    if action == "robot_docs_guide":
        return robot_guide()
    if action == "robot_docs_schemas":
        return robot_schemas()
    if action == "governance_status":
        return store.governance_status(config_path=config.config_path)
    if action == "governance_v3_gap_audit":
        return store.governance_v3_completion_gap_audit(config_path=config.config_path)
    if action == "governance_v3_acceptance_smoke":
        return store.governance_v3_acceptance_smoke(
            config_path=config.config_path,
            query=_str(params.get("query"), "pytest"),
            session_id=_str(params.get("session"), "sess-current"),
            work_dir=_path(params.get("work_dir")),
        )
    if action == "governance_preflight":
        return _governance_preflight(store, params, config)
    if action == "governance_instrumentation":
        return store.governance_business_command_instrumentation(
            config_path=config.config_path,
            command=_str(params.get("command"), "threadvault retrieval query"),
            role=_str(params.get("role"), "reader"),
            audit_log=_path(params.get("audit_log")),
            actor=_optional_str(params.get("actor")),
            target_type=_optional_str(params.get("target_type")),
            target_id=_optional_str(params.get("target_id")),
        )
    if action == "governance_external_model_preflight":
        return store.governance_external_model_preflight(
            config_path=config.config_path,
            command=_str(params.get("command"), "threadvault summarize"),
            role=_str(params.get("role"), "reader"),
            audit_log=_path(params.get("audit_log")),
            actor=_optional_str(params.get("actor")),
            target_type=_optional_str(params.get("target_type")),
            target_id=_optional_str(params.get("target_id")),
        )
    raise ValueError(f"No executor for {action}.")


def build_personal_ui_server(store: ArchiveStore, config: PersonalUIServerConfig) -> ThreadingHTTPServer:
    class PersonalUIHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._send_bytes(HTTPStatus.OK, INDEX_HTML.encode("utf-8"), "text/html; charset=utf-8")
                return
            if parsed.path == "/zh":
                self._send_bytes(HTTPStatus.OK, INDEX_HTML_ZH.encode("utf-8"), "text/html; charset=utf-8")
                return
            if parsed.path == "/assets/app.css":
                self._send_bytes(HTTPStatus.OK, APP_CSS.encode("utf-8"), "text/css; charset=utf-8")
                return
            if parsed.path == "/assets/app.js":
                self._send_bytes(HTTPStatus.OK, APP_JS.encode("utf-8"), "application/javascript; charset=utf-8")
                return
            if parsed.path == "/assets/app.zh.js":
                self._send_bytes(HTTPStatus.OK, APP_JS_ZH.encode("utf-8"), "application/javascript; charset=utf-8")
                return
            response = handle_api_get(store, self.path, config)
            self._send_json(response["status_code"], response["payload"])

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == "/api/ui-heartbeat":
                self.server.last_heartbeat_at = time.monotonic()  # type: ignore[attr-defined]
                self.server.heartbeat_seen = True  # type: ignore[attr-defined]
                self._send_json(HTTPStatus.OK.value, {"ok": True})
                return
            if parsed.path != "/api/action":
                self._send_json(HTTPStatus.NOT_FOUND.value, _error("route_not_found", f"No route for {parsed.path}.", path=parsed.path))
                return
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw_body = self.rfile.read(length) if length else b"{}"
            try:
                body = json.loads(raw_body.decode("utf-8"))
            except json.JSONDecodeError:
                self._send_json(HTTPStatus.BAD_REQUEST.value, _error("invalid_json", "Request body must be JSON."))
                return
            response = handle_api_action(store, body, config)
            self._send_json(response["status_code"], response["payload"])

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _send_json(self, status_code: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False, indent=2, default=str).encode("utf-8")
            self._send_bytes(HTTPStatus(status_code), body, "application/json; charset=utf-8")

        def _send_bytes(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
            self.send_response(status.value)
            self.send_header("Content-Type", content_type)
            if content_type.startswith(("text/html", "text/css", "application/javascript")):
                self.send_header("Cache-Control", "no-store, max-age=0")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer((config.host, config.port), PersonalUIHandler)
    server.last_heartbeat_at = time.monotonic()  # type: ignore[attr-defined]
    server.heartbeat_seen = False  # type: ignore[attr-defined]
    return server


def start_personal_ui_close_monitor(server: ThreadingHTTPServer, config: PersonalUIServerConfig) -> None:
    def stop_after_close() -> None:
        poll_interval = min(1.0, max(0.05, config.close_timeout_seconds / 4))
        while True:
            time.sleep(poll_interval)
            if not getattr(server, "heartbeat_seen", False):
                continue
            elapsed = time.monotonic() - getattr(server, "last_heartbeat_at", time.monotonic())
            if elapsed >= config.close_timeout_seconds:
                server.shutdown()
                return

    threading.Thread(target=stop_after_close, daemon=True).start()


def serve_personal_ui(store: ArchiveStore, config: PersonalUIServerConfig, *, open_browser: bool = False) -> None:
    server = build_personal_ui_server(store, config)
    if open_browser:
        webbrowser.open(config.open_url)
    if config.exit_on_close:
        start_personal_ui_close_monitor(server, config)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def run_personal_ui_smoke(
    store: ArchiveStore,
    config: PersonalUIServerConfig,
    *,
    query: str = "pytest",
    session_id: str = "sess-current",
    work_dir: Path | None = None,
) -> dict[str, Any]:
    work_root = (work_dir or (default_db_path().parent / "threadvault-ui-smoke")).expanduser()
    work_root.mkdir(parents=True, exist_ok=True)
    checks: list[dict[str, Any]] = []

    def add_check(code: str, category: str, required: bool, probe: Any) -> None:
        try:
            ok, message, evidence = probe()
        except Exception as exc:  # pragma: no cover - defensive smoke reporting
            ok = False
            message = str(exc)
            evidence = {"exception": exc.__class__.__name__}
        checks.append(
            {
                "code": code,
                "category": category,
                "ok": bool(ok),
                "required": required,
                "message": message,
                "evidence": evidence,
            }
        )

    def response_ok(response: dict[str, Any]) -> bool:
        return response["ok"] is True and response["status_code"] < 400

    add_check(
        "ui_serve_help_available",
        "cli",
        True,
        lambda: (
            "ui" in capabilities()["commands"],
            "threadvault ui serve is registered with loopback defaults.",
            {"serve_command": PERSONAL_UI_SERVE_COMMAND, "ui_command_registered": "ui" in capabilities()["commands"]},
        ),
    )

    def bind_server_probe() -> tuple[bool, str, dict[str, Any]]:
        smoke_config = PersonalUIServerConfig(host="127.0.0.1", port=0, db_path=config.db_path, config_path=config.config_path)
        server = build_personal_ui_server(store, smoke_config)
        try:
            host, port = server.server_address[:2]
            ok = host == "127.0.0.1" and int(port) > 0
            return ok, "Personal UI server binds on loopback.", {"host": host, "port": port, "public_network_default": False}
        finally:
            server.server_close()

    add_check("ui_server_loopback_bind", "server", True, bind_server_probe)

    def health_probe() -> tuple[bool, str, dict[str, Any]]:
        response = handle_api_get(store, "/api/health", config)
        payload = response["payload"]
        ok = response_ok(response) and payload["ok"] is True and payload["server"]["loopback_default"] is True
        return ok, "/api/health returns ok with local defaults.", {"schema": response["schema"], "server": payload["server"]}

    add_check("health_route_ok", "api", True, health_probe)

    def overview_probe() -> tuple[bool, str, dict[str, Any]]:
        response = handle_api_get(store, f"/api/client/overview?query={query}&limit=10", config)
        payload = response["payload"]
        session_ids = [item.get("session_id") for item in payload.get("sessions", [])]
        ok = response_ok(response) and session_id in session_ids
        return ok, "/api/client/overview lists the fixture session.", {"session_ids": session_ids, "session_count": len(session_ids)}

    add_check("client_overview_lists_sessions", "api", True, overview_probe)

    def retrieve_probe() -> tuple[bool, str, dict[str, Any]]:
        response = handle_api_get(store, f"/api/retrieve?q={query}&limit=5", config)
        payload = response["payload"]
        result_count = len(payload.get("results", []))
        ok = response_ok(response) and payload["contract_version"].startswith("agent_retrieval") and result_count > 0
        return ok, "/api/retrieve returns agent retrieval results.", {
            "contract_version": payload.get("contract_version"),
            "result_count": result_count,
        }

    add_check("retrieve_route_returns_results", "api", True, retrieve_probe)

    def session_probe() -> tuple[bool, str, dict[str, Any]]:
        response = handle_api_get(store, f"/api/client/session?session={session_id}&event_limit=5&max_chars=300", config)
        payload = response["payload"]
        event_count = len(payload.get("events", []))
        ok = response_ok(response) and payload["contract_version"].startswith("client_session") and event_count > 0
        return ok, "/api/client/session returns summary and event previews.", {
            "contract_version": payload.get("contract_version"),
            "event_count": event_count,
            "summary_keys": sorted(payload.get("summary", {}).keys()),
        }

    add_check("client_session_returns_preview", "api", True, session_probe)

    def safe_action_probe() -> tuple[bool, str, dict[str, Any]]:
        response = handle_api_action(store, {"action": "stats", "params": {}}, config)
        payload = response["payload"]
        ok = response_ok(response) and payload["ok"] is True and payload["status"] == "ok"
        return ok, "/api/action executes a safe read action.", {
            "action": payload.get("action"),
            "sessions": payload.get("result", {}).get("sessions"),
        }

    add_check("safe_action_executes", "action", True, safe_action_probe)

    def export_preview_probe() -> tuple[bool, str, dict[str, Any]]:
        out = work_root / "export-preview"
        response = handle_api_action(
            store,
            {"action": "client_export_preview", "params": {"session": session_id, "out": str(out), "profile": "markdown"}},
            config,
        )
        payload = response["payload"]
        diagnostics = payload.get("result", {}).get("diagnostics", {})
        ok = response_ok(response) and diagnostics.get("writes_files") is False and not out.exists()
        return ok, "Export preview reports no file writes.", {"writes_files": diagnostics.get("writes_files"), "out_exists": out.exists()}

    add_check("export_preview_does_not_write", "safety", True, export_preview_probe)

    def dangerous_reject_probe() -> tuple[bool, str, dict[str, Any]]:
        actions = ["restore_apply", "vacuum", "reindex", "schema_write"]
        evidence: dict[str, Any] = {}
        ok = True
        for action in actions:
            response = handle_api_action(store, {"action": action, "params": {}}, config)
            payload = response["payload"]
            evidence[action] = {"status_code": response["status_code"], "status": payload["status"]}
            ok = ok and response["status_code"] == 403 and payload["status"] == "confirm_required"
        return ok, "Dangerous actions reject without confirm=true.", evidence

    add_check("dangerous_actions_require_confirm", "safety", True, dangerous_reject_probe)

    def boundary_probe() -> tuple[bool, str, dict[str, Any]]:
        caps = capabilities()
        health = build_health_payload(config)
        flags = caps["feature_flags"]
        ok = (
            flags["personal_ui_desktop_wrapper"] is False
            and flags["personal_ui_team_mode"] is False
            and flags["personal_ui_cloud_sync"] is False
            and flags["cloud_sync"] is False
            and flags["external_llm_summary"] is False
            and health["defaults"]["external_model_calls"] is False
            and health["server"]["authentication_required"] is False
        )
        return ok, "Personal UI keeps local-first non-default boundaries.", {
            "default_host": config.host,
            "cloud_sync": flags["cloud_sync"],
            "team_mode": flags["personal_ui_team_mode"],
            "external_llm_summary": flags["external_llm_summary"],
            "authentication_required": health["server"]["authentication_required"],
        }

    add_check("local_privacy_boundaries_hold", "boundary", True, boundary_probe)

    def v2_probe() -> tuple[bool, str, dict[str, Any]]:
        payload = store.retrieve(query=query, limit=5)
        result_count = len(payload.get("results", []))
        ok = payload["contract_version"].startswith("retrieval") and result_count > 0
        return ok, "Accepted v2 retrieval interface still returns results.", {
            "contract_version": payload.get("contract_version"),
            "result_count": result_count,
            "engine": payload.get("diagnostics", {}).get("engine"),
        }

    add_check("v2_retrieval_non_regression", "non_regression", True, v2_probe)

    def v3_probe() -> tuple[bool, str, dict[str, Any]]:
        payload = store.governance_v3_acceptance_smoke(
            config_path=config.config_path,
            query=query,
            session_id=session_id,
            work_dir=work_root / "v3-smoke",
        )
        ok = payload["ok"] is True and payload["status"] == "accepted"
        return ok, "Accepted v3 governance smoke still passes.", {
            "status": payload.get("status"),
            "failed_check_count": payload.get("summary", {}).get("failed_check_count"),
            "required_check_count": payload.get("summary", {}).get("required_check_count"),
        }

    add_check("v3_acceptance_non_regression", "non_regression", True, v3_probe)

    def discovery_probe() -> tuple[bool, str, dict[str, Any]]:
        caps = capabilities()
        guide = robot_guide()
        schemas = robot_schemas()
        schema_path = Path("docs/schemas/personal_ui_smoke.schema.json")
        required_docs = [
            Path("docs/progress/archive/legacy-v4/README.md"),
            Path("docs/progress/archive/legacy-v4/phases/phase-05-v4-acceptance-smoke/plan.md"),
            Path("docs/progress/archive/legacy-v4/phases/phase-05-v4-acceptance-smoke/acceptance.md"),
        ]
        ok = (
            "ui smoke" in caps["json_outputs"]
            and caps["feature_flags"].get("personal_ui_acceptance_smoke") is True
            and guide["personal_ui"]["smoke_schema"] == "personal_ui_smoke"
            and "personal_ui_smoke" in schemas
            and schema_path.exists()
            and all(path.exists() for path in required_docs)
        )
        return ok, "Discovery surfaces and Phase 05 docs are present.", {
            "json_output_registered": "ui smoke" in caps["json_outputs"],
            "schema_registered": "personal_ui_smoke" in schemas,
            "schema_artifact_exists": schema_path.exists(),
            "docs_present": [str(path) for path in required_docs if path.exists()],
        }

    add_check("discovery_schema_docs_present", "discovery", True, discovery_probe)

    add_check(
        "retired_deep_research_report_absent",
        "documentation",
        True,
        lambda: (
            not Path("deep-research-report.md").exists(),
            "Retired root deep-research-report.md remains absent.",
            {"exists": Path("deep-research-report.md").exists()},
        ),
    )

    required = [check for check in checks if check["required"]]
    failed_required = [check for check in required if not check["ok"]]
    criteria = [
        {
            "code": "local_ui_server_and_routes",
            "ok": all(_check_ok(checks, code) for code in [
                "ui_server_loopback_bind",
                "health_route_ok",
                "client_overview_lists_sessions",
                "retrieve_route_returns_results",
                "client_session_returns_preview",
            ]),
        },
        {
            "code": "action_safety",
            "ok": all(_check_ok(checks, code) for code in [
                "safe_action_executes",
                "export_preview_does_not_write",
                "dangerous_actions_require_confirm",
            ]),
        },
        {
            "code": "local_first_privacy_first",
            "ok": _check_ok(checks, "local_privacy_boundaries_hold"),
        },
        {
            "code": "v2_v3_non_regression",
            "ok": all(_check_ok(checks, code) for code in [
                "v2_retrieval_non_regression",
                "v3_acceptance_non_regression",
            ]),
        },
        {
            "code": "discovery_traceability",
            "ok": all(_check_ok(checks, code) for code in [
                "discovery_schema_docs_present",
                "retired_deep_research_report_absent",
            ]),
        },
    ]
    status = "accepted" if not failed_required and all(item["ok"] for item in criteria) else "failed"
    return {
        "contract_version": PERSONAL_UI_SMOKE_CONTRACT_VERSION,
        "status": status,
        "ok": status == "accepted",
        "server": {
            "default_host": "127.0.0.1",
            "configured_host": config.host,
            "configured_port": config.port,
            "public_network_default": False,
            "serve_command": PERSONAL_UI_SERVE_COMMAND,
            "smoke_command": PERSONAL_UI_SMOKE_COMMAND,
        },
        "checks": checks,
        "summary": {
            "required_check_count": len(required),
            "passed_check_count": sum(1 for check in checks if check["ok"]),
            "failed_check_count": sum(1 for check in checks if not check["ok"]),
            "failed_required_check_count": len(failed_required),
            "criteria_count": len(criteria),
            "criteria_satisfied_count": sum(1 for item in criteria if item["ok"]),
        },
        "criteria": criteria,
        "boundaries": {
            "local_first": True,
            "privacy_first": True,
            "cloud_sync_default": False,
            "team_mode_default": False,
            "login_default": False,
            "public_server_default": False,
            "external_model_calls_default": False,
            "react_vite_node_required": False,
        },
        "diagnostics": {
            "db_path": str(config.db_path) if config.db_path else str(store.db_path),
            "config_path": str(config.config_path) if config.config_path else None,
            "query": query,
            "session_id": session_id,
            "work_dir": str(work_root),
        },
    }


def _response(status: HTTPStatus, schema: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": status.value < 400,
        "status_code": status.value,
        "schema": schema,
        "payload": payload,
    }


def _error(code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"ok": False, "error": code, "message": message, **extra}


def _privacy_summary_from_findings(findings: list[Any]) -> dict[str, Any]:
    effective = [finding for finding in findings if not bool(getattr(finding, "allowlisted", False))]
    high_risk = [
        finding
        for finding in effective
        if str(getattr(finding, "severity", "")).lower() in {"high", "critical"}
    ]
    by_severity: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    for finding in effective:
        severity = str(getattr(finding, "severity", "unknown"))
        kind = str(getattr(finding, "kind", "unknown"))
        by_severity[severity] = by_severity.get(severity, 0) + 1
        by_kind[kind] = by_kind.get(kind, 0) + 1
    return {
        "findings_count": len(findings),
        "effective_findings_count": len(effective),
        "high_risk_findings_count": len(high_risk),
        "blocked": bool(high_risk),
        "by_severity": by_severity,
        "by_kind": by_kind,
    }


def _check_ok(checks: list[dict[str, Any]], code: str) -> bool:
    return any(check["code"] == code and check["ok"] for check in checks)


def _action_payload(
    action: str | None,
    ok: bool,
    status: str,
    confirm: bool,
    *,
    message: str | None = None,
    spec: PersonalUIActionSpec | None = None,
    result: Any = None,
) -> dict[str, Any]:
    return {
        "contract_version": PERSONAL_UI_ACTION_CONTRACT_VERSION,
        "ok": ok,
        "action": action,
        "status": status,
        "confirm": confirm,
        "message": message,
        "result": result,
        "safety": {
            "dangerous_action": bool(spec.dangerous_action) if spec else False,
            "confirm_required": bool(spec.confirm_required) if spec else False,
            "preview_required": bool(spec.preview_required) if spec else False,
            "dry_run_default": bool(spec.dry_run_default) if spec else True,
            "implemented": bool(spec.implemented) if spec else False,
            "label": spec.label if spec else None,
        },
        "available_actions": sorted(ACTION_REGISTRY),
    }


def _governance_preflight(store: ArchiveStore, params: dict[str, Any], config: PersonalUIServerConfig) -> dict[str, Any]:
    kind = _str(params.get("kind"), "summary_search")
    common = {
        "config_path": config.config_path,
        "command": _str(params.get("command"), "threadvault retrieval query"),
        "role": _str(params.get("role"), "reader"),
        "audit_log": _path(params.get("audit_log")),
        "actor": _optional_str(params.get("actor")),
        "target_type": _optional_str(params.get("target_type")),
        "target_id": _optional_str(params.get("target_id")),
    }
    if kind == "export_backup":
        return store.governance_export_backup_preflight(**common)
    if kind == "restore_retention":
        return store.governance_restore_retention_preflight(**common)
    if kind == "raw_read":
        return store.governance_raw_read_preflight(**common)
    if kind == "export_preview":
        return store.governance_export_preview_preflight(**common)
    if kind == "external_model":
        return store.governance_external_model_preflight(**common)
    return store.governance_summary_search_preflight(**common)


def _required_str(params: dict[str, Any], name: str) -> str:
    value = _optional_str(params.get(name))
    if not value:
        raise ValueError(f"{name} is required")
    return value


def _required_query(params: dict[str, Any]) -> str:
    return _required_str(params, "query")


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _str(value: Any, default: str) -> str:
    return _optional_str(value) or default


def _path(value: Any) -> Path | None:
    text = _optional_str(value)
    if text is None:
        return None
    return Path(text).expanduser()


def _required_path(params: dict[str, Any], name: str) -> Path:
    value = _path(params.get(name))
    if value is None:
        raise ValueError(f"{name} is required")
    return value


def _default_work_dir(name: str) -> Path:
    return default_db_path().parent / name


def _int_value(value: Any, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Expected integer, got {value!r}") from exc
    return max(1, parsed)


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return _int_value(value, 1)


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "apply"}


def _string_list(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return [str(value)]


def _privacy_mode(value: Any) -> str:
    mode = _str(value, "warn")
    if mode not in {"warn", "redact", "fail"}:
        raise ValueError("privacy_mode must be warn, redact, or fail")
    return mode


def _row_payload(value: Any) -> Any:
    if hasattr(value, "to_payload"):
        return value.to_payload()
    return _object_payload(value)


def _object_payload(value: Any) -> Any:
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return value


def _first(params: dict[str, list[str]], name: str) -> str | None:
    values = params.get(name)
    if not values:
        return None
    return values[0]


def _int_param(params: dict[str, list[str]], name: str, default: int) -> int:
    value = _first(params, name)
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError:
        return default
    return max(1, parsed)
