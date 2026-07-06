# Progress

## Current Stage

ThreadVault is at the 1.0.0 native desktop release stage. The native Tkinter app is the discoverable primary local interface, the browser Web UI CLI/launcher entrypoints remain retired, and the former Web UI runtime module, active schemas, and tests have been removed from the active package.
The archive database default has been moved from the Windows AppData location to the project-local `data/threadvault.db`, with custom path support through `--db`, `THREADVAULT_DB`, and `[storage].archive_db`. The active package version is now `1.0.0`.

The local knowledge base now keeps raw archive evidence intact while default search/retrieval uses a clean knowledge index over `events.indexed_text`. Low-value empty/machine events are skipped, binary/image blobs are metadata-only, and large tool outputs are truncated for indexing.

ThreadVault now exposes a read-only MCP stdio server for Codex, ZCode, OpenCode, and other MCP-capable local agents. The first tool set covers capabilities, stats, doctor, retrieval, session detail, and export preview without writing files.
The MCP integration guide now documents Codex, OpenCode, ZCode, Obsidian, and AI self-configuration workflows without changing runtime behavior.
The public `0.34.0` release preparation is in progress: MIT licensing is present, GitHub visibility is already public, community/security files were added, and local data/export/backup artifacts are ignored.
Skill candidate exports are now lightweight progressive packets: `SKILL.md` routes through `references/index.md`, compact session summaries, per-session detail files, and a short-snippet evidence index instead of forcing a raw transcript-style evidence dump.
ThreadVault now has a minimal native Tkinter desktop app launched by `threadvault desktop launch`. The first native migration slice covers browse/search/session summary, export preview, privacy warnings, MCP integration, health diagnostics, and advanced command references without adding Electron, React, Tauri, WebView, or a frontend build pipeline.
The native desktop app now also covers data-safety and maintenance actions: backup, backup verification, read-only restore planning, FTS reindex, and SQLite vacuum. Write-like native desktop actions use confirmation prompts before running.
The native desktop Advanced tab now has read-only panels for JSON Schemas, robot docs, and governance status, reducing the remaining need for the browser workbench during development and audits.
The native desktop Safety tab now supports restore apply for verified backups into new non-overwrite target databases, with a native confirmation prompt and an explicit refusal when the target already exists.
The native desktop Advanced tab now supports schema write with an explicit output directory and native confirmation prompt.
The native desktop Advanced tab now also has a read-only governance diagnostics aggregation for status, readiness, gaps, identity, backup/policy readiness, and v3 completion checks.
Native desktop runtime QA found and fixed a Tk thread-safety issue: Tk variables are now read on the UI thread before background worker dispatch, and initial refresh is scheduled after Tk startup. Follow-up hwnd screenshot QA captured the native window, confirmed the empty search state renders a clear prompt, and fixed Advanced-tab button overflow at `860x520`.
The desktop CLI now has a non-window `threadvault desktop smoke --json` command for automated verification of Tkinter availability, desktop gateway loading, and no-browser/no-server boundaries.
The repo now includes `启动ThreadVault桌面版.cmd`, a double-click native desktop launcher that runs desktop smoke before starting the Tkinter app and does not start a browser/Web UI server.
The old `启动ThreadVault中文界面.cmd` launcher no longer starts a browser or local Web UI server; it redirects to the native desktop launcher.
Capabilities and robot docs now expose `interface_policy.primary_local_interface = native_desktop`, keep `threadvault desktop launch` and `threadvault desktop smoke --json` in recommended commands, move former Web UI commands into `retired_commands`, point historical evidence to `docs/progress/archive/legacy-v4/`, and use base contract marker `1.0`.

## Recently Completed

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

## Current Validation

Latest validation for the current `1.0.0` native desktop release:

```powershell
py -3.12 -m pytest tests\test_v28_capabilities_schema_contract.py tests\test_v401_personal_ui_readiness.py tests\test_v407_desktop_app.py tests\test_v105_codex_skill_target.py -q
py -3.12 -m ruff check src\threadvault\store.py src\threadvault\schemas.py src\threadvault\cli.py src\threadvault\desktop_data.py src\threadvault\desktop_app.py tests\test_v28_capabilities_schema_contract.py tests\test_v401_personal_ui_readiness.py tests\test_v407_desktop_app.py tests\test_v105_codex_skill_target.py
threadvault capabilities --json
threadvault robot-docs guide --json
py -3.12 -c "import importlib.metadata as m, threadvault; print(threadvault.__version__); print(m.version('threadvault'))"
```

Current release result: full pytest passed with `400 passed in 58.78s`, full ruff passed, desktop smoke passed, CLI discovery reported `native_desktop` as primary, and version metadata reported `1.0.0`. Detailed acceptance is recorded in `docs/progress/releases/v1.0.0/ACCEPTANCE.md`.

Previous focused validation for the `0.48.0` native-first capability alignment:

- Expanded related capabilities/Web UI/desktop/Skill regression passed with `51 passed`.
- Focused ruff passed.
- CLI smoke confirmed capabilities report `native_desktop` / `legacy_fallback` and robot docs keep Web UI commands only under `legacy_fallback_commands`.
- Source and installed metadata both reported `0.48.0`.

Previous focused validation for the `0.47.0` desktop-first launcher guidance change:

- Expanded related regression: `46 passed`.
- Focused ruff passed for the touched desktop/CLI/store/Web UI compatibility/test surface.

Previous focused validation for the `0.46.0` native desktop launcher change:

- Desktop smoke CLI returned `ok: true`.
- Expanded related regression: `46 passed`.
- Focused ruff passed.

Previous focused validation for the `0.45.0` native desktop smoke command change:

- Desktop smoke CLI returned `ok: true`.
- Expanded related regression: `45 passed`.
- Focused ruff passed.

Previous focused validation for the `0.44.0` native desktop thread-safety change:

- Expanded related regression: `44 passed`.
- Focused ruff passed.
Runtime QA launched the Tk window, exposed the original worker issue, and then captured native Windows hwnd screenshots after the fix. The screenshots confirmed the compact window renders, the empty search-results state shows a clear prompt, and the Advanced tab controls fit after splitting governance controls onto their own row.

Previous focused validation for the `0.43.0` native desktop governance diagnostics change:

- Expanded related regression: `43 passed`.
- Focused ruff passed.

Previous focused validation for the `0.42.0` native desktop schema write change:

- Expanded related regression: `43 passed`.
- Focused ruff passed.

Previous focused validation for the `0.41.0` native desktop restore apply change:

- Expanded related regression: `42 passed`.
- Focused ruff passed.

Previous focused validation for the `0.40.0` native desktop advanced read-panel change:

- Expanded related regression: `42 passed`.
- Focused ruff passed.

Previous focused validation for the `0.39.0` native desktop data-safety action change:

- Expanded related regression: `41 passed`.
- Focused ruff passed.

Previous focused validation for the `0.38.0` native desktop app shell:

- Focused desktop/local UI discovery: `10 passed`.
- Expanded related regression: `40 passed`.

Latest focused validation for the previous `0.37.0` compact UI density change:

```powershell
python -m ruff check src\threadvault\personal_ui.py tests\test_v403_personal_ui_workbench.py tests\test_v406_ui_chinese_localization.py
node -e "<extract APP_JS from personal_ui.py and compile with new Function(...)>"
rg -n -- "--control-height: 32px|--radius: 4px|0\.37\.0" src tests README.md docs pyproject.toml
```

Current compact-UI result: ruff passed, `APP_JS` syntax passed, and static CSS/version checks passed.
Focused pytest was attempted but blocked in the current restricted runtime because `py` is unavailable, the bundled Python lacks `attrs`, the default Conda Python lacks `attrs`, and the project Python executable is denied by the sandbox.

MCP validation:

- `threadvault mcp manifest --json` emitted a `threadvault_mcp_manifest.v1` payload with 6 read-only tools.
- `threadvault validate-json --schema mcp_manifest --input <user-temp>\threadvault-mcp-manifest.json --json` passed.
- Stdio smoke for `threadvault mcp serve` returned MCP `initialize` and `tools/list` JSON-RPC responses.
- `threadvault robot-docs schemas --json` lists `mcp_manifest`.
- `threadvault agent manifest --json` reports `mcp_runtime_included = true`.

Real archive migration validation:

- `data/threadvault.db` is schema version `5`.
- `events_fts` uses `indexed_text` and remains aligned with `events`: 56,680 rows each.
- Clean index diagnostics: 35,618 searchable events, 21,062 skipped events, 4,603 truncated events, 12 metadata-only events.
- Indexed characters reduced from 54,625,653 raw characters to 18,340,385 indexed characters.

Additional documentation-focused validation:

```powershell
py -3.12 -m pytest tests\test_v401_personal_ui_readiness.py tests\test_v403_personal_ui_workbench.py -q
```

Recent result: `22 passed` when run with `tests\test_v406_ui_chinese_localization.py` included.

Additional checks:

- Previous full validation before the compact-density CSS change passed with `422 passed` and full ruff passed.
- `py -3.12 -m pytest tests\test_v403_personal_ui_workbench.py tests\test_v406_ui_chinese_localization.py tests\test_v404_ui_action_coverage.py tests\test_v105_codex_skill_target.py -q` passed with `31 passed`.
- `py -3.12 -m ruff check src\threadvault\personal_ui.py tests\test_v403_personal_ui_workbench.py tests\test_v406_ui_chinese_localization.py tests\test_v404_ui_action_coverage.py` passed.
- Source files now report `0.37.0`.
- Browser QA using local Chrome confirmed the `0.36.0` information-architecture UI had no horizontal overflow at desktop or 390px mobile width; compact `0.37.0` browser QA is still pending due current runtime browser tooling limits.
- `/api/health` reports the archive DB path and default export directory separately.
- Browser QA confirmed a real export write reaches completed state with spinner animation stopped.
- Browser QA generated a real local Skill export under `<repo-root>\threadvault-ui-output`.
- Archive DB relocation validation passed for project-local default, environment override, and config override.
- Existing AppData archive DB was copied to `<repo-root>\data\threadvault.db`; direct SQLite verification found 11 sessions, 56,680 events, 244 turns, 91 warnings, and 5 projects.
- Python 3.12 `py_compile` passed for touched config, CLI, UI, schema, version, and focused test files.
- `pytest` and `ruff` are now runnable through the upgraded Anaconda Python 3.12 environment.

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
- `docs/progress/releases/v0.34.0/`

## Risks

- Archived legacy documentation still contains older lowercase phase filenames as historical evidence.
- Historical roadmap files describe goals from before v1-v4 completion and may read like future tense.
- Local generated output directories may contain private data and should be treated as local-only artifacts.
- Historical Git commits may still contain a legacy DOCX planning artifact; current release prep removes it from the current tree but does not rewrite history.
- The native desktop app does not yet cover every low-frequency historical Web UI action with native confirmation gates; overwrite restore and some governance/audit write operations remain command-based during migration.
- Native screenshot QA is now possible through the Tk hwnd path; broader manual workflow review is still required before declaring the Web UI fully replaceable.
- Existing private archive data previously stored under AppData must be copied or intentionally migrated into `data/threadvault.db` before the new default shows the same archived sessions.
- Clean-index classification thresholds are conservative and may need tuning after more real corpus review.
- `<python-env>` has an unrelated existing dependency warning: `selenium` requires `websocket-client~=1.8`.

## Next Steps

- Continue migrating any remaining low-frequency operations that belong in the native desktop UI, adding explicit native confirmation gates before enabling destructive actions.
- Consider adding an "open export directory" helper after designing a safe local-only route.
- Consider exposing clean-index diagnostics in the UI maintenance panel.
- Consider adding dry-run integration installers for Codex, ZCode, OpenCode, and Obsidian after MCP usage stabilizes.
