# Changelog

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
