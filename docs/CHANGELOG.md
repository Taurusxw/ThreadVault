# Changelog

## 2026-07-29 - 2.4.2 Deterministic Windows CI Hotfix

- Neutralized GitHub Actions' forced ANSI styling inside `CliRunner` tests so CLI content assertions are independent of escape-code placement on Python 3.11 and 3.12.
- Kept the real isolated desktop-smoke and MCP-manifest steps in the native GitHub Actions environment.
- Preserved the immutable v2.4.1 tag and published the compatibility correction as a separate patch release.

## 2026-07-29 - 2.4.1 Foolproof Archive Integration And Native Desktop Polish

- Added read-only source freshness inspection and targeted catch-up for missing, changed, stale-parser, or newly touched Codex transcripts across active and archived session directories.
- Changed smart backup to catch up sources before tier selection and block when catch-up fails, preventing a verified but known-stale database backup.
- Added dry-run-first `threadvault codex status/install` commands that pin and diagnose the supported user Stop hook and read-only Codex MCP registration together.
- Added a confirmed one-click Codex integration action and source-freshness status to the native desktop workbench and Backup Center.
- Added a Windows GitHub Actions matrix with ruff, branch coverage (70% gate), isolated desktop smoke, and MCP manifest checks.
- Fixed a real rendered-startup regression where Treeview widgets were treated as stateful inputs, leaving the window empty, and added a live Tk initial-refresh regression test.
- Fixed SQLite read-only connection lifetimes so Windows retention and verified-backup cleanup do not leave database files locked.

- Reframed the native desktop app around the daily archive/search/open/export/backup path with a compact identity header, one primary action per work area, and a discoverable secondary-actions menu.
- Added one semantic Tk visual system for ttk controls, `Text` surfaces, popup menus, confirmation dialogs, tree selections, scrollbars, disabled states, and progress feedback; native OS file pickers remain platform-owned.
- Replaced full Treeview teardown/rebuild refreshes with in-place reconciliation that preserves selection, focus, and scroll position and visibly reports whether rows changed.
- Reused friendly Codex state titles only while the local state SQLite database and WAL/SHM signatures are unchanged; archive snapshots remain fresh and no persistent cache was added.
- Avoided rewriting the current `schema_version` metadata on every `init_db()` call while preserving missing/stale-version repair behavior.
- Explicitly close SQLite backup connections so automatic retention can remove superseded temporary backups reliably on Windows.
- Isolated default archive DB, Codex home, config, and restore-history paths for the test suite in pytest temporary directories so routine verification does not touch ignored live runtime data.

## 2026-07-14 - 2.4.0 Foolproof Native Desktop Workflows

- Replaced raw session identifiers with scrollable title/project/time tables and warning badges, using read-only Codex state only for friendly title enrichment.
- Added a first-class Backup Center that shows automatic schedule, next run, disk guard, selected tier, retention policy, and a one-click smart-backup action over the existing storage policy.
- Completed native export as preview, privacy review, immutable plan validation, explicit confirmation, and actual file writing with a manifest.
- Defaulted restore to a collision-free new database filename and kept overwrite refusal.
- Made health diagnostics load automatically, separated maintenance actions, added directory/file pickers, keyboard shortcuts, visible focus, scrollbars, Chinese labels, and background progress feedback.
- Bumped desktop contracts to `desktop_app.v2` and `desktop_smoke.v2`, with capability and robot-guide discovery for the new workflows.
- Published the complete personal-only 2.x baseline with separate English and Simplified Chinese project manuals and v2.4.0 release acceptance records.

## 2026-07-14 - 2.3.0 Foolproof Smart Backups

- Added `threadvault storage auto` as the single normal backup entrypoint with dry-run and explicit apply modes.
- Added automatic bootstrap Evidence, daily Core, weekly Evidence, and monthly Forensic selection; only the highest due changed tier runs.
- Added logical change detection, a 5 GiB free-space reserve, post-create verification, a cross-process lock, and a machine-readable last-run record.
- Added bounded automatic retention (Core 3, Evidence 2, Forensic 1) without deleting manual backups or unique live archive content.
- Added the `storage_auto` JSON Schema and regression coverage for selection, unchanged skips, retention, disk blocking, and CLI contract validation.

## 2026-07-14 - 2.2.0 Hot/Cold Archive Lifecycle

- Added schema v8 event storage metadata and immutable content-addressed cold blobs.
- Kept canonical human conversation and the clean FTS index hot while externalizing compacted history, large tool output, patches, metadata payloads, and image assets.
- Removed exact duplicate agent-message bodies and stopped repeating message/token bodies in `turns`.
- Added copy-on-write storage audit/rebuild/verify/event/prune workflows with conversation-digest acceptance.
- Added Core, Evidence, and Forensic backup profiles plus deep verification.
- Migrated the real archive from 5.293 GiB to about 1.16 GiB hot storage, retained cold evidence, and completed an incremental catch-up with zero import failures.

## 2026-07-13 - 2.1.0 Automatic Codex Archiving

### Version

- Bumped package version from `2.0.0` to `2.1.0` for a new user-visible automatic ingestion workflow and current Codex event compatibility.
- Kept JSON contract `2.0` and bumped database schema from v6 to v7 for the idempotent parser-warning taxonomy migration; no stored columns changed.

### Changed

- Added targeted single-transcript import for Codex `Stop` hooks, so each completed turn can update the archive without rescanning the full Codex home.
- Added idempotent, dry-run-first `threadvault codex-hook install`; `--apply` writes the supported user-level `~/.codex/hooks.json` while preserving unrelated hooks.
- Kept queue history for hook ingestion and records each applied request as `completed` or `failed`.
- Recognized `world_state` and `inter_agent_communication_metadata` as supported metadata that remains in the raw archive but is excluded from the clean text index.
- Accepted repeated `session_meta` records as valid parent/subagent provenance instead of emitting duplicate warnings.
- Fixed collaborative transcript identity so `session_meta.id` is the archived child/thread id while `session_id` remains parent provenance; unchanged files are automatically reprocessed when `parse_version` advances.
- Documented and installed the ThreadVault read-only MCP server through the official `codex mcp add` workflow.

### Validation

- Full rebuild snapshot imported all 320 discovered JSONL files and processed 790,799 events with seven genuine `missing_function_call_output` warnings and no unknown-event warnings; a final incremental catch-up then scanned 326 active transcripts and completed with zero failures.
- Full validation and live integration evidence are recorded in `docs/progress/rounds/2026-07-13-round-002-automatic-ingestion-and-codex-integration.md`.

## 2026-07-13 - 2.0.0 Personal-Only Runtime

### Version

- Bumped package version from `1.0.1` to `2.0.0` because active team/governance/shared-server commands and JSON contracts were intentionally removed.
- Bumped the base JSON contract marker from `1.0` to `2.0`.
- Bumped database schema version from `5` to `6` for the compacted-event compatibility migration.

### Changed

- Removed the active governance module, shared HTTP server prototype, governance CLI tree, desktop governance panels, config fields, JSON schemas, and associated tests.
- Preserved personal privacy scan, export preview, explicit confirmation, backup verification, conservative restore, and read-only MCP safety gates.
- Reduced the former large store/CLI/schema surfaces and split MCP transport, validation, and read-only query execution into focused modules.
- Added strict JSON-RPC lifecycle/request validation, tool input-schema enforcement, read-only SQLite/query-only access, path redaction, and non-creating missing-DB behavior to MCP.
- Added native support for Codex `compacted` records and an idempotent v6 migration for 89 stale `unknown_current_type` records in the existing local archive.
- Removed stale `~hreadvault-*` distribution metadata and documented a project `.venv` workflow that isolates ThreadVault from unrelated global Selenium/Trio dependency warnings.

### Validation

- Focused and full validation is recorded in `docs/progress/rounds/2026-07-13-round-001-personal-only-modularization.md`.

## 2026-07-06 - 1.0.1 Web UI Residue Removal

### Version

- Bumped package version from `1.0.0` to `1.0.1`.

### Changed

- Removed the remaining old Chinese Web UI launcher from the active tree.
- Removed the legacy Web UI readiness test from the active test suite.
- Removed Web UI retired-interface metadata from capabilities and robot docs.
- Updated current docs so native desktop discovery is the only active local UI path.

### Validation

- Focused validation is recorded in `docs/progress/rounds/2026-07-06-round-023-remove-web-ui-residue.md`.

## 2026-07-06 - 1.0.0 Native Desktop Release

### Version

- Bumped package version from `0.49.0` to `1.0.0`.
- Bumped the base JSON contract marker from `0.8` to `1.0`.

### Changed

- Made the native Tkinter desktop app the 1.0.0 primary local interface.
- Removed the active `threadvault.personal_ui` runtime module.
- Removed active `personal_ui_health`, `personal_ui_action`, and `personal_ui_smoke` schema registrations and generated artifacts.
- Removed active Web UI runtime tests; v4 Web UI records remain under `docs/progress/archive/legacy-v4/`.
- Updated capabilities and robot docs to point retired browser Web UI evidence to the legacy-v4 archive.

### Validation

- Release validation is recorded in `docs/progress/releases/v1.0.0/ACCEPTANCE.md`.

## 2026-07-06 - 0.49.0 Web UI Command Retirement

### Version

- Bumped package version from `0.48.0` to `0.49.0`.

### Changed

- Retired `threadvault ui serve` and `threadvault ui smoke` from the active CLI.
- Changed capabilities and robot docs so `personal_web_ui` is reported as retired rather than fallback.
- Moved former Web UI commands into `retired_commands` metadata only.
- Changed `启动ThreadVault中文界面.cmd` so it no longer starts a browser or local Web UI server; it redirects to the desktop launcher.
- Bumped the base capabilities/robot schema contract marker from `0.7` to `0.8` for the retired-interface discovery change.

### Validation

- Focused Web UI retirement and desktop tests passed: `33 passed`.

## 2026-07-06 - 0.48.0 Native-First Capability Alignment

### Version

- Bumped package version from `0.47.0` to `0.48.0`.

### Changed

- Added `interface_policy` to capabilities and robot docs so `native_desktop` is discoverable as the primary local interface for the 1.0.0 migration.
- Bumped the base capabilities/robot schema contract marker from `0.6` to `0.7` for the new required discovery field.
- Moved legacy Web UI commands out of robot-doc recommended commands and into `legacy_fallback_commands`.
- Updated project rules and active docs to treat the Tkinter desktop app as the primary local interface and the browser Web UI as a legacy fallback.

### Validation

- Expanded related capabilities/Web UI/desktop/Skill regression passed: `51 passed`.
- Focused ruff passed for the changed store/schema/CLI/test surface.
- CLI smoke confirmed native desktop primary discovery and Web UI legacy fallback commands.

## 2026-07-06 - Native Desktop UI Major Release Gate

### Added

- Added a release gate: once the native desktop UI is complete enough to replace the browser Web UI as the primary local interface, the next release should advance the package major version instead of continuing the `0.x` line.

### Version

- No package version bump; this records a future release gate and does not change runtime behavior.

## 2026-07-06 - 0.47.0 Desktop-First Launcher Guidance

### Version

- Bumped package version from `0.46.0` to `0.47.0`.

### Changed

- Updated `启动ThreadVault中文界面.cmd` to identify itself as the legacy browser fallback.
- The legacy Web UI launcher now recommends `启动ThreadVault桌面版.cmd` as the daily entrypoint.

### Validation

- Expanded related regression tests passed: `46 passed`.
- Focused ruff passed for the desktop, CLI/store, Web UI compatibility, export, and related test surface.

## 2026-07-06 - 0.46.0 Native Desktop Launcher Script

### Version

- Bumped package version from `0.45.0` to `0.46.0`.

### Added

- Added `启动ThreadVault桌面版.cmd` as a double-click native desktop launcher.
- The launcher runs `desktop smoke --json` before starting `desktop launch` and does not start a browser or Web UI server.

### Validation

- Desktop smoke CLI returned `ok: true`.
- Expanded related regression tests passed: `46 passed`.
- Focused ruff passed for the desktop, CLI/store, Web UI compatibility, export, and related test surface.

## 2026-07-06 - 0.45.0 Native Desktop Smoke Command

### Version

- Bumped package version from `0.44.0` to `0.45.0`.

### Added

- Added `threadvault desktop smoke --json` for non-window desktop runtime verification.
- Added a `desktop_smoke.v1` payload covering Tkinter availability, no-browser/no-server boundaries, gateway snapshot loading, and integration/advanced diagnostics.

### Validation

- Desktop smoke CLI was run against a fixture-backed temporary database and returned `ok: true`.
- Expanded related regression tests passed: `45 passed`.
- Focused ruff passed for the desktop, CLI/store, Web UI compatibility, export, and related test surface.

## 2026-07-06 - 0.44.0 Native Desktop Thread Safety

### Version

- Bumped package version from `0.43.0` to `0.44.0`.

### Fixed

- Moved Tkinter variable reads out of background worker lambdas and into the main UI thread before dispatch.
- Deferred initial desktop refresh with `root.after(0, ...)` instead of starting background loading during construction.
- Added an empty-state message in the native desktop search-results list before a query is entered.
- Split Advanced-tab controls across compact rows so governance buttons no longer overflow the window.

### Validation

- Runtime QA launched the native Tk window, exposed the original `main thread is not in main loop` worker issue, captured Windows hwnd screenshots after the fix, and verified the Advanced tab layout at `860x520`.
- Expanded related regression tests passed: `44 passed`.
- Focused ruff passed for the desktop, CLI/store, Web UI compatibility, export, and related test surface.

## 2026-07-06 - 0.43.0 Native Desktop Governance Diagnostics

### Version

- Bumped package version from `0.42.0` to `0.43.0`.

### Added

- Added a native desktop governance diagnostics panel that aggregates status, enforcement gaps, policy/server readiness, central audit/policy/backup readiness, identity readiness, and v3 completion gap checks.
- Added desktop data coverage for the governance diagnostics aggregation.

### Validation

- Expanded related regression tests passed: `43 passed`.
- Focused ruff passed for the desktop, CLI/store, Web UI compatibility, export, and related test surface.

## 2026-07-06 - 0.42.0 Native Desktop Schema Write

### Version

- Bumped package version from `0.41.0` to `0.42.0`.

### Added

- Added native desktop schema write with an explicit output directory and confirmation prompt.
- Added desktop data coverage for writing packaged JSON Schema files.

### Validation

- Expanded related regression tests passed: `43 passed`.
- Focused ruff passed for the desktop, CLI/store, Web UI compatibility, export, and related test surface.

## 2026-07-06 - 0.41.0 Native Desktop Restore Apply

### Version

- Bumped package version from `0.40.0` to `0.41.0`.

### Added

- Added native desktop restore apply for verified backups restored into new, non-overwrite target databases.
- Added a desktop restore confirmation prompt and target-exists refusal before calling the restore workflow.
- Added desktop data coverage for successful restore apply and refused overwrite attempts.

### Validation

- Expanded related regression tests passed: `42 passed`.
- Focused ruff passed for the desktop, CLI/store, Web UI compatibility, export, and related test surface.

## 2026-07-06 - 0.40.0 Native Desktop Advanced Read Panels

### Version

- Bumped package version from `0.39.0` to `0.40.0`.

### Added

- Added native desktop advanced read-only panels for JSON Schemas, robot docs, and governance status.
- Added desktop gateway methods for schema summaries, robot usage guidance, and local governance status.
- Added Advanced-tab controls for reading a named schema, robot docs, and governance status without opening the Web UI.

### Validation

- Expanded related regression tests passed: `42 passed`.
- Focused ruff passed for the desktop, CLI/store, Web UI compatibility, export, and related test surface.

## 2026-07-06 - 0.39.0 Native Desktop Data Safety Actions

### Version

- Bumped package version from `0.38.0` to `0.39.0`.

### Added

- Added native desktop data-safety actions for local backup, backup verification, and read-only restore planning.
- Added native desktop maintenance actions for FTS reindex and SQLite vacuum.
- Added native confirmation prompts before backup, reindex, and vacuum write operations.

### Changed

- Expanded the desktop data gateway so the Tkinter UI uses a single desktop-facing interface for archive, export preview, warnings, MCP, health, backup, restore planning, and maintenance.

### Validation

- Expanded related regression tests passed: `41 passed`.
- Focused ruff passed for the desktop, CLI/store, Web UI compatibility, export, and related test surface.

## 2026-07-06 - 0.38.0 Native Desktop App Slice

### Version

- Bumped package version from `0.37.0` to `0.38.0`.

### Added

- Added `threadvault desktop launch` for a minimal native Tkinter desktop app.
- Added `desktop_data.py` as a desktop-facing data interface over existing `ArchiveStore` client contracts.
- Added compact native tabs for browse/search/session summary, export preview, safety warnings, MCP integration, health diagnostics, and advanced command reference.
- Added background worker loading for desktop actions so long archive/search/export/safety reads do not block the Tk main thread.

### Changed

- Robot/capabilities discovery now advertises the native desktop app, launch command, toolkit, and no-browser/no-server requirements.

### Validation

- Focused desktop, personal UI readiness/workbench/localization, local UI discovery, and Skill export tests passed: `40 passed`.
- Focused ruff passed for the desktop modules, CLI/store discovery, and related tests.

## 2026-07-06 - 0.37.0 Compact Personal UI Density

### Version

- Bumped package version from `0.36.0` to `0.37.0`.

### Changed

- Updated the personal Web UI to a compact desktop-tool visual style inspired by small native utility windows.
- Reduced global spacing, panel padding, heading scale, table row height, and navigation width.
- Standardized compact control height, low-radius borders, and flatter panels across Basic and Pro modes.
- Kept the existing static no-build frontend architecture and all privacy/export safety gates.

### Validation

- Ruff passed for the touched personal UI and localization test surface.
- Static checks confirmed the compact CSS tokens and `0.37.0` version metadata in source files and docs.
- `APP_JS` syntax validation passed through Node.
- Focused pytest was attempted in the current restricted runtime, but collection was blocked because the available Python environments lack `attrs` / cannot execute the project Python launcher.

## 2026-07-06 - 0.36.0 Personal UI Information Architecture

### Version

- Bumped package version from `0.35.0` to `0.36.0`.

### Changed

- Simplified the professional personal UI navigation from separate low-frequency control pages into eight ordered work areas: Archive, Search, Session, Integrations, Export, Data Safety, Health, and Advanced.
- Added an Integrations page that surfaces MCP setup commands, read-only safety boundaries, and agent-facing checks for Codex, ZCode, OpenCode, Obsidian, and MCP-capable clients.
- Updated Basic Mode to follow the daily workflow: find old work, open context, then reuse it through MCP setup or a lightweight Skill preview.
- Moved privacy plus backup/restore workflows into Data Safety, maintenance plus config into Health, and schema/governance diagnostics into Advanced.
- Updated Chinese localization for the refreshed UI structure.

### Validation

- Full pytest passed with `422 passed`.
- Full ruff passed for `src` and `tests`.
- Browser QA using local Chrome confirmed the refreshed Chinese UI has no horizontal overflow at desktop or mobile width.

## 2026-07-06 - 0.35.0 Lightweight Skill Candidate Export

### Version

- Bumped package version from `0.34.0` to `0.35.0`.

### Changed

- Changed `export-target skill` output into a lightweight Codex Skill candidate layout.
- Added `references/index.md` as the Skill packet map and reading-order entrypoint.
- Added per-session `references/session-SESSION_ID.md` detail files so Codex can load only relevant session context.
- Changed `references/evidence.md` from raw evidence blocks into a short-snippet evidence index with ThreadVault event IDs.
- Updated Skill preview planning so UI/client previews show the same lightweight reference layout before writing files.

### Validation

- Focused Skill export and client preview tests were updated for the new layout.

## 2026-07-06 - Open Source v0.34.0 Release Prep

### Added

- Added `SECURITY.md` with vulnerability reporting guidance and local data boundaries.
- Added `CONTRIBUTING.md` with development checks and privacy expectations.
- Added `.env.example` for optional local environment overrides.
- Added `docs/progress/releases/v0.34.0/` release notes, acceptance, and artifact guidance.

### Changed

- Expanded `.gitignore` guardrails for local databases, generated exports, backups, environment files, and private local output folders.
- Removed the legacy DOCX planning artifact from the current release tree.

### Version

- No package version bump; this round prepares the existing `0.34.0` runtime for public release.

## 2026-07-06 - MCP Integration Guide

### Added

- Added `docs/MCP_INTEGRATION.md` with setup snippets for Codex, OpenCode, ZCode, and Obsidian workflows.
- Added an AI self-configuration protocol for reading project docs, verifying the MCP manifest, and generating dry-run client config.

### Changed

- Linked the MCP integration guide from `README.md`, `docs/README.md`, `docs/DOC_INDEX.md`, `docs/API.md`, and `docs/THREADVAULT_USAGE_MANUAL.md`.

### Version

- No package version bump; this round only documents existing `0.34.0` MCP runtime behavior.

## 2026-07-06 - 0.34.0 MCP Stdio Server

### Version

- Bumped package version from `0.33.0` to `0.34.0`.

### Added

- Added `threadvault mcp manifest --json` for MCP server discovery and integration guidance.
- Added `threadvault mcp serve` as a stdio JSON-RPC MCP server.
- Added read-only MCP tools for capabilities, stats, doctor, agent retrieval, session detail, and export preview.
- Added `mcp_manifest` schema registration and robot/capabilities discovery entries.

### Changed

- Agent manifest now reports `mcp_runtime_included = true`.
- Architecture, API, knowledge graph, development, and Chinese usage docs now describe the MCP联动 plan for Codex, ZCode, OpenCode, and Obsidian.

### Validation

- Focused MCP/readiness pytest passed: `13 passed`.
- Focused ruff passed for MCP, CLI, schema, store, agent interface, and touched tests.
- `threadvault schemas write --out docs\schemas --json` wrote `docs/schemas/mcp_manifest.schema.json`.
- `threadvault mcp manifest --json` emitted a valid `mcp_manifest` payload.
- `threadvault validate-json --schema mcp_manifest --input <user-temp>\threadvault-mcp-manifest.json --json` passed.
- Stdio smoke for `threadvault mcp serve` returned MCP `initialize` and `tools/list` JSON-RPC responses.

## 2026-07-06 - 0.33.0 Clean Knowledge Index

### Version

- Bumped package version from `0.32.0` to `0.33.0`.

### Added

- Added a clean knowledge index layer with `events.indexed_text`, `events.index_policy`, and `events.value_level`.
- Added default indexing rules that skip empty/low-value machine events, metadata-only index inline binary/image evidence, and truncate oversized tool outputs.
- Added `search_index` diagnostics to stats payloads and doctor output.

### Changed

- Search and retrieval now use cleaned `indexed_text` by default while preserving raw `text_content` and `payload_json` for audit and exports.
- Bumped database schema version from `4` to `5`.

### Validation

- Migrated the real project-local archive database at `data/threadvault.db` to schema `5`.
- Verified `events_fts` uses `indexed_text` and remains count-aligned with `events` at 56,680 rows.
- Verified clean index diagnostics: 35,618 searchable events, 21,062 skipped events, 4,603 truncated events, 12 metadata-only events, and indexed text reduced from 54,625,653 raw characters to 18,340,385 indexed characters.
- `<python-env>` was upgraded from Python `3.9.20` to Python `3.12.13`, then project dev dependencies were reinstalled.
- `ruff` passed for the clean-index implementation and focused tests.
- Focused pytest passed: `24 passed`.

## 2026-07-06 - 0.32.0 Project-Local Archive DB

### Version

- Bumped package version from `0.31.0` to `0.32.0`.

### Changed

- Changed the default archive database location to the project-local `data/threadvault.db`.
- Added archive DB override support through `THREADVAULT_DB` and `[storage].archive_db`, while preserving per-command `--db`.
- Updated local UI health/path documentation so the shown index DB path reflects the effective archive database.
- Added project versioning rules for substantive optimization/development rounds.

### Validation

- Python 3.12 `py_compile` passed for touched config, CLI, UI, schema, version, and focused test files.
- Direct path-resolution smoke checks passed for project-local default, `THREADVAULT_DB`, and `[storage].archive_db`.
- Copied the existing local AppData archive database to `data/threadvault.db` and verified it contains 11 sessions, 56,680 events, 244 turns, 91 warnings, and 5 projects.
- `pytest` and `ruff` were not runnable in the available local interpreters because project dependencies were not installed in PATH-accessible environments.

## 2026-07-03

### Fixed

- Fixed personal UI session detail rendering so event previews use `text_preview` before fallback fields.
- Added readable local timestamp formatting and Chinese role labels in session event tables.
- Folded raw machine context summaries into a short human-readable UI note while preserving the raw JSON panel output.
- Fixed the export page preview gate so write actions are disabled until a matching export preview is generated.
- Prevented frontend export actions from hard-coding `preview_accepted: true`.
- Added export summary rendering for output paths, privacy finding counts, high-risk counts, and selected privacy mode.
- Preserved raw JSON output keys and detailed privacy findings in the debug panel.
- Fixed dangerous action cancellation so dismissing confirmation does not send a backend write request.
- Fixed completed UI activity feedback so "完成 / 导出已写入" no longer keeps the spinner animation running.

### Changed

- Added stronger Chinese UI localization checks for export, backup, restore, schema, and maintenance labels.
- Added JavaScript syntax checks for English and Chinese UI assets.
- Added standard project documentation entrypoints and round-level development traces.
- Added `CONTEXT.md` with canonical ThreadVault domain terms.
- Expanded `docs/KNOWLEDGE_GRAPH.md` into a detailed entity, relationship, data-flow, UI action, and safety-boundary map.
- Expanded standard docs for architecture, API, database, development, rules, progress, index, and Chinese usage.
- Migrated legacy `docs/v0` through `docs/v4` and `docs/development-progress.md` into `docs/progress/archive/` after user confirmation, then removed the old locations.

### Validation

- Focused UI pytest suite passed.
- Documentation-focused pytest checks passed.
- Served English and Chinese JavaScript assets passed `node --check` in the UI interaction round.
- Local personal UI health endpoint returned `ok` on `127.0.0.1:8766`.
- Browser verification confirmed completed export state stops spinner animation.
