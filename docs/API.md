# API

This document summarizes the local personal UI API surfaces and the JSON-facing contracts that the UI depends on. It is a practical guide for debugging the local browser UI and for adding new UI actions without bypassing existing ThreadVault modules.

It also records the MCP stdio surface used by Codex, ZCode, OpenCode, and other MCP-capable local agents. The MCP surface reuses `ArchiveStore`, `agent_interface`, and `client_interface`; it does not parse Codex transcripts or query SQLite tables directly.

## Local Server

Default local URL:

```text
http://127.0.0.1:8766
```

Chinese UI route:

```text
/zh
```

The default launcher and `threadvault ui serve` keep the server on loopback. The server is a local stdlib HTTP server, not a hosted cloud service.

## Health Route

| Route | Purpose | Important Fields |
|---|---|---|
| `GET /api/health` | Returns server status, command metadata, feature flags, and local paths. | `server`, `paths.db_path`, `paths.default_export_dir`, `actions.available_actions` |

The UI top bar uses this route to show:

- **索引库 / Index DB**: the SQLite archive database.
- **导出目录 / Export folder**: the default folder for generated export files.

These paths are intentionally different.
The index DB path is resolved from `--db`, `THREADVAULT_DB`, `[storage].archive_db`, or the project-local `data/threadvault.db` default.

## Read Routes

| Route | Purpose | Store Method / Module | Writes? |
|---|---|---|---|
| `GET /api/client/overview` | Returns local session overview and optional search metadata. | `ArchiveStore.client_overview` | No |
| `GET /api/client/session` | Returns session detail, summary, event previews, and evidence IDs. | `ArchiveStore.client_session` | No |
| `GET /api/client/warnings` | Returns warning detail and privacy summary for a session. | `ArchiveStore.client_warnings` | No |
| `GET /api/retrieve` | Runs agent-facing retrieval for UI search. | `ArchiveStore.agent_retrieve` | No |

## MCP Stdio Interface

ThreadVault exposes a local MCP server:

```powershell
threadvault mcp manifest --json
threadvault mcp serve
```

The transport is stdio and the server speaks JSON-RPC MCP lifecycle/tool methods. The first tool set is deliberately read-only:

| MCP Tool | Store Method / Module | Purpose | Writes? |
|---|---|---|---|
| `threadvault_capabilities` | `store.capabilities` | Discover commands, JSON contracts, and feature flags. | No |
| `threadvault_stats` | `ArchiveStore.stats` | Read archive counts and clean-index diagnostics. | No |
| `threadvault_doctor` | `ArchiveStore.doctor` | Run local DB, FTS, and Codex discovery diagnostics. | No |
| `threadvault_retrieve` | `ArchiveStore.agent_retrieve` | Return agent-facing retrieval results for historical context. | No |
| `threadvault_session` | `ArchiveStore.client_session` | Return session summary, evidence, and event previews. | No |
| `threadvault_export_preview` | `ArchiveStore.client_export_preview` | Preview Markdown/Obsidian/Skill output without writing files. | No |

MCP clients should use `threadvault_export_preview` to inspect planned output and then ask the user to run an explicit `threadvault export-target ...` command if files should be written. This keeps Obsidian/Skill export gates visible and avoids silent writes from an agent tool call.

For concrete Codex, OpenCode, ZCode, Obsidian, and AI self-configuration guidance, see `docs/MCP_INTEGRATION.md`.

### MCP联动计划书

目标：让 ThreadVault 成为本机 agent 记忆中枢，而不是让 Codex、ZCode、OpenCode、Obsidian 各自重新解析会话文件。

实施阶段：

1. `0.34.0` 提供 MCP stdio read-only 工具集，覆盖检索、会话详情、诊断、能力发现和导出预览。
2. 后续增加 `threadvault integrations doctor`，检查 Codex/ZCode/OpenCode/Obsidian 是否能看到 MCP 或导出目录。
3. 后续增加 `threadvault integrations install <target> --dry-run`，只生成配置计划；`--apply` 才写入工具配置。
4. 后续考虑新增受控写工具，但必须保留 preview、privacy、governance、confirm gate。

各工具建议：

| Tool | Recommended Link | Notes |
|---|---|---|
| Codex | MCP stdio server plus Codex hook enqueue/import flow. | Hook 只排队导入，不做重扫描；MCP 负责读历史。 |
| ZCode | MCP server registration; optional Skill/Plugin wrapper later. | 共享同一个 ThreadVault MCP，不复制 retrieval logic。 |
| OpenCode | MCP server registration plus read-only memory agent. | 通过权限配置限制写入，导出写文件走显式 CLI。 |
| Obsidian | `export-target obsidian` and MCP export preview. | Obsidian 消费 Markdown vault，不直接读 SQLite。 |

Common query parameters:

| Parameter | Routes | Meaning |
|---|---|---|
| `query` / `q` | overview, retrieve | Search text. |
| `limit` | overview, retrieve | Result/session limit. |
| `session` | session, warnings, retrieve | Session filter or detail target. |
| `mode` | retrieve | `fts` or `hybrid`. |
| `event_limit` | session | Number of event previews to return. |
| `max_chars` | session | Max text length per event preview. |

## Action Route

| Route | Purpose |
|---|---|
| `POST /api/action` | Runs a registered personal UI action with safety metadata and structured results. |

Request shape:

```json
{
  "action": "client_export_preview",
  "params": {
    "session": "SESSION_ID",
    "profile": "skill",
    "privacy_mode": "warn",
    "out": "<repo-root>\\threadvault-ui-output"
  }
}
```

Response shape:

```json
{
  "schema": "personal_ui_action",
  "payload": {
    "ok": true,
    "action": "client_export_preview",
    "result": {},
    "safety": {},
    "error": null
  }
}
```

Exact payloads are validated by `personal_ui_action.schema.json`.

## Action Safety Rules

The action registry in `personal_ui.py` marks actions with safety metadata.

| Safety Flag | Meaning | Examples |
|---|---|---|
| `preview_required` | A write action requires a matching preview state. | `export_session`, `export_target_markdown`, `export_target_obsidian`, `export_target_skill` |
| `confirm_required` | Backend requires explicit `confirm=true`. | `restore_apply`, `reindex`, `vacuum`, schema writes |
| `dangerous_action` | UI should visually distinguish and gate the action. | restore apply, vacuum, prune actions |
| `dry_run_default` | Action should plan/list by default instead of applying destructive changes. | prune/history/restore planning flows |

Important rules:

- Export writes require preview acceptance.
- Restore, vacuum, reindex, and schema write operations require confirmation.
- Backup can write directly but must show the target path/result.
- Prune apply operations must stay dry-run unless explicitly confirmed/applied.

## Action Families

| Family | Actions | Notes |
|---|---|---|
| Archive browsing | `sessions_list`, `client_overview`, `client_session` | Read archive/session payloads. |
| Retrieval | `search`, `retrieval_query`, `hybrid_retrieval`, `agent_retrieve` | Search and agent-facing retrieval. |
| Summary/vector | `summarize`, `summary_chunks`, `vector_status`, `vector_index`, `vector_query` | `vector_index` writes optional vector chunks when config permits. |
| Privacy/warnings | `privacy_scan`, `warnings`, `warnings_summary`, `client_warnings` | Read-only diagnostics. |
| Export | `client_export_preview`, `export_preview`, `export_session`, `export_target_*` | Preview first, then write. |
| Config/maintenance | `config_*`, `stats`, `doctor`, `self_test`, `reindex`, `vacuum` | Reindex/vacuum mutate derived DB state. |
| Backup/restore | `backup`, `backup_verify`, `backup_history_*`, `restore_plan`, `restore_apply`, `restore_history_*` | Restore apply changes the target database. |
| Audit/schema/docs | `audit_*`, `schemas_*`, `validate_json`, `robot_docs_*`, `capabilities` | Schema writes create/update local schema files. |
| Governance | `governance_status`, `governance_preflight`, `governance_instrumentation`, `governance_external_model_preflight`, v3 smoke/gap actions | Optional local governance diagnostics and instrumentation. |

## Export Workflow API

The UI export flow is intentionally multi-step:

```text
choose session/profile/privacy
  -> POST /api/action action=client_export_preview
  -> user reviews planned files and privacy summary
  -> POST /api/action action=export_target_* with preview_accepted=true
  -> output files and manifest are written
```

If session, profile, privacy mode, or output path changes, the frontend invalidates the old preview. The backend still rejects preview-required writes without accepted preview metadata.

## UI Contract Notes

- The right-side JSON panel intentionally preserves raw keys, command strings, paths, and privacy findings.
- Human-readable Chinese summaries are rendered in the main UI.
- Session event previews should use `text_preview` first, then fallback fields.
- Activity feedback uses running/done/failed states; completed actions should not keep spinner animation active.
- Locked write actions remain clickable enough to explain why they are locked, but must not send backend writes.

## Debugging Checklist

Use these commands when the UI seems stale or confusing:

```powershell
Invoke-WebRequest -Uri http://127.0.0.1:8766/api/health -UseBasicParsing
threadvault ui smoke --json
threadvault capabilities --json
threadvault robot-docs schemas --json
```

When testing Chinese UI JavaScript assets, extract or serve the page and run:

```powershell
node --check <served-app.js>
node --check <served-app.zh.js>
```

For behavior changes, run focused tests:

```powershell
py -3.12 -m pytest tests/test_v402_local_ui_server.py tests/test_v403_personal_ui_workbench.py tests/test_v404_ui_action_coverage.py tests/test_v406_ui_chinese_localization.py -q
```
