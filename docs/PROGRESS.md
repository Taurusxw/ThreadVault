# Progress

## Current Stage

ThreadVault v4 personal Web UI hardening is in progress. The documentation completeness pass is complete for the active standard docs: path boundaries, basic/pro mode, preview/write flow, local archive database, export outputs, and safety gates are now covered.
The archive database default has been moved from the Windows AppData location to the project-local `data/threadvault.db`, with custom path support through `--db`, `THREADVAULT_DB`, and `[storage].archive_db`. The active package version is now `0.34.0`.

The local knowledge base now keeps raw archive evidence intact while default search/retrieval uses a clean knowledge index over `events.indexed_text`. Low-value empty/machine events are skipped, binary/image blobs are metadata-only, and large tool outputs are truncated for indexing.

ThreadVault now exposes a read-only MCP stdio server for Codex, ZCode, OpenCode, and other MCP-capable local agents. The first tool set covers capabilities, stats, doctor, retrieval, session detail, and export preview without writing files.
The MCP integration guide now documents Codex, OpenCode, ZCode, Obsidian, and AI self-configuration workflows without changing runtime behavior.
The public `0.34.0` release preparation is in progress: MIT licensing is present, GitHub visibility is already public, community/security files were added, and local data/export/backup artifacts are ignored.

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

## Current Validation

Latest focused validation:

```powershell
py -3.12 -m pytest tests\test_v334_mcp_stdio_server.py tests\test_v206_agent_interface.py tests\test_v301_client_interface_readiness.py -q
py -3.12 -m ruff check src\threadvault\mcp.py src\threadvault\mcp_contracts.py src\threadvault\cli.py src\threadvault\agent_interface.py src\threadvault\store.py src\threadvault\schemas.py tests\test_v334_mcp_stdio_server.py tests\test_v206_agent_interface.py tests\test_v301_client_interface_readiness.py
```

Current focused result: `13 passed`; ruff passed.

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

- `ruff` passed for the touched UI/test Python surface.
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
- `docs/progress/releases/v0.34.0/`

## Risks

- Archived legacy documentation still contains older lowercase phase filenames as historical evidence.
- Historical roadmap files describe goals from before v1-v4 completion and may read like future tense.
- Browser plugin automation can be interrupted by native confirmation dialogs. Independent Chrome/Playwright may be more reliable for full visual QA.
- Local generated output directories may contain private data and should be treated as local-only artifacts.
- Historical Git commits may still contain a legacy DOCX planning artifact; current release prep removes it from the current tree but does not rewrite history.
- Broad Chinese localization by string replacement remains fragile and should be replaced with a structured translation table in a future cleanup.
- Existing private archive data previously stored under AppData must be copied or intentionally migrated into `data/threadvault.db` before the new default shows the same archived sessions.
- Clean-index classification thresholds are conservative and may need tuning after more real corpus review.
- `<python-env>` has an unrelated existing dependency warning: `selenium` requires `websocket-client~=1.8`.

## Next Steps

- Continue v4 UI QA with a stable browser automation path.
- Consider adding an "open export directory" helper after designing a safe local-only route.
- Consider exposing clean-index diagnostics in the UI maintenance panel.
- Consider adding dry-run integration installers for Codex, ZCode, OpenCode, and Obsidian after MCP usage stabilizes.
