# Progress

## Current Stage

ThreadVault is now on the personal-only `2.4.2` line. The native Tkinter app is the primary local interface; MCP is a local read-only stdio interface. Active team mode, governance/identity/policy contracts, the shared HTTP server prototype, and former browser UI runtime are absent from the package. Their v3/v4 records remain archived historical evidence.

The project-local hot archive remains `data/threadvault.db`, with overrides through `--db`, `THREADVAULT_DB`, and `[storage].archive_db`. Bulky reversible evidence now lives in sibling `data/threadvault-cold`; FTS continues to use cleaned `events.indexed_text`.

Core structure remains personal-only and modular. MCP is split into transport/dispatch (`mcp.py`), read-only execution (`mcp_runtime.py`), and validation (`mcp_validation.py`). New archive-freshness and Codex-configuration responsibilities live in `source_sync.py` and `codex_integration.py`; store, CLI, and desktop layers remain shallow adapters for those workflows.

Database schema v8 adds hot/cold event metadata, content-addressed blobs, exact assistant-body deduplication, and copy-on-write migration. The real archive currently has 404 sessions, 939,614 events, 3,904 turns, seven genuine incomplete function-call warnings, and equal event/FTS counts. Deep verification found 98,913 cold blobs (3.681 GB stored) with zero missing or invalid references.

Automatic ingestion now has two layers: a user-level Codex `Stop` hook imports only the transcript named by each event, while `storage sync` and smart backup compare the full discoverable source set with import provenance and target only stale files. Smart backup blocks if catch-up fails. `codex status/install` configures and diagnoses the exact Hook and read-only MCP registration together.

Development now uses an isolated `.venv`. The project environment passes `pip check`; unrelated missing dependencies in the global Selenium/Trio installation are outside ThreadVault's dependency graph.

## Recently Completed

- Bumped to `2.4.2` after the first public matrix exposed Typer 0.27.0/Python 3.11 CLI incompatibility; bounded Typer below 0.27 without rewriting the v2.4.1 tag.
- Added source freshness and targeted catch-up, catch-up-first smart backup, combined Codex Hook/MCP setup, generated contracts, and desktop one-click integration.
- Registered the exact read-only ThreadVault MCP entry and caught the live archive up while Codex was active; created and deeply verified a new Evidence backup.
- Added Windows Python 3.11/3.12 CI with ruff, 70% branch coverage, isolated desktop smoke, and MCP manifest gates.
- Reproduced and fixed an empty rendered desktop caused by Treeview state handling; added live Tk and Windows file-lock regressions.
- Bumped package version to `2.4.1` and turned the desktop shell into a restrained workbench: a clear archive/search/open/export/backup path, centralized Tk native styling, themed confirmation/menu surfaces, and stable in-place table refreshes.
- Kept every archive snapshot fresh while caching only friendly Codex title metadata behind SQLite/WAL/SHM signatures; unchanged table refreshes retain selection, focus, and scroll without row mutations.
- Stopped current-schema initialization from rewriting its metadata and isolated default archive DB, Codex home, config, and restore history across the test suite.
- Prepared the public `v2.4.0` release with standalone switchable English/Chinese manuals, cumulative 2.x release notes, acceptance evidence, and explicit private-artifact boundaries.
- Bumped package version to `2.4.0` and completed the foolproof desktop workflow: friendly session tables, smart Backup Center, confirmed export, safe restore defaults, automatic health summaries, path pickers, scrolling, focus, and Chinese labels.
- Bumped package version to `2.3.0` and added one-command smart backup selection, verification, disk guards, last-run status, and bounded automatic retention.
- Bumped package version to `2.2.0`, implemented the hot/cold lifecycle, migrated the live archive, and verified Core/Evidence backups.
- Bumped package version to `2.1.0` and connected targeted per-turn Codex archiving plus MCP registration.
- Added supported parsing for current Codex world/inter-agent metadata without polluting the clean search index.
- Reclassified repeated `session_meta` records as valid collaborative provenance rather than parser warnings.
- Bumped package version to `2.0.0`, removed active team/governance/shared-server surfaces, and retained personal safety gates.
- Split and hardened MCP transport, validation, and read-only query execution.
- Added compacted-event parsing plus schema v6 repair of 89 stale warnings in the real local archive.
- Removed stale `~hreadvault-*` metadata and established a clean project `.venv` workflow.
- Improved Chinese personal UI interaction quality.
- Fixed session detail event preview rendering.
- Added readable timestamps and role labels in session detail tables.
- Added real export preview gating for frontend write actions.
- Added Chinese export summaries while preserving raw JSON output.
- Verified local export and backup write paths.
- Fixed completed activity feedback so completed actions stop spinner animation and show a stable done state.
- Added `CONTEXT.md` canonical vocabulary.
- Expanded `docs/KNOWLEDGE_GRAPH.md` into a full entity, relationship, flow, and safety-boundary map.
- Expanded standard docs for architecture, API, database, development, rules, document index, and usage.
- Migrated legacy `docs/v0` through `docs/v4` and `docs/development-progress.md` into `docs/progress/archive/` after user confirmation, then removed the old locations.
- Added project-local archive DB path resolution and configurable archive DB overrides.
- Bumped package version from `0.31.0` to `0.32.0` and documented versioning rules.
- Added clean knowledge indexing for Codex archive events.
- Bumped package version from `0.32.0` to `0.33.0` and database schema version from `4` to `5`.
- Upgraded `<python-env>` from Python `3.9.20` to Python `3.12.13` and reinstalled project dev dependencies.
- Added `threadvault mcp manifest` and `threadvault mcp serve` for MCP stdio integration.
- Added `docs/MCP_INTEGRATION.md` with concrete MCP setup snippets and AI self-configuration rules.
- Added open-source release guardrails: `SECURITY.md`, `CONTRIBUTING.md`, `.env.example`, local artifact ignore rules, and `docs/progress/releases/v0.34.0/`.
- Bumped package version from `0.34.0` to `0.35.0` and optimized Codex Skill candidate exports for progressive reference loading.
- Bumped package version from `0.35.0` to `0.36.0` and refreshed the personal UI navigation for MCP/AI reuse workflows.
- Bumped package version from `0.36.0` to `0.37.0` and compacted the personal UI visual density across all pages.
- Bumped package version from `0.37.0` to `0.38.0` and added the first native desktop app migration slice over existing safe client contracts.
- Bumped package version from `0.38.0` to `0.39.0` and migrated data-safety/maintenance actions into the native desktop app with confirmation prompts.
- Bumped package version from `0.39.0` to `0.40.0` and migrated advanced read-only Schema, Robot Docs, and Governance panels into the native desktop app.
- Bumped package version from `0.40.0` to `0.41.0` and added conservative native desktop restore apply for new target databases.
- Bumped package version from `0.41.0` to `0.42.0` and added native desktop schema write with confirmation.
- Bumped package version from `0.42.0` to `0.43.0` and added native desktop governance diagnostics aggregation.
- Bumped package version from `0.43.0` to `0.44.0` and hardened native desktop Tk thread safety after runtime QA.
- Bumped package version from `0.44.0` to `0.45.0` and added a non-window native desktop smoke command.
- Bumped package version from `0.45.0` to `0.46.0` and added a native desktop Windows launcher script.
- Bumped package version from `0.46.0` to `0.47.0` and marked the Web UI launcher as a legacy fallback with desktop-first guidance.
- Bumped package version from `0.47.0` to `0.48.0` and aligned capabilities, robot docs, project rules, and active docs around native desktop as the primary 1.0.0 local interface.
- Bumped package version from `0.48.0` to `0.49.0` and retired active Web UI CLI commands plus the browser launcher path.
- Bumped package version from `0.49.0` to `1.0.0`, removed the active personal Web UI runtime, schemas, and tests, and added v1.0.0 release records.
- Bumped package version from `1.0.0` to `1.0.1`, removed the remaining old Web UI launcher/readiness test, and cleaned Web UI retired metadata out of active discovery.

## Current Validation

Latest validation for the complete `2.4.2` release baseline:

```powershell
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m pytest --cov=threadvault --cov-report=term-missing
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\threadvault.exe desktop smoke --db <temporary-db> --json
```

Current result: `311 passed, 1 skipped` with `74.88%` branch coverage; source/test ruff, `compileall`, `pip check`, generated schemas, isolated `desktop_smoke.v2`, and the six-tool read-only MCP manifest passed. Rendered Windows QA covered real sessions, Backup Center, Codex Integration, focus/scroll/disabled states, and confirmed actions; the reproduced empty-window regression was fixed. Live doctor reports schema v8, 404 sessions, 939,614 events, seven warnings, FTS 939,614/939,614, and no maintenance suggestion. Deep cold verification reports 98,913 blobs with zero missing or invalid references. The exact Hook and MCP configs match; current Hook trust/coverage still requires Codex-owned `/hooks` review and the next Stop event.

Detailed pre-2.x validation remains in the corresponding round and release records. Those historical snapshots describe the state at their original version and are not the current runtime baseline.

## Recent Development Trace

- `docs/progress/rounds/2026-07-03-round-001-personal-ui-interaction-fix.md`
- `docs/progress/rounds/2026-07-03-round-002-documentation-completeness.md`
- `docs/progress/rounds/2026-07-06-round-001-project-local-archive-db.md`
- `docs/progress/rounds/2026-07-06-round-002-clean-knowledge-index.md`
- `docs/progress/rounds/2026-07-06-round-003-mcp-stdio-server.md`
- `docs/progress/rounds/2026-07-06-round-004-mcp-integration-guide.md`
- `docs/progress/rounds/2026-07-06-round-005-open-source-v034-release.md`
- `docs/progress/rounds/2026-07-06-round-006-lightweight-skill-export.md`
- `docs/progress/rounds/2026-07-06-round-007-personal-ui-ia-refresh.md`
- `docs/progress/rounds/2026-07-06-round-008-compact-ui-density.md`
- `docs/progress/rounds/2026-07-06-round-009-native-desktop-app.md`
- `docs/progress/rounds/2026-07-06-round-010-native-desktop-safety-actions.md`
- `docs/progress/rounds/2026-07-06-round-011-native-desktop-advanced-read-panels.md`
- `docs/progress/rounds/2026-07-06-round-012-native-desktop-restore-apply.md`
- `docs/progress/rounds/2026-07-06-round-013-native-desktop-schema-write.md`
- `docs/progress/rounds/2026-07-06-round-014-native-desktop-governance-diagnostics.md`
- `docs/progress/rounds/2026-07-06-round-015-native-desktop-thread-safety.md`
- `docs/progress/rounds/2026-07-06-round-016-native-desktop-smoke-command.md`
- `docs/progress/rounds/2026-07-06-round-017-native-desktop-launcher.md`
- `docs/progress/rounds/2026-07-06-round-018-desktop-first-launcher-guidance.md`
- `docs/progress/rounds/2026-07-06-round-019-native-ui-major-release-gate.md`
- `docs/progress/rounds/2026-07-06-round-020-native-first-capability-alignment.md`
- `docs/progress/rounds/2026-07-06-round-021-web-ui-command-retirement.md`
- `docs/progress/rounds/2026-07-06-round-022-v100-native-desktop-release.md`
- `docs/progress/rounds/2026-07-06-round-023-remove-web-ui-residue.md`
- `docs/progress/rounds/2026-07-13-round-001-personal-only-modularization.md`
- `docs/progress/rounds/2026-07/2026-07-28-round-001-native-desktop-workbench.md`
- `docs/progress/rounds/2026-07/2026-07-29-round-001-foolproof-archive-integration.md`
- `docs/progress/releases/v0.34.0/`
- `docs/progress/releases/v1.0.0/`
- `docs/progress/releases/v1.0.1/`
- `docs/progress/releases/v2.4.1/`
- `docs/progress/releases/v2.4.2/`

## Risks

- Archived legacy documentation intentionally preserves older architecture and terminology as historical evidence.
- Local databases, cold blobs, exports, backups, and generated output can contain private data and must remain ignored local artifacts.
- Codex must be restarted after a new/changed MCP registration, and non-managed Hook trust remains a Codex-owned exact-command review through `/hooks`.
- The active transcript may appear pending between messages; its Stop hook or the next smart-backup catch-up closes that temporary gap.
- Native OS file pickers remain platform-owned and therefore retain the operating system theme.
- Tkinter keyboard and visible-label accessibility passed rendered QA, but a full NVDA narration pass remains a non-blocking follow-up.

## Next Steps

- Keep the personal-only boundary explicit when adding future commands or contracts.
- Consider adding an "open export directory" helper after designing a safe local-only route.
- Consider extending the proven dry-run/apply installer pattern to ZCode, OpenCode, and Obsidian after their client configuration surfaces stabilize.
