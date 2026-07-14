# Progress

## Current Stage

ThreadVault is now on the personal-only `2.4.0` line. The native Tkinter app is the primary local interface; MCP is a local read-only stdio interface. Active team mode, governance/identity/policy contracts, the shared HTTP server prototype, and former browser UI runtime are absent from the package. Their v3/v4 records remain archived historical evidence.

The project-local hot archive remains `data/threadvault.db`, with overrides through `--db`, `THREADVAULT_DB`, and `[storage].archive_db`. Bulky reversible evidence now lives in sibling `data/threadvault-cold`; FTS continues to use cleaned `events.indexed_text`.

Core structure has been reduced and clarified: the former governance/shared-server modules were deleted, `store.py` is about 1,266 lines, `cli.py` about 1,927, and `schemas.py` about 1,803. MCP is split into transport/dispatch (`mcp.py`), read-only execution (`mcp_runtime.py`), and validation (`mcp_validation.py`).

Database schema v8 adds hot/cold event metadata, content-addressed blobs, exact assistant-body deduplication, and copy-on-write migration. The real archive was rebuilt with equal source/target counts and an identical canonical conversation digest, then incrementally caught up to 342 sessions and 835,177 events with seven genuine incomplete function-call warnings.

Automatic ingestion is now a supported, targeted path: a user-level Codex `Stop` hook records a queue item and imports only the transcript named by the hook payload. The hook installer is dry-run-first and preserves unrelated user hooks. The read-only ThreadVault MCP server is registered separately through Codex's MCP configuration.

Development now uses an isolated `.venv`. The project environment passes `pip check`; unrelated missing dependencies in the global Selenium/Trio installation are outside ThreadVault's dependency graph.

## Recently Completed

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

Latest validation for the current `2.4.0` native-desktop workflow baseline:

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\threadvault.exe desktop smoke --json
.\.venv\Scripts\threadvault.exe mcp manifest --json
.\.venv\Scripts\threadvault.exe doctor --db data\threadvault.db --json
```

Current result: `295 passed`, full-project ruff passed, and `pip check` found no broken requirements. Source and installed metadata both report `2.4.0`; desktop smoke reports `desktop_smoke.v2`; MCP manifest reports 2.4.0 and six read-only tools; the live schema-v8/FTS doctor passed at 342 sessions and 835,177 events with seven known warnings. Rendered Windows QA confirmed friendly title/project rows without thread URI labels, the Backup Center status/schedule/disk view, disabled-before-preview and enabled-after-preview export confirmation, and automatic health diagnosis. Tk's Windows accessibility tree still exposes panes more reliably than child control names, so full NVDA narration remains an explicit residual risk. Public release acceptance is recorded under `docs/progress/releases/v2.4.0/`.

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
- `docs/progress/releases/v0.34.0/`
- `docs/progress/releases/v1.0.0/`
- `docs/progress/releases/v1.0.1/`

## Risks

- Archived legacy documentation intentionally preserves older architecture and terminology as historical evidence.
- Local databases, cold blobs, exports, backups, and generated output can contain private data and must remain ignored local artifacts.
- Long-running Codex MCP processes must be restarted after upgrading ThreadVault so they load the v2.4.0 runtime.
- Tkinter keyboard and visible-label accessibility passed rendered QA, but a full NVDA narration pass remains a non-blocking follow-up.

## Next Steps

- Keep the personal-only boundary explicit when adding future commands or contracts.
- Consider adding an "open export directory" helper after designing a safe local-only route.
- Consider extending the proven dry-run/apply installer pattern to ZCode, OpenCode, and Obsidian after their client configuration surfaces stabilize.
