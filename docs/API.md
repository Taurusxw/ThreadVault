# API

This document summarizes ThreadVault's JSON-facing contracts, MCP surface, and capability discovery. It is a practical guide for debugging machine-facing payloads and for keeping UI actions behind existing ThreadVault modules.

It also records the MCP stdio surface used by Codex, ZCode, OpenCode, and other MCP-capable local agents. The MCP surface reuses ThreadVault's JSON contracts and read-only query semantics; it does not parse Codex transcripts, create databases, run migrations, or write files.

## Interface Discovery

`threadvault capabilities --json` and `threadvault robot-docs guide --json` expose the active interface policy:

| Field | Meaning |
|---|---|
| `interface_policy.primary_local_interface` | `native_desktop`; the personal-only 2.x UI line. |
| `interface_policy.primary_command` | `threadvault desktop launch`. |
| `interface_policy.primary_smoke_command` | `threadvault desktop smoke --json`. |

The primary local interface does not require a browser, server, WebView, Electron, React, Tauri, or a frontend build pipeline.

## MCP Stdio Interface

ThreadVault exposes a local MCP server:

```powershell
threadvault mcp manifest --json
threadvault mcp serve
```

The transport is stdio and the server speaks JSON-RPC MCP lifecycle/tool methods. The first tool set is deliberately read-only:

| MCP Tool | Store Method / Module | Purpose | Writes? |
|---|---|---|---|
| `threadvault_capabilities` | MCP runtime + capability contracts | Discover commands, JSON contracts, and feature flags. | No |
| `threadvault_stats` | MCP read-only runtime | Read archive counts and clean-index diagnostics. | No |
| `threadvault_doctor` | MCP read-only runtime | Run DB, FTS, and optional local-debug discovery diagnostics. | No |
| `threadvault_retrieve` | MCP read-only runtime | Return agent-facing retrieval results for historical context. | No |
| `threadvault_session` | MCP read-only runtime | Return session summary, evidence, and event previews. | No |
| `threadvault_export_preview` | MCP read-only runtime | Preview Markdown/Obsidian/Skill output without writing files. | No |

MCP clients should use `threadvault_export_preview` to inspect planned output and then ask the user to run an explicit `threadvault export-target ...` command if files should be written. This keeps Obsidian/Skill export gates visible and avoids silent writes from an agent tool call.

For concrete Codex, OpenCode, ZCode, Obsidian, and AI self-configuration guidance, see `docs/MCP_INTEGRATION.md`.

Codex registration uses the supported CLI surface:

```powershell
codex mcp add threadvault -- <threadvault-exe> mcp serve --db <archive-db>
codex mcp list
```

MCP startup may require a new Codex task after configuration changes. It remains independent from automatic ingestion: MCP reads the existing database, while a user-level `Stop` hook updates that database.

## Codex Hook And Ingestion Contracts

`threadvault codex-hook ingest --apply` consumes the Codex hook JSON object from stdin. It records an `ingestion_queue` request and imports only `transcript_path`; the normal hook response remains `{"continue": true}` so archive failures do not interrupt the Codex turn.

`threadvault codex-hook install` is dry-run-first. With `--apply`, it idempotently adds one ThreadVault `Stop` handler to `~/.codex/hooks.json`, preserves unrelated hook handlers, and reports that Codex trust review is required. The generated/installed hook uses the supported `Stop` input fields `session_id`, `transcript_path`, `cwd`, and `hook_event_name`.

### MCP联动计划书

目标：让 ThreadVault 成为本机 agent 记忆中枢，而不是让 Codex、ZCode、OpenCode、Obsidian 各自重新解析会话文件。

实施阶段：

1. `0.34.0` 提供 MCP stdio read-only 工具集，覆盖检索、会话详情、诊断、能力发现和导出预览。
2. `2.1.0` 已提供 Codex hook 的 dry-run/apply installer，并通过 `codex mcp add` 完成本机 MCP 注册。
3. `2.2.0` 新增 `storage` 命令组；MCP 仍保持只读，普通检索不直接暴露冷库文件路径。
4. `2.3.0` 新增 `storage auto --apply`，由单一策略自动选择、验证和保留备份档位。
5. `2.4.0` 的桌面 `desktop_app.v2` 把智能备份状态和预览后确认导出接入同一个 `DesktopDataGateway`；MCP 仍只读。
6. 后续可增加统一的 `threadvault integrations doctor`，检查 Codex/ZCode/OpenCode/Obsidian 是否能看到 MCP、hook 或导出目录。
7. 后续若考虑受控 MCP 写工具，必须保留 preview、privacy 和 confirm gate；2.x 默认仍为只读 MCP。

各工具建议：

| Tool | Recommended Link | Notes |
|---|---|---|
| Codex | MCP stdio server plus targeted Codex `Stop` hook import. | Hook 只导入当前 transcript，不做全目录重扫描；MCP 负责读历史。 |
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
| Storage lifecycle | `storage audit`, `storage rebuild`, `storage verify`, `storage event`, `storage prune`, `storage backup`, `storage verify-backup`, `storage auto` | Rebuild/prune/manual backup require explicit apply or targets; smart backup writes only with `--apply`. |
| Audit/schema/docs | `audit_*`, `schemas_*`, `validate_json`, `robot_docs_*`, `capabilities` | Schema writes create/update local schema files. |

### Storage JSON contracts

- `storage_audit`: hot bytes, event composition, storage classes, cold totals, and policy description.
- `storage_rebuild`: source/target paths, byte reduction, event counts, conversation digest, doctor, and cold validations.
- `storage_verify`: blob counts, missing/invalid totals, bytes, and deep-check status.
- `storage_event`: one event with its original cold payload hydrated.
- `storage_prune`: dry-run/apply result for unreferenced metadata and files.
- `storage_backup` / `storage_backup_verify`: Core/Evidence/Forensic manifest and verification results.
- `storage_auto`: dry-run or applied smart decision with `action`, selected `profile`, reason, logical archive state, disk guard, verification, and retention results. `action` is `backup`, `created`, `skip`, `blocked`, or a verification failure state.

## Export Workflow API

The UI export flow is intentionally multi-step:

```text
choose session/profile/privacy
  -> desktop or CLI client_export_preview
  -> user reviews planned files and privacy summary
  -> desktop confirms the immutable DesktopExportPlan, or CLI explicitly invokes export_target_*
  -> output files and manifest are written
```

If session, profile, privacy mode, or output path changes, the desktop invalidates the old `DesktopExportPlan`. `DesktopDataGateway.execute_export` rejects blocked/non-executable plans, and the Tk layer additionally requires a native confirmation. CLI export commands remain explicit write commands rather than claiming a cross-process preview token.

## Desktop Contract Notes

- Human-readable Chinese summaries are rendered in the native desktop app while CLI JSON remains machine-readable.
- Session event previews use `text_preview` first, then fallback fields.
- Long operations run outside the Tk main thread and report running/done/failed states.
- Write operations keep backend preview, verification, and confirmation gates even when the desktop button is disabled or guarded.

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
