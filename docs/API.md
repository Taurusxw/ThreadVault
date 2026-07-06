# API

This document summarizes ThreadVault's JSON-facing contracts, MCP surface, and retired interface metadata. It is a practical guide for debugging machine-facing payloads and for keeping UI actions behind existing ThreadVault modules.

It also records the MCP stdio surface used by Codex, ZCode, OpenCode, and other MCP-capable local agents. The MCP surface reuses `ArchiveStore`, `agent_interface`, and `client_interface`; it does not parse Codex transcripts or query SQLite tables directly.

## Interface Discovery

`threadvault capabilities --json` and `threadvault robot-docs guide --json` expose the active interface policy:

| Field | Meaning |
|---|---|
| `interface_policy.primary_local_interface` | `native_desktop`; the 1.0.0 local UI line. |
| `interface_policy.primary_command` | `threadvault desktop launch`. |
| `interface_policy.primary_smoke_command` | `threadvault desktop smoke --json`. |
| `interface_policy.retired_interface_status` | `retired` for the browser Web UI. |
| `interface_policy.retired_interface_archive` | `docs/progress/archive/legacy-v4/`; historical v4 Web UI evidence. |
| `retired_commands` | Former Web UI commands retained as metadata only; they are not active CLI commands. |

The primary local interface does not require a browser, server, WebView, Electron, React, Tauri, or a frontend build pipeline.

## Retired Browser Web UI

`threadvault ui serve` and `threadvault ui smoke` are retired from the active CLI, and the `threadvault.personal_ui` runtime module plus active `personal_ui_*` schemas are removed from the 1.0.0 package.

Historical route, static asset, localization, action registry, and acceptance evidence remains under `docs/progress/archive/legacy-v4/`. Do not use the v4 archive as a live API contract for new work.

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

Use these commands when the primary desktop UI or contract discovery seems stale or confusing:

```powershell
threadvault desktop smoke --json
threadvault capabilities --json
threadvault robot-docs schemas --json
```

For behavior changes, run focused tests:

```powershell
py -3.12 -m pytest tests/test_v28_capabilities_schema_contract.py tests/test_v407_desktop_app.py -q
```
