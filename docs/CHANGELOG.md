# Changelog

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
