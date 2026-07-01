# ThreadVault Development Progress

## 2026-07-01 - v4 UI Serve Exit On Close

### Completed

- Added a browser heartbeat from the static UI to `POST /api/ui-heartbeat`.
- Added server-side heartbeat tracking and a close monitor that shuts down `threadvault ui serve` after an opened page
  stops sending heartbeats.
- Added `PersonalUIServerConfig.exit_on_close` and `close_timeout_seconds`.
- Added `threadvault ui serve --exit-on-close/--no-exit-on-close`.
- Defaulted `--exit-on-close` behavior to `--open`, so normal `threadvault ui serve --open` exits after the opened
  browser page is closed, while manually hosted service sessions keep running unless explicitly opted in.
- Preserved existing API/action/schema behavior; `/api/ui-heartbeat` is a local UI lifecycle route only.

### Validation

- `py -3.12 -m pytest tests\test_v406_ui_chinese_localization.py -q` -> 6 passed.
- `py -3.12 -m pytest tests\test_v402_local_ui_server.py tests\test_v403_personal_ui_workbench.py tests\test_v404_ui_action_coverage.py tests\test_v405_v4_acceptance_smoke.py tests\test_v406_ui_chinese_localization.py -q` -> 26 passed.
- `py -3.12 -m ruff check .` -> passed.
- `threadvault ui smoke --json` -> passed with `status = accepted`, `ok = true`, `required_check_count = 14`,
  `failed_required_check_count = 0`, and `criteria_satisfied_count = 5`.
- `threadvault ui serve --help` -> passed and showed `--exit-on-close/--no-exit-on-close`.

### Next

- For ordinary browser-launched use, prefer `threadvault ui serve --open --lang zh`; closing the opened page will let the
  local server exit after the heartbeat timeout.

## 2026-07-01 - v4 UI Scroll Fix

### Completed

- Re-read the required v4 source documents before implementation:
  - `docs/README.md`
  - `docs/roadmap/major-version-roadmap.md`
  - `docs/v3/README.md`
  - `docs/v3/phases/phase-33-v3-final-acceptance-smoke/acceptance.md`
  - `docs/v2/README.md`
  - `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
  - `docs/THREADVAULT_USAGE_MANUAL.md`
  - `docs/development-progress.md`
  - `docs/v4/README.md`
- Used `frontend-testing-debugging` guidance and the in-app Browser runtime to reproduce and verify the right-side JSON
  panel scroll behavior.
- Updated `APP_CSS` in `src/threadvault/personal_ui.py` so the desktop layout uses a fixed viewport grid:
  - `body` owns the viewport and no longer scrolls on desktop.
  - `.workspace` and `.content` get their own bounded scrolling.
  - `.json-panel` keeps its heading fixed while `.json-panel pre` scrolls independently.
  - mobile layouts keep natural page scrolling.
- Added versioned static asset URLs and `Cache-Control: no-store, max-age=0` for HTML/CSS/JS responses, after verifying
  that the user's still-running `127.0.0.1:8766` service was serving the old CSS with `.json-panel { overflow: auto; }`.
- Restarted stale `ui serve` processes and reinstalled the editable console entrypoint so ordinary
  `threadvault ui serve --lang zh` serves the current workspace assets.
- Updated `tests/test_v403_personal_ui_workbench.py` to guard the bounded scroll CSS rules.
- Updated `tests/test_v406_ui_chinese_localization.py` to verify versioned Chinese assets and no-store CSS responses.
- Preserved existing English and Chinese UI text, routes, APIs, schemas, action ids, and safety behavior.

### Validation

- Browser-rendered validation on `http://127.0.0.1:8767/zh`:
  - title was `ThreadVault 个人界面`.
  - right JSON content length was `19452`.
  - `document.scrollingElement.scrollTop` stayed `0`.
  - `.json-panel pre.scrollTop` changed from `0` to `900`.
  - JSON heading top stayed at `14`, so `JSON 输出 / 清空` remained visible.
- `py -3.12 -m pytest tests\test_v403_personal_ui_workbench.py -q` -> 6 passed.
- `py -3.12 -m pytest tests\test_v403_personal_ui_workbench.py tests\test_v406_ui_chinese_localization.py -q` ->
  11 passed.
- `py -3.12 -m pytest tests\test_v402_local_ui_server.py tests\test_v403_personal_ui_workbench.py tests\test_v404_ui_action_coverage.py tests\test_v405_v4_acceptance_smoke.py tests\test_v406_ui_chinese_localization.py -q` -> 25 passed.
- `py -3.12 -m ruff check .` -> passed.
- `threadvault ui serve --lang zh` on `127.0.0.1:8766` -> served `/zh` with
  `/assets/app.css?v=20260701-scroll2`, `/assets/app.zh.js?v=20260701-scroll2`, and `Cache-Control: no-store, max-age=0`.
- Browser-rendered validation on ordinary `http://127.0.0.1:8766/zh` after reinstall:
  - stylesheet href was `http://127.0.0.1:8766/assets/app.css?v=20260701-scroll2`.
  - `document.scrollingElement.scrollTop` stayed `0`.
  - `.json-panel pre.scrollTop` changed from `0` to `900`.
  - JSON heading top stayed at `14`.
- `threadvault ui smoke --json` -> passed with `status = accepted`, `ok = true`, `required_check_count = 14`,
  `failed_required_check_count = 0`, and `criteria_satisfied_count = 5`.
- `Test-Path deep-research-report.md` -> `False`.

### Next

- If further UI polish is requested, keep it scoped to existing static HTML/CSS/JS and preserve the local-first backend
  seams.

## 2026-07-01 - v4 Phase 06 UI Chinese Localization

### Completed

- Re-read the required v4 source documents before implementation:
  - `docs/README.md`
  - `docs/roadmap/major-version-roadmap.md`
  - `docs/v3/README.md`
  - `docs/v3/phases/phase-33-v3-final-acceptance-smoke/acceptance.md`
  - `docs/v2/README.md`
  - `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
  - `docs/THREADVAULT_USAGE_MANUAL.md`
  - `docs/development-progress.md`
  - `docs/v4/README.md`
- Used `frontend-design` and `codebase-design` guidance to keep localization additive and inside the existing static
  Personal UI module seam.
- Added Chinese UI resources in `src/threadvault/personal_ui.py`:
  - `INDEX_HTML_ZH`
  - `APP_JS_ZH`
- Added Chinese static routes:
  - `/zh`
  - `/assets/app.zh.js`
- Kept `/`, `/assets/app.js`, `/assets/app.css`, `/api/*`, `/api/action`, schema names, JSON fields, and action ids
  unchanged.
- Added `threadvault ui serve --lang en|zh`, defaulting to `en`.
- Made `--lang zh --open` open `/zh` while default `--open` still opens `/`.
- Added Phase 06 docs:
  - `docs/v4/phases/phase-06-ui-chinese-localization/plan.md`
  - `docs/v4/phases/phase-06-ui-chinese-localization/design-notes.md`
  - `docs/v4/phases/phase-06-ui-chinese-localization/acceptance.md`
- Updated `docs/v4/README.md` with Phase 06 links.
- Added `tests/test_v406_ui_chinese_localization.py`.
- Preserved local-first/privacy-first defaults. No React, Vite, Node, i18n framework, cloud sync, login, public-server
  default, team enforcement, parser rewrite, SQLite retrieval rewrite, or parallel backend was added.

### Validation

- `py -3.12 -m pytest tests\test_v406_ui_chinese_localization.py -q` -> 5 passed.
- `py -3.12 -m pytest tests\test_v402_local_ui_server.py tests\test_v403_personal_ui_workbench.py tests\test_v404_ui_action_coverage.py tests\test_v405_v4_acceptance_smoke.py tests\test_v406_ui_chinese_localization.py -q` -> 25 passed.
- `py -3.12 -m ruff check .` -> passed.
- `py -3.12 -m pytest` -> 405 passed.
- `threadvault ui smoke --json` -> passed with `status = accepted`, `ok = true`, `required_check_count = 14`,
  `failed_required_check_count = 0`, and `criteria_satisfied_count = 5`.
- `threadvault ui serve --help` -> passed and showed `--lang` with default `en`.
- `Test-Path deep-research-report.md` -> `False`.

### Next

- Phase 06 is accepted as an additive Chinese localization layer over the v4 Personal Web UI.
- Future localization work should remain additive unless a later phase explicitly introduces a full i18n framework.

## 2026-07-01 - v4 Phase 05 v4 Acceptance Smoke

### Completed

- Re-read the required v4 source documents before implementation:
  - `docs/README.md`
  - `docs/roadmap/major-version-roadmap.md`
  - `docs/v3/README.md`
  - `docs/v3/phases/phase-33-v3-final-acceptance-smoke/acceptance.md`
  - `docs/v2/README.md`
  - `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
  - `docs/THREADVAULT_USAGE_MANUAL.md`
  - `docs/development-progress.md`
  - `docs/v4/README.md`
  - `docs/v4/phases/phase-05-v4-acceptance-smoke/plan.md`
- Used `codebase-design` guidance to keep the v4 acceptance smoke as one deep Personal UI runtime interface over
  existing route, action, v2 retrieval, and v3 governance seams.
- Added `run_personal_ui_smoke()` in `src/threadvault/personal_ui.py`.
- Added `threadvault ui smoke --db PATH --config PATH --work-dir PATH --json`.
- Made no-argument `threadvault ui smoke --json` hermetic in the repo by importing `tests/fixtures/codex_home` into a
  temporary database when no `--db` is supplied, instead of mutating the user's default database.
- Added `personal_ui_smoke.v1` schema support and regenerated `docs/schemas/personal_ui_smoke.schema.json`.
- Updated capabilities, robot guide, and robot schemas to advertise the smoke command and schema.
- Added Phase 05 docs:
  - `docs/v4/phases/phase-05-v4-acceptance-smoke/design-notes.md`
  - `docs/v4/phases/phase-05-v4-acceptance-smoke/acceptance.md`
- Updated `docs/v4/README.md` with Phase 05 acceptance links.
- Added `tests/test_v405_v4_acceptance_smoke.py`.
- Preserved local-first/privacy-first defaults. No React, Vite, Node, cloud sync, login, public-server default, team
  enforcement, external model calls, parser rewrite, SQLite retrieval rewrite, exporter rewrite, or privacy bypass was
  added.

### Validation

- `py -3.12 -m pytest tests\test_v405_v4_acceptance_smoke.py -q` -> 4 passed.
- `py -3.12 -m ruff check src\threadvault\personal_ui.py src\threadvault\cli.py src\threadvault\store.py src\threadvault\schemas.py tests\test_v405_v4_acceptance_smoke.py` -> passed.
- `threadvault schemas write --out docs\schemas --json` -> passed and wrote `personal_ui_smoke.schema.json`.
- `threadvault capabilities --json` -> passed and advertised `ui smoke` and `personal_ui_acceptance_smoke`.
- `threadvault robot-docs guide --json` -> passed and advertised `threadvault ui smoke --json`.
- `threadvault robot-docs schemas --json` -> passed and included `personal_ui_smoke`.
- `threadvault ui serve --help` -> passed and showed `--host` default `127.0.0.1`, `--port` default `8766`, and `--open`.
- `threadvault ui smoke --db TEMP_DB --work-dir TEMP_WORK --json` after importing fixture sessions -> passed with
  `status = accepted`, `ok = true`, `required_check_count = 14`, `failed_required_check_count = 0`, and
  `criteria_satisfied_count = 5`.
- `threadvault ui smoke --json` -> passed with a temporary fixture database, `status = accepted`, `ok = true`,
  `required_check_count = 14`, `failed_required_check_count = 0`, and `criteria_satisfied_count = 5`.
- `py -3.12 -m pytest tests\test_v402_local_ui_server.py tests\test_v403_personal_ui_workbench.py tests\test_v404_ui_action_coverage.py tests\test_v405_v4_acceptance_smoke.py -q` -> 20 passed.
- `Test-Path deep-research-report.md` -> `False`.
- `py -3.12 -m ruff check .` -> passed.
- `py -3.12 -m pytest` -> 400 passed.

### Bugs Found

- First smoke draft expected the v2 retrieval contract string to start with `retrieval_query`; the accepted runtime
  returns `retrieval.v1`. Relaxed the non-regression check to the current accepted contract family.
- The first default `threadvault ui smoke --json` run checked the empty user default database and failed fixture-session
  criteria. Updated the command to use a temporary imported fixture database when no `--db` is provided.
- Focused lint caught two long evidence-return lines in `personal_ui.py`; wrapped them before final validation.

### Next

- v4 Phase 05 is accepted as the final Personal Web UI smoke.
- v4 Personal Web UI is complete for the local personal scope described in `docs/v4/README.md`.
- Future work should be planned as opt-in post-v4 hardening or a later version line:
  - richer browser polish
  - packaged desktop wrapper
  - explicit real-archive smoke presets
  - additional governance UI affordances

## 2026-07-01 - v4 Phase 04 UI Action Coverage

### Completed

- Re-read the required v4 source documents before implementation:
  - `docs/README.md`
  - `docs/roadmap/major-version-roadmap.md`
  - `docs/v3/README.md`
  - `docs/v3/phases/phase-33-v3-final-acceptance-smoke/acceptance.md`
  - `docs/v2/README.md`
  - `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
  - `docs/THREADVAULT_USAGE_MANUAL.md`
  - `docs/development-progress.md`
  - `docs/v4/README.md`
  - `docs/v4/phases/phase-04-ui-action-coverage/plan.md`
  - `docs/v4/phases/phase-01-personal-ui-readiness/coverage-matrix.md`
- Used `frontend-design` guidance for native controls and `codebase-design` guidance to keep `/api/action` as the deep
  personal UI action interface over existing ThreadVault modules.
- Added `PersonalUIActionSpec` and `ACTION_REGISTRY` in `src/threadvault/personal_ui.py`.
- Replaced placeholder `/api/action` behavior with centralized action execution, error shaping, confirmation checks,
  preview checks, and dry-run safety defaults.
- Wired representative and required action families to existing `ArchiveStore` methods or existing CLI helper modules:
  ingestion, sessions, search/retrieval/agent, summary/vector, privacy/warnings, export preview/export targets, config,
  maintenance, backup/restore/history, audit, schemas/validation, discovery, and governance diagnostics.
- Enforced Phase 04 safety rules:
  - `restore_apply`, `vacuum`, `reindex`, `schema_write`, and `schemas_write` require `confirm=true`
  - export write actions require `preview_accepted=true`
  - prune/history apply actions require confirmation when `apply=true`
  - backup returns the target path
- Updated the static workbench JavaScript to send useful action params and native confirmation flags.
- Updated capabilities, robot guide, robot schemas, and generated schema artifacts for the implemented action registry.
- Added Phase 04 docs:
  - `docs/v4/phases/phase-04-ui-action-coverage/design-notes.md`
  - `docs/v4/phases/phase-04-ui-action-coverage/acceptance.md`
- Updated `docs/v4/README.md` with Phase 04 acceptance links.
- Added `tests/test_v404_ui_action_coverage.py`.
- Preserved local-first/privacy-first defaults. No React, Vite, Node, cloud sync, login, public-server default, team
  enforcement, external model calls, parser rewrite, SQLite retrieval rewrite, exporter rewrite, or privacy bypass was
  added.

### Validation

- `py -3.12 -m pytest tests\test_v404_ui_action_coverage.py -q` -> 5 passed.
- `py -3.12 -m pytest tests\test_v402_local_ui_server.py tests\test_v403_personal_ui_workbench.py tests\test_v404_ui_action_coverage.py -q` -> 16 passed.
- `py -3.12 -m ruff check src\threadvault\personal_ui.py src\threadvault\store.py src\threadvault\schemas.py tests\test_v402_local_ui_server.py tests\test_v404_ui_action_coverage.py` -> passed.
- `threadvault schemas write --out docs\schemas --json` -> passed and regenerated `personal_ui_action.schema.json`.
- `threadvault capabilities --json` -> passed and advertised `personal_ui_action_registry`.
- `threadvault robot-docs guide --json` -> passed and advertised `POST /api/action`, dangerous action confirmations,
  and export preview requirements.
- `threadvault robot-docs schemas --json` -> passed and included the updated `personal_ui_action` summary.
- `Test-Path deep-research-report.md` -> `False`.
- `py -3.12 -m ruff check .` -> passed.
- `py -3.12 -m pytest` -> 396 passed.
- `threadvault ui smoke --json` -> still not implemented; remains the Phase 05 acceptance deliverable.

### Bugs Found

- Focused validation found the Phase 02 unknown-action test still expected `restore_apply` to be unknown. Updated it to
  assert the new Phase 04 behavior: `restore_apply` is known and blocked without `confirm=true`.
- Focused validation found two assertions that expected fields not present in existing accepted contracts. Updated the
  tests to match the current `reindex` payload and `client_export_preview.diagnostics.writes_files`.
- `ruff` caught several long lines in the new registry and JavaScript strings; wrapped them before final validation.

### Next

- Continue v4 with Phase 05: implement `threadvault ui smoke --json` and verify the full local-first Personal Web UI
  acceptance criteria.

## 2026-07-01 - v4 Phase 03 Personal UI Workbench

### Completed

- Re-read the required v4 source documents before implementation:
  - `docs/README.md`
  - `docs/roadmap/major-version-roadmap.md`
  - `docs/v3/README.md`
  - `docs/v3/phases/phase-33-v3-final-acceptance-smoke/acceptance.md`
  - `docs/v2/README.md`
  - `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
  - `docs/THREADVAULT_USAGE_MANUAL.md`
  - `docs/development-progress.md`
  - `docs/v4/README.md`
  - `docs/v4/phases/phase-03-personal-ui-workbench/plan.md`
- Used `frontend-design` guidance for the native workbench UI and `codebase-design` guidance to keep the workbench
  client-side over the existing Phase 02 routes instead of creating a parallel backend.
- Expanded `src/threadvault/personal_ui.py` static assets into a single-page workbench with:
  - left navigation
  - top search/status bar with database path
  - main work area
  - right JSON output panel
  - Archive, Search, Session, Export, Privacy, Maintenance, Backup/Restore, Config, Schemas, and Governance views
- Added JavaScript workflows for health, archive overview, retrieval/search, session detail, warnings, raw JSON
  inspection, and Phase 04 action-placeholder calls through `/api/action`.
- Kept write-heavy and dangerous operations as explicit Phase 04 placeholders. The UI now labels preview, dry-run, and
  `confirm=true` requirements for export, restore apply, reindex, vacuum, schema write, and backup target display.
- Added Phase 03 docs:
  - `docs/v4/phases/phase-03-personal-ui-workbench/design-notes.md`
  - `docs/v4/phases/phase-03-personal-ui-workbench/acceptance.md`
- Updated `docs/v4/README.md` with Phase 03 acceptance links.
- Added `tests/test_v403_personal_ui_workbench.py`.
- Preserved local-first/privacy-first defaults. No React, Vite, Node, cloud sync, login, public-server default, team
  enforcement, external model calls, parser rewrite, SQLite retrieval rewrite, or privacy bypass was added.

### Validation

- `py -3.12 -m pytest tests\test_v403_personal_ui_workbench.py -q` -> 6 passed.
- `py -3.12 -m ruff check src\threadvault\personal_ui.py tests\test_v403_personal_ui_workbench.py` -> passed.
- `threadvault ui serve --help` -> passed and showed `--host` default `127.0.0.1`, `--port` default `8766`, and `--open`.
- `threadvault capabilities --json` -> passed and still advertised `personal_web_ui`, local defaults, and no UI cloud/team
  defaults.
- Browser-rendered smoke with the in-app Browser plugin on `http://127.0.0.1:8776` using fixture sessions -> passed:
  - page title was `ThreadVault Personal UI`
  - Archive rendered fixture sessions
  - JSON panel rendered `client_overview.v1`
  - global search for `pytest` switched the main pane to Search
  - JSON panel rendered `agent_retrieval.v1`
  - desktop and mobile fallback screenshots had no framework overlay and no console warnings/errors
- `threadvault ui smoke --json` -> expected failure with `No such command 'smoke'`; this remains the Phase 05 acceptance
  deliverable.
- `Test-Path deep-research-report.md` -> `False`.
- `py -3.12 -m ruff check .` -> passed.
- `py -3.12 -m pytest` -> 391 passed.
- `threadvault ui smoke --json` -> still not implemented; remains the Phase 05 acceptance deliverable.

### Bugs Found

- Browser validation found the top status/database path could crowd the search form at desktop width with the JSON panel
  open. Fixed the topbar grid so status uses its own row, the database path ellipsizes, and the search/refresh controls
  remain visible and non-overlapping.

### Next

- Complete validation for Phase 03.
- Continue v4 with Phase 04: implement the unified UI action registry and wire actions to existing ThreadVault
  interfaces with centralized safety checks.

## 2026-07-01 - v4 Phase 02 Local UI Server

### Completed

- Re-read the required v4 source documents before implementation:
  - `docs/README.md`
  - `docs/roadmap/major-version-roadmap.md`
  - `docs/v3/README.md`
  - `docs/v3/phases/phase-33-v3-final-acceptance-smoke/acceptance.md`
  - `docs/v2/README.md`
  - `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
  - `docs/THREADVAULT_USAGE_MANUAL.md`
  - `docs/development-progress.md`
  - `docs/v4/README.md`
  - `docs/v4/phases/phase-02-local-ui-server/plan.md`
- Used `frontend-design` guidance for the minimal static UI shell and `codebase-design` guidance for keeping the HTTP
  server shallow over existing deep modules.
- Read the `documents` skill because the active objective included `@documents`; no DOCX deliverable was requested, so
  no DOCX render workflow was needed.
- Added `src/threadvault/personal_ui.py` with:
  - `PersonalUIServerConfig`
  - `build_health_payload`
  - `handle_api_get`
  - `handle_api_action`
  - `build_personal_ui_server`
  - `serve_personal_ui`
  - minimal static HTML/CSS/JS assets
- Added `threadvault ui serve --host 127.0.0.1 --port 8766 --open`.
- Added read routes:
  - `GET /`
  - `GET /assets/app.css`
  - `GET /assets/app.js`
  - `GET /api/health`
  - `GET /api/capabilities`
  - `GET /api/client/overview`
  - `GET /api/client/session?session=...`
  - `GET /api/client/warnings?session=...`
  - `GET /api/retrieve?q=...`
  - `POST /api/action`
- Kept the HTTP route implementation delegated to existing `ArchiveStore` and discovery interfaces. No shell-out backend
  wrapper, parser rewrite, SQLite retrieval rewrite, privacy bypass, cloud sync, login, team mode, React, Vite, or Node
  dependency was added.
- Added `personal_ui_health` and `personal_ui_action` JSON schemas and regenerated schema artifacts under `docs/schemas/`.
- Updated `capabilities --json`, `robot-docs guide --json`, and `robot-docs schemas --json` discovery surfaces.
- Added `tests/test_v402_local_ui_server.py`.
- Added Phase 02 docs:
  - `docs/v4/phases/phase-02-local-ui-server/design-notes.md`
  - `docs/v4/phases/phase-02-local-ui-server/acceptance.md`
- Updated `docs/v4/README.md` with Phase 02 acceptance links.

### Validation

- `py -3.12 -m pytest tests\test_v402_local_ui_server.py -q` -> 5 passed.
- `py -3.12 -m ruff check src\threadvault\personal_ui.py src\threadvault\cli.py src\threadvault\store.py src\threadvault\schemas.py tests\test_v402_local_ui_server.py` -> passed.
- `threadvault schemas write --out docs\schemas --json` -> passed and wrote `personal_ui_health.schema.json` and
  `personal_ui_action.schema.json`.
- `threadvault ui serve --help` -> passed and showed `--host` default `127.0.0.1`, `--port` default `8766`, and `--open`.
- `threadvault capabilities --json` -> passed and advertised `ui`, `personal_web_ui`, and local personal UI defaults.
- `threadvault robot-docs guide --json` -> passed and advertised the Personal UI module and schemas.
- `threadvault robot-docs schemas --json` -> passed and included `personal_ui_health` and `personal_ui_action`.
- `Test-Path deep-research-report.md` -> `False`.
- `py -3.12 -m ruff check .` -> passed.
- `py -3.12 -m pytest` -> 385 passed.
- `threadvault ui smoke --json` -> not available yet; this is expected because `ui smoke` is the Phase 05 acceptance
  deliverable, not a Phase 02 deliverable.

### Bugs Found

- Initial discovery draft listed `ui serve` under `json_outputs`, but `ui serve` is a long-running command rather than a
  JSON-emitting command. Removed it from `json_outputs` and kept it in `commands` and `robot-docs guide`.
- Focused lint found one unused test import during development; removed it before final validation.

### Next

- v4 Phase 02 is accepted as the local UI server foundation.
- Continue v4 with Phase 03: build the single-page Personal UI Workbench over the Phase 02 routes.

## 2026-07-01 - v4 Phase 01 Personal UI Readiness

### Completed

- Used the `frontend-design` and `codebase-design` skill guidance for v4 Personal Web UI planning and module seam
  discipline.
- Read the required v4 source documents before implementation:
  - `docs/README.md`
  - `docs/roadmap/major-version-roadmap.md`
  - `docs/v3/README.md`
  - `docs/v3/phases/phase-33-v3-final-acceptance-smoke/acceptance.md`
  - `docs/v2/README.md`
  - `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
  - `docs/THREADVAULT_USAGE_MANUAL.md`
  - `docs/development-progress.md`
- Created `docs/v4/README.md` as the v4 Personal Web UI documentation entrypoint.
- Added Phase 01 readiness documents:
  - `docs/v4/phases/phase-01-personal-ui-readiness/plan.md`
  - `docs/v4/phases/phase-01-personal-ui-readiness/design-notes.md`
  - `docs/v4/phases/phase-01-personal-ui-readiness/coverage-matrix.md`
  - `docs/v4/phases/phase-01-personal-ui-readiness/acceptance.md`
- Added planned v4 phase skeletons:
  - `docs/v4/phases/phase-02-local-ui-server/plan.md`
  - `docs/v4/phases/phase-03-personal-ui-workbench/plan.md`
  - `docs/v4/phases/phase-04-ui-action-coverage/plan.md`
  - `docs/v4/phases/phase-05-v4-acceptance-smoke/plan.md`
- Updated `docs/README.md` with the v4 documentation entry and v4 starting-point checklist.
- Added `tests/test_v401_personal_ui_readiness.py` to lock the v4 docs, phase plans, coverage matrix, and local-first
  discovery assumptions.
- Preserved the accepted v1/v2/v3 runtime boundaries. No parser, SQLite retrieval, export, privacy, backup, restore,
  vector, agent, client, governance, Web server, or CLI runtime implementation was changed.

### Validation

- `py -3.12 -m pytest tests\test_v401_personal_ui_readiness.py -q` -> 4 passed.
- `py -3.12 -m ruff check tests\test_v401_personal_ui_readiness.py` -> passed.
- `threadvault capabilities --json` -> passed and confirmed existing local-first, v2/v3 client/governance, and cloud/external model disabled defaults.
- `Test-Path deep-research-report.md` -> `False`.
- `py -3.12 -m ruff check .` -> passed.
- `py -3.12 -m pytest` -> 380 passed.

### Bugs Found

- The first focused test expected an exact `Advanced Governance` phrase before the Phase 03 plan used that capitalization.
  Updated the plan wording to preserve the requested terminology.
- `ruff` required import sorting in the new focused test; fixed with `ruff --fix` and reran validation.

### Next

- v4 Phase 01 is accepted as the Personal UI readiness and planning baseline.
- Continue v4 with Phase 02: implement `src/threadvault/personal_ui.py` and
  `threadvault ui serve --host 127.0.0.1 --port 8766 --open`.

## 2026-06-30 - v0.3 Agent-Friendly Archive

### Completed

- Added `state_5.sqlite` read-only enrichment through `threads.rollout_path`.
- Added `capabilities`, `robot-docs guide`, `robot-docs schemas`, `reindex`, and `vacuum`.
- Added `export --format md|json|jsonl|csv`.
- Added `--profile full|brief|agent|review`.
- Added project Markdown summaries with evidence event IDs.
- Consolidated turn aggregation through `SessionWriter`.
- Added v0.3 tests for state enrichment, robot docs, export formats, reindex, and documentation presence.
- Added phase plan and external project review documents.

### Validation

- Completed final verification:
  - `py -3.12 -m pytest` -> 11 passed
  - `threadvault --help` -> passed
  - `threadvault capabilities --json` -> passed
  - `threadvault robot-docs guide` -> passed
  - `threadvault robot-docs schemas` -> passed
  - `threadvault export --format json/jsonl/csv` smoke -> passed
  - `threadvault reindex --fts-only --json` smoke -> passed

### Bugs Found

- Previous test runs generated `__pycache__`; cleanup completed after verification.

### Next

- Consider richer state metadata fields after collecting more real Codex `state_5.sqlite` examples.
- Consider a stable JSON schema file if external agents begin depending on ThreadVault output.

## 2026-06-30 - v0.4 Real Corpus and Privacy Hardening

### Completed

- Added `CodexJsonlAdapter` parser implementation seam.
- Added record classification and function call pairing warnings.
- Added `ingest-sample --dry-run --json`.
- Added `warnings --summary --json`.
- Added privacy severity, redaction, fail mode, and `privacy-scan`.
- Added summary evidence coverage fields.
- Added v0.4 phase plan and external project review documents.

### Validation

- Completed final verification:
  - `py -3.12 -m pytest` -> 16 passed
  - `threadvault --help` -> passed
  - `threadvault ingest-sample --codex-home tests/fixtures/codex_home --dry-run --json` -> passed
  - `threadvault privacy-scan --session sess-current --db <tmp.db> --json` -> passed
  - `threadvault export --session sess-privacy --privacy-mode redact --db <tmp.db> --out <tmp-out> --json` -> passed
  - `threadvault warnings --summary --json` -> passed
  - `threadvault doctor --json` parse health -> passed

### Bugs Found

- Existing exact fixture-count assertions failed after adding the v0.4 fixture; tests were updated to assert behavior instead of hard-coded fixture count.
- `ingest-sample` initially constructed a default `ArchiveStore`; it now calls the sampler directly to avoid touching the default database path.

### Next

- Evaluate true-positive and false-positive privacy findings on private data without storing raw content in fixtures.

## 2026-06-30 - v0.5 Quality Contracts and Maintenance

### Completed

- Fixed duplicate function-call pairing warning generation in the parser facade.
- Added exact parser warning regression coverage for current, legacy, fork, and pairing fixtures.
- Added v0.5 contract metadata to `capabilities --json`.
- Upgraded `robot-docs schemas --json` with JSON Schema-style output while preserving legacy schema keys.
- Added privacy allowlist config support through `--privacy-config`.
- Added `rules_version`, `allowlisted_count`, and `effective_findings_count` to `privacy-scan --json`.
- Expanded `doctor --json` with schema object checks and maintenance suggestions.
- Added `self-test --json` for local database and fixture parser smoke checks.
- Added v0.5 phase plan and external project review documents.

### Validation

- Completed final verification:
  - `py -3.12 -m pytest` -> 23 passed
  - `threadvault --help` -> passed
  - `threadvault capabilities --json` -> passed
  - `threadvault robot-docs schemas --json` -> passed
  - `threadvault ingest-sample --codex-home tests/fixtures/codex_home --dry-run --json` -> passed
  - `threadvault warnings --summary --json --db <tmp.db>` -> passed
  - `threadvault privacy-scan --session sess-privacy --db <tmp.db> --json` -> passed
  - `threadvault export --session sess-privacy --privacy-mode fail --db <tmp.db> --out <tmp-out> --json` -> passed with expected exit code 2
  - `threadvault reindex --fts-only --db <tmp.db> --json` -> passed
  - `threadvault doctor --db <tmp.db> --codex-home tests/fixtures/codex_home --json` -> passed
  - `threadvault self-test --db <tmp.db> --json` -> passed
  - `py -3.12 -m ruff check .` -> passed

### Bugs Found

- `parse_session_file()` appended call pairing warnings after `iter_normalized_events()` had already emitted them. This could duplicate `missing_function_call_output`, `orphan_function_call_output`, and `duplicate_function_call_output`; v0.5 removes the second pass and adds exact count tests.

### Next

- Consider publishing formal JSON schema files if external agents begin consuming ThreadVault outside this repository.
- Evaluate privacy allowlist ergonomics on real local data without storing raw transcripts.

## 2026-06-30 - v0.6 Schema Validation Contracts

### Completed

- Added `jsonschema` as the mature validation library for JSON Schema Draft 2020-12.
- Added `threadvault.schemas` as the single schema contract module.
- Added `threadvault schemas list/show/write`.
- Added `threadvault validate-json --schema NAME --input payload.json --json`.
- Generated packaged schema files under `docs/schemas/`.
- Updated `capabilities --json` and `robot-docs guide` to advertise schema and validation commands.
- Added v0.6 tests for schema commands and validation pass/fail behavior.
- Added v0.6 phase plan and external project review documents.

### Validation

- Completed final verification:
  - `py -3.12 -m pytest` -> 26 passed
  - `py -3.12 -m ruff check .` -> passed
  - `threadvault --help` -> passed
  - `threadvault schemas list --json` -> passed
  - `threadvault schemas show search_minimal --json` -> passed
  - `threadvault schemas write --out docs/schemas --json` -> passed
  - `threadvault validate-json --schema search_minimal --input <tmp-json> --json` -> passed

### Bugs Found

- After adding `jsonschema`, the installed editable package initially lacked the new dependency; `py -3.12 -m pip install -e ".[dev]"` fixed the local environment before schema generation.
- A v0.5 regression test hard-coded `contract_version == "0.5"`; it was updated to assert backward-compatible version presence while allowing v0.6 contract evolution.

### Next

- Consider adding schema validation smoke tests for more command outputs, such as `doctor`, `privacy_scan`, and `warnings_summary`.

## 2026-06-30 - v0.7 Real Corpus Anonymous Audit

### Completed

- Added anonymized corpus audit output for real Codex home diagnostics.
- Changed `ingest-sample --json` default output to hide raw paths and session IDs.
- Added `--include-paths` as explicit local debugging opt-in.
- Added `audit-corpus --json`.
- Added `corpus_audit` JSON Schema and packaged `docs/schemas/corpus_audit.schema.json`.
- Added tests proving default audit outputs do not include fixture absolute paths or raw session IDs.
- Added v0.7 phase plan and external project review documents.

### Validation

- Completed final verification:
  - `py -3.12 -m pytest` -> 30 passed
  - `py -3.12 -m ruff check .` -> passed
  - `threadvault ingest-sample --codex-home tests/fixtures/codex_home --dry-run --json` -> passed
  - `threadvault audit-corpus --codex-home tests/fixtures/codex_home --json` -> passed
  - `threadvault audit-corpus --codex-home tests/fixtures/codex_home --include-paths --json` -> passed
  - `threadvault schemas show corpus_audit --json` -> passed

### Bugs Found

- Real corpus sampling previously included raw `path` and `session_id` in JSON output. v0.7 makes this opt-in through `--include-paths`.
- A Windows JSON path assertion initially compared unescaped path text against serialized JSON; the test now checks parsed fields directly.

### Next

- Consider adding persistent anonymous audit report export with timestamps and no raw content.

## 2026-06-30 - v0.8 Audit Report History Diff

### Completed

- Extended `audit-corpus` with `--out` to write timestamped anonymous JSON reports.
- Added audit report metadata: `report_version`, `generated_at`, `source`, `limit`, and privacy note.
- Added `audit-diff --before FILE --after FILE --json`.
- Added aggregate deltas for files, events, warnings, parseable ratio, warning codes, and classifications.
- Added regression flags for increased warnings, decreased parseable ratio, and new warning codes.
- Added `corpus_audit_report` and `corpus_audit_diff` schemas.
- Added v0.8 tests for report writing, privacy-safe persisted output, diff behavior, and schema validation.
- Added v0.8 phase plan and external project review documents.

### Validation

- Completed final verification:
  - `py -3.12 -m pytest` -> 33 passed
  - `py -3.12 -m ruff check .` -> passed
  - `threadvault audit-corpus --codex-home tests/fixtures/codex_home --out <tmp-reports> --json` -> passed
  - `threadvault validate-json --schema corpus_audit_report --input <report.json> --json` -> passed
  - `threadvault audit-diff --before <report-a.json> --after <report-b.json> --json` -> passed
  - `threadvault schemas show corpus_audit_diff --json` -> passed

### Bugs Found

- `ruff` caught import ordering and a long comprehension line in new v0.8 files; both were fixed before final validation.

### Next

- Consider adding `audit-history list` once report directories become a first-class workflow.

## 2026-06-30 - v0.9 Audit History Workflow

### Completed

- Added audit report discovery for `threadvault-audit-*.json`.
- Added malformed report tolerance with JSON warnings.
- Added `audit-history list --dir DIR --json`.
- Added `audit-history latest --dir DIR --json`.
- Added `audit-history diff-latest --dir DIR --json`.
- Added `audit_history_list` and `audit_history_latest` schemas.
- Added tests for report list/latest/diff-latest and malformed report handling.
- Added v0.9 phase plan and external project review documents.

### Validation

- Completed final verification:
  - `py -3.12 -m pytest` -> 37 passed
  - `py -3.12 -m ruff check .` -> passed
  - `threadvault audit-history list --dir <tmp-reports> --json` -> passed
  - `threadvault audit-history latest --dir <tmp-reports> --json` -> passed
  - `threadvault audit-history diff-latest --dir <tmp-reports> --json` -> passed
  - `threadvault schemas show audit_history_list --json` -> passed
  - `threadvault schemas show audit_history_latest --json` -> passed

### Bugs Found

- `ruff` caught import ordering and a long import line in new v0.9 changes; both were fixed before final validation.

### Next

- Consider adding report pruning or retention policy after history workflows stabilize.

## 2026-06-30 - v0.10 Audit History Retention

### Completed

- Added retention planning over valid `threadvault-audit-*.json` reports.
- Added `audit-history prune --dir DIR --keep N --json` dry-run mode.
- Added explicit `--apply` for deletion.
- Kept malformed report files out of automatic deletion.
- Added `audit_history_prune` schema.
- Added tests for dry-run, apply deletion, malformed report tolerance, and schema validation.
- Added v0.10 phase plan and external project review documents.

### Validation

- Completed final verification:
  - `py -3.12 -m pytest` -> 40 passed
  - `py -3.12 -m ruff check .` -> passed
  - `threadvault audit-history prune --dir <tmp-reports> --keep 2 --json` -> passed
  - `threadvault audit-history prune --dir <tmp-reports> --keep 2 --apply --json` -> passed
  - `threadvault schemas show audit_history_prune --json` -> passed

### Bugs Found

- No implementation bugs found in v0.10 final validation.

### Next

- Consider adding retention policy config after command behavior is stable.

## 2026-06-30 - v0.11 Audit Retention Config

### Completed

- Added v0.11 phase plan and external project review documents.
- Extended local `threadvault.toml` parsing with `[audit_history] keep = N`.
- Updated `audit-history prune` so `--keep` is optional when config provides a keep value.
- Preserved CLI precedence: `--keep` overrides configured `audit_history.keep`.
- Added `--config PATH` and JSON `keep_source` for agent traceability.
- Updated `audit_history_prune` schema to document `keep_source`.
- Added tests for config default, CLI override, missing keep, invalid config, and v0.11 docs.

### Validation

- Completed partial implementation validation:
  - `py -3.12 -m pytest tests\test_v10_audit_prune.py tests\test_v11_audit_config.py` -> 8 passed
  - `py -3.12 -m ruff check src\threadvault\privacy_config.py src\threadvault\cli.py tests\test_v11_audit_config.py` -> passed
- Completed final verification:
  - `py -3.12 -m pytest` -> 45 passed
  - `py -3.12 -m ruff check .` -> passed
  - `threadvault audit-history prune --dir <tmp-reports> --config <threadvault.toml> --json` -> passed
  - `threadvault audit-history prune --dir <tmp-reports> --config <threadvault.toml> --keep 1 --json` -> passed
  - `threadvault audit-history prune --dir <tmp-reports> --config <threadvault.toml> --apply --json` -> passed
  - `threadvault --help` -> passed
  - `threadvault schemas show audit_history_prune --json` -> passed

### Bugs Found

- No implementation bugs found in the first v0.11 validation pass.

### Next

- Consider promoting `privacy_config.py` to a broader `app_config.py` compatibility wrapper if more non-privacy settings are added.

## 2026-06-30 - v0.12 App Config Module

### Completed

- Added v0.12 phase plan and external project review documents.
- Added canonical `threadvault.app_config` module for local TOML configuration.
- Moved allowlist parsing and `audit_history.keep` parsing into `app_config.py`.
- Kept `threadvault.privacy_config` as a compatibility wrapper exporting the old names.
- Updated internal imports to use `app_config`.
- Added tests for `load_app_config`, compatibility `load_privacy_config`, invalid boolean keep values, and v0.12 docs.
- Updated README and research Markdown appendices.

### Validation

- Completed partial implementation validation:
  - `py -3.12 -m pytest tests\test_v12_app_config.py tests\test_v11_audit_config.py tests\test_v05_contracts.py` -> 16 passed
  - `py -3.12 -m ruff check src\threadvault\app_config.py src\threadvault\privacy_config.py tests\test_v12_app_config.py` -> passed
- Completed final verification:
  - `py -3.12 -m pytest` -> 49 passed
  - `py -3.12 -m ruff check .` -> passed
  - `threadvault audit-history prune --dir <tmp-reports> --config <threadvault.toml> --json` -> passed
  - `threadvault --help` -> passed
  - `py -3.12 -c "from threadvault.app_config import load_app_config; from threadvault.privacy_config import load_privacy_config; ..."` -> passed

### Bugs Found

- The first v0.12 test fixture used a TOML basic string for a Windows regex and produced an invalid `\C` regex escape after TOML parsing. The fixture and README were updated to show TOML literal strings for Windows path regex patterns.

### Next

- Consider adding a documented `threadvault config show --json` command if config troubleshooting becomes common.

## 2026-06-30 - v0.13 Config Observability

### Completed

- Added v0.13 phase plan and external project review documents.
- Added `describe_app_config()` and `diagnose_app_config()` to `app_config.py`.
- Added `threadvault config show`.
- Added `threadvault config doctor`.
- Kept default config summaries privacy-preserving by hiding raw allowlist text/pattern values.
- Added explicit `--include-values` local debugging opt-in for `config show`.
- Added tests for missing config, valid config, invalid TOML, invalid regex, invalid keep values, JSON output, and v0.13 docs.
- Added `config_show` and `config_doctor` JSON schemas and refreshed packaged schema files.
- Added config commands to capabilities JSON output.
- Updated README and research Markdown appendices.

### Validation

- Completed partial implementation validation:
  - `py -3.12 -m pytest tests\test_v13_config_cli.py tests\test_v12_app_config.py tests\test_v11_audit_config.py` -> 16 passed
  - `py -3.12 -m ruff check src\threadvault\app_config.py src\threadvault\cli.py tests\test_v13_config_cli.py` -> passed
  - `py -3.12 -m pytest tests\test_v13_config_cli.py tests\test_v06_schemas.py tests\test_v05_contracts.py` -> 18 passed
  - `py -3.12 -m ruff check src\threadvault\schemas.py src\threadvault\store.py tests\test_v13_config_cli.py` -> passed
- Completed final verification:
  - `py -3.12 -m pytest` -> 57 passed
  - `py -3.12 -m ruff check .` -> passed
  - `threadvault config show --json` -> passed
  - `threadvault config doctor --json` -> passed
  - `threadvault config show --config <threadvault.toml> --json` -> passed
  - `threadvault config doctor --config <threadvault.toml> --json` -> passed
  - `threadvault config doctor --config <bad.toml> --json` -> returned structured JSON and exit 1 as expected
  - `threadvault schemas show config_show --json` -> passed
  - `threadvault schemas show config_doctor --json` -> passed
  - `threadvault validate-json --schema config_show --input <show.json> --json` -> passed
  - `threadvault validate-json --schema config_doctor --input <doctor.json> --json` -> passed
  - `threadvault capabilities --json` -> passed

### Bugs Found

- Initial implementation omitted JSON schemas/capabilities entries for the new config outputs. Added `config_show` and `config_doctor` schemas, refreshed packaged schemas, and added a validation regression test.

### Next

- Run full test and lint suite, then smoke-test `threadvault config show/doctor`.

## 2026-06-30 - v0.14 Config Init Template

### Completed

- Added v0.14 phase plan and external project review documents.
- Added `default_config_template()` and `init_app_config()` to `app_config.py`.
- Added `threadvault config init`.
- Kept config initialization safe by refusing to overwrite existing files unless `--force` is explicit.
- Included generated config health diagnostics in `config init --json`.
- Added `config_init` JSON schema and refreshed packaged schema files.
- Added `config init` to capabilities JSON output.
- Fixed README Windows path regex examples to use TOML literal strings.
- Added tests for template validity, create, no-overwrite, force overwrite, schema validation, README regex example, and v0.14 docs.

### Validation

- Completed partial implementation validation:
  - `py -3.12 -m pytest tests\test_v14_config_init.py tests\test_v13_config_cli.py tests\test_v06_schemas.py tests\test_v05_contracts.py` -> 24 passed
  - `py -3.12 -m ruff check src\threadvault\app_config.py src\threadvault\cli.py src\threadvault\schemas.py src\threadvault\store.py tests\test_v14_config_init.py` -> initially failed on one long schema line, then passed after wrapping
  - `py -3.12 -m pytest tests\test_v14_config_init.py` -> 6 passed
- Completed final verification:
  - `py -3.12 -m pytest` -> 63 passed
  - `py -3.12 -m ruff check .` -> passed
  - `threadvault config init --config <tmp>/threadvault.toml --json` -> passed
  - `threadvault config doctor --config <tmp>/threadvault.toml --json` -> passed
  - `threadvault config init --config <tmp>/threadvault.toml --json` -> returned structured `config_exists` and exit 1 as expected
  - `threadvault config init --config <tmp>/threadvault.toml --force --json` -> passed
  - `threadvault validate-json --schema config_init --input <payload.json> --json` -> passed
  - `threadvault schemas show config_init --json` -> passed
  - `threadvault capabilities --json` -> passed
  - `threadvault --help` -> passed

### Bugs Found

- README still had a Windows path regex example using a TOML basic string despite the v0.12 finding. Updated it to a TOML literal string and added a regression test.
- `ruff` caught a long `config_init` schema required list. Wrapped it before final validation.

### Next

- Consider adding `config path --json` only if users need a smaller command than `config show`.

## 2026-06-30 - v0.15 Database Backup

### Completed

- Added v0.15 phase plan and external project review documents.
- Added SQLite backup helper using `Connection.backup()`.
- Added `ArchiveStore.backup()`.
- Added `threadvault backup --out PATH --force --json`.
- Added `backup` JSON schema and refreshed packaged schema files.
- Added `backup` to capabilities JSON output.
- Added tests for directory backup, explicit file backup, no-overwrite behavior, force overwrite, readable backup database, schema validation, and v0.15 docs.
- Updated README and research Markdown appendices.

### Validation

- Completed partial implementation validation:
  - `py -3.12 -m pytest tests\test_v15_backup.py tests\test_v06_schemas.py tests\test_v05_contracts.py` -> initially failed on force-overwrite of a non-SQLite file, then 15 passed after fix
  - `py -3.12 -m ruff check src\threadvault\database.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v15_backup.py` -> initially failed on import ordering, then passed after fix
- Completed final verification:
  - `py -3.12 -m pytest` -> 68 passed
  - `py -3.12 -m ruff check .` -> passed
  - `threadvault import --codex-home tests\fixtures\codex_home --db <tmp>/threadvault.db --json` -> passed
  - `threadvault backup --db <tmp>/threadvault.db --out <tmp>/backups --json` -> passed
  - `threadvault backup --db <tmp>/threadvault.db --out <tmp>/backup.db --json` -> passed
  - `threadvault backup --db <tmp>/threadvault.db --out <tmp>/backup.db --json` -> returned structured `backup_exists` and exit 1 as expected
  - `threadvault backup --db <tmp>/threadvault.db --out <tmp>/backup.db --force --json` -> passed
  - `threadvault validate-json --schema backup --input <payload.json> --json` -> passed
  - `threadvault schemas show backup --json` -> passed
  - `threadvault capabilities --json` -> passed
  - `threadvault --help` -> passed

### Bugs Found

- `backup --force` failed when the existing destination was not a SQLite database because SQLite tried to open the old file before backup. Fixed by unlinking existing destination files when `force=True`.
- `ruff` caught import ordering in `store.py`; imports were consolidated.

### Next

- Consider a future restore design only after documenting overwrite, validation, and backup provenance safeguards.

## 2026-06-30 - v0.16 Backup Verify

### Completed

- Added v0.16 phase plan and external project review documents.
- Added read-only SQLite connection helper.
- Added `verify_database_backup()` using `PRAGMA integrity_check`, existing database doctor checks, schema version lookup, and stats.
- Added `ArchiveStore.verify_backup()`.
- Added `threadvault backup-verify --backup PATH --json`.
- Added `backup_verify` JSON schema and refreshed packaged schema files.
- Added `backup-verify` to capabilities JSON output.
- Added tests for valid backup verification, missing backup file, non-SQLite file, schema validation, and v0.16 docs.
- Updated README and research Markdown appendices.

### Validation

- Completed partial implementation validation:
  - `py -3.12 -m pytest tests\test_v16_backup_verify.py tests\test_v15_backup.py tests\test_v06_schemas.py tests\test_v05_contracts.py` -> 19 passed
  - `py -3.12 -m ruff check src\threadvault\database.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v16_backup_verify.py` -> initially failed on import sorting, then passed after `ruff --fix`
  - `py -3.12 -m pytest tests\test_v16_backup_verify.py` -> 4 passed
- Completed final verification:
  - `py -3.12 -m pytest` -> 72 passed
  - `py -3.12 -m ruff check .` -> passed
  - `threadvault import --codex-home tests\fixtures\codex_home --db <tmp>/threadvault.db --json` -> passed
  - `threadvault backup --db <tmp>/threadvault.db --out <tmp>/backup.db --json` -> passed
  - `threadvault backup-verify --backup <tmp>/backup.db --json` -> passed
  - `threadvault validate-json --schema backup_verify --input <payload.json> --json` -> passed
  - `threadvault backup-verify --backup <bad.db> --json` -> returned structured `invalid_sqlite_database` and exit 1 as expected
  - `threadvault schemas show backup_verify --json` -> passed
  - `threadvault capabilities --json` -> passed
  - `threadvault --help` -> passed

### Bugs Found

- `ruff` caught import ordering in `store.py`; fixed with ruff's import organizer.

### Next

- Keep restore out of scope until a separate phase defines overwrite, provenance, and validation safeguards.

## 2026-06-30 - v0.17 Backup History

### Completed

- Added v0.17 phase plan and external project review documents.
- Added `backup_history.py` for backup directory discovery.
- Added `threadvault backup-history list`.
- Added `threadvault backup-history latest`.
- Added `threadvault backup-history verify-latest`.
- Added `backup_history_list`, `backup_history_latest`, and `backup_history_verify_latest` JSON schemas.
- Added backup-history commands to capabilities JSON output.
- Added tests for list/latest ordering, verify-latest success, empty directory structured error, invalid backup warnings, schema validation, and v0.17 docs.
- Updated README and research Markdown appendices.

### Validation

- Completed partial implementation validation:
  - `py -3.12 -m pytest tests\test_v17_backup_history.py tests\test_v16_backup_verify.py tests\test_v15_backup.py tests\test_v06_schemas.py tests\test_v05_contracts.py` -> 23 passed
  - `py -3.12 -m ruff check src\threadvault\backup_history.py src\threadvault\cli.py src\threadvault\schemas.py src\threadvault\store.py tests\test_v17_backup_history.py` -> passed
- Completed final verification:
  - `py -3.12 -m pytest` -> 76 passed
  - `py -3.12 -m ruff check .` -> passed
  - `threadvault import --codex-home tests\fixtures\codex_home --db <tmp>/threadvault.db --json` -> passed
  - `threadvault backup --db <tmp>/threadvault.db --out <tmp>/backups --json` -> passed
  - `threadvault backup-history list --dir <tmp>/backups --json` -> passed
  - `threadvault backup-history latest --dir <tmp>/backups --json` -> passed
  - `threadvault backup-history verify-latest --dir <tmp>/backups --json` -> passed
  - `threadvault validate-json --schema backup_history_list --input <payload.json> --json` -> passed
  - `threadvault validate-json --schema backup_history_latest --input <payload.json> --json` -> passed
  - `threadvault validate-json --schema backup_history_verify_latest --input <payload.json> --json` -> passed
  - `threadvault schemas show backup_history_list --json` -> passed
  - `threadvault schemas show backup_history_latest --json` -> passed
  - `threadvault schemas show backup_history_verify_latest --json` -> passed
  - `threadvault capabilities --json` -> passed
  - `threadvault --help` -> passed

### Bugs Found

- No implementation bugs found in the first v0.17 validation pass.

### Next

- Consider backup retention/prune only after backup-specific safeguards are designed.

## 2026-06-30 - v0.18 Backup Retention

### Completed

- Added v0.18 phase plan and external project review documents.
- Added `prune_backup_history()` to the backup history module.
- Added `threadvault backup-history prune --dir DIR --keep N [--apply] --json`.
- Kept backup pruning dry-run by default; deletion requires explicit `--apply`.
- Scoped deletion to valid canonical `threadvault-backup-*.db` files discovered by backup-history listing.
- Preserved malformed backup-like files as warnings instead of deleting them automatically.
- Added `backup_history_prune` JSON schema and refreshed packaged schema files.
- Added `backup-history prune` to capabilities JSON output.
- Added tests for dry-run behavior, apply deletion, invalid backup preservation, schema validation, and v0.18 docs.
- Updated README and research Markdown appendices.

### Validation

- Completed partial implementation validation:
  - `py -3.12 -m pytest tests\test_v18_backup_prune.py tests\test_v17_backup_history.py` -> 7 passed
  - `py -3.12 -m ruff check src\threadvault\backup_history.py tests\test_v18_backup_prune.py` -> passed
- Completed final verification:
  - `py -3.12 -m pytest` -> 79 passed
  - `py -3.12 -m ruff check .` -> passed
  - `threadvault import --codex-home tests\fixtures\codex_home --db <tmp>\threadvault.db --json` -> passed
  - `threadvault backup --db <tmp>\threadvault.db --out <tmp>\backups\threadvault-backup-20260630T000000Z.db --json` -> passed
  - `threadvault backup-history prune --dir <tmp>\backups --keep 2 --json` -> passed
  - `threadvault backup-history prune --dir <tmp>\backups --keep 2 --apply --json` -> passed
  - `threadvault validate-json --schema backup_history_prune --input <payload.json> --json` -> passed
  - `threadvault schemas show backup_history_prune --json` -> passed
  - `threadvault capabilities --json` -> passed
  - `threadvault --help` -> passed

### Bugs Found

- On Windows, deleting backups immediately after verification could raise `PermissionError` because SQLite file handles may linger briefly. Fixed by collecting garbage before deletion and retrying unlink on `PermissionError`.

### Next

- Consider retention config for backup-history only after observing whether users want a shared retention policy with audit-history.

## 2026-06-30 - v0.19 Backup Retention Config

### Completed

- Added v0.19 phase plan and external project review documents.
- Extended `threadvault.app_config.AppConfig` with `backup_history_keep`.
- Added `[backup_history] keep = N` parsing and validation.
- Updated the starter config template, `config show`, and `config doctor` summaries to include backup retention.
- Updated `backup-history prune` so `--keep` is optional when config provides `backup_history.keep`.
- Preserved precedence: CLI `--keep` overrides config.
- Added `keep_source` to `backup_history_prune` JSON output and schema.
- Added v0.19 tests for config default, CLI override, missing keep, invalid config, schema validation, and docs.
- Updated README and research Markdown appendices.

### Validation

- Completed partial implementation validation:
  - `py -3.12 -m pytest tests\test_v19_backup_config.py tests\test_v18_backup_prune.py tests\test_v13_config_cli.py tests\test_v12_app_config.py tests\test_v06_schemas.py` -> 24 passed
  - `py -3.12 -m ruff check tests\test_v19_backup_config.py --fix` -> fixed one import-order issue
- Completed final verification:
  - `py -3.12 -m pytest` -> 85 passed
  - `py -3.12 -m ruff check .` -> passed
  - `threadvault import --codex-home tests\fixtures\codex_home --db <tmp>\threadvault.db --json` -> passed
  - `threadvault backup --db <tmp>\threadvault.db --out <tmp>\backups\threadvault-backup-20260630T000000Z.db --json` -> passed
  - `threadvault backup-history prune --dir <tmp>\backups --config <threadvault.toml> --json` -> passed with `keep_source=config`
  - `threadvault backup-history prune --dir <tmp>\backups --config <threadvault.toml> --keep 1 --json` -> passed with `keep_source=cli`
  - `threadvault validate-json --schema backup_history_prune --input <payload.json> --json` -> passed
  - `threadvault config show --config <threadvault.toml> --json` -> passed and reported `backup_history.keep`
  - `threadvault schemas show backup_history_prune --json` -> passed
  - `threadvault capabilities --json` -> passed
  - `threadvault --help` -> passed

### Bugs Found

- `ruff` caught import ordering in `tests/test_v19_backup_config.py`; fixed with ruff's import organizer.

### Next

- Consider whether backup retention config should support named profiles only if real users need different policies for daily and release backups.

## 2026-06-30 - v0.20 Backup Provenance Manifest

### Completed

- Added v0.20 phase plan and external project review documents.
- Added `threadvault.backup_manifest` module for sidecar manifest generation and verification.
- Updated `backup` to write `<backup>.manifest.json` by default.
- Added `backup --no-manifest` for scripts that only want the SQLite `.db`.
- Added `backup-manifest --backup PATH --json`.
- Added `backup-verify --manifest` to embed read-only manifest verification in backup verification.
- Added `backup_manifest` JSON schema and refreshed packaged schema files.
- Added tests for default manifest writing, no-manifest mode, modified backup detection, schema validation, and v0.20 docs.
- Updated README and research Markdown appendices.

### Validation

- Completed partial implementation validation:
  - `py -3.12 -m pytest tests\test_v20_backup_manifest.py tests\test_v16_backup_verify.py tests\test_v15_backup.py tests\test_v06_schemas.py tests\test_v05_contracts.py` -> 24 passed
  - `py -3.12 -m ruff check src\threadvault\store.py tests\test_v20_backup_manifest.py --fix` -> fixed import ordering
- Completed final verification:
  - `py -3.12 -m pytest` -> 90 passed
  - `py -3.12 -m ruff check .` -> passed
  - `threadvault import --codex-home tests\fixtures\codex_home --db <tmp>\threadvault.db --json` -> passed
  - `threadvault backup --db <tmp>\threadvault.db --out <tmp>\backups --json` -> passed and wrote a sidecar manifest
  - `threadvault backup-manifest --backup <backup.db> --json` -> passed
  - `threadvault backup-verify --backup <backup.db> --manifest --json` -> passed
  - `threadvault validate-json --schema backup_manifest --input <payload.json> --json` -> passed
  - `threadvault validate-json --schema backup_verify --input <payload.json> --json` -> passed
  - `threadvault schemas show backup_manifest --json` -> passed
  - `threadvault capabilities --json` -> passed
  - `threadvault --help` -> passed

### Bugs Found

- `ruff` caught two long lines in `backup_manifest.py` and import ordering in new/changed files. Both were fixed before final validation.

### Next

- Consider restore only after a separate restore safety plan defines destination handling, overwrite refusal, pre-restore backup, and provenance requirements.

## 2026-06-30 - v0.21 Restore Plan Preflight

### Completed

- Added v0.21 phase plan and external project review documents.
- Added `threadvault.restore_plan` module for read-only restore preflight.
- Added `ArchiveStore.restore_plan()`.
- Added `threadvault restore-plan --backup BACKUP --target-db TARGET --json`.
- Reused existing backup verification and backup manifest verification instead of duplicating SQLite checks.
- Added `restore_plan` JSON schema and refreshed packaged schema files.
- Added tests for valid manifest-backed backups, missing manifest warnings, existing target warnings, target-equals-backup errors, schema validation, and v0.21 docs.
- Updated README and research Markdown appendices.

### Validation

- Completed partial implementation validation:
  - `py -3.12 -m pytest tests\test_v21_restore_plan.py tests\test_v20_backup_manifest.py tests\test_v16_backup_verify.py tests\test_v06_schemas.py tests\test_v05_contracts.py` -> 24 passed
- Completed final verification:
  - `py -3.12 -m pytest` -> 95 passed
  - `py -3.12 -m ruff check .` -> passed
  - `threadvault import --codex-home tests\fixtures\codex_home --db <tmp>\threadvault.db --json` -> passed
  - `threadvault backup --db <tmp>\threadvault.db --out <tmp>\backups --json` -> passed
  - `threadvault restore-plan --backup <backup.db> --target-db <restore>\threadvault-restored.db --json` -> passed
  - `threadvault validate-json --schema restore_plan --input <payload.json> --json` -> passed
  - `threadvault schemas show restore_plan --json` -> passed
  - `threadvault capabilities --json` -> passed
  - `threadvault --help` -> passed
  - Smoke confirmed `restore-plan` did not create the target database.

### Bugs Found

- `ruff` caught one long warning line in `restore_plan.py`; fixed before final validation.

### Next

- Consider an actual restore command only after defining explicit overwrite refusal, mandatory pre-restore backup, manifest requirements, and post-restore verification.

## 2026-07-01 - v0.22 Safe Restore

### Completed

- Added v0.22 phase plan and external project review documents.
- Added `threadvault.restore` module for safety-gated restore execution.
- Added `ArchiveStore.restore()`.
- Added `threadvault restore --backup BACKUP --target-db TARGET --json`.
- Kept restore dry-run by default; writes require `--apply`.
- Required backup verification before apply.
- Required manifest verification before apply, with explicit `--allow-missing-manifest` for legacy backups.
- Required `--overwrite` for existing targets.
- Required `--pre-restore-backup-dir` when applying overwrite, and reused SQLite backup API for pre-restore target backups.
- Verified restored targets after apply.
- Added `restore` JSON schema and refreshed packaged schema files.
- Added tests for dry-run, apply, overwrite gates, pre-restore backup, missing manifest opt-in, schema validation, and v0.22 docs.
- Updated README and research Markdown appendices.

### Validation

- Completed partial implementation validation:
  - `py -3.12 -m pytest tests\test_v22_restore.py tests\test_v21_restore_plan.py tests\test_v20_backup_manifest.py tests\test_v15_backup.py tests\test_v06_schemas.py` -> 25 passed
  - `py -3.12 -m ruff check src\threadvault\restore.py --fix` -> fixed one unused import
- Completed final verification:
  - `py -3.12 -m pytest` -> 102 passed
  - `py -3.12 -m ruff check .` -> passed
  - `threadvault import --codex-home tests\fixtures\codex_home --db <tmp>\threadvault.db --json` -> passed
  - `threadvault backup --db <tmp>\threadvault.db --out <tmp>\backups --json` -> passed
  - `threadvault restore --backup <backup.db> --target-db <restore>\threadvault-restored.db --json` -> passed and wrote nothing
  - `threadvault restore --backup <backup.db> --target-db <restore>\threadvault-restored.db --apply --json` -> passed
  - `threadvault validate-json --schema restore --input <payload.json> --json` -> passed
  - `threadvault backup-verify --backup <restored.db> --manifest --json` -> passed
  - `threadvault schemas show restore --json` -> passed
  - `threadvault capabilities --json` -> passed
  - `threadvault --help` -> passed

### Bugs Found

- `ruff` caught an unused `doctor` import in `restore.py`; removed before final validation.
- Smoke testing found that restore copied the original backup manifest beside the target, leaving manifest paths and checksum provenance tied to the source backup. Fixed by generating a fresh target manifest after restore and added a regression assertion that `backup-manifest --backup <restored.db>` succeeds.

### Next

- Consider adding a restore history log only if users need an audit trail of applied restores.

## 2026-07-01 - v0.23 Restore History

### Completed

- Added v0.23 phase plan and external project review documents.
- Added `threadvault.restore_history` module for local JSONL restore history.
- Added `--restore-history PATH` to `restore`.
- Appended restore history only after successful `restore --apply`.
- Added `restore-history list --history PATH --json`.
- Added `restore-history latest --history PATH --json`.
- Added malformed history line warnings while continuing list/latest reads.
- Added `restore_history_list` and `restore_history_latest` schemas and refreshed packaged schema files.
- Added tests for custom history writing, list/latest, malformed line tolerance, dry-run/failed restore no-write behavior, schema validation, and v0.23 docs.
- Updated README and research Markdown appendices.

### Validation

- Completed partial implementation validation:
  - `py -3.12 -m pytest tests\test_v23_restore_history.py tests\test_v22_restore.py tests\test_v06_schemas.py tests\test_v05_contracts.py` -> 22 passed
  - `py -3.12 -m ruff check src\threadvault\restore_history.py src\threadvault\restore.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v23_restore_history.py` -> passed
- Completed final verification:
  - `py -3.12 -m pytest` -> 107 passed
  - `py -3.12 -m ruff check .` -> passed
  - `threadvault import --codex-home tests\fixtures\codex_home --db <tmp>\threadvault.db --json` -> passed
  - `threadvault backup --db <tmp>\threadvault.db --out <tmp>\backups --json` -> passed
  - `threadvault restore --backup <backup.db> --target-db <restore>\threadvault-restored.db --apply --restore-history <history.jsonl> --json` -> passed
  - `threadvault restore-history list --history <history.jsonl> --json` -> passed
  - `threadvault restore-history latest --history <history.jsonl> --json` -> passed
  - `threadvault validate-json --schema restore_history_list --input <payload.json> --json` -> passed
  - `threadvault validate-json --schema restore_history_latest --input <payload.json> --json` -> passed
  - `threadvault schemas show restore_history_list --json` -> passed
  - `threadvault capabilities --json` -> passed
  - `threadvault --help` -> passed

### Bugs Found

- Initial implementation referenced a nonexistent `config.app_data_dir()`. Fixed by using existing `default_data_dir()`.
- `ruff` caught long history warning/test lines; wrapped before validation.

### Next

- Consider adding restore history retention only if local history grows enough to need pruning.

## 2026-07-01 - v0.24 Restore History Retention

### Completed

- Added v0.24 phase plan and external project review documents.
- Added `prune_restore_history()` to `threadvault.restore_history`.
- Added `threadvault restore-history prune --history PATH --keep N [--apply] --json`.
- Kept restore history pruning dry-run by default.
- Implemented apply as a rewrite of the JSONL history file, not deletion of backup/database artifacts.
- Preserved malformed/non-object history lines during apply and reported warnings.
- Added `restore_history_prune` schema and refreshed packaged schema files.
- Added tests for dry-run, apply, malformed-line preservation, missing history file behavior, schema validation, and v0.24 docs.
- Updated README and research Markdown appendices.

### Validation

- Completed partial implementation validation:
  - `py -3.12 -m pytest tests\test_v24_restore_history_prune.py tests\test_v23_restore_history.py tests\test_v06_schemas.py tests\test_v05_contracts.py` -> 20 passed
  - `py -3.12 -m ruff check src\threadvault\restore_history.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v24_restore_history_prune.py` -> passed
- Completed final verification:
  - `py -3.12 -m pytest` -> 112 passed
  - `py -3.12 -m ruff check .` -> passed
  - `threadvault import --codex-home tests\fixtures\codex_home --db <tmp>\threadvault.db --json` -> passed
  - `threadvault backup --db <tmp>\threadvault.db --out <tmp>\backups --json` -> passed
  - Three `threadvault restore --apply --restore-history <history.jsonl>` commands -> passed
  - `threadvault restore-history prune --history <history.jsonl> --keep 2 --json` -> passed and did not rewrite
  - `threadvault restore-history prune --history <history.jsonl> --keep 2 --apply --json` -> passed and rewrote to two valid records
  - `threadvault validate-json --schema restore_history_prune --input <payload.json> --json` -> passed
  - `threadvault restore-history latest --history <history.jsonl> --json` -> passed
  - `threadvault schemas show restore_history_prune --json` -> passed
  - `threadvault capabilities --json` -> passed
  - `threadvault --help` -> passed

### Bugs Found

- No implementation bugs found in the first v0.24 validation pass.

### Next

- Consider config-driven restore history retention only if command behavior proves useful in real local workflows.

## 2026-07-01 - v0.25 Restore History Retention Config

### Completed

- Added v0.25 phase plan and external project review documents.
- Extended `threadvault.app_config.AppConfig` with `restore_history_keep`.
- Added `[restore_history] keep = 20` to the default local config template.
- Parsed and validated `restore_history.keep` with the same integer rules as audit/backup retention.
- Added restore history retention information to `config show` and config diagnostics.
- Added `--config PATH` to `restore-history prune`.
- Made `restore-history prune --keep` optional when `[restore_history].keep` is configured.
- Preserved CLI precedence over config and surfaced `keep_source` in JSON output.
- Added `keep_source` to the `restore_history_prune` JSON schema and refreshed packaged schemas.
- Added regression tests for config default, CLI override, missing keep/config, invalid config, config show, schema validation, and v0.25 docs.
- Updated README and research Markdown appendices.

### Validation

- Completed partial implementation validation:
  - `py -3.12 -m pytest tests\test_v25_restore_history_config.py tests\test_v24_restore_history_prune.py tests\test_v13_config_cli.py tests\test_v12_app_config.py tests\test_v06_schemas.py` -> 29 passed
- Completed final verification:
  - `py -3.12 -m ruff check src\threadvault\app_config.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v25_restore_history_config.py tests\test_v12_app_config.py` -> passed
  - `py -3.12 -m pytest` -> 120 passed
  - `py -3.12 -m ruff check .` -> passed
  - `threadvault import --codex-home tests\fixtures\codex_home --db <tmp>\threadvault.db --json` -> passed
  - `threadvault backup --db <tmp>\threadvault.db --out <tmp>\backups --json` -> passed
  - Three `threadvault restore --apply --restore-history <history.jsonl>` commands -> passed
  - `threadvault restore-history prune --history <history.jsonl> --config <threadvault.toml> --json` -> passed with `keep_source=config`
  - `threadvault restore-history prune --history <history.jsonl> --config <threadvault.toml> --keep 1 --json` -> passed with `keep_source=cli`
  - `threadvault validate-json --schema restore_history_prune --input <payload.json> --json` -> passed
  - `threadvault config show --config <threadvault.toml> --json` -> passed
  - `threadvault schemas show restore_history_prune --json` -> passed
  - `threadvault capabilities --json` -> passed
  - `threadvault --help` -> passed

### Bugs Found

- No implementation bugs found in the first v0.25 targeted validation pass.

### Next

- Consider adding a shared retention helper only if audit/backup/restore resolution logic grows beyond the current small repeated pattern.

## 2026-07-01 - v0.26 Retention Resolution Helper

### Completed

- Added v0.26 phase plan and external project review documents.
- Added `threadvault.retention.resolve_retention_keep()` for shared retention keep resolution.
- Updated audit, backup, and restore history prune commands to use the shared helper.
- Preserved public command options, error messages, JSON `keep_source`, and dry-run/apply behavior.
- Added direct helper tests covering CLI precedence, all three config sections, missing config errors, and invalid config propagation.
- Refreshed packaged JSON schemas.
- Updated README and research Markdown appendices.

### Validation

- Completed partial implementation validation:
  - `py -3.12 -m pytest tests\test_v26_retention.py tests\test_v11_audit_config.py tests\test_v19_backup_config.py tests\test_v25_restore_history_config.py` -> 22 passed
- Completed final verification:
  - `py -3.12 -m ruff check src\threadvault\retention.py src\threadvault\cli.py tests\test_v26_retention.py` -> passed
  - `py -3.12 -m pytest` -> 125 passed
  - `py -3.12 -m ruff check .` -> passed
  - `threadvault audit-history prune --dir <reports> --config <threadvault.toml> --json` -> passed with `keep_source=config`
  - `threadvault backup-history prune --dir <backups> --config <threadvault.toml> --json` -> passed with `keep_source=config`
  - `threadvault restore-history prune --history <history.jsonl> --config <threadvault.toml> --json` -> passed with `keep_source=config`
  - `threadvault --help` -> passed

### Bugs Found

- No implementation bugs found in the first v0.26 targeted validation pass.

### Next

- Continue hardening maintenance commands only where repeated behavior has real drift risk.

## 2026-07-01 - v0.27 Retention Schema Contract

### Completed

- Added v0.27 phase plan and external project review documents.
- Tightened `audit_history_prune`, `backup_history_prune`, and `restore_history_prune` schemas so `keep_source` is required and restricted to `cli|config`.
- Added a shared `KEEP_SOURCE_SCHEMA` in `threadvault.schemas`.
- Added schema contract tests for accepted and rejected `keep_source` values.
- Refreshed packaged JSON schemas.
- Updated README and research Markdown appendices.

### Validation

- Completed partial implementation validation:
  - `py -3.12 -m pytest tests\test_v27_retention_schema_contract.py tests\test_v06_schemas.py tests\test_v11_audit_config.py tests\test_v19_backup_config.py tests\test_v25_restore_history_config.py` -> 24 passed
- Completed final verification:
  - `py -3.12 -m ruff check src\threadvault\schemas.py tests\test_v27_retention_schema_contract.py` -> passed after import-order fix
  - `py -3.12 -m pytest` -> 129 passed
  - `py -3.12 -m ruff check .` -> passed
  - `threadvault schemas show audit_history_prune --json` -> passed; `keep_source` required and enum `cli,config`
  - `threadvault schemas show backup_history_prune --json` -> passed; `keep_source` required and enum `cli,config`
  - `threadvault schemas show restore_history_prune --json` -> passed; `keep_source` required and enum `cli,config`
  - `threadvault --help` -> passed

### Bugs Found

- Found schema drift: audit prune had enum but did not require `keep_source`; backup and restore prune required `keep_source` but accepted any string. Fixed by sharing one schema snippet and adding contract tests.
- `ruff` found unsorted imports in the new v0.27 test file. Fixed with `ruff --fix`.

### Next

- Continue auditing public JSON schemas for places where runtime behavior is narrower than the published contract.

## 2026-07-01 - v0.28 Capabilities Schema Contract

### Completed

- Added v0.28 phase plan and external project review documents.
- Tightened the `capabilities` schema to require stable runtime discovery fields:
  - `stability_policy`
  - `json_outputs`
  - `export_formats`
  - `export_profiles`
  - `privacy_modes`
  - `search_fields`
  - `feature_flags`
- Added missing capabilities schema properties for export profiles, privacy modes, search fields, and stability policy.
- Updated `robot-docs schemas --json` capabilities field summary to match the schema.
- Added tests that validate real `threadvault capabilities --json` output against the capabilities schema.
- Refreshed packaged JSON schemas.
- Updated README and research Markdown appendices.

### Validation

- Completed partial implementation validation:
  - `py -3.12 -m pytest tests\test_v28_capabilities_schema_contract.py tests\test_v05_contracts.py tests\test_v06_schemas.py` -> 15 passed
- Completed final verification:
  - `py -3.12 -m ruff check src\threadvault\schemas.py src\threadvault\store.py tests\test_v28_capabilities_schema_contract.py` -> passed after import-order fix
  - `py -3.12 -m pytest` -> 134 passed
  - `py -3.12 -m ruff check .` -> passed
  - `threadvault capabilities --json` -> passed
  - `threadvault schemas show capabilities --json` -> passed; stable discovery fields are required
  - `threadvault robot-docs schemas --json` -> passed; capabilities summary includes stable discovery fields
  - `threadvault validate-json --schema capabilities --input <capabilities.json> --json` -> passed
  - `threadvault --help` -> passed

### Bugs Found

- Found capabilities schema drift: README/runtime exposed stable discovery fields that were not required by the schema. Fixed by requiring the existing runtime fields and adding schema tests.
- `ruff` found unsorted imports in the new v0.28 test file. Fixed with `ruff --fix`.

### Next

- Continue auditing public JSON schemas for runtime/schema/documentation drift.

## 2026-07-01 - v0.29 Doctor Schema Contract

### Completed

- Added v0.29 phase plan and external project review documents.
- Tightened the `doctor` schema to require stable runtime diagnostic fields:
  - `parse_health`
  - `schema_version`
  - `schema_objects`
  - `maintenance_suggestions`
  - `python`
  - `platform`
  - `db_path`
  - `codex_home`
  - `session_dirs`
  - `missing_session_dirs`
  - `jsonl_files`
  - `codex_state`
- Added tests that validate real `threadvault doctor --json` output against the doctor schema.
- Refreshed packaged JSON schemas.
- Updated README and research Markdown appendices.

### Validation

- Completed partial implementation validation:
  - `py -3.12 -m pytest tests\test_v29_doctor_schema_contract.py tests\test_v05_contracts.py tests\test_v06_schemas.py` -> 14 passed
- Completed final verification:
  - `py -3.12 -m ruff check src\threadvault\schemas.py tests\test_v29_doctor_schema_contract.py` -> passed
  - `py -3.12 -m pytest` -> 138 passed
  - `py -3.12 -m ruff check .` -> passed
  - `threadvault doctor --db <tmp.db> --codex-home tests\fixtures\codex_home --json` -> passed
  - `threadvault schemas show doctor --json` -> passed; stable doctor fields are required
  - `threadvault validate-json --schema doctor --input <doctor.json> --json` -> passed
  - `threadvault --help` -> passed

### Bugs Found

- Found doctor schema drift: runtime and README exposed schema objects, parse health, environment metadata, and Codex state diagnostics, but the schema only required early `ok/checks/stats` fields. Fixed by requiring stable top-level diagnostic fields.

### Next

- Continue auditing public JSON schemas for runtime/schema/documentation drift, then prepare a broader completion audit.

## 2026-07-01 - v0.30 Completion Gap Audit

### Completed

- Added v0.30 phase plan and external project review documents.
- Created `docs/v0/phases/phase-30-completion-gap-audit/completion-gap-audit.md`.
- Audited the current implementation against:
  - original CLI MVP requirements;
  - v0.2-v0.5 data-layer, privacy, real-corpus, and JSON contract goals;
  - later maintenance, backup, restore, retention, and schema-hardening phases.
- Classified deferred non-CLI scope: Web UI, TUI, desktop app, MCP server, REST API, vector database, cloud sync, team permissions, external LLM summarization, and deep Obsidian integration.
- Updated README with the completion/gap audit location.
- Updated research Markdown appendices.

### Validation

- Evidence collection completed:
  - `threadvault --help` -> passed and listed core/maintenance command groups
  - `threadvault capabilities --json` -> passed and reported 40 JSON outputs
  - `threadvault schemas list --json` -> passed and reported 29 schemas
- Completed final verification:
  - `py -3.12 -m pytest` -> 138 passed
  - `py -3.12 -m ruff check .` -> passed
  - `threadvault --help` -> passed
  - `threadvault capabilities --json` -> passed with 40 JSON outputs
  - `threadvault schemas list --json` -> passed with 29 schemas
  - `threadvault self-test --db <tmp.db> --json` -> passed
  - `threadvault doctor --db <tmp.db> --codex-home tests\fixtures\codex_home --json` -> passed

### Bugs Found

- No code bugs found in the v0.30 audit pass.

### Next

- Decide whether to perform a final CLI MVP acceptance pass, mark the long-running goal complete for the CLI/data-layer scope, or run a DOCX synchronization phase first.

## 2026-07-01 - v0.31 Final CLI MVP Acceptance

### Completed

- Added v0.31 phase plan and external project review documents.
- Ran a full temporary-workspace CLI acceptance chain using `tests/fixtures/codex_home`.
- Created `docs/v0/phases/phase-31-final-cli-mvp-acceptance/final-cli-mvp-acceptance.md`.
- Verified import, list, search, summarize, multi-format export, privacy scan/redaction, stats, doctor, self-test, reindex, backup, manifest, restore-plan, restore, and restore history.
- Validated representative JSON payloads with `threadvault validate-json`.
- Updated README and research Markdown appendices.

### Acceptance Smoke

- Overall acceptance chain -> passed.
- `threadvault import` -> imported 4 sessions, 28 events, 7 warnings.
- `threadvault search pytest --fields minimal` -> 3 hits.
- `threadvault summarize --session sess-current` -> 6 evidence event IDs.
- `threadvault export --format md/json/jsonl/csv` -> all files written.
- `threadvault privacy-scan --session sess-privacy` -> 3 findings.
- `threadvault export --privacy-mode redact` -> redacted export written.
- `threadvault reindex --fts-only` -> `events=28`, `events_fts=28`.
- `threadvault backup`, `backup-verify --manifest`, `backup-manifest` -> passed.
- `threadvault restore-plan`, `restore --apply --restore-history`, `restore-history list` -> passed.

### Validation

- Completed final verification:
  - `py -3.12 -m pytest` -> 138 passed
  - `py -3.12 -m ruff check .` -> passed

### Bugs Found

- No code bugs found in the v0.31 acceptance smoke.

### Next

- CLI/data-layer objective is ready to mark complete. DOCX synchronization remains a separate optional deliverable.

## 2026-07-01 - Major Version Roadmap Planning

### Completed

- Added `docs/roadmap/major-version-roadmap.md`.
- Added `docs/roadmap/v1-personal-knowledge-layer.md`.
- Added `docs/roadmap/v2-retrieval-and-interfaces.md`.
- Added `docs/roadmap/v3-clients-and-team-governance.md`.
- Reclassified deferred scope into `v1` personal knowledge layer, `v2` retrieval/interface layer, and `v3` richer client/team governance layer.
- Captured architecture deepening targets: `Ingestion Automation`, `Export Target`, `Summary Pipeline`, and `Retrieval` modules.
- Updated README roadmap links.

### Validation

- Planned validation:
  - `rg -n "major-version-roadmap|v1-personal-knowledge-layer|v2-retrieval-and-interfaces|v3-clients-and-team-governance" README.md docs`
  - `py -3.12 -m ruff check .`
  - `py -3.12 -m pytest`

### Bugs Found

- Not applicable. This phase only adds planning Markdown and does not change runtime behavior.

### Next

- Start v1 planning with the `Ingestion Automation` module before implementing Hook-driven workflows.

## 2026-07-01 - v1 Phase 01 Ingestion Automation Queue

### Completed

- Added `docs/v1/README.md` as the active v1 development archive index.
- Added `docs/v1/phases/phase-01-ingestion-automation-queue/plan.md` before implementation.
- Added `docs/v1/phases/phase-01-ingestion-automation-queue/acceptance.md` for phase validation evidence.
- Added the `threadvault.ingestion` module with a small queue interface:
  - `enqueue_ingestion`
  - `list_ingestion_queue`
  - `process_ingestion_queue`
- Added a persistent `ingestion_queue` table to the SQLite schema and bumped the internal database schema version to `3`.
- Added `ArchiveStore` methods for ingestion queue enqueue/list/process.
- Added the `threadvault ingest-queue` CLI group:
  - `enqueue`
  - `list`
  - `process`
- Kept `process` dry-run by default; imports only run when `--apply` is passed.
- Added `ingestion_enqueue`, `ingestion_queue_list`, and `ingestion_process` JSON schemas.
- Updated capabilities and robot schema discovery for the new queue workflow.
- Updated `docs/README.md`, root `README.md`, and `docs/THREADVAULT_USAGE_MANUAL.md` with v1 and queue navigation.
- Added `tests/test_v101_ingestion_queue.py`.

### Validation

- Completed partial validation:
  - `py -3.12 -m pytest tests\test_v101_ingestion_queue.py` -> 6 passed
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote ingestion queue schemas
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 144 passed
  - `threadvault ingest-queue --help` -> passed and listed `enqueue`, `list`, and `process`
  - `threadvault capabilities --json` -> passed and advertised `ingest-queue` plus `ingestion_queue: true`
  - `threadvault schemas list --json` -> passed and listed `ingestion_enqueue`, `ingestion_process`, and `ingestion_queue_list`
  - `Test-Path deep-research-report.md` -> `False`

### Bugs Found

- The first schema refresh attempt used Bash heredoc syntax in PowerShell and failed before changing files. Re-ran schema generation through `threadvault schemas write`.
- Inserting the new usage-manual section created duplicate `5.5` headings. Fixed the numbering for export and summary sections.

### Next

- Run full pytest, ruff, and CLI smoke checks.
- If validation passes, continue v1 with Hook integration on top of the queue interface or move to batch export manifests, depending on the next phase plan.

## 2026-07-01 - v1 Phase 02 Codex Hook Adapter

### Completed

- Used the `openai-docs` skill route for Codex Hook source lookup. The manual helper failed with HTTP 403, so official OpenAI web docs were used for Hook constraints.
- Added `docs/v1/phases/phase-02-codex-hook-adapter/plan.md` before implementation.
- Added `docs/v1/phases/phase-02-codex-hook-adapter/acceptance.md` for phase validation evidence.
- Updated `docs/v1/README.md` with the Phase 02 index row.
- Added `threadvault.codex_hooks`, a Hook adapter module with a small interface:
  - `handle_codex_hook_payload`
  - `build_codex_hook_config`
  - `hook_continue_response`
  - `infer_codex_home`
- Added `ArchiveStore.handle_codex_hook` and `ArchiveStore.codex_hook_config`.
- Added the `threadvault codex-hook` CLI group:
  - `ingest`
  - `config`
- Kept Hook ingestion lightweight: `codex-hook ingest` enqueues work and does not import transcripts.
- Made default Hook stdout Codex-compatible JSON. ThreadVault diagnostics require `--diagnostic-json`.
- Added `codex_hook_ingest` and `codex_hook_config` JSON schemas.
- Updated capabilities and robot schema discovery for the Codex Hook adapter.
- Updated `docs/THREADVAULT_USAGE_MANUAL.md` with Hook config and processing instructions.
- Added `tests/test_v102_codex_hook_adapter.py`.

### Validation

- Completed partial validation:
  - `py -3.12 -m pytest tests\test_v102_codex_hook_adapter.py` -> 9 passed after one small path-type fix
  - `py -3.12 -m ruff check src\threadvault\codex_hooks.py src\threadvault\cli.py src\threadvault\store.py tests\test_v102_codex_hook_adapter.py` -> passed after line-length and import-order fixes
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote Codex Hook schemas
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 153 passed
  - `threadvault codex-hook --help` -> passed and listed `ingest` and `config`
  - `threadvault codex-hook config --json` -> passed and emitted a `Stop` hook snippet
  - `threadvault capabilities --json` -> passed and advertised `codex-hook` plus `codex_hook_adapter: true`
  - `threadvault schemas list --json` -> passed and listed `codex_hook_ingest` and `codex_hook_config`

### Bugs Found

- `infer_codex_home()` initially accepted only string transcript paths. Tests exposed that a `Path` input was natural for module callers, so it now accepts both `str` and `Path`.
- Ruff flagged two long Typer option lines in `cli.py`; split them across lines.
- Ruff flagged import ordering in `store.py`; fixed with ruff.

### Next

- Run full pytest, ruff, and CLI smoke checks.
- If validation passes, continue v1 toward batch export manifests or a small Hook installation guidance phase.

## 2026-07-01 - v1 Phase 03 Export Target Manifest

### Completed

- Added `docs/v1/phases/phase-03-export-target-manifest/plan.md` before implementation.
- Added `docs/v1/phases/phase-03-export-target-manifest/acceptance.md` for validation evidence.
- Updated `docs/v1/README.md` with the Phase 03 index row and clearer v1 phase documentation rules.
- Added `threadvault.export_targets`, the first v1 `Export Target` module with:
  - `ExportTargetRequest`
  - `export_target`
- Added a database helper for session selection by explicit IDs.
- Added `ArchiveStore.export_target`.
- Added the `threadvault export-target markdown` CLI command with repeatable `--session`, optional `--project`, `--out`, `--privacy-mode`, `--privacy-config`, and `--json`.
- Implemented `threadvault-export-manifest.json` output for target exports.
- Added the `export_target_manifest` JSON schema and refreshed generated schema artifacts under `docs/schemas/`.
- Updated capabilities and robot schema discovery for the new export target manifest workflow.
- Updated `docs/THREADVAULT_USAGE_MANUAL.md` with batch target export examples and manifest explanation.
- Added `tests/test_v103_export_target_manifest.py`.

### Validation

- Completed partial validation:
  - `py -3.12 -m pytest tests\test_v103_export_target_manifest.py` -> 7 passed
  - `py -3.12 -m ruff check src\threadvault\export_targets.py src\threadvault\database.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v103_export_target_manifest.py` -> passed after formatting/import fixes
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote `export_target_manifest.schema.json`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 160 passed
  - `threadvault export-target --help` -> passed and listed `markdown`
  - `threadvault export-target markdown --help` -> passed and listed selection, output, privacy, and JSON options
  - `threadvault capabilities --json` -> passed and advertised `export-target` plus `export_target_manifest: true`
  - `threadvault schemas list --json` -> passed and listed `export_target_manifest`
  - `Test-Path deep-research-report.md` -> `False`
  - `rg -n "docs/plans|docs/research/|ThreadVault-report-v1\.md" README.md docs tests src` -> no stale project references outside the validation command text itself
  - `py -3.12 -m pip install -e ".[dev]"` -> passed and refreshed editable package metadata for `threadvault==0.31.0`
  - `py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"` -> `0.31.0` and `0.31.0`

### Bugs Found

- No runtime bugs found in final validation.
- The stale-reference search matched only the validation command text in Phase 03 records, not live project links.

### Next

- Continue v1 toward an Obsidian/Markdown vault target layout built on the export target manifest seam.

## 2026-07-01 - v1 Phase 04 Obsidian Markdown Vault Target

### Completed

- Added `docs/v1/phases/phase-04-obsidian-markdown-vault/plan.md` before implementation.
- Added `docs/v1/phases/phase-04-obsidian-markdown-vault/acceptance.md` for validation evidence.
- Updated `docs/v1/README.md` with the Phase 04 index row.
- Extended `threadvault.export_targets` so the existing `ExportTargetRequest` / `export_target` interface supports:
  - `profile="markdown"`
  - `profile="obsidian"`
- Kept archive selection, privacy aggregation, evidence aggregation, skipped item reporting, and manifest writing inside the `Export Target` module.
- Added the Obsidian/Markdown vault target layout:
  - `index.md`
  - `sessions/{session_id}.md`
  - `evidence/{session_id}-evidence.md`
  - `threadvault-export-manifest.json`
- Added wiki-style links between vault index, session summary pages, and evidence pages.
- Added `threadvault export-target obsidian` with repeatable `--session`, optional `--project`, `--out`, `--privacy-mode`, `--privacy-config`, and `--json`.
- Updated capabilities and robot guide discovery for the obsidian target.
- Updated `docs/THREADVAULT_USAGE_MANUAL.md` with Obsidian/Markdown vault examples.
- Added `tests/test_v104_obsidian_vault_target.py`.

### Validation

- Completed partial validation:
  - `py -3.12 -m ruff check src\threadvault\export_targets.py src\threadvault\cli.py src\threadvault\store.py tests\test_v104_obsidian_vault_target.py` -> passed
  - `py -3.12 -m pytest tests\test_v104_obsidian_vault_target.py` -> 7 passed after correcting one test expectation about the first evidence event
  - `py -3.12 -m pytest tests\test_v103_export_target_manifest.py` -> 7 passed
- Completed final verification:
  - `threadvault schemas write --out docs\schemas --json` -> passed and refreshed generated schema artifacts
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 167 passed
  - `threadvault export-target --help` -> passed and listed `markdown` and `obsidian`
  - `threadvault export-target obsidian --help` -> passed and listed selection, output, privacy, and JSON options
  - `threadvault capabilities --json` -> passed and advertised `export-target obsidian` plus `obsidian_vault_target: true`
  - `threadvault schemas list --json` -> passed and listed `export_target_manifest`
  - `py -3.12 -m pip install -e ".[dev]"` -> passed and refreshed editable package metadata for `threadvault==0.31.0`
  - `Test-Path deep-research-report.md` -> `False`
  - `py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"` -> `0.31.0` and `0.31.0`

### Bugs Found

- Ruff caught one syntax indentation issue and one unnecessary f-string while reshaping `export_targets.py`; fixed before continuing.
- The first Phase 04 test assumed evidence page content would start with `Event 1`, but summaries intentionally select text-bearing evidence events. Updated the test to assert on real evidence content instead.

### Next

- Continue v1 toward Codex Skill target generation on top of the same export target seam.

## 2026-07-01 - v1 Phase 05 Codex Skill Target

### Completed

- Read `skill-creator` guidance for Skill structure and concise `SKILL.md` design before planning.
- Added `docs/v1/phases/phase-05-codex-skill-target/plan.md` before implementation.
- Added `docs/v1/phases/phase-05-codex-skill-target/acceptance.md` for validation evidence.
- Updated `docs/v1/README.md` with the Phase 05 index row.
- Extended `threadvault.export_targets` so the existing `ExportTargetRequest` / `export_target` interface supports `profile="skill"`.
- Added optional `skill_name` and `skill_description` metadata to `ExportTargetRequest`.
- Added deterministic Skill candidate generation:
  - `SKILL.md`
  - `references/sessions.md`
  - `references/evidence.md`
  - `threadvault-export-manifest.json`
- Added Skill name normalization using lowercase letters, digits, and hyphens.
- Kept Skill output as a reviewable candidate folder; it does not auto-install into `$CODEX_HOME/skills`.
- Added `threadvault export-target skill` with repeatable `--session`, optional `--project`, `--out`, `--skill-name`, `--skill-description`, `--privacy-mode`, `--privacy-config`, and `--json`.
- Updated capabilities and robot guide discovery for the Skill target.
- Updated `docs/THREADVAULT_USAGE_MANUAL.md` with Skill candidate examples.
- Added `tests/test_v105_codex_skill_target.py`.

### Validation

- Completed partial validation:
  - `py -3.12 -m ruff check src\threadvault\export_targets.py src\threadvault\cli.py src\threadvault\store.py tests\test_v105_codex_skill_target.py` -> passed
  - `py -3.12 -m pytest tests\test_v105_codex_skill_target.py` -> 7 passed
  - `py -3.12 -m pytest tests\test_v104_obsidian_vault_target.py tests\test_v103_export_target_manifest.py` -> 14 passed
- Completed final verification:
  - `threadvault schemas write --out docs\schemas --json` -> passed and refreshed generated schema artifacts
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 174 passed
  - `threadvault export-target --help` -> passed and listed `markdown`, `obsidian`, and `skill`
  - `threadvault export-target skill --help` -> passed and listed selection, output, Skill metadata, privacy, and JSON options
  - `threadvault capabilities --json` -> passed and advertised `export-target skill` plus `codex_skill_target: true`
  - `threadvault schemas list --json` -> passed and listed `export_target_manifest`
  - `py -3.12 -m pip install -e ".[dev]"` -> passed and refreshed editable package metadata for `threadvault==0.31.0`
  - `Test-Path deep-research-report.md` -> `False`
  - `py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"` -> `0.31.0` and `0.31.0`

### Bugs Found

- No bugs found in validation.

### Next

- Continue v1 toward a final v1 acceptance smoke over fixture data and an anonymized local audit workflow.

## 2026-07-01 - v1 Phase 06 v1 Acceptance Smoke

### Completed

- Added `docs/v1/phases/phase-06-v1-acceptance-smoke/plan.md` before implementation.
- Added `docs/v1/phases/phase-06-v1-acceptance-smoke/v1-acceptance.md` for final v1 acceptance evidence.
- Updated `docs/v1/README.md` with the Phase 06 acceptance row.
- Added `tests/test_v106_v1_acceptance.py`.
- Added an end-to-end v1 smoke over fixture data:
  - `codex-hook ingest --diagnostic-json`
  - `ingest-queue process --apply`
  - v0 `list` and `search`
  - `export-target markdown`
  - `export-target obsidian`
  - `export-target skill`
- Added v1 discovery checks for capabilities, schemas, phase docs, and retired `deep-research-report.md` policy.

### Validation

- Completed partial validation:
  - `py -3.12 -m ruff check tests\test_v106_v1_acceptance.py` -> passed
  - `py -3.12 -m pytest tests\test_v106_v1_acceptance.py` -> 3 passed
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 177 passed
  - `threadvault capabilities --json` -> passed and advertised all v1 feature flags
  - `threadvault schemas list --json` -> passed and listed all v1 schemas
  - `threadvault export-target --help` -> passed and listed `markdown`, `obsidian`, and `skill`
  - `threadvault ingest-queue --help` -> passed and listed `enqueue`, `list`, and `process`
  - `threadvault codex-hook --help` -> passed and listed `ingest` and `config`
  - `py -3.12 -m pip install -e ".[dev]"` -> passed and refreshed editable package metadata for `threadvault==0.31.0`
  - `Test-Path deep-research-report.md` -> `False`
  - `py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"` -> `0.31.0` and `0.31.0`

### Bugs Found

- No bugs found in validation.

### Next

- v1 is accepted against the roadmap boundary.
- Future work should move to v2 retrieval/interface planning unless a separate v1 packaging/versioning/document-sync phase is requested.

## 2026-07-01 - v2 Phase 01 Retrieval Module FTS Wrapper

### Completed

- Used the `codebase-design` skill guidance for module/interface/seam vocabulary.
- Confirmed the current repository uses `docs/roadmap/v2-retrieval-and-interfaces.md`, `docs/v0/`, and `docs/v1/`; the goal text's `docs/roadmap/v2-personal-knowledge-layer.md` and `docs/v0-v1/` paths do not exist.
- Added `docs/v2/README.md` as the active v2 development archive index.
- Added `docs/v2/phases/phase-01-retrieval-module-fts-wrapper/plan.md` before implementation.
- Added `docs/v2/phases/phase-01-retrieval-module-fts-wrapper/acceptance.md` for validation evidence.
- Updated `docs/README.md` so v2 is the active development line and v1 is accepted history.
- Added `threadvault.retrieval` with:
  - `RetrievalQuery`
  - `retrieve`
  - `RETRIEVAL_MODES = ["fts"]`
- Routed `ArchiveStore.search()` through the retrieval module.
- Moved the current quoted retry fallback for awkward FTS input into the retrieval module.
- Preserved current `threadvault search` CLI and JSON schema outputs.
- Updated capabilities and robot docs to advertise:
  - `retrieval_module: true`
  - `retrieval_modes: ["fts"]`
- Updated the capabilities JSON schema to include `retrieval_modes`.
- Added `tests/test_v201_retrieval_module.py`.

### Validation

- Completed partial validation:
  - `py -3.12 -m ruff check src\threadvault\retrieval.py src\threadvault\store.py src\threadvault\schemas.py tests\test_v201_retrieval_module.py` -> passed after ruff import ordering fix
  - `py -3.12 -m pytest tests\test_v201_retrieval_module.py tests\test_v28_capabilities_schema_contract.py tests\test_v06_schemas.py` -> 15 passed
- Completed final verification:
  - `threadvault schemas write --out docs\schemas --json` -> passed
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 184 passed
  - `threadvault search pytest --json --fields minimal` -> passed and emitted a JSON array
  - `threadvault capabilities --json` -> passed and advertised `retrieval_module` plus `retrieval_modes: ["fts"]`
  - `threadvault schemas list --json` -> passed
  - `py -3.12 -m pip install -e ".[dev]"` -> passed and refreshed editable package metadata for `threadvault==0.31.0`
  - `Test-Path deep-research-report.md` -> `False`
  - `py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"` -> `0.31.0` and `0.31.0`

### Bugs Found

- Initial retrieval tests guessed the wrong fixture text for a `function_call_output` filter. Corrected the test to query `failed`, which is present in fixture output.
- Initial awkward FTS retry test used a query that did not match fixture content. Corrected it to `parser.py)`, which exercises special input handling and returns fixture results.

### Next

- v2 Phase 01 is accepted.
- Continue v2 toward retrieval JSON contracts and diagnostics.

## 2026-07-01 - v2 Phase 02 Retrieval JSON Contracts And Diagnostics

### Completed

- Used the `codebase-design` skill guidance for retrieval module interface depth and seam placement.
- Added `docs/v2/phases/phase-02-retrieval-json-contracts-diagnostics/plan.md` before implementation.
- Added `docs/v2/phases/phase-02-retrieval-json-contracts-diagnostics/design-notes.md` to record the main design choice:
  - keep `threadvault search --json` as the legacy array contract.
  - add `threadvault retrieval query/diagnose` as the v2 object contract with diagnostics.
- Added `docs/v2/phases/phase-02-retrieval-json-contracts-diagnostics/acceptance.md`.
- Updated `docs/v2/README.md` with the Phase 02 plan, design notes, and acceptance links.
- Updated `docs/THREADVAULT_USAGE_MANUAL.md` with v2 retrieval contract examples and schema validation examples.
- Extended `threadvault.retrieval` with:
  - `RETRIEVAL_CONTRACT_VERSION`
  - `RetrievalDiagnostics`
  - `RetrievalResponse`
  - `retrieve_response`
  - `build_retrieval_diagnostics`
  - `fts_index_status`
- Kept `retrieve(conn, query)` as a compatibility helper returning `list[SearchResult]`.
- Added `ArchiveStore.retrieve(...)` for the v2 retrieval object payload.
- Added `ArchiveStore.retrieval_diagnostics()` for diagnostics without running a query.
- Added CLI commands:
  - `threadvault retrieval query QUERY`
  - `threadvault retrieval diagnose`
- Added JSON schemas:
  - `retrieval_query`
  - `retrieval_diagnostics`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities and robot docs discovery for the new retrieval commands, schemas, and `retrieval_diagnostics` feature flag.
- Added `tests/test_v202_retrieval_contracts_diagnostics.py`.

### Validation

- Completed focused validation:
  - `py -3.12 -m ruff check src\threadvault\retrieval.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v202_retrieval_contracts_diagnostics.py` -> passed
  - `py -3.12 -m pytest tests\test_v202_retrieval_contracts_diagnostics.py` -> 6 passed
- Completed schema and related regression validation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote `retrieval_query` plus `retrieval_diagnostics` schema artifacts
  - `py -3.12 -m pytest tests\test_v202_retrieval_contracts_diagnostics.py tests\test_v201_retrieval_module.py tests\test_v28_capabilities_schema_contract.py tests\test_v06_schemas.py` -> 21 passed
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 190 passed
  - `threadvault retrieval query pytest --json` -> passed and emitted the v2 retrieval object contract
  - `threadvault retrieval diagnose --json` -> passed and emitted diagnostics with FTS index status
  - `threadvault search pytest --json --fields minimal` -> passed and emitted the legacy JSON array contract
  - `threadvault capabilities --json` -> passed and advertised `retrieval`, `retrieval query`, `retrieval diagnose`, and `retrieval_diagnostics: true`
  - `threadvault schemas list --json` -> passed and listed `retrieval_query` plus `retrieval_diagnostics`
  - `threadvault retrieval --help` -> passed and listed `query` plus `diagnose`
  - `threadvault retrieval query --help` -> passed and listed filters, fields, mode, and JSON options
  - `threadvault retrieval diagnose --help` -> passed
  - `py -3.12 -m pip install -e ".[dev]"` -> passed and refreshed editable package metadata for `threadvault==0.31.0`
  - `Test-Path deep-research-report.md` -> `False`
  - `py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"` -> `0.31.0` and `0.31.0`

### Bugs Found

- No bugs found in final validation.

### Next

- v2 Phase 02 is accepted.
- Continue v2 toward summary/evidence chunk selection for optional embeddings.

## 2026-07-01 - v2 Phase 03 Summary Evidence Chunk Selection

### Completed

- Used the `codebase-design` skill guidance for Summary Pipeline module interface depth and seam placement.
- Added `docs/v2/phases/phase-03-summary-evidence-chunks/plan.md` before implementation.
- Added `docs/v2/phases/phase-03-summary-evidence-chunks/design-notes.md` to record:
  - chunk selection before embeddings.
  - provider-neutral chunk shape.
  - deterministic chunk IDs.
  - mandatory evidence traceability.
- Added `docs/v2/phases/phase-03-summary-evidence-chunks/acceptance.md`.
- Updated `docs/v2/README.md` with Phase 03 plan, design notes, and acceptance links.
- Updated `docs/THREADVAULT_USAGE_MANUAL.md` with `summary-pipeline chunks` examples and `summary_chunks` validation guidance.
- Added `threadvault.summary_pipeline` with:
  - `SUMMARY_CHUNKS_CONTRACT_VERSION`
  - `SummaryChunkRequest`
  - `build_summary_chunks`
- Added deterministic chunk types:
  - `session_summary`
  - `turn_summary`
  - `evidence`
- Added internal context filtering so `session_meta` and `turn_context` events are not emitted as chunk text.
- Added `ArchiveStore.summary_chunks(...)`.
- Added CLI command:
  - `threadvault summary-pipeline chunks`
- Added JSON schema:
  - `summary_chunks`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities and robot docs discovery for the Summary Pipeline command, schema, and `summary_evidence_chunks` feature flag.
- Added `tests/test_v203_summary_evidence_chunks.py`.

### Validation

- Completed focused validation:
  - `py -3.12 -m ruff check src\threadvault\summary_pipeline.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v203_summary_evidence_chunks.py` -> passed
  - `py -3.12 -m pytest tests\test_v203_summary_evidence_chunks.py` -> 6 passed
- Completed schema and related regression validation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote `summary_chunks.schema.json`
  - `py -3.12 -m pytest tests\test_v203_summary_evidence_chunks.py tests\test_v202_retrieval_contracts_diagnostics.py tests\test_v201_retrieval_module.py tests\test_v28_capabilities_schema_contract.py tests\test_v06_schemas.py` -> 27 passed
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 196 passed
  - `threadvault summary-pipeline chunks --db TEMP_DB --session sess-current --json` -> passed and emitted `session_summary`, `turn_summary`, and `evidence` chunks
  - `threadvault summary-pipeline chunks --db TEMP_DB --project E:\Codex\ThreadVault --json` -> passed and selected fixture project sessions
  - `threadvault capabilities --json` -> passed and advertised `summary-pipeline`, `summary-pipeline chunks`, and `summary_evidence_chunks: true`
  - `threadvault schemas list --json` -> passed and listed `summary_chunks`
  - `threadvault summary-pipeline --help` -> passed and listed `chunks`
  - `threadvault summary-pipeline chunks --help` -> passed and listed session/project selection plus chunk controls
  - `py -3.12 -m pip install -e ".[dev]"` -> passed and refreshed editable package metadata for `threadvault==0.31.0`
  - `Test-Path deep-research-report.md` -> `False`
  - `py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"` -> `0.31.0` and `0.31.0`

### Bugs Found

- Initial project-selection test assumed the fixture project only contained `sess-current`; the fixture also contains `sess-fork`. Updated the test to assert project selection includes both matching sessions.
- Initial CLI smoke showed `turn_context` JSON in turn chunk text. Tightened chunk selection to exclude internal `session_meta` and `turn_context` events from chunk text and summary chunk evidence IDs.

### Next

- v2 Phase 03 is accepted.
- Continue v2 toward a local vector adapter behind an explicit configuration gate.

## 2026-07-01 - v2 Phase 04 Local Vector Adapter

### Completed

- Used the `codebase-design` skill guidance for vector adapter seam placement and module depth.
- Added `docs/v2/phases/phase-04-local-vector-adapter/plan.md` before implementation.
- Added `docs/v2/phases/phase-04-local-vector-adapter/design-notes.md` to record:
  - vector indexing is config-gated by default.
  - `local-hash` is a deterministic local adapter, not a neural semantic model.
  - vector input comes from `summary_chunks`, not all raw events.
  - SQLite stores a derived rebuildable index.
  - hybrid retrieval is deferred to the next phase.
- Added `docs/v2/phases/phase-04-local-vector-adapter/acceptance.md`.
- Updated `docs/v2/README.md` with Phase 04 plan, design notes, and acceptance links.
- Updated `docs/THREADVAULT_USAGE_MANUAL.md` with vector config, index, query, status, and schema validation examples.
- Extended `threadvault.toml` config support with:
  - `retrieval.vector.enabled`
  - `retrieval.vector.adapter`
  - `retrieval.vector.dimensions`
- Updated the default config template with a disabled `[retrieval.vector]` section.
- Bumped database `SCHEMA_VERSION` from `3` to `4`.
- Added local derived vector index tables:
  - `vector_index_meta`
  - `vector_chunks`
- Added `threadvault.vector_adapter` with:
  - `VECTOR_CONTRACT_VERSION`
  - `LOCAL_VECTOR_ADAPTER`
  - `VectorIndexRequest`
  - `build_vector_index`
  - `query_vector_index`
  - `vector_index_status`
  - `embed_text`
- Added deterministic local feature-hashing vectors with no external provider or model dependency.
- Added `ArchiveStore.vector_index(...)`, `ArchiveStore.vector_query(...)`, and `ArchiveStore.vector_status(...)`.
- Added CLI commands:
  - `threadvault vector index`
  - `threadvault vector query`
  - `threadvault vector status`
- Added JSON schemas:
  - `vector_index`
  - `vector_query`
  - `vector_status`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities and robot docs discovery for the vector commands, schemas, and local vector feature flags.
- Added `tests/test_v204_local_vector_adapter.py`.

### Validation

- Completed focused validation:
  - `py -3.12 -m ruff check src\threadvault\app_config.py src\threadvault\database.py src\threadvault\vector_adapter.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v204_local_vector_adapter.py` -> passed
  - `py -3.12 -m pytest tests\test_v204_local_vector_adapter.py` -> 5 passed
- Completed schema and related regression validation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote `vector_index`, `vector_query`, and `vector_status` schema artifacts
  - `py -3.12 -m pytest tests\test_v204_local_vector_adapter.py tests\test_v203_summary_evidence_chunks.py tests\test_v202_retrieval_contracts_diagnostics.py tests\test_v201_retrieval_module.py tests\test_v28_capabilities_schema_contract.py tests\test_v29_doctor_schema_contract.py tests\test_v12_app_config.py tests\test_v06_schemas.py` -> 42 passed
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 201 passed
  - `threadvault vector index --db TEMP_DB --session sess-current --json` without enabled config -> exited 1 with JSON error code `vector_disabled`
  - `threadvault vector index --db TEMP_DB --session sess-current --config TEMP_CONFIG --json` -> passed and indexed 3 chunks from `summary_chunks`
  - `threadvault vector query "parser failure" --db TEMP_DB --config TEMP_CONFIG --json` -> passed and returned ranked chunks with scores and evidence event IDs
  - `threadvault vector status --db TEMP_DB --config TEMP_CONFIG --json` -> passed and reported enabled config plus matching vector index chunks
  - `threadvault capabilities --json` -> passed and advertised schema version `4`, vector commands, and local vector feature flags
  - `threadvault schemas list --json` -> passed and listed `vector_index`, `vector_query`, and `vector_status`
  - `threadvault vector --help` -> passed and listed `index`, `query`, and `status`
  - `threadvault vector index --help` -> passed and listed session/project selection, config, db, chunk controls, and JSON options
  - `threadvault vector query --help` -> passed and listed query, config, db, limit, and JSON options
  - `threadvault vector status --help` -> passed
  - `py -3.12 -m pip install -e ".[dev]"` -> passed and refreshed editable package metadata for `threadvault==0.31.0`
  - `Test-Path deep-research-report.md` -> `False`
  - `py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"` -> `0.31.0` and `0.31.0`

### Bugs Found

- No bugs found in final validation.

### Next

- v2 Phase 04 is accepted.
- Continue v2 toward hybrid ranking and search explanation fields.

## 2026-07-01 - v2 Phase 05 Hybrid Ranking And Search Explanations

### Completed

- Used the `codebase-design` skill guidance for hybrid retrieval module interface depth and reuse.
- Added `docs/v2/phases/phase-05-hybrid-ranking-explanations/plan.md` before implementation.
- Added `docs/v2/phases/phase-05-hybrid-ranking-explanations/design-notes.md` to record:
  - hybrid retrieval degrades to FTS-only when vector is unavailable.
  - hybrid uses a new mixed-result JSON contract.
  - ranking explanations belong in the module, not the CLI.
  - ranking uses deterministic transparent weights.
- Added `docs/v2/phases/phase-05-hybrid-ranking-explanations/acceptance.md`.
- Updated `docs/v2/README.md` with Phase 05 plan, design notes, and acceptance links.
- Updated `docs/THREADVAULT_USAGE_MANUAL.md` with hybrid retrieval examples and `hybrid_retrieval` validation guidance.
- Added `threadvault.hybrid_retrieval` with:
  - `HYBRID_RETRIEVAL_CONTRACT_VERSION`
  - `HYBRID_RANKING_WEIGHTS`
  - `HybridRetrievalRequest`
  - `hybrid_retrieve`
- Added hybrid ranking over FTS event results and optional vector chunk results.
- Added per-result score breakdowns and explanation fields:
  - `scores`
  - `explanation.matched_by`
  - `explanation.rank_factors`
- Added FTS-only degradation when vector config is missing, disabled, unavailable, or empty.
- Added `ArchiveStore.hybrid_retrieve(...)`.
- Added CLI command:
  - `threadvault retrieval hybrid`
- Added JSON schema:
  - `hybrid_retrieval`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities and robot docs discovery for hybrid retrieval.
- Added `tests/test_v205_hybrid_retrieval.py`.

### Validation

- Completed focused validation:
  - `py -3.12 -m ruff check src\threadvault\hybrid_retrieval.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v205_hybrid_retrieval.py` -> passed after line-width fix
  - `py -3.12 -m pytest tests\test_v205_hybrid_retrieval.py` -> 5 passed
- Completed schema and related regression validation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote `hybrid_retrieval.schema.json`
  - `py -3.12 -m pytest tests\test_v205_hybrid_retrieval.py tests\test_v204_local_vector_adapter.py tests\test_v203_summary_evidence_chunks.py tests\test_v202_retrieval_contracts_diagnostics.py tests\test_v201_retrieval_module.py tests\test_v28_capabilities_schema_contract.py tests\test_v06_schemas.py` -> 37 passed
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 206 passed
  - `threadvault retrieval hybrid pytest --db TEMP_DB --json` -> passed and returned FTS-only hybrid response with `vector.status = disabled_by_config`
  - `threadvault retrieval hybrid "parser failure" --db TEMP_DB --config TEMP_CONFIG --json` -> passed and returned mixed FTS/vector results with score breakdowns and explanations
  - `threadvault capabilities --json` -> passed and advertised `retrieval hybrid` plus `hybrid_retrieval: true`
  - `threadvault schemas list --json` -> passed and listed `hybrid_retrieval`
  - `threadvault retrieval hybrid --help` -> passed and listed query, config, db, limit, vector-limit, filters, and JSON options
  - `py -3.12 -m pip install -e ".[dev]"` -> passed and refreshed editable package metadata for `threadvault==0.31.0`
  - `Test-Path deep-research-report.md` -> `False`
  - `py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"` -> `0.31.0` and `0.31.0`

### Bugs Found

- No behavioral bugs found in final validation.
- Ruff caught one long type annotation line in `src\threadvault\hybrid_retrieval.py`; reformatted it before final validation.

### Next

- v2 Phase 05 is accepted.
- Continue v2 toward an MCP or agent-facing retrieval interface on top of the same retrieval and hybrid contracts.

## 2026-07-01 - v2 Phase 06 Agent-Facing Retrieval Interface

### Completed

- Used the `codebase-design` skill guidance to keep the agent-facing interface as a deep module over existing retrieval and hybrid modules.
- Added `docs/v2/phases/phase-06-agent-facing-retrieval-interface/plan.md` before implementation.
- Added `docs/v2/phases/phase-06-agent-facing-retrieval-interface/design-notes.md` to record:
  - Phase 06 implements an agent-facing JSON interface, not a full MCP server runtime.
  - `hybrid` is the default mode because it preserves FTS fallback.
  - direct vector querying is not exposed as a standalone agent mode in this phase.
  - local path metadata is hidden by default and exposed only through `--local-debug`.
- Added `docs/v2/phases/phase-06-agent-facing-retrieval-interface/acceptance.md`.
- Updated `docs/v2/README.md` with the Phase 06 plan, design notes, and acceptance links.
- Updated `docs/THREADVAULT_USAGE_MANUAL.md` with agent interface commands and schema validation guidance.
- Added `threadvault.agent_interface` with:
  - `AGENT_INTERFACE_CONTRACT_VERSION`
  - `AGENT_RETRIEVAL_CONTRACT_VERSION`
  - `AGENT_RETRIEVAL_MODES`
  - `AgentRetrievalRequest`
  - `agent_manifest`
  - `agent_retrieve`
- Added agent-facing retrieval over:
  - `retrieve_response` for FTS mode.
  - `hybrid_retrieve` for hybrid mode.
- Added privacy-preserving default result shaping and explicit `--local-debug` metadata output.
- Added `ArchiveStore.agent_manifest(...)` and `ArchiveStore.agent_retrieve(...)`.
- Added CLI command group:
  - `threadvault agent manifest`
  - `threadvault agent retrieve`
- Added JSON schemas:
  - `agent_interface_manifest`
  - `agent_retrieval`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities and robot docs discovery for the agent interface.
- Added `tests/test_v206_agent_interface.py`.

### Validation

- Completed focused validation:
  - `py -3.12 -m pytest tests\test_v206_agent_interface.py` -> 6 passed
  - `py -3.12 -m ruff check src\threadvault\agent_interface.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v206_agent_interface.py` -> passed after import ordering fix
- Completed schema and adjacent v2 regression validation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote `agent_interface_manifest.schema.json` and `agent_retrieval.schema.json`
  - `py -3.12 -m pytest tests\test_v206_agent_interface.py tests\test_v205_hybrid_retrieval.py tests\test_v204_local_vector_adapter.py tests\test_v202_retrieval_contracts_diagnostics.py tests\test_v28_capabilities_schema_contract.py tests\test_v06_schemas.py` -> 30 passed
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 212 passed
  - `threadvault agent manifest --json` -> passed and emitted `agent_interface.v1`
  - `threadvault agent retrieve pytest --db TEMP_DB --json` -> passed and emitted hybrid-mode `agent_retrieval.v1` with FTS-only degradation
  - `threadvault agent retrieve pytest --mode fts --db TEMP_DB --local-debug --json` -> passed and emitted local debug metadata with `privacy.raw_paths_included = true`
  - `threadvault capabilities --json` -> passed and listed `agent` plus `agent_retrieval_interface`
  - `threadvault schemas list --json` -> passed and listed `agent_interface_manifest` and `agent_retrieval`
  - `threadvault agent manifest --help` -> passed
  - `threadvault agent retrieve --help` -> passed
  - `Test-Path deep-research-report.md` -> `False`
  - `py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"` -> `0.31.0` and `0.31.0`

### Bugs Found

- Ruff caught unsorted imports in `src\threadvault\store.py`; fixed with `ruff --fix`.
- Manual CLI smoke exposed that FTS-only agent scores were easier to read when normalized by returned rank position; adjusted `threadvault.agent_interface` without changing underlying retrieval ordering.

### Next

- v2 Phase 06 is accepted.
- Continue v2 toward final acceptance smoke covering FTS-only and vector-enabled retrieval/interface modes.

## 2026-07-01 - v2 Phase 07 v2 Acceptance Smoke

### Completed

- Added `docs/v2/phases/phase-07-v2-acceptance-smoke/plan.md` before implementation.
- Added `tests/test_v207_v2_acceptance.py` to verify the completed v2 product line:
  - FTS-only retrieval and agent path.
  - vector-enabled hybrid and agent path.
  - capabilities, robot docs, schema registry, schema artifacts, phase docs, and retired report policy.
- Added `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`.
- Updated `docs/v2/README.md` with the Phase 07 acceptance row.

### Validation

- Completed focused validation:
  - `py -3.12 -m pytest tests\test_v207_v2_acceptance.py` -> 3 passed
  - `py -3.12 -m ruff check tests\test_v207_v2_acceptance.py` -> passed
- Completed adjacent v2 validation:
  - `py -3.12 -m pytest tests\test_v201_retrieval_module.py tests\test_v202_retrieval_contracts_diagnostics.py tests\test_v203_summary_evidence_chunks.py tests\test_v204_local_vector_adapter.py tests\test_v205_hybrid_retrieval.py tests\test_v206_agent_interface.py tests\test_v207_v2_acceptance.py` -> 38 passed
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 215 passed
  - `threadvault capabilities --json` -> passed and listed v2 commands and feature flags
  - `threadvault schemas list --json` -> passed and listed all v2 schemas
  - `threadvault retrieval query pytest --db TEMP_DB --json` -> passed
  - `threadvault retrieval hybrid pytest --db TEMP_DB --json` -> passed with FTS-only degradation
  - `threadvault agent manifest --json` -> passed
  - `threadvault agent retrieve pytest --db TEMP_DB --json` -> passed
  - `threadvault vector status --db TEMP_DB --json` -> passed with vector disabled by default
  - `Test-Path deep-research-report.md` -> `False`
  - `py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"` -> `0.31.0` and `0.31.0`

### Bugs Found

- No bugs found in focused Phase 07 validation.
- No bugs found in final v2 acceptance validation.

### Next

- v2 is accepted against the roadmap's retrieval and interfaces goals.
- Next major line is v3 clients and team governance unless a separate v2 hardening/release phase is requested.

## 2026-07-01 - v3 Phase 01 Client Interface Readiness Audit

### Completed

- Used the `codebase-design` skill guidance to keep v3 client planning focused on existing deep module interfaces rather than shallow pass-through wrappers.
- Added `docs/v3/README.md` as the v3 documentation entrypoint and development-rule index.
- Added `docs/v3/phases/phase-01-client-interface-readiness-audit/plan.md` before implementation.
- Added `docs/v3/phases/phase-01-client-interface-readiness-audit/design-notes.md` to record:
  - richer clients should adapt existing archive/export/summary/retrieval/vector/hybrid/agent-facing interfaces.
  - v3 should not rewrite v2 retrieval, hybrid ranking, vector indexing, or agent-facing retrieval.
  - local-first defaults remain mandatory.
  - server, cloud, team, and governance capabilities remain opt-in.
- Added `docs/v3/phases/phase-01-client-interface-readiness-audit/acceptance.md`.
- Updated `docs/README.md` with v3 navigation and the v3 starting document set.
- Added `tests/test_v301_client_interface_readiness.py` to verify:
  - v3 docs and Phase 01 docs exist.
  - v3 docs preserve the retired `deep-research-report.md` policy.
  - discovery surfaces advertise retrieval, hybrid retrieval, summary chunks, vector status, export targets, and agent retrieval.
  - local-first, vector-disabled-by-default, no-cloud-sync, and no-external-LLM defaults remain intact.
  - `agent manifest --json` stays safe for clients by default.

### Validation

- Completed focused validation:
  - `py -3.12 -m pytest tests\test_v301_client_interface_readiness.py` -> 3 passed
  - `py -3.12 -m ruff check tests\test_v301_client_interface_readiness.py` -> passed
- Completed adjacent interface validation:
  - `py -3.12 -m pytest tests\test_v206_agent_interface.py tests\test_v207_v2_acceptance.py tests\test_v301_client_interface_readiness.py` -> 12 passed
- Completed repository lint validation:
  - `py -3.12 -m ruff check .` -> passed
- Completed manual smoke:
  - `threadvault capabilities --json` -> passed and advertised v2/v3-ready interface commands and local-first feature flags
  - `threadvault agent manifest --json` -> passed and reported `mcp_runtime_included = false`, `local_vector_enabled = false`, and `external_model_calls = false`
  - `Test-Path deep-research-report.md` -> `False`

### Bugs Found

- No implementation bugs found in focused or adjacent validation.
- The current workspace is not a Git repository, so change tracking used file-level checks and automated validation rather than `git diff`.

### Next

- v3 Phase 01 is accepted as the client-interface readiness baseline.
- Continue v3 toward Phase 02: select and implement the first richer client entrypoint, likely a narrow local client adapter/facade or CLI-discoverable client manifest before choosing a heavier desktop or IDE shell.

## 2026-07-01 - v3 Phase 02 Client Manifest Entrypoint

### Completed

- Added `docs/v3/phases/phase-02-client-manifest-entrypoint/plan.md` before implementation.
- Added `docs/v3/phases/phase-02-client-manifest-entrypoint/design-notes.md` to record:
  - the first v3 client-facing entrypoint is a manifest, not a UI shell.
  - the manifest is pure discovery and does not read the archive database or raw Codex transcripts.
  - clients should reuse `agent retrieve`, `retrieval hybrid`, `export-target`, `vector status`, and schema commands.
  - server mode remains opt-in and deferred.
- Added `docs/v3/phases/phase-02-client-manifest-entrypoint/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 02 row.
- Added `threadvault.client_interface` with:
  - `CLIENT_INTERFACE_CONTRACT_VERSION`
  - `CLIENT_FAMILIES`
  - `client_manifest`
- Added `ArchiveStore.client_manifest(...)`.
- Added CLI command group:
  - `threadvault client manifest`
- Added JSON schema:
  - `client_interface_manifest`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities and robot docs discovery for the client manifest.
- Added `tests/test_v302_client_manifest.py`.

### Validation

- Completed focused validation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote `client_interface_manifest.schema.json`
  - `py -3.12 -m pytest tests\test_v302_client_manifest.py` -> 4 passed
  - `py -3.12 -m ruff check src\threadvault\client_interface.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v302_client_manifest.py` -> passed
- Completed adjacent interface validation:
  - `py -3.12 -m pytest tests\test_v206_agent_interface.py tests\test_v207_v2_acceptance.py tests\test_v301_client_interface_readiness.py tests\test_v302_client_manifest.py` -> 16 passed
- Completed manual smoke:
  - `threadvault client manifest --json` -> passed and emitted `client_interface.v1`
  - `threadvault schemas list --json` -> passed and listed `client_interface_manifest`
  - `threadvault capabilities --json` -> passed and listed `client` plus `client manifest`
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 222 passed

### Bugs Found

- The first focused test run checked for the packaged schema artifact while `schemas write` was still running in a parallel command. Reran schema generation and the focused test sequentially.
- Ruff caught one long line in `src\threadvault\client_interface.py`; wrapped the vector entrypoint list before final validation.

### Next

- v3 Phase 02 is accepted as the first client-facing discovery entrypoint.
- Continue v3 toward Phase 03: implement a richer local client workflow on top of the manifest and existing interfaces, with a likely starting point in browse/search/export ergonomics before heavier desktop, IDE, or server packaging.

## 2026-07-01 - v3 Phase 03 Client Overview Workflow

### Completed

- Added `docs/v3/phases/phase-03-client-overview-workflow/plan.md` before implementation.
- Added `docs/v3/phases/phase-03-client-overview-workflow/design-notes.md` to record:
  - `client overview` is a local read-only workflow for richer client first screens.
  - browse data comes from existing session listing.
  - search data comes from the existing agent-facing retrieval interface.
  - raw local paths and search metadata remain behind `--local-debug`.
- Added `docs/v3/phases/phase-03-client-overview-workflow/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 03 row.
- Extended `threadvault.client_interface` with:
  - `CLIENT_OVERVIEW_CONTRACT_VERSION`
  - `client_overview`
- Added `ArchiveStore.client_overview(...)`.
- Added CLI command:
  - `threadvault client overview`
- Added JSON schema:
  - `client_overview`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities and robot docs discovery for the client overview workflow.
- Updated the Phase 02 client manifest so it advertises `client_overview` and the new overview commands.
- Added `tests/test_v303_client_overview.py`.

### Validation

- Completed focused validation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote `client_overview.schema.json`
  - `py -3.12 -m pytest tests\test_v303_client_overview.py` -> 4 passed
  - `py -3.12 -m ruff check src\threadvault\client_interface.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v303_client_overview.py` -> passed
- Completed adjacent interface validation:
  - `py -3.12 -m pytest tests\test_v206_agent_interface.py tests\test_v207_v2_acceptance.py tests\test_v302_client_manifest.py tests\test_v303_client_overview.py` -> 17 passed
- Completed manual smoke:
  - `threadvault client overview --db TEMP_DB --json` -> passed and returned fixture sessions without raw paths
  - `threadvault client overview --db TEMP_DB --query pytest --json` -> passed and returned agent-backed search results without metadata
  - `threadvault schemas list --json` -> passed and listed `client_overview`
  - `threadvault capabilities --json` -> passed and listed `client overview`
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 226 passed

### Bugs Found

- Initial adjacent validation failed because the Phase 02 client manifest test expected exactly `["client_interface_manifest"]`; Phase 03 intentionally extends that discovery list to include `client_overview`, so the test was updated to the current contract.
- Ruff caught import ordering in `src\threadvault\client_interface.py`; fixed before final validation.

### Next

- v3 Phase 03 is accepted as the first local browse/search/export-oriented client workflow.
- Continue v3 toward Phase 04: add a session detail or export preview workflow so richer clients can move from overview cards into a safe, evidence-backed detail/export action without reading raw transcripts directly.

## 2026-07-01 - v3 Phase 04 Client Session Detail Workflow

### Completed

- Used the `codebase-design` skill guidance to keep session detail payload shaping in the client interface while reusing existing database and summary modules.
- Added `docs/v3/phases/phase-04-client-session-detail-workflow/plan.md` before implementation.
- Added `docs/v3/phases/phase-04-client-session-detail-workflow/design-notes.md` to record:
  - `client session` is the detail companion to `client overview`.
  - session lookup remains in the database layer.
  - local summary generation remains in the existing summary module.
  - event previews are bounded and must not become raw transcript dumps.
  - raw path and event file path metadata remain behind `--local-debug`.
- Added `docs/v3/phases/phase-04-client-session-detail-workflow/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 04 row.
- Extended `threadvault.client_interface` with:
  - `CLIENT_SESSION_CONTRACT_VERSION`
  - `client_session_detail`
- Added `ArchiveStore.client_session(...)`.
- Added CLI command:
  - `threadvault client session`
- Added JSON schema:
  - `client_session`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot docs, and client manifest discovery for the client session workflow.
- Added `tests/test_v304_client_session_detail.py`.
- Updated Phase 02 and Phase 03 discovery tests to include the new `client_session` schema.

### Validation

- Completed focused validation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote `client_session.schema.json`
  - `py -3.12 -m pytest tests\test_v304_client_session_detail.py` -> 4 passed
  - `py -3.12 -m ruff check src\threadvault\client_interface.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v304_client_session_detail.py` -> passed
- Completed adjacent interface validation:
  - `py -3.12 -m pytest tests\test_v206_agent_interface.py tests\test_v207_v2_acceptance.py tests\test_v303_client_overview.py tests\test_v304_client_session_detail.py` -> 17 passed
  - `py -3.12 -m pytest tests\test_v302_client_manifest.py tests\test_v303_client_overview.py tests\test_v304_client_session_detail.py` -> 12 passed
- Completed manual smoke:
  - `threadvault client session --db TEMP_DB --session sess-current --json` -> passed and omitted raw path/file path metadata
  - `threadvault client session --db TEMP_DB --session sess-current --local-debug --json` -> passed and included explicit local debug metadata
  - `threadvault schemas list --json` -> passed and listed `client_session`
  - `threadvault capabilities --json` -> passed and listed `client session`
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 230 passed

### Bugs Found

- Initial focused validation used `--max-chars 20`, below the CLI's documented lower bound of 50. The test was corrected to use the public command contract.
- `client_session_detail` initially assumed the raw `get_session()` row included event and warning counts. `ArchiveStore.client_session(...)` now computes those counts from existing event/warning queries before shaping the payload.
- Event preview initially treated `sqlite3.Row` as a dict with `.get(...)`. Replaced that with direct row-key access.
- Phase 02 and Phase 03 tests had exact schema-list assertions; they were updated to reflect the current additive discovery contract.

### Next

- v3 Phase 04 is accepted as a safe local session detail workflow for richer clients.
- Continue v3 toward Phase 05: add an export preview workflow so clients can inspect planned export files, privacy mode, and evidence coverage before invoking file-writing export commands.

## 2026-07-01 - v3 Phase 05 Client Export Preview Workflow

### Completed

- Used the `codebase-design` skill guidance to keep export preview as a deep read-only interface over the existing export target module.
- Added `docs/v3/phases/phase-05-client-export-preview-workflow/plan.md` before implementation.
- Added `docs/v3/phases/phase-05-client-export-preview-workflow/design-notes.md` to record:
  - preview must never create output directories or write export files.
  - preview reuses export target selection, privacy scanning, and evidence shaping instead of duplicating export behavior in the client layer.
  - `actions.execute` points clients to the real `export-target` command after user confirmation.
  - team permissions and server-mediated approval remain deferred to later v3 phases.
- Added `docs/v3/phases/phase-05-client-export-preview-workflow/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 05 row.
- Extended `threadvault.export_targets` with `preview_export_target(...)` and preview helpers for markdown, Obsidian, and Codex skill targets.
- Extended `threadvault.client_interface` with:
  - `CLIENT_EXPORT_PREVIEW_CONTRACT_VERSION`
  - `client_export_preview`
- Added `ArchiveStore.client_export_preview(...)`.
- Added CLI command:
  - `threadvault client export-preview`
- Added JSON schema:
  - `client_export_preview`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot docs, and client manifest discovery for the client export preview workflow.
- Added `tests/test_v305_client_export_preview.py`.
- Updated Phase 02, Phase 03, and Phase 04 discovery tests to include the new `client_export_preview` schema.

### Validation

- Completed focused validation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote `client_export_preview.schema.json`
  - `py -3.12 -m pytest tests\test_v305_client_export_preview.py` -> 4 passed
  - `py -3.12 -m ruff check src\threadvault\export_targets.py src\threadvault\client_interface.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v305_client_export_preview.py` -> passed
- Completed adjacent export and client validation:
  - `py -3.12 -m pytest tests\test_v103_export_target_manifest.py tests\test_v104_obsidian_vault_target.py tests\test_v105_codex_skill_target.py tests\test_v304_client_session_detail.py tests\test_v305_client_export_preview.py` -> 29 passed
- Completed manual smoke:
  - `threadvault client export-preview --db TEMP_DB --session sess-current --out TEMP_OUT --json` -> passed and returned planned files without creating the output directory
  - `threadvault client export-preview --db TEMP_DB --session sess-privacy --privacy-mode fail --out TEMP_OUT --json` -> passed and reported blocked privacy findings without creating the output directory
  - `Test-Path TEMP_OUT` -> `False`
  - `threadvault schemas list --json` -> passed and listed `client_export_preview`
  - `threadvault capabilities --json` -> passed and listed `client export-preview`
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 234 passed

### Bugs Found

- Ruff caught long lines in the new export preview implementation; wrapped them before final validation.
- Phase 02, Phase 03, and Phase 04 tests had exact schema-list assertions; they were updated to reflect the current additive discovery contract.

### Next

- v3 Phase 05 is accepted as a safe read-only export preview workflow for richer clients.
- Continue v3 toward Phase 06: either add warning/privacy detail workflows for client remediation, or begin the optional team governance baseline with opt-in identity, role, and audit-log planning.

## 2026-07-01 - v3 Phase 06 Client Warning Detail Workflow

### Completed

- Used the `codebase-design` skill guidance to keep warning/privacy details behind a small client-facing interface.
- Added `docs/v3/phases/phase-06-client-warning-detail-workflow/plan.md` before implementation.
- Added `docs/v3/phases/phase-06-client-warning-detail-workflow/design-notes.md` to record:
  - `client warnings` is read-only remediation context.
  - warning details come from existing parse warning records.
  - privacy details come from the existing privacy scan path.
  - raw local paths and raw warning excerpts remain behind `--local-debug`.
  - team permissions, shared audit records, and server-mediated approvals remain deferred.
- Added `docs/v3/phases/phase-06-client-warning-detail-workflow/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 06 row.
- Extended `threadvault.client_interface` with:
  - `CLIENT_WARNINGS_CONTRACT_VERSION`
  - `client_warnings_detail`
- Added `ArchiveStore.client_warnings(...)`.
- Added CLI command:
  - `threadvault client warnings`
- Added JSON schema:
  - `client_warnings`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot docs, and client manifest discovery for the client warning detail workflow.
- Added `tests/test_v306_client_warning_detail.py`.
- Updated Phase 02 through Phase 05 discovery tests to include the new `client_warnings` schema.

### Validation

- Completed focused validation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote `client_warnings.schema.json`
  - `py -3.12 -m pytest tests\test_v306_client_warning_detail.py` -> 4 passed
  - `py -3.12 -m ruff check src\threadvault\client_interface.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v306_client_warning_detail.py` -> passed
- Completed adjacent v3 client validation:
  - `py -3.12 -m pytest tests\test_v302_client_manifest.py tests\test_v303_client_overview.py tests\test_v304_client_session_detail.py tests\test_v305_client_export_preview.py tests\test_v306_client_warning_detail.py` -> 20 passed
- Completed manual smoke:
  - `threadvault client warnings --db TEMP_DB --session sess-privacy --json` -> passed
  - `threadvault client warnings --db TEMP_DB --session sess-current --local-debug --json` -> passed
  - `threadvault schemas list --json` -> passed
  - `threadvault capabilities --json` -> passed
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 238 passed

### Bugs Found

- The first focused test assumed `sess-privacy` had no parser warnings. Fixture import proved it also has parse warnings, so the test was corrected to assert safe default shaping rather than an incorrect count.

### Next

- v3 Phase 06 is accepted as a safe warning/privacy detail workflow for richer clients.
- Continue v3 toward Phase 07: start the optional team governance baseline with opt-in local governance config, role vocabulary, and audit-log planning while preserving local-first defaults.

## 2026-07-01 - v3 Phase 07 Governance Baseline

### Completed

- Used the `codebase-design` skill guidance to keep governance status as a small deep module before adding enforcement.
- Added `docs/v3/phases/phase-07-governance-baseline/plan.md` before implementation.
- Added `docs/v3/phases/phase-07-governance-baseline/design-notes.md` to record:
  - governance baseline precedes permission enforcement.
  - `[governance] enabled = true` is opt-in and does not require server/cloud behavior.
  - initial access vocabulary is `raw_transcript`, `summary_search`, `export`, `delete_retention`, and `restore`.
  - permission enforcement, audit persistence, shared server identity, and centralized backup policy remain deferred.
- Added `docs/v3/phases/phase-07-governance-baseline/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 07 row.
- Extended `threadvault.app_config` with:
  - `governance_enabled`
  - default config template `[governance] enabled = false`
  - config show/doctor summaries for governance state
- Added `threadvault.governance` with:
  - `GOVERNANCE_STATUS_CONTRACT_VERSION`
  - `governance_status`
  - access level, role, sensitive operation, audit requirement, and default boundary vocabulary
- Added `ArchiveStore.governance_status(...)`.
- Added CLI command group:
  - `threadvault governance status`
- Added JSON schema:
  - `governance_status`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot docs, and client manifest discovery for the governance baseline.
- Added `tests/test_v307_governance_baseline.py`.
- Updated the Phase 02 client manifest test to assert the new `governance_status` payload shape.

### Validation

- Completed focused validation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote `governance_status.schema.json`
  - `py -3.12 -m pytest tests\test_v307_governance_baseline.py` -> 5 passed
  - `py -3.12 -m ruff check src\threadvault\app_config.py src\threadvault\governance.py src\threadvault\client_interface.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v307_governance_baseline.py` -> passed
- Completed adjacent config/client validation:
  - `py -3.12 -m pytest tests\test_v12_app_config.py tests\test_v13_config_cli.py tests\test_v14_config_init.py tests\test_v302_client_manifest.py tests\test_v307_governance_baseline.py` -> 29 passed
- Completed manual smoke:
  - `threadvault governance status --json` -> passed
  - `threadvault governance status --config TEMP_CONFIG --json` -> passed with `[governance] enabled = true`
  - `threadvault config show --config TEMP_CONFIG --json` -> passed and exposed governance config summary
  - `threadvault schemas list --json` -> passed
  - `threadvault capabilities --json` -> passed
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 243 passed

### Bugs Found

- Ruff caught an unused governance contract import in `client_interface.py`; removed it.
- The Phase 02 client manifest test still expected the old flat governance placeholder. Updated it to assert the new `governance_status` payload shape.

### Next

- v3 Phase 07 is accepted as the opt-in governance baseline.
- Continue v3 toward Phase 08: add an append-only local audit log plan/workflow for sensitive operations, still disabled or explicitly invoked until enforcement phases wire it into commands.

## 2026-07-01 - v3 Phase 08 Local Audit Log Workflow

### Completed

- Used the `codebase-design` skill guidance to keep audit log operations behind a small explicit governance interface.
- Added `docs/v3/phases/phase-08-local-audit-log-workflow/plan.md` before implementation.
- Added `docs/v3/phases/phase-08-local-audit-log-workflow/design-notes.md` to record:
  - explicit audit commands come before automatic command instrumentation.
  - audit logs are append-only JSONL.
  - audit records should contain operation metadata, not raw transcript content.
  - role enforcement, centralized server audit, identity providers, and cloud sync remain deferred.
- Added `docs/v3/phases/phase-08-local-audit-log-workflow/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 08 row.
- Extended `threadvault.governance` with:
  - `GOVERNANCE_AUDIT_APPEND_CONTRACT_VERSION`
  - `GOVERNANCE_AUDIT_LIST_CONTRACT_VERSION`
  - `GOVERNANCE_AUDIT_RECORD_VERSION`
  - `append_audit_record`
  - `list_audit_records`
  - local audit command discovery constants
- Updated `governance_status(...)` so audit log support is discoverable while permission enforcement and shared server remain disabled.
- Added `ArchiveStore.governance_audit_append(...)` and `ArchiveStore.governance_audit_list(...)`.
- Added CLI commands:
  - `threadvault governance audit append`
  - `threadvault governance audit list`
- Added JSON schemas:
  - `governance_audit_append`
  - `governance_audit_list`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot docs, and governance discovery for audit append/list.
- Added `tests/test_v308_local_audit_log.py`.
- Updated the Phase 07 governance baseline test to reflect that audit log support now exists while permissions/server remain disabled.

### Validation

- Completed focused validation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote `governance_audit_append.schema.json` and `governance_audit_list.schema.json`
  - `py -3.12 -m pytest tests\test_v308_local_audit_log.py` -> 4 passed
  - `py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v308_local_audit_log.py` -> passed
- Completed adjacent governance/discovery validation:
  - `py -3.12 -m pytest tests\test_v307_governance_baseline.py tests\test_v308_local_audit_log.py tests\test_v302_client_manifest.py tests\test_v28_capabilities_schema_contract.py` -> 18 passed
- Completed manual smoke:
  - `threadvault governance audit append --log TEMP_LOG --operation export_archive --actor local --status ok --target-type session --target-id sess-current --json` -> passed
  - `threadvault governance audit list --log TEMP_LOG --json` -> passed
  - `threadvault governance status --json` -> passed
  - `threadvault schemas list --json` -> passed
  - `threadvault capabilities --json` -> passed
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 247 passed

### Bugs Found

- The first malformed-line test used a partial object that schema validation rejected. The implementation now treats incomplete audit objects as `invalid_audit_record` warnings and excludes them from valid records.
- Ruff caught long audit command strings and a long warning line; command constants and wrapped warning payloads fixed them.
- The Phase 07 baseline test expected `audit_log_implemented = false`; updated it to reflect Phase 08 while keeping server and permission enforcement disabled.

### Next

- v3 Phase 08 is accepted as the explicit local audit log workflow.
- Continue v3 toward Phase 09: add a permission preflight/check workflow on top of the Phase 07 access vocabulary and Phase 08 audit commands, still without enforcing permissions on existing local CLI commands by default.

## 2026-07-01 - v3 Phase 09 Permission Preflight Workflow

### Completed

- Used the `codebase-design` skill guidance to keep permission checks as explicit preflight behavior before command enforcement.
- Added `docs/v3/phases/phase-09-permission-preflight-workflow/plan.md` before implementation.
- Added `docs/v3/phases/phase-09-permission-preflight-workflow/design-notes.md` to record:
  - preflight checks come before enforcement.
  - disabled governance means denial is not enforced, but `would_allow` remains visible.
  - role and access vocabulary reuse Phase 07.
  - optional audit logging reuses Phase 08.
  - identity, server policy, central audit storage, and automatic command instrumentation remain deferred.
- Added `docs/v3/phases/phase-09-permission-preflight-workflow/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 09 row.
- Extended `threadvault.governance` with:
  - `GOVERNANCE_PERMISSION_CHECK_CONTRACT_VERSION`
  - `PERMISSION_CHECK_COMMAND`
  - `check_permission`
- Added `ArchiveStore.governance_permission_check(...)`.
- Added CLI command:
  - `threadvault governance permission check`
- Added JSON schema:
  - `governance_permission_check`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot docs, and governance discovery for permission preflight.
- Added `tests/test_v309_permission_preflight.py`.

### Validation

- Completed focused validation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote `governance_permission_check.schema.json`
  - `py -3.12 -m pytest tests\test_v309_permission_preflight.py` -> 5 passed
  - `py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v309_permission_preflight.py` -> passed
- Completed adjacent governance/discovery validation:
  - `py -3.12 -m pytest tests\test_v307_governance_baseline.py tests\test_v308_local_audit_log.py tests\test_v309_permission_preflight.py tests\test_v302_client_manifest.py tests\test_v28_capabilities_schema_contract.py` -> 23 passed
- Completed manual smoke:
  - `threadvault governance permission check --operation export_archive --role reviewer --json` -> passed
  - `threadvault governance permission check --operation read_raw_transcript --role reader --config TEMP_CONFIG --audit-log TEMP_LOG --actor reader --target-type session --target-id sess-current --json` -> passed
  - `threadvault governance audit list --log TEMP_LOG --json` -> passed
  - `threadvault schemas list --json` -> passed
  - `threadvault capabilities --json` -> passed
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 252 passed

### Bugs Found

- No implementation bugs found in Phase 09 validation.

### Next

- v3 Phase 09 is accepted as the explicit permission preflight workflow.
- Continue v3 toward Phase 10: add governance enforcement planning/gap audit for which existing commands should later call permission preflight and audit append, without turning enforcement on by default.

## 2026-07-01 - v3 Phase 10 Governance Enforcement Gap Audit

### Completed

- Used the `codebase-design` skill guidance to keep enforcement planning behind a small explicit governance interface.
- Added `docs/v3/phases/phase-10-governance-enforcement-gap-audit/plan.md` before implementation.
- Added `docs/v3/phases/phase-10-governance-enforcement-gap-audit/design-notes.md` to record:
  - audit comes before enforcement.
  - the first inventory is static and product-curated.
  - current command behavior must not change in this phase.
  - future enforcement phases can use the inventory as their checklist.
- Added and accepted `docs/v3/phases/phase-10-governance-enforcement-gap-audit/acceptance.md`.
- Added and finalized `docs/v3/phases/phase-10-governance-enforcement-gap-audit/gap-audit.md`.
- Updated `docs/v3/README.md` with the Phase 10 row.
- Extended `threadvault.governance` with:
  - `GOVERNANCE_ENFORCEMENT_GAPS_CONTRACT_VERSION`
  - `ENFORCEMENT_GAPS_COMMAND`
  - `ENFORCEMENT_GAP_COMMANDS`
  - `governance_enforcement_gaps`
- Updated `governance_status(...)` so the enforcement gap audit is discoverable while permission enforcement, server mode, and cloud sync remain disabled.
- Added `ArchiveStore.governance_enforcement_gaps(...)`.
- Added CLI command:
  - `threadvault governance enforcement gaps`
- Added JSON schema:
  - `governance_enforcement_gaps`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot docs, and schema discovery for the enforcement gap audit.
- Added `tests/test_v310_governance_enforcement_gaps.py`.

### Validation

- Completed schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote `governance_enforcement_gaps.schema.json`
- Completed focused validation:
  - `py -3.12 -m pytest tests\test_v310_governance_enforcement_gaps.py` -> 4 passed
  - `py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v310_governance_enforcement_gaps.py` -> passed
- Completed adjacent governance/client/discovery validation:
  - `py -3.12 -m pytest tests\test_v307_governance_baseline.py tests\test_v308_local_audit_log.py tests\test_v309_permission_preflight.py tests\test_v310_governance_enforcement_gaps.py tests\test_v302_client_manifest.py tests\test_v28_capabilities_schema_contract.py` -> 27 passed
- Completed manual smoke:
  - `threadvault governance enforcement gaps --json` -> passed and reported 16 command surfaces
  - `threadvault schemas list --json` -> passed and listed `governance_enforcement_gaps`
  - `threadvault capabilities --json` -> passed and advertised `governance enforcement gaps`
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 256 passed

### Bugs Found

- Focused ruff caught an unsorted import in `src/threadvault/store.py`; import order was fixed.

### Next

- v3 Phase 10 is accepted as the governance enforcement gap audit.
- Continue v3 toward Phase 11: choose the first opt-in enforcement slice from the gap audit, likely export/backup permission preflight in dry-run or explicitly enabled mode, while preserving local-first defaults.

## 2026-07-01 - v3 Phase 11 Governance Enforcement Dry Run

### Completed

- Used the `codebase-design` skill guidance to keep enforcement preview behavior behind a small explicit governance interface.
- Added `docs/v3/phases/phase-11-governance-enforcement-dry-run/plan.md` before implementation.
- Added `docs/v3/phases/phase-11-governance-enforcement-dry-run/design-notes.md` to record:
  - dry-run checks come before apply/enforcement.
  - Phase 10 inventory remains the source for command-to-operation mapping.
  - Phase 09 permission logic is reused for role access decisions.
  - server, cloud, and external model behavior remain out of scope and disabled by default.
  - optional audit logging records only the dry-run check, not execution of the checked command.
- Added and accepted `docs/v3/phases/phase-11-governance-enforcement-dry-run/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 11 row.
- Extended `threadvault.governance` with:
  - `GOVERNANCE_ENFORCEMENT_CHECK_CONTRACT_VERSION`
  - `ENFORCEMENT_CHECK_COMMAND`
  - `governance_enforcement_check`
- Added `ArchiveStore.governance_enforcement_check(...)`.
- Added CLI command:
  - `threadvault governance enforcement check`
- Added JSON schema:
  - `governance_enforcement_check`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot docs, and schema discovery for the enforcement dry-run workflow.
- Added `tests/test_v311_governance_enforcement_dry_run.py`.

### Validation

- Completed schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote `governance_enforcement_check.schema.json`
- Completed focused validation:
  - `py -3.12 -m pytest tests\test_v311_governance_enforcement_dry_run.py` -> 6 passed
  - `py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v311_governance_enforcement_dry_run.py` -> passed
- Completed adjacent governance/discovery validation:
  - `py -3.12 -m pytest tests\test_v309_permission_preflight.py tests\test_v310_governance_enforcement_gaps.py tests\test_v311_governance_enforcement_dry_run.py tests\test_v307_governance_baseline.py tests\test_v308_local_audit_log.py tests\test_v28_capabilities_schema_contract.py` -> 29 passed
- Completed manual smoke:
  - `threadvault governance enforcement check --command "threadvault export" --role reviewer --json` -> passed and returned `status = would_allow`
  - `threadvault governance enforcement check --command "threadvault client session" --role reader --json` -> passed and returned `status = would_block`
  - `threadvault schemas list --json` -> passed and listed `governance_enforcement_check`
  - `threadvault capabilities --json` -> passed and advertised `governance enforcement check`
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 262 passed

### Bugs Found

- No implementation bugs found in Phase 11 validation.

### Next

- v3 Phase 11 is accepted as the governance enforcement dry-run workflow.
- Continue v3 toward Phase 12: choose a narrow opt-in apply path, likely export/backup command preflight behind explicit governance config, or add a server-readiness/policy document before any automatic command instrumentation.

## 2026-07-01 - v3 Phase 12 Governance Policy Readiness

### Completed

- Used the `codebase-design` skill guidance to keep policy readiness behind a small explicit governance interface.
- Added `docs/v3/phases/phase-12-governance-policy-readiness/plan.md` before implementation.
- Added `docs/v3/phases/phase-12-governance-policy-readiness/design-notes.md` to record:
  - readiness reporting comes before business command instrumentation.
  - the readiness manifest is a gate for future enforcement phases.
  - local-first and privacy-first defaults must stay visible.
  - server identity, centralized policy storage, automatic business command preflight, automatic audit, centralized audit, and shared backup/restore policy remain incomplete.
  - v2 retrieval, hybrid retrieval, vector indexing, and agent-facing retrieval remain unchanged.
- Added and accepted `docs/v3/phases/phase-12-governance-policy-readiness/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 12 row.
- Extended `threadvault.governance` with:
  - `GOVERNANCE_POLICY_READINESS_CONTRACT_VERSION`
  - `POLICY_READINESS_COMMAND`
  - `governance_policy_readiness`
- Added `ArchiveStore.governance_policy_readiness(...)`.
- Added CLI command:
  - `threadvault governance policy readiness`
- Added JSON schema:
  - `governance_policy_readiness`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot docs, and schema discovery for the policy readiness workflow.
- Added `tests/test_v312_governance_policy_readiness.py`.

### Validation

- Completed schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote `governance_policy_readiness.schema.json`
- Completed focused validation:
  - `py -3.12 -m pytest tests\test_v312_governance_policy_readiness.py` -> 5 passed
  - `py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v312_governance_policy_readiness.py` -> passed
- Completed adjacent governance/discovery validation:
  - `py -3.12 -m pytest tests\test_v310_governance_enforcement_gaps.py tests\test_v311_governance_enforcement_dry_run.py tests\test_v312_governance_policy_readiness.py tests\test_v28_capabilities_schema_contract.py tests\test_v307_governance_baseline.py tests\test_v309_permission_preflight.py` -> 30 passed
- Completed manual smoke:
  - `threadvault governance policy readiness --json` -> passed and returned `overall_status = not_ready_for_team_enforcement`
  - `threadvault schemas list --json` -> passed and listed `governance_policy_readiness`
  - `threadvault capabilities --json` -> passed and advertised `governance policy readiness`
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 267 passed

### Bugs Found

- No implementation bugs found in Phase 12 validation.

### Next

- v3 Phase 12 is accepted as the governance policy readiness manifest.
- Continue v3 toward Phase 13: either implement the first explicitly opt-in business command preflight slice for export/backup, or design server identity and centralized policy storage before shared team enforcement.

## 2026-07-01 - v3 Phase 13 Export/Backup Governance Preflight

### Completed

- Used the `codebase-design` skill guidance to keep export/backup preflight behind a small explicit governance interface.
- Added `docs/v3/phases/phase-13-export-backup-governance-preflight/plan.md` before implementation.
- Added `docs/v3/phases/phase-13-export-backup-governance-preflight/design-notes.md` to record:
  - explicit preflight comes before business command instrumentation.
  - the first business-oriented preflight is limited to export and backup commands.
  - the preflight must not run the checked command or write export/backup artifacts.
  - privacy expectations must be visible even though this command does not scan content.
  - v2 retrieval, hybrid retrieval, vector indexing, and agent-facing retrieval remain unchanged.
- Added and accepted `docs/v3/phases/phase-13-export-backup-governance-preflight/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 13 row.
- Extended `threadvault.governance` with:
  - `GOVERNANCE_EXPORT_BACKUP_PREFLIGHT_CONTRACT_VERSION`
  - `EXPORT_BACKUP_PREFLIGHT_COMMAND`
  - `EXPORT_BACKUP_PREFLIGHT_COMMANDS`
  - `governance_export_backup_preflight`
- Added `ArchiveStore.governance_export_backup_preflight(...)`.
- Added CLI command:
  - `threadvault governance preflight export-backup`
- Added JSON schema:
  - `governance_export_backup_preflight`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot docs, and schema discovery for the export/backup preflight workflow.
- Added `tests/test_v313_export_backup_governance_preflight.py`.

### Validation

- Completed schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote `governance_export_backup_preflight.schema.json`
- Completed focused validation:
  - `py -3.12 -m pytest tests\test_v313_export_backup_governance_preflight.py` -> 6 passed
  - `py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v313_export_backup_governance_preflight.py` -> passed
- Completed adjacent governance/discovery validation:
  - `py -3.12 -m pytest tests\test_v311_governance_enforcement_dry_run.py tests\test_v312_governance_policy_readiness.py tests\test_v313_export_backup_governance_preflight.py tests\test_v310_governance_enforcement_gaps.py tests\test_v309_permission_preflight.py tests\test_v28_capabilities_schema_contract.py` -> 31 passed
- Completed manual smoke:
  - `threadvault governance preflight export-backup --command "threadvault export" --role reviewer --json` -> passed and returned `preflight_status = would_allow`
  - `threadvault governance preflight export-backup --command "threadvault backup" --role reader --json` -> passed and returned `preflight_status = would_block`
  - `threadvault schemas list --json` -> passed and listed `governance_export_backup_preflight`
  - `threadvault capabilities --json` -> passed and advertised `governance preflight export-backup`
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 273 passed

### Bugs Found

- No implementation bugs found in Phase 13 validation.

### Next

- v3 Phase 13 is accepted as the explicit export/backup governance preflight workflow.
- Continue v3 toward Phase 14: choose either restore/retention preflight, raw transcript read preflight, or a server identity/policy planning phase before any automatic business command instrumentation.

## 2026-07-01 - v3 Phase 14 Restore/Retention Governance Preflight

### Completed

- Used the `codebase-design` skill guidance to keep restore/retention preflight behind a small explicit governance interface.
- Added `docs/v3/phases/phase-14-restore-retention-governance-preflight/plan.md` before implementation.
- Added `docs/v3/phases/phase-14-restore-retention-governance-preflight/design-notes.md` to record:
  - restore and retention commands are high-risk because they can replace archive state, rewrite history, or delete evidence.
  - explicit preflight comes before business command instrumentation.
  - the phase covers only restore and retention commands.
  - the preflight must not restore databases, rewrite history, delete files, or apply retention.
  - v2 retrieval, hybrid retrieval, vector indexing, and agent-facing retrieval remain unchanged.
- Added and accepted `docs/v3/phases/phase-14-restore-retention-governance-preflight/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 14 row.
- Extended `threadvault.governance` with:
  - `GOVERNANCE_RESTORE_RETENTION_PREFLIGHT_CONTRACT_VERSION`
  - `RESTORE_RETENTION_PREFLIGHT_COMMAND`
  - `RESTORE_RETENTION_PREFLIGHT_COMMANDS`
  - `governance_restore_retention_preflight`
- Added `ArchiveStore.governance_restore_retention_preflight(...)`.
- Added CLI command:
  - `threadvault governance preflight restore-retention`
- Added JSON schema:
  - `governance_restore_retention_preflight`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot docs, and schema discovery for the restore/retention preflight workflow.
- Added `tests/test_v314_restore_retention_governance_preflight.py`.

### Validation

- Completed schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote `governance_restore_retention_preflight.schema.json`
- Completed focused validation:
  - `py -3.12 -m pytest tests\test_v314_restore_retention_governance_preflight.py` -> 6 passed
  - `py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v314_restore_retention_governance_preflight.py` -> passed
- Completed adjacent governance/discovery validation:
  - `py -3.12 -m pytest tests\test_v313_export_backup_governance_preflight.py tests\test_v314_restore_retention_governance_preflight.py tests\test_v311_governance_enforcement_dry_run.py tests\test_v312_governance_policy_readiness.py tests\test_v310_governance_enforcement_gaps.py tests\test_v28_capabilities_schema_contract.py` -> 32 passed
- Completed manual smoke:
  - `threadvault governance preflight restore-retention --command "threadvault restore" --role maintainer --json` -> passed and returned `preflight_status = would_allow`
  - `threadvault governance preflight restore-retention --command "threadvault audit-history prune" --role reader --json` -> passed and returned `preflight_status = would_block`
  - `threadvault schemas list --json` -> passed and listed `governance_restore_retention_preflight`
  - `threadvault capabilities --json` -> passed and advertised `governance preflight restore-retention`
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 279 passed

### Bugs Found

- No implementation bugs found in Phase 14 validation.

### Next

- v3 Phase 14 is accepted as the explicit restore/retention governance preflight workflow.
- Continue v3 toward Phase 15: choose raw transcript/client read preflight, search/retrieval preflight, or a server identity/policy planning phase before automatic business command instrumentation.

## 2026-07-01 - v3 Phase 15 Raw Read Governance Preflight

### Completed

- Used the `codebase-design` skill guidance to keep raw-read preflight behind a small explicit governance interface.
- Added `docs/v3/phases/phase-15-raw-read-governance-preflight/plan.md` before implementation.
- Added `docs/v3/phases/phase-15-raw-read-governance-preflight/design-notes.md` to record:
  - raw transcript reads are high sensitivity.
  - explicit preflight comes before client command instrumentation.
  - the phase covers only `threadvault client session`.
  - the preflight must not return raw transcript text, event previews, local debug metadata, raw paths, or session detail payloads.
  - v2 retrieval, hybrid retrieval, vector indexing, and agent-facing retrieval remain unchanged.
- Added and accepted `docs/v3/phases/phase-15-raw-read-governance-preflight/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 15 row.
- Extended `threadvault.governance` with:
  - `GOVERNANCE_RAW_READ_PREFLIGHT_CONTRACT_VERSION`
  - `RAW_READ_PREFLIGHT_COMMAND`
  - `RAW_READ_PREFLIGHT_COMMANDS`
  - `governance_raw_read_preflight`
- Reused a shared private preflight-status helper for export/backup, restore/retention, and raw-read preflight results.
- Added `ArchiveStore.governance_raw_read_preflight(...)`.
- Added CLI command:
  - `threadvault governance preflight raw-read`
- Added JSON schema:
  - `governance_raw_read_preflight`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot docs, and schema discovery for the raw-read preflight workflow.
- Added `tests/test_v315_raw_read_governance_preflight.py`.

### Validation

- Completed schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote `governance_raw_read_preflight.schema.json`
- Completed focused validation:
  - `py -3.12 -m pytest tests\test_v315_raw_read_governance_preflight.py` -> 6 passed
  - `py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v315_raw_read_governance_preflight.py` -> passed
- Completed adjacent governance/discovery validation:
  - `py -3.12 -m pytest tests\test_v315_raw_read_governance_preflight.py tests\test_v314_restore_retention_governance_preflight.py tests\test_v313_export_backup_governance_preflight.py tests\test_v311_governance_enforcement_dry_run.py tests\test_v310_governance_enforcement_gaps.py tests\test_v28_capabilities_schema_contract.py` -> 33 passed
- Completed manual smoke:
  - `threadvault governance preflight raw-read --command "threadvault client session" --role owner --json` -> passed and returned `preflight_status = would_allow`
  - `threadvault governance preflight raw-read --command "threadvault client session" --role reader --json` -> passed and returned `preflight_status = would_block`
  - `threadvault schemas list --json` -> passed and listed `governance_raw_read_preflight`
  - `threadvault capabilities --json` -> passed and advertised `governance preflight raw-read`
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 285 passed

### Bugs Found

- No implementation bugs found in Phase 15 validation.
- `git status --short` could not run because the workspace is not a git repository; validation used file-level tests and CLI smoke checks instead.

### Next

- v3 Phase 15 is accepted as the explicit raw-read governance preflight workflow.
- Continue v3 toward Phase 16: choose summary/search read preflight for retrieval and agent-facing reads, or design server identity and centralized policy storage before automatic business command instrumentation.

## 2026-07-01 - v3 Phase 16 Summary/Search Governance Preflight

### Completed

- Used the `codebase-design` skill guidance to keep summary/search preflight behind a small explicit governance interface.
- Re-read the required v3 source documents before implementation:
  - `docs/README.md`
  - `docs/roadmap/major-version-roadmap.md`
  - `docs/roadmap/v3-clients-and-team-governance.md`
  - `docs/v2/README.md`
  - `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
  - `docs/v3/README.md`
  - `docs/v3/phases/phase-15-raw-read-governance-preflight/acceptance.md`
  - `docs/development-progress.md`
- Added `docs/v3/phases/phase-16-summary-search-governance-preflight/plan.md` before implementation.
- Added `docs/v3/phases/phase-16-summary-search-governance-preflight/design-notes.md` to record:
  - summary/search reads use a separate access level from raw transcripts.
  - explicit preflight comes before retrieval, agent, or warning command instrumentation.
  - the phase covers only `threadvault client warnings`, `threadvault agent retrieve`, `threadvault retrieval query`, and `threadvault retrieval hybrid`.
  - the preflight must not return search results, snippets, warning details, evidence chunks, raw paths, local debug metadata, or session payloads.
  - v2 retrieval, hybrid retrieval, vector indexing, and agent-facing retrieval remain unchanged.
- Added and accepted `docs/v3/phases/phase-16-summary-search-governance-preflight/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 16 row.
- Extended `threadvault.governance` with:
  - `GOVERNANCE_SUMMARY_SEARCH_PREFLIGHT_CONTRACT_VERSION`
  - `SUMMARY_SEARCH_PREFLIGHT_COMMAND`
  - `SUMMARY_SEARCH_PREFLIGHT_COMMANDS`
  - `governance_summary_search_preflight`
- Added `ArchiveStore.governance_summary_search_preflight(...)`.
- Added CLI command:
  - `threadvault governance preflight summary-search`
- Added JSON schema:
  - `governance_summary_search_preflight`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot docs, and schema discovery for the summary/search preflight workflow.
- Added `tests/test_v316_summary_search_governance_preflight.py`.

### Validation

- Completed schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote `governance_summary_search_preflight.schema.json`
- Completed focused validation:
  - `py -3.12 -m pytest tests\test_v316_summary_search_governance_preflight.py` -> 7 passed
  - `py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v316_summary_search_governance_preflight.py` -> passed
- Completed adjacent governance/discovery validation:
  - `py -3.12 -m pytest tests\test_v316_summary_search_governance_preflight.py tests\test_v315_raw_read_governance_preflight.py tests\test_v314_restore_retention_governance_preflight.py tests\test_v313_export_backup_governance_preflight.py tests\test_v311_governance_enforcement_dry_run.py tests\test_v310_governance_enforcement_gaps.py tests\test_v28_capabilities_schema_contract.py` -> 40 passed
- Completed manual smoke:
  - `threadvault governance preflight summary-search --command "threadvault retrieval query" --role reader --json` -> passed and returned `preflight_status = would_allow`
  - `threadvault governance preflight summary-search --command "threadvault unknown" --role reader --json` -> passed and returned `preflight_status = unknown_command`
  - `threadvault schemas list --json` -> passed and listed `governance_summary_search_preflight`
  - `threadvault capabilities --json` -> passed and advertised `governance preflight summary-search`
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 292 passed

### Bugs Found

- No implementation bugs found in Phase 16 validation.

### Next

- v3 Phase 16 is accepted as the explicit summary/search governance preflight workflow.
- Continue v3 toward Phase 17: choose export-preview governance preflight, external model adapter governance planning, or server identity and centralized policy storage before automatic business command instrumentation.

## 2026-07-01 - v3 Phase 17 Export Preview Governance Preflight

### Completed

- Used the `codebase-design` skill guidance to keep export-preview preflight behind a small explicit governance interface.
- Re-read the required v3 source documents before implementation:
  - `docs/README.md`
  - `docs/roadmap/major-version-roadmap.md`
  - `docs/roadmap/v3-clients-and-team-governance.md`
  - `docs/v2/README.md`
  - `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
  - `docs/v3/README.md`
  - `docs/v3/phases/phase-16-summary-search-governance-preflight/acceptance.md`
  - `docs/development-progress.md`
- Added `docs/v3/phases/phase-17-export-preview-governance-preflight/plan.md` before implementation.
- Added `docs/v3/phases/phase-17-export-preview-governance-preflight/design-notes.md` to record:
  - export preview is read-only but uses export access.
  - explicit preflight comes before client export-preview instrumentation.
  - the phase covers only `threadvault client export-preview`.
  - the preflight must not generate export previews, return manifests, scan content, write files, expose local paths, or return raw metadata.
  - v2 retrieval, hybrid retrieval, vector indexing, and agent-facing retrieval remain unchanged.
- Added and accepted `docs/v3/phases/phase-17-export-preview-governance-preflight/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 17 row.
- Extended `threadvault.governance` with:
  - `GOVERNANCE_EXPORT_PREVIEW_PREFLIGHT_CONTRACT_VERSION`
  - `EXPORT_PREVIEW_PREFLIGHT_COMMAND`
  - `EXPORT_PREVIEW_PREFLIGHT_COMMANDS`
  - `governance_export_preview_preflight`
- Added `ArchiveStore.governance_export_preview_preflight(...)`.
- Added CLI command:
  - `threadvault governance preflight export-preview`
- Added JSON schema:
  - `governance_export_preview_preflight`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot docs, and schema discovery for the export-preview preflight workflow.
- Added `tests/test_v317_export_preview_governance_preflight.py`.

### Validation

- Completed schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote `governance_export_preview_preflight.schema.json`
- Completed focused validation:
  - `py -3.12 -m pytest tests\test_v317_export_preview_governance_preflight.py` -> 6 passed
  - `py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v317_export_preview_governance_preflight.py` -> passed
- Completed adjacent governance/discovery validation:
  - `py -3.12 -m pytest tests\test_v317_export_preview_governance_preflight.py tests\test_v316_summary_search_governance_preflight.py tests\test_v315_raw_read_governance_preflight.py tests\test_v313_export_backup_governance_preflight.py tests\test_v311_governance_enforcement_dry_run.py tests\test_v310_governance_enforcement_gaps.py tests\test_v28_capabilities_schema_contract.py` -> 40 passed
- Completed manual smoke:
  - `threadvault governance preflight export-preview --command "threadvault client export-preview" --role reviewer --json` -> passed and returned `preflight_status = would_allow`
  - `threadvault governance preflight export-preview --command "threadvault client export-preview" --role reader --json` -> passed and returned `preflight_status = would_block`
  - `threadvault schemas list --json` -> passed and listed `governance_export_preview_preflight`
  - `threadvault capabilities --json` -> passed and advertised `governance preflight export-preview`
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 298 passed

### Bugs Found

- No implementation bugs found in Phase 17 validation.

### Next

- v3 Phase 17 is accepted as the explicit export-preview governance preflight workflow.
- Continue v3 toward Phase 18: choose external model adapter governance planning, server identity and centralized policy storage, or the first opt-in automatic command instrumentation slice.

## 2026-07-01 - v3 Phase 18 External Model Governance Preflight

### Completed

- Used the `codebase-design` skill guidance to keep external-model preflight behind a small explicit governance interface.
- Re-read the required v3 source documents before implementation:
  - `docs/README.md`
  - `docs/roadmap/major-version-roadmap.md`
  - `docs/roadmap/v3-clients-and-team-governance.md`
  - `docs/v2/README.md`
  - `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
  - `docs/v3/README.md`
  - `docs/v3/phases/phase-17-export-preview-governance-preflight/acceptance.md`
  - `docs/development-progress.md`
- Added `docs/v3/phases/phase-18-external-model-governance-preflight/plan.md` before implementation.
- Added `docs/v3/phases/phase-18-external-model-governance-preflight/design-notes.md` to record:
  - external model calls stay opt-in.
  - external model adapters currently map to export access.
  - the preflight must not send prompts, transcript text, embeddings, summaries, local metadata, paths, or provider requests.
  - future adapters require outbound policy, privacy scan/redaction decision, evidence validation, and audit behavior before shared execution.
  - v2 retrieval, hybrid retrieval, vector indexing, summary pipeline, and agent-facing retrieval remain unchanged.
- Added and accepted `docs/v3/phases/phase-18-external-model-governance-preflight/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 18 row.
- Extended `threadvault.governance` with:
  - `GOVERNANCE_EXTERNAL_MODEL_PREFLIGHT_CONTRACT_VERSION`
  - `EXTERNAL_MODEL_PREFLIGHT_COMMAND`
  - `EXTERNAL_MODEL_PREFLIGHT_COMMANDS`
  - `governance_external_model_preflight`
- Added `ArchiveStore.governance_external_model_preflight(...)`.
- Added CLI command:
  - `threadvault governance preflight external-model`
- Added JSON schema:
  - `governance_external_model_preflight`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot docs, and schema discovery for the external-model preflight workflow.
- Added `tests/test_v318_external_model_governance_preflight.py`.

### Validation

- Completed schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote `governance_external_model_preflight.schema.json`
- Completed focused validation:
  - `py -3.12 -m pytest tests\test_v318_external_model_governance_preflight.py` -> 6 passed
  - `py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v318_external_model_governance_preflight.py` -> passed after organizing `src\threadvault\store.py` imports
- Completed adjacent governance/discovery validation:
  - `py -3.12 -m pytest tests\test_v318_external_model_governance_preflight.py tests\test_v317_export_preview_governance_preflight.py tests\test_v316_summary_search_governance_preflight.py tests\test_v313_export_backup_governance_preflight.py tests\test_v311_governance_enforcement_dry_run.py tests\test_v310_governance_enforcement_gaps.py tests\test_v28_capabilities_schema_contract.py` -> 40 passed
- Completed manual smoke:
  - `threadvault governance preflight external-model --command "external model adapters" --role reviewer --json` -> passed and returned `preflight_status = would_allow`
  - `threadvault governance preflight external-model --command "external model adapters" --role reader --json` -> passed and returned `preflight_status = would_block`
  - `threadvault schemas list --json` -> passed and listed `governance_external_model_preflight`
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 304 passed

### Bugs Found

- Focused ruff caught unsorted imports in `src\threadvault\store.py`; `ruff --fix` organized the import block.

### Next

- v3 Phase 18 is accepted as the explicit external-model governance preflight workflow.
- Continue v3 toward Phase 19: choose server identity and centralized policy storage planning, centralized audit retention planning, or the first opt-in automatic command instrumentation slice.

## 2026-07-01 - v3 Phase 19 Server Policy Readiness

### Completed

- Used the `codebase-design` skill guidance to keep server policy readiness behind a small explicit governance interface.
- Re-read the required v3 source documents before implementation:
  - `docs/README.md`
  - `docs/roadmap/major-version-roadmap.md`
  - `docs/roadmap/v3-clients-and-team-governance.md`
  - `docs/v2/README.md`
  - `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
  - `docs/v3/README.md`
  - `docs/v3/phases/phase-18-external-model-governance-preflight/acceptance.md`
  - `docs/development-progress.md`
- Added `docs/v3/phases/phase-19-server-policy-readiness/plan.md` before implementation.
- Added `docs/v3/phases/phase-19-server-policy-readiness/design-notes.md` to record:
  - readiness comes before server runtime.
  - server/team mode remains opt-in and not required for local CLI.
  - centralized policy storage is a future module.
  - automatic business command instrumentation remains deferred.
  - v2 retrieval, hybrid retrieval, vector indexing, summary pipeline, and agent-facing retrieval remain unchanged.
- Added and accepted `docs/v3/phases/phase-19-server-policy-readiness/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 19 row.
- Extended `threadvault.governance` with:
  - `GOVERNANCE_SERVER_POLICY_READINESS_CONTRACT_VERSION`
  - `SERVER_POLICY_READINESS_COMMAND`
  - `governance_server_policy_readiness`
- Added `ArchiveStore.governance_server_policy_readiness(...)`.
- Added CLI command:
  - `threadvault governance server policy-readiness`
- Added JSON schema:
  - `governance_server_policy_readiness`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot docs, and schema discovery for the server policy readiness workflow.
- Added `tests/test_v319_server_policy_readiness.py`.

### Validation

- Completed schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote `governance_server_policy_readiness.schema.json`
- Completed focused validation:
  - `py -3.12 -m pytest tests\test_v319_server_policy_readiness.py` -> 4 passed
  - `py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v319_server_policy_readiness.py` -> passed
- Completed adjacent governance/discovery validation:
  - `py -3.12 -m pytest tests\test_v319_server_policy_readiness.py tests\test_v318_external_model_governance_preflight.py tests\test_v312_governance_policy_readiness.py tests\test_v28_capabilities_schema_contract.py` -> 20 passed
- Completed manual smoke:
  - `threadvault governance server policy-readiness --json` -> passed and returned `overall_status = not_ready_for_shared_enforcement`
  - `threadvault schemas list --json` -> passed and listed `governance_server_policy_readiness`
  - `threadvault capabilities --json` -> passed and advertised `governance server policy-readiness`
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 308 passed

### Bugs Found

- No implementation bugs found in Phase 19 validation.

### Next

- v3 Phase 19 is accepted as the server policy readiness manifest.
- Continue v3 toward Phase 20: choose centralized audit retention planning, centralized backup/restore policy planning, or the first opt-in automatic command instrumentation slice after identity and policy readiness are explicit.

## 2026-07-01 - v3 Phase 20 Centralized Audit Retention Readiness

### Completed

- Used the `codebase-design` skill guidance to keep centralized audit readiness behind a small explicit governance
  interface.
- Re-read the required v3 source documents before implementation:
  - `docs/README.md`
  - `docs/roadmap/major-version-roadmap.md`
  - `docs/roadmap/v3-clients-and-team-governance.md`
  - `docs/v2/README.md`
  - `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
  - `docs/v3/README.md`
  - `docs/v3/phases/phase-20-centralized-audit-retention-readiness/plan.md`
  - `docs/v3/phases/phase-20-centralized-audit-retention-readiness/design-notes.md`
  - `docs/development-progress.md`
- Accepted `docs/v3/phases/phase-20-centralized-audit-retention-readiness/acceptance.md`.
- Extended `threadvault.governance` Phase 20 readiness payload through public store, CLI, schema, capabilities, robot guide,
  and robot schema discovery surfaces.
- Added `ArchiveStore.governance_centralized_audit_readiness(...)`.
- Added CLI command:
  - `threadvault governance audit centralized-readiness`
- Added JSON schema:
  - `governance_centralized_audit_readiness`
- Regenerated schema artifacts under `docs/schemas/`.
- Added `tests/test_v320_centralized_audit_readiness.py`.
- Preserved local-first/privacy-first invariants:
  - `server_required = false`
  - `server_opt_in = true`
  - `cloud_sync = false`
  - local JSONL audit remains available and local-only
  - centralized audit remains not ready
  - v2 retrieval, hybrid retrieval, vector indexing, summary pipeline, and agent-facing retrieval remain unchanged

### Validation

- Completed schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote
    `governance_centralized_audit_readiness.schema.json`
- Completed focused validation:
  - `py -3.12 -m pytest tests\test_v320_centralized_audit_readiness.py` -> 4 passed
  - `py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v320_centralized_audit_readiness.py` -> passed
- Completed adjacent governance/discovery validation:
  - `py -3.12 -m pytest tests\test_v320_centralized_audit_readiness.py tests\test_v319_server_policy_readiness.py tests\test_v308_local_audit_log.py tests\test_v28_capabilities_schema_contract.py` -> 17 passed
- Completed manual smoke:
  - `threadvault governance audit centralized-readiness --json` -> passed and returned
    `overall_status = not_ready_for_centralized_audit`
  - `threadvault schemas list --json` -> passed and listed `governance_centralized_audit_readiness`
  - `threadvault capabilities --json` -> passed and advertised `governance audit centralized-readiness`
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 312 passed

### Bugs Found

- No implementation bugs found in Phase 20 validation.

### Next

- v3 Phase 20 is accepted as the centralized audit retention readiness manifest.
- Continue v3 toward Phase 21: choose centralized backup/restore policy readiness, identity/actor binding readiness, or a
  final v3 gap audit before implementing the first opt-in shared/server prototype slice.

## 2026-07-01 - v3 Phase 21 v3 Completion Gap Audit

### Completed

- Used the `codebase-design` skill guidance to keep the completion gap audit behind a small explicit governance
  interface.
- Re-read the required v3 source documents before implementation:
  - `docs/README.md`
  - `docs/roadmap/major-version-roadmap.md`
  - `docs/roadmap/v3-clients-and-team-governance.md`
  - `docs/v2/README.md`
  - `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
  - `docs/v3/README.md`
  - `docs/development-progress.md`
- Added `docs/v3/phases/phase-21-v3-completion-gap-audit/plan.md` before implementation.
- Added `docs/v3/phases/phase-21-v3-completion-gap-audit/design-notes.md`.
- Added and accepted `docs/v3/phases/phase-21-v3-completion-gap-audit/gap-audit.md`.
- Added and accepted `docs/v3/phases/phase-21-v3-completion-gap-audit/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 21 row.
- Added a v3 completion gap audit workflow:
  - `threadvault governance v3 gap-audit`
- Added JSON schema:
  - `governance_v3_completion_gap_audit`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot docs, and schema discovery for the v3 completion gap audit workflow.
- Added `tests/test_v321_v3_completion_gap_audit.py`.
- Recorded that v3 is still incomplete and blocked on accepted richer client runtime, optional shared/server runtime,
  identity/actor binding, centralized policy store, centralized audit store, centralized backup/restore policy,
  automatic governance instrumentation, and final v3 acceptance smoke.
- Preserved local-first/privacy-first invariants and left accepted v2 retrieval, hybrid retrieval, vector indexing,
  summary pipeline, and agent-facing retrieval unchanged.

### Validation

- Completed schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote
    `governance_v3_completion_gap_audit.schema.json`
- Completed focused validation:
  - `py -3.12 -m pytest tests\test_v321_v3_completion_gap_audit.py` -> 4 passed
  - `py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v321_v3_completion_gap_audit.py` -> passed
- Completed adjacent governance/discovery validation:
  - `py -3.12 -m pytest tests\test_v321_v3_completion_gap_audit.py tests\test_v320_centralized_audit_readiness.py tests\test_v319_server_policy_readiness.py tests\test_v28_capabilities_schema_contract.py` -> 17 passed
- Completed manual smoke:
  - `threadvault governance v3 gap-audit --json` -> passed and returned `overall_status = incomplete` and
    `v3_complete = false`
  - `threadvault schemas list --json` -> passed and listed `governance_v3_completion_gap_audit`
  - `threadvault capabilities --json` -> passed and advertised `governance v3 gap-audit`
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 316 passed

### Bugs Found

- No implementation bugs found in Phase 21 validation.

### Next

- v3 Phase 21 is accepted as the current completion gap audit.
- Continue v3 toward Phase 22: identity and actor binding readiness, centralized policy store readiness, centralized
  backup/restore policy readiness, or the first opt-in shared/server prototype slice.

## 2026-07-01 - v3 Phase 22 Identity Actor Binding Readiness

### Completed

- Used the `codebase-design` skill guidance to keep identity and actor binding readiness behind a small explicit
  governance interface.
- Re-read the required v3 source documents before implementation:
  - `docs/README.md`
  - `docs/roadmap/major-version-roadmap.md`
  - `docs/roadmap/v3-clients-and-team-governance.md`
  - `docs/v2/README.md`
  - `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
  - `docs/v3/README.md`
  - `docs/development-progress.md`
- Added `docs/v3/phases/phase-22-identity-actor-binding-readiness/plan.md` before implementation.
- Added `docs/v3/phases/phase-22-identity-actor-binding-readiness/design-notes.md`.
- Added and accepted `docs/v3/phases/phase-22-identity-actor-binding-readiness/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 22 row.
- Added an identity and actor binding readiness workflow:
  - `threadvault governance identity actor-readiness`
- Added JSON schema:
  - `governance_identity_actor_readiness`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot docs, and schema discovery for the identity actor readiness workflow.
- Added `tests/test_v322_identity_actor_readiness.py`.
- Recorded that manual local actor labels are available but insufficient for shared enforcement or authenticated actor
  provenance.
- Preserved local-first/privacy-first invariants and left accepted v2 retrieval, hybrid retrieval, vector indexing,
  summary pipeline, and agent-facing retrieval unchanged.

### Validation

- Completed schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote
    `governance_identity_actor_readiness.schema.json`
- Completed focused validation:
  - `py -3.12 -m pytest tests\test_v322_identity_actor_readiness.py` -> 4 passed
  - `py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v322_identity_actor_readiness.py` -> passed
- Completed adjacent governance/discovery validation:
  - `py -3.12 -m pytest tests\test_v322_identity_actor_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v319_server_policy_readiness.py tests\test_v28_capabilities_schema_contract.py` -> 17 passed
- Completed manual smoke:
  - `threadvault governance identity actor-readiness --json` -> passed and returned
    `overall_status = not_ready_for_identity_binding`
  - `threadvault schemas list --json` -> passed and listed `governance_identity_actor_readiness`
  - `threadvault capabilities --json` -> passed and advertised `governance identity actor-readiness`
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 320 passed

### Bugs Found

- No implementation bugs found in Phase 22 validation.

### Next

- v3 Phase 22 is accepted as the identity and actor binding readiness manifest.
- Continue v3 toward Phase 23: centralized policy store readiness, centralized backup/restore policy readiness, or the
  first opt-in shared/server prototype slice after identity readiness is explicit.

## 2026-07-01 - v3 Phase 23 Centralized Policy Store Readiness

### Completed

- Used the `codebase-design` skill guidance to keep centralized policy store readiness behind a small explicit governance
  interface.
- Re-read the required v3 source documents before implementation:
  - `docs/README.md`
  - `docs/roadmap/major-version-roadmap.md`
  - `docs/roadmap/v3-clients-and-team-governance.md`
  - `docs/v2/README.md`
  - `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
  - `docs/v3/README.md`
  - `docs/development-progress.md`
- Added `docs/v3/phases/phase-23-centralized-policy-store-readiness/plan.md` before implementation.
- Added `docs/v3/phases/phase-23-centralized-policy-store-readiness/design-notes.md`.
- Added and accepted `docs/v3/phases/phase-23-centralized-policy-store-readiness/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 23 row.
- Added a centralized policy store readiness workflow:
  - `threadvault governance policy central-readiness`
- Added JSON schema:
  - `governance_central_policy_readiness`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot docs, and schema discovery for the central policy readiness workflow.
- Added `tests/test_v323_central_policy_store_readiness.py`.
- Recorded that local governance role vocabulary and permission preflight are available but insufficient for shared
  enforcement without central policy storage, versioning, provenance, migration/rollback, and identity-bound role
  resolution.
- Preserved local-first/privacy-first invariants and left accepted v2 retrieval, hybrid retrieval, vector indexing,
  summary pipeline, and agent-facing retrieval unchanged.

### Validation

- Completed schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote
    `governance_central_policy_readiness.schema.json`
- Completed focused validation:
  - `py -3.12 -m pytest tests\test_v323_central_policy_store_readiness.py` -> 4 passed
  - `py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v323_central_policy_store_readiness.py` -> passed
- Completed adjacent governance/discovery validation:
  - `py -3.12 -m pytest tests\test_v323_central_policy_store_readiness.py tests\test_v322_identity_actor_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v28_capabilities_schema_contract.py` -> 17 passed
- Completed manual smoke:
  - `threadvault governance policy central-readiness --json` -> passed and returned
    `overall_status = not_ready_for_central_policy_store`
  - `threadvault schemas list --json` -> passed and listed `governance_central_policy_readiness`
  - `threadvault capabilities --json` -> passed and advertised `governance policy central-readiness`
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 324 passed

### Bugs Found

- No implementation bugs found in Phase 23 validation.

### Next

- v3 Phase 23 is accepted as the centralized policy store readiness manifest.
- Continue v3 toward Phase 24: centralized backup/restore policy readiness, policy adapter contract design, or the first
  opt-in shared/server prototype slice after identity and central policy readiness are explicit.

## 2026-07-01 - v3 Phase 24 Centralized Backup/Restore Policy Readiness

### Completed

- Used the `codebase-design` skill guidance to keep centralized backup/restore policy readiness behind a small explicit
  governance interface.
- Re-read the required v3 source documents before implementation:
  - `docs/README.md`
  - `docs/roadmap/major-version-roadmap.md`
  - `docs/roadmap/v3-clients-and-team-governance.md`
  - `docs/v2/README.md`
  - `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
  - `docs/v3/README.md`
  - `docs/development-progress.md`
- Added `docs/v3/phases/phase-24-centralized-backup-restore-policy-readiness/plan.md` before implementation.
- Added `docs/v3/phases/phase-24-centralized-backup-restore-policy-readiness/design-notes.md`.
- Added and accepted `docs/v3/phases/phase-24-centralized-backup-restore-policy-readiness/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 24 row.
- Added a centralized backup/restore policy readiness workflow:
  - `threadvault governance backup central-readiness`
- Added JSON schema:
  - `governance_central_backup_readiness`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot docs, and schema discovery for the central backup readiness workflow.
- Added `tests/test_v324_central_backup_readiness.py`.
- Recorded that local backup, restore, backup manifest, restore plan, restore history, local retention, export/backup
  preflight, and restore/retention preflight are available but insufficient for shared backup/restore policy.
- Preserved local-first/privacy-first invariants and left accepted v2 retrieval, hybrid retrieval, vector indexing,
  summary pipeline, and agent-facing retrieval unchanged.

### Validation

- Completed schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote
    `governance_central_backup_readiness.schema.json`
- Completed focused validation:
  - `py -3.12 -m pytest tests\test_v324_central_backup_readiness.py` -> 4 passed
  - `py -3.12 -m ruff check src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v324_central_backup_readiness.py` -> passed
- Completed adjacent governance/discovery validation:
  - `py -3.12 -m pytest tests\test_v324_central_backup_readiness.py tests\test_v323_central_policy_store_readiness.py tests\test_v320_centralized_audit_readiness.py tests\test_v28_capabilities_schema_contract.py` -> 17 passed
- Completed manual smoke:
  - `threadvault governance backup central-readiness --json` -> passed and returned
    `overall_status = not_ready_for_centralized_backup_restore_policy`
  - `threadvault schemas list --json` -> passed and listed `governance_central_backup_readiness`
  - `threadvault capabilities --json` -> passed and advertised `governance backup central-readiness`
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 328 passed

### Bugs Found

- No implementation bugs found in Phase 24 validation.

### Next

- v3 Phase 24 is accepted as the centralized backup/restore policy readiness manifest.
- Continue v3 toward Phase 25: policy adapter contract design, first opt-in shared/server read-only prototype slice, or
  automatic governance instrumentation planning before final v3 acceptance smoke.

## 2026-07-01 - v3 Phase 25 Read-Only Shared Server Prototype

### Completed

- Used the `codebase-design` skill guidance to keep the shared/server prototype behind a small explicit interface.
- Re-read the required v3 source documents before implementation:
  - `docs/README.md`
  - `docs/roadmap/major-version-roadmap.md`
  - `docs/roadmap/v3-clients-and-team-governance.md`
  - `docs/v2/README.md`
  - `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
  - `docs/v3/README.md`
  - `docs/development-progress.md`
- Added `docs/v3/phases/phase-25-read-only-shared-server-prototype/plan.md` before implementation.
- Added `docs/v3/phases/phase-25-read-only-shared-server-prototype/design-notes.md`.
- Added and accepted `docs/v3/phases/phase-25-read-only-shared-server-prototype/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 25 row.
- Added `threadvault.shared_server` as an opt-in read-only server prototype module.
- Added CLI commands:
  - `threadvault governance server read-only-manifest`
  - `threadvault governance server read-only-smoke`
  - `threadvault governance server serve-read-only --enable`
- Added JSON schemas:
  - `governance_read_only_server_manifest`
  - `governance_read_only_server_smoke`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot docs, and schema discovery for the read-only server prototype.
- Added `tests/test_v325_read_only_shared_server_prototype.py`.
- Updated Phase 19 server policy readiness expectations to recognize the accepted read-only prototype while preserving
  `shared_enforcement_ready = false`.
- Updated Phase 21 v3 gap audit to remove `optional_shared_server_runtime_missing`, mark
  `shared_read_only_deployment = prototype_accepted`, and keep `v3_complete = false`.
- Preserved local-first/privacy-first defaults and left accepted v2 retrieval, hybrid retrieval, vector indexing,
  summary pipeline, and agent-facing retrieval unchanged.

### Validation

- Completed schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote
    `governance_read_only_server_manifest.schema.json` and `governance_read_only_server_smoke.schema.json`
- Completed focused validation:
  - `py -3.12 -m pytest tests\test_v325_read_only_shared_server_prototype.py -q` -> 5 passed
  - `py -3.12 -m pytest tests\test_v325_read_only_shared_server_prototype.py tests\test_v321_v3_completion_gap_audit.py -q` -> 9 passed
  - `py -3.12 -m ruff check src\threadvault\shared_server.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py src\threadvault\governance.py tests\test_v325_read_only_shared_server_prototype.py tests\test_v321_v3_completion_gap_audit.py` -> passed
- Completed adjacent server/client/discovery validation:
  - `py -3.12 -m pytest tests\test_v325_read_only_shared_server_prototype.py tests\test_v321_v3_completion_gap_audit.py tests\test_v319_server_policy_readiness.py tests\test_v303_client_overview.py tests\test_v28_capabilities_schema_contract.py -q` -> 22 passed
  - `py -3.12 -m ruff check src\threadvault\shared_server.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py src\threadvault\governance.py tests\test_v325_read_only_shared_server_prototype.py tests\test_v321_v3_completion_gap_audit.py tests\test_v319_server_policy_readiness.py` -> passed
- Completed manual smoke:
  - `threadvault governance server read-only-manifest --json` -> passed and returned `runtime.prototype = true`
  - `threadvault governance server read-only-smoke --query pytest --json` -> passed and returned `ok = true`
  - `threadvault governance v3 gap-audit --json` -> passed and returned `v3_complete = false`
  - `threadvault schemas list --json` -> passed and listed the new read-only server schemas
  - `threadvault capabilities --json` -> passed and advertised the new read-only server JSON outputs
  - `Test-Path deep-research-report.md` -> `False`

### Bugs Found

- Adjacent Phase 19 tests still expected no server runtime at all. Updated them to distinguish the accepted read-only
  prototype from missing shared/team enforcement.

### Next

- v3 Phase 25 is accepted as the first opt-in read-only shared/server prototype.
- Continue v3 toward Phase 26: automatic governance instrumentation for one narrow business command slice, richer client
  runtime acceptance or explicit deferral, and final v3 acceptance smoke preparation.

## 2026-07-01 - v3 Phase 26 Client Export Preview Governance Instrumentation

### Completed

- Used the `codebase-design` skill guidance to place instrumentation at the `ArchiveStore.client_export_preview` seam.
- Re-read the required v3 source documents before implementation:
  - `docs/README.md`
  - `docs/roadmap/major-version-roadmap.md`
  - `docs/roadmap/v3-clients-and-team-governance.md`
  - `docs/v2/README.md`
  - `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
  - `docs/v3/README.md`
  - `docs/development-progress.md`
- Added `docs/v3/phases/phase-26-client-export-preview-governance-instrumentation/plan.md` before implementation.
- Added `docs/v3/phases/phase-26-client-export-preview-governance-instrumentation/design-notes.md`.
- Added and accepted `docs/v3/phases/phase-26-client-export-preview-governance-instrumentation/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 26 row.
- Added explicit governance instrumentation options to `threadvault client export-preview`:
  - `--governance-role`
  - `--governance-config`
  - `--governance-audit-log`
  - `--governance-actor`
- Reused `governance_export_preview_preflight` from the business command path.
- Added `governance_instrumentation` to the `client_export_preview` JSON payload.
- Added blocked preview payloads when governance is enabled and the role is denied.
- Added optional local preflight audit writes from the business command path.
- Updated capabilities, robot guide, robot schemas, and generated schema artifacts.
- Added `tests/test_v326_client_export_preview_governance_instrumentation.py`.
- Updated Phase 19, Phase 20, and Phase 21 expectations to distinguish one accepted instrumentation slice from broad
  unfinished coverage.
- Preserved local-first/privacy-first defaults and left accepted v2 retrieval, hybrid retrieval, vector indexing,
  summary pipeline, and agent-facing retrieval unchanged.

### Validation

- Completed schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and regenerated `client_export_preview.schema.json`
- Completed focused validation:
  - `py -3.12 -m pytest tests\test_v326_client_export_preview_governance_instrumentation.py -q` -> 5 passed
  - `py -3.12 -m ruff check src\threadvault\client_interface.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py src\threadvault\governance.py tests\test_v326_client_export_preview_governance_instrumentation.py` -> passed after wrapping long governance descriptions
- Completed adjacent client/governance/discovery validation:
  - `py -3.12 -m pytest tests\test_v326_client_export_preview_governance_instrumentation.py tests\test_v305_client_export_preview.py tests\test_v317_export_preview_governance_preflight.py tests\test_v321_v3_completion_gap_audit.py tests\test_v319_server_policy_readiness.py tests\test_v320_centralized_audit_readiness.py tests\test_v28_capabilities_schema_contract.py -q` -> 32 passed
  - `py -3.12 -m ruff check src\threadvault\client_interface.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py src\threadvault\governance.py tests\test_v326_client_export_preview_governance_instrumentation.py tests\test_v321_v3_completion_gap_audit.py tests\test_v319_server_policy_readiness.py tests\test_v320_centralized_audit_readiness.py` -> passed
- Completed manual smoke:
  - Instrumented reviewer preview -> passed with `preflight_allowed`, `preview_generated = true`, and
    `governance_blocked = false`
  - Governance-enabled reader preview -> passed with `preflight_blocked`, `planned_file_count = 0`, and
    `governance_blocked = true`
  - Audit smoke -> passed and listed a local `export_preview_preflight` record with
    `business_command_executed = false` and `files_written = false`
  - `threadvault governance v3 gap-audit --json` -> passed and returned
    `current_phase = phase-26-client-export-preview-governance-instrumentation`, `automatic_instrumentation =
    partially_accepted`, and `v3_complete = false`

### Bugs Found

- Adjacent tests still expected zero instrumented business commands. Updated them to reflect the accepted
  `client export-preview` instrumentation slice while preserving broad instrumentation blockers.

### Next

- v3 Phase 26 is accepted as the first automatic governance instrumentation slice.
- Continue v3 toward Phase 27: expand instrumentation coverage, accept or explicitly defer richer client runtime, and
  prepare final v3 acceptance smoke.

## 2026-07-01 - v3 Phase 27 Local TUI Client Runtime

### Completed

- Used the `codebase-design` skill guidance to keep the richer client runtime behind a small explicit module interface.
- Re-read the required v3 source documents before implementation:
  - `docs/README.md`
  - `docs/roadmap/major-version-roadmap.md`
  - `docs/roadmap/v3-clients-and-team-governance.md`
  - `docs/v2/README.md`
  - `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
  - `docs/v3/README.md`
  - `docs/development-progress.md`
- Added `docs/v3/phases/phase-27-local-tui-client-runtime/plan.md` before implementation.
- Added `docs/v3/phases/phase-27-local-tui-client-runtime/design-notes.md`.
- Added and accepted `docs/v3/phases/phase-27-local-tui-client-runtime/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 27 row.
- Added `threadvault.client_runtime` as the local TUI runtime module.
- Added CLI command:
  - `threadvault client tui`
- Added JSON schema:
  - `client_tui_runtime`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated client manifest, capabilities, robot guide, robot schemas, and v3 completion gap audit.
- Added `tests/test_v327_local_tui_client_runtime.py`.
- Updated older client/server/governance tests that intentionally track the current client schema list and current v3
  phase count.
- Preserved local-first/privacy-first defaults and left accepted v2 retrieval, hybrid retrieval, vector indexing,
  summary pipeline, and agent-facing retrieval unchanged.

### Validation

- Completed schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote
    `client_tui_runtime.schema.json`
- Completed focused validation:
  - `py -3.12 -m pytest tests\test_v327_local_tui_client_runtime.py -q` -> 5 passed
- Completed adjacent client/governance/discovery validation:
  - `py -3.12 -m pytest tests\test_v327_local_tui_client_runtime.py tests\test_v303_client_overview.py tests\test_v305_client_export_preview.py tests\test_v321_v3_completion_gap_audit.py tests\test_v28_capabilities_schema_contract.py -q` -> 22 passed
  - `py -3.12 -m pytest tests\test_v302_client_manifest.py tests\test_v304_client_session_detail.py tests\test_v306_client_warning_detail.py tests\test_v325_read_only_shared_server_prototype.py tests\test_v326_client_export_preview_governance_instrumentation.py tests\test_v327_local_tui_client_runtime.py -q` -> 27 passed
- Completed manual smoke:
  - `threadvault client tui --db TEMP_DB --json` -> passed with `contract_version = client_tui_runtime.v1`
  - `threadvault client tui --db TEMP_DB --query pytest --json` -> passed and reused hybrid retrieval diagnostics
  - `threadvault client tui --db TEMP_DB --export-preview-session sess-current --out TEMP_OUT --json` -> passed with
    `client_export_preview.v1` embedded and `writes_files = false`
  - `threadvault client tui --db TEMP_DB --query pytest --export-preview-session sess-current` -> rendered ThreadVault,
    Sessions, Search, and Export Preview sections
  - `threadvault governance v3 gap-audit --json` -> passed and returned
    `accepted_phase_count = 27`, `current_phase = phase-27-local-tui-client-runtime`,
    `richer_client_runtime.status = accepted_minimal_tui_runtime`, and `v3_complete = false`
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 343 passed

### Bugs Found

- Full regression found older client discovery and v3 gap-audit tests that still expected the Phase 26 schema list,
  phase count, and current phase. Updated them to reflect the accepted local TUI runtime while preserving all remaining
  governance blockers.

### Next

- v3 Phase 27 is accepted as the minimal local richer client runtime.
- Continue v3 toward Phase 28: implement the next governance blocker, likely identity actor binding or a central policy
  store prototype, while keeping server/team capabilities opt-in and local CLI behavior unchanged.

## 2026-07-01 - v3 Phase 28 Identity Actor Binding Runtime

### Completed

- Used the `codebase-design` skill guidance to keep the identity actor binding runtime behind explicit config,
  governance, store, CLI, and schema boundaries.
- Re-read the required v3 source documents before implementation:
  - `docs/README.md`
  - `docs/roadmap/major-version-roadmap.md`
  - `docs/roadmap/v3-clients-and-team-governance.md`
  - `docs/v2/README.md`
  - `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
  - `docs/v3/README.md`
  - `docs/development-progress.md`
- Added `docs/v3/phases/phase-28-identity-actor-binding-runtime/plan.md` before implementation.
- Added `docs/v3/phases/phase-28-identity-actor-binding-runtime/design-notes.md`.
- Accepted `docs/v3/phases/phase-28-identity-actor-binding-runtime/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 28 row.
- Added local static governance actor config support under `[governance.identity] actors = []`.
- Added `threadvault governance identity bind` as an opt-in actor binding command.
- Added store and governance runtime support for actor binding, role mapping, request metadata, and optional local audit
  writes with operation `identity_actor_binding`.
- Added JSON schema:
  - `governance_identity_actor_binding`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot guide, robot schemas, identity readiness, server policy readiness, centralized audit
  readiness, central policy readiness, central backup readiness, and the v3 completion gap audit.
- Added `tests/test_v328_identity_actor_binding_runtime.py`.
- Updated older v3 tests that intentionally track the current phase count and current phase.
- Preserved local-first/privacy-first defaults and left accepted v2 retrieval, hybrid retrieval, vector indexing,
  summary pipeline, and agent-facing retrieval unchanged.

### Validation

- Completed schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote
    `governance_identity_actor_binding.schema.json`
- Completed focused validation:
  - `py -3.12 -m pytest tests\test_v328_identity_actor_binding_runtime.py -q` -> 6 passed
- Completed adjacent validation:
  - `py -3.12 -m pytest tests\test_v328_identity_actor_binding_runtime.py tests\test_v322_identity_actor_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v319_server_policy_readiness.py tests\test_v320_centralized_audit_readiness.py tests\test_v323_central_policy_store_readiness.py tests\test_v324_central_backup_readiness.py tests\test_v12_app_config.py tests\test_v13_config_cli.py tests\test_v28_capabilities_schema_contract.py -q` -> 51 passed
  - `py -3.12 -m ruff check src\threadvault\app_config.py src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v328_identity_actor_binding_runtime.py tests\test_v322_identity_actor_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v319_server_policy_readiness.py tests\test_v320_centralized_audit_readiness.py tests\test_v323_central_policy_store_readiness.py tests\test_v324_central_backup_readiness.py tests\test_v12_app_config.py tests\test_v13_config_cli.py` -> passed
- Completed manual smoke:
  - `threadvault governance identity bind --config CONFIG --actor reviewer@example --command "threadvault client export-preview" --operation export_archive --target-type session --target-id sess-current --client-id threadvault-local-tui --audit-log AUDIT --json` -> passed with `binding.bound = true`, `role_mapping.roles = ["reviewer"]`, and `audit.written = true`
  - `threadvault governance audit list --log AUDIT --json` -> passed and listed operation `identity_actor_binding`
  - `threadvault governance identity actor-readiness --config CONFIG --json` -> passed with
    `identity_binding_ready = true` while preserving shared governance blockers
  - `threadvault governance v3 gap-audit --json` -> passed with `accepted_phase_count = 28`,
    `current_phase = phase-28-identity-actor-binding-runtime`, `blocking_count = 5`, and `v3_complete = false`
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 351 passed

### Bugs Found

- Full regression found three older Phase 25-27 tests that still expected `accepted_phase_count = 27` and
  `current_phase = phase-27-local-tui-client-runtime`. Updated them to reflect the accepted Phase 28 state while
  preserving the checks for their original capabilities.

### Next

- v3 Phase 28 is accepted as the local identity actor binding prerequisite for team governance.
- Continue v3 toward Phase 29 with one of the remaining blockers:
  - `central_policy_store_missing`
  - `centralized_audit_store_missing`
  - `centralized_backup_restore_policy_missing`
  - `automatic_governance_instrumentation_incomplete`
  - `v3_acceptance_smoke_missing`

## 2026-07-01 - v3 Phase 29 Central Policy Store Runtime

### Completed

- Used the `codebase-design` skill guidance to keep central policy loading, validation, and actor/operation resolution
  behind one small governance runtime interface.
- Re-read the required v3 source documents before implementation:
  - `docs/README.md`
  - `docs/roadmap/major-version-roadmap.md`
  - `docs/roadmap/v3-clients-and-team-governance.md`
  - `docs/v2/README.md`
  - `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
  - `docs/v3/README.md`
  - `docs/development-progress.md`
- Re-read Phase 23 central policy readiness docs and Phase 28 identity actor binding acceptance before implementation.
- Added `docs/v3/phases/phase-29-central-policy-store-runtime/plan.md` before implementation.
- Added `docs/v3/phases/phase-29-central-policy-store-runtime/design-notes.md`.
- Accepted `docs/v3/phases/phase-29-central-policy-store-runtime/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 29 row.
- Added local config support for `[governance.policy] central_store`.
- Added `threadvault governance policy central-store` as an opt-in local central policy runtime command.
- Added policy document validation for contract, policy id, version, provenance, roles, access levels, and actor role
  bindings.
- Added actor-to-policy role resolution and operation allow/deny preview using existing governance roles, access
  levels, and sensitive operations.
- Added JSON schema:
  - `governance_central_policy_store`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot guide, robot schemas, central policy readiness, server policy readiness, central backup
  readiness, and the v3 completion gap audit.
- Added `tests/test_v329_central_policy_store_runtime.py`.
- Updated older v3 tests that intentionally track the current phase count and central policy readiness state.
- Preserved local-first/privacy-first defaults and left accepted v2 retrieval, hybrid retrieval, vector indexing,
  summary pipeline, and agent-facing retrieval unchanged.

### Validation

- Completed schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote
    `governance_central_policy_store.schema.json`
- Completed focused and adjacent validation:
  - `py -3.12 -m pytest tests\test_v329_central_policy_store_runtime.py tests\test_v323_central_policy_store_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v319_server_policy_readiness.py tests\test_v324_central_backup_readiness.py -q` -> 22 passed
  - `py -3.12 -m ruff check src\threadvault\app_config.py src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v329_central_policy_store_runtime.py tests\test_v323_central_policy_store_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v319_server_policy_readiness.py tests\test_v324_central_backup_readiness.py` -> passed
- Completed wider v3 validation:
  - `py -3.12 -m pytest tests\test_v319_server_policy_readiness.py tests\test_v320_centralized_audit_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v322_identity_actor_readiness.py tests\test_v323_central_policy_store_readiness.py tests\test_v324_central_backup_readiness.py tests\test_v325_read_only_shared_server_prototype.py tests\test_v326_client_export_preview_governance_instrumentation.py tests\test_v327_local_tui_client_runtime.py tests\test_v328_identity_actor_binding_runtime.py tests\test_v329_central_policy_store_runtime.py tests\test_v28_capabilities_schema_contract.py tests\test_v12_app_config.py tests\test_v13_config_cli.py -q` -> 72 passed
- Completed manual smoke:
  - `threadvault governance policy central-store --config CONFIG --actor reviewer@example --operation export_archive --json` -> passed with `policy.valid = true`, `store.available = true`, `operation_resolution.allowed = true`, and `enforcement.shared_enforcement_ready = false`
  - `threadvault governance policy central-readiness --config CONFIG --json` -> passed with
    `central_policy_ready = true` and `safe_to_enable_team_enforcement = false`
  - `threadvault governance server policy-readiness --config CONFIG --json` -> passed with
    `central_store_implemented = true` and shared enforcement still not ready
  - `threadvault governance backup central-readiness --config CONFIG --json` -> passed with central policy dependency
    ready and centralized backup still not ready
  - `threadvault governance v3 gap-audit --json` -> passed with `accepted_phase_count = 29`,
    `current_phase = phase-29-central-policy-store-runtime`, `blocking_count = 4`, and `v3_complete = false`
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 357 passed

### Bugs Found

- Wider validation found older readiness and gap-audit tests that still expected central policy storage to be entirely
  missing and Phase 28 to be current. Updated them to distinguish the accepted local central policy store runtime from
  remaining shared enforcement, centralized audit, centralized backup, and instrumentation blockers.

### Next

- v3 Phase 29 is accepted as the local central policy store runtime.
- Continue v3 toward Phase 30 with one of the remaining blockers:
  - `centralized_audit_store_missing`
  - `centralized_backup_restore_policy_missing`
  - `automatic_governance_instrumentation_incomplete`
  - `v3_acceptance_smoke_missing`

## 2026-07-01 - v3 Phase 30 Centralized Audit Store Runtime

### Completed

- Used the `codebase-design` skill guidance to keep the centralized audit store behind one small governance runtime
  interface with append, list, and verify actions.
- Re-read the required v3 source documents before implementation:
  - `docs/README.md`
  - `docs/roadmap/major-version-roadmap.md`
  - `docs/roadmap/v3-clients-and-team-governance.md`
  - `docs/v2/README.md`
  - `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
  - `docs/v3/README.md`
  - `docs/development-progress.md`
- Re-read Phase 20 centralized audit readiness documentation before implementation.
- Added `docs/v3/phases/phase-30-centralized-audit-store-runtime/plan.md` before implementation.
- Added `docs/v3/phases/phase-30-centralized-audit-store-runtime/design-notes.md`.
- Accepted `docs/v3/phases/phase-30-centralized-audit-store-runtime/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 30 row.
- Added local config support for `[governance.audit] central_store`.
- Added `threadvault governance audit centralized-store` as an opt-in local centralized audit store runtime command.
- Added append/list/verify behavior for centralized audit JSONL records with record hash and previous-hash validation.
- Added JSON schema:
  - `governance_centralized_audit_store`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot guide, robot schemas, centralized audit readiness, server policy readiness, central backup
  readiness, and the v3 completion gap audit.
- Added `tests/test_v330_centralized_audit_store_runtime.py`.
- Updated older v3 tests that intentionally track current phase count and centralized audit readiness state.
- Preserved local-first/privacy-first defaults and left accepted v2 retrieval, hybrid retrieval, vector indexing,
  summary pipeline, and agent-facing retrieval unchanged.

### Validation

- Completed schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote
    `governance_centralized_audit_store.schema.json`
- Completed focused and adjacent validation:
  - `py -3.12 -m pytest tests\test_v330_centralized_audit_store_runtime.py tests\test_v320_centralized_audit_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v319_server_policy_readiness.py tests\test_v324_central_backup_readiness.py -q` -> 21 passed
  - `py -3.12 -m ruff check src\threadvault\app_config.py src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v330_centralized_audit_store_runtime.py tests\test_v320_centralized_audit_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v319_server_policy_readiness.py tests\test_v324_central_backup_readiness.py` -> passed
- Completed wider v3 validation:
  - `py -3.12 -m pytest tests\test_v319_server_policy_readiness.py tests\test_v320_centralized_audit_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v322_identity_actor_readiness.py tests\test_v323_central_policy_store_readiness.py tests\test_v324_central_backup_readiness.py tests\test_v325_read_only_shared_server_prototype.py tests\test_v326_client_export_preview_governance_instrumentation.py tests\test_v327_local_tui_client_runtime.py tests\test_v328_identity_actor_binding_runtime.py tests\test_v329_central_policy_store_runtime.py tests\test_v330_centralized_audit_store_runtime.py tests\test_v308_local_audit_log.py tests\test_v28_capabilities_schema_contract.py tests\test_v12_app_config.py tests\test_v13_config_cli.py -q` -> 81 passed
- Completed manual smoke:
  - `threadvault governance audit centralized-store --config CONFIG --action append --operation export_archive --actor reviewer@example --status ok --target-type session --target-id sess-current --metadata client=threadvault-local-tui --json` -> passed with `append.written = true`, `store.available = true`, and hash-chain verification ok
  - `threadvault governance audit centralized-store --config CONFIG --action list --actor reviewer@example --json` -> passed with `query.returned_count = 1`
  - `threadvault governance audit centralized-store --config CONFIG --action verify --json` -> passed with
    `verification.ok = true` and `hash_chain_valid = true`
  - `threadvault governance audit centralized-readiness --config CONFIG --json` -> passed with
    `centralized_audit_ready = true`, `store_implemented = true`, and retention/backup/instrumentation still not ready
  - `threadvault governance server policy-readiness --config CONFIG --json` -> passed with
    `audit.centralized_store_implemented = true` and shared enforcement still not ready
  - `threadvault governance backup central-readiness --config CONFIG --json` -> passed with centralized audit store
    runtime available and centralized backup still not ready
  - `threadvault governance v3 gap-audit --json` -> passed with `accepted_phase_count = 30`,
    `current_phase = phase-30-centralized-audit-store-runtime`, `blocking_count = 3`, and `v3_complete = false`
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 362 passed

### Bugs Found

- Focused and wider validation found older readiness and gap-audit tests that still expected the centralized audit store
  to be missing and Phase 29 to be current. Updated them to distinguish the accepted local centralized audit store
  runtime from remaining backup/restore policy, broad instrumentation, and final acceptance blockers.

### Next

- v3 Phase 30 is accepted as the local centralized audit store runtime.
- Continue v3 toward Phase 31 with one of the remaining blockers:
  - `centralized_backup_restore_policy_missing`
  - `automatic_governance_instrumentation_incomplete`
  - `v3_acceptance_smoke_missing`

## 2026-07-01 - v3 Phase 31 Centralized Backup/Restore Policy Runtime

### Completed

- Used the `codebase-design` skill guidance to keep centralized backup/restore policy validation and operation preview
  behind one governance runtime interface.
- Re-read the required v3 source documents before implementation:
  - `docs/README.md`
  - `docs/roadmap/major-version-roadmap.md`
  - `docs/roadmap/v3-clients-and-team-governance.md`
  - `docs/v2/README.md`
  - `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
  - `docs/v3/README.md`
  - `docs/development-progress.md`
- Re-read Phase 24 centralized backup/restore policy readiness docs and Phase 28-30 governance runtime acceptances
  before implementation.
- Added `docs/v3/phases/phase-31-centralized-backup-restore-policy-runtime/plan.md` before implementation.
- Added `docs/v3/phases/phase-31-centralized-backup-restore-policy-runtime/design-notes.md`.
- Accepted `docs/v3/phases/phase-31-centralized-backup-restore-policy-runtime/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 31 row.
- Added local config support for `[governance.backup] policy`.
- Added `threadvault governance backup policy` as an opt-in local centralized backup/restore policy runtime command.
- Added policy validation for repository, backup, restore approval, retention, legal hold, recovery testing, migration,
  and provenance sections.
- Added operation preview for `backup_archive`, `restore_backup`, `delete_or_prune`, `recovery_test`, and
  `migrate_local_history`.
- Kept shared restore execution and broad automatic enforcement false; the runtime validates and previews policy only.
- Added JSON schema:
  - `governance_central_backup_policy`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot guide, robot schemas, centralized backup readiness, centralized audit readiness, server
  policy readiness, and the v3 completion gap audit.
- Added `tests/test_v331_centralized_backup_restore_policy_runtime.py`.
- Updated older v3 tests that intentionally track current phase count, centralized backup policy, audit retention
  policy, and v3 blocker state.
- Preserved local-first/privacy-first defaults and left accepted v2 retrieval, hybrid retrieval, vector indexing,
  summary pipeline, and agent-facing retrieval unchanged.

### Validation

- Completed schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote
    `governance_central_backup_policy.schema.json`
- Completed focused validation:
  - `py -3.12 -m pytest tests\test_v331_centralized_backup_restore_policy_runtime.py -q` -> 5 passed
- Completed adjacent validation:
  - `py -3.12 -m pytest tests\test_v331_centralized_backup_restore_policy_runtime.py tests\test_v324_central_backup_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v319_server_policy_readiness.py tests\test_v320_centralized_audit_readiness.py tests\test_v330_centralized_audit_store_runtime.py tests\test_v329_central_policy_store_runtime.py tests\test_v328_identity_actor_binding_runtime.py tests\test_v327_local_tui_client_runtime.py tests\test_v326_client_export_preview_governance_instrumentation.py tests\test_v325_read_only_shared_server_prototype.py tests\test_v12_app_config.py tests\test_v13_config_cli.py tests\test_v28_capabilities_schema_contract.py -q` -> 74 passed
  - `py -3.12 -m ruff check src\threadvault\app_config.py src\threadvault\governance.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v331_centralized_backup_restore_policy_runtime.py tests\test_v324_central_backup_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v319_server_policy_readiness.py tests\test_v320_centralized_audit_readiness.py tests\test_v330_centralized_audit_store_runtime.py tests\test_v329_central_policy_store_runtime.py tests\test_v328_identity_actor_binding_runtime.py tests\test_v327_local_tui_client_runtime.py tests\test_v326_client_export_preview_governance_instrumentation.py tests\test_v325_read_only_shared_server_prototype.py` -> passed
- Completed wider v3 validation:
  - `py -3.12 -m pytest tests\test_v319_server_policy_readiness.py tests\test_v320_centralized_audit_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v322_identity_actor_readiness.py tests\test_v323_central_policy_store_readiness.py tests\test_v324_central_backup_readiness.py tests\test_v325_read_only_shared_server_prototype.py tests\test_v326_client_export_preview_governance_instrumentation.py tests\test_v327_local_tui_client_runtime.py tests\test_v328_identity_actor_binding_runtime.py tests\test_v329_central_policy_store_runtime.py tests\test_v330_centralized_audit_store_runtime.py tests\test_v331_centralized_backup_restore_policy_runtime.py tests\test_v308_local_audit_log.py tests\test_v28_capabilities_schema_contract.py tests\test_v12_app_config.py tests\test_v13_config_cli.py -q` -> 86 passed
- Completed manual smoke:
  - Valid maintainer restore preview -> passed with `allow_status = would_allow`, `allow = true`, and
    `shared_execution_ready = false`
  - Reader restore preview -> passed with `deny_status = would_block` and `deny = false`
  - Central backup readiness -> passed with `central_backup_ready = true`, `shared_restore_ready = false`,
    `safe_shared_restore = false`, and `central_backup_blocking = 0`
  - `threadvault governance v3 gap-audit --json` -> passed with `accepted_phase_count = 31`,
    `current_phase = phase-31-centralized-backup-restore-policy-runtime`, `blocking_count = 2`, and
    `v3_complete = false`
  - `Test-Path deep-research-report.md` -> `False`
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 367 passed

### Bugs Found

- Adjacent validation found older readiness and gap-audit tests that still expected centralized backup/restore policy,
  audit retention policy, and Phase 30 to be current. Updated them to distinguish the accepted local policy runtime from
  remaining automatic instrumentation and final v3 acceptance blockers.
- Manual smoke found `shared_restore_ready` was too optimistic after policy validation. Tightened it to stay false until
  shared restore execution is explicitly instrumented and accepted.

### Next

- v3 Phase 31 is accepted as the local centralized backup/restore policy runtime.
- Continue v3 toward Phase 32 with the remaining blockers:
  - `automatic_governance_instrumentation_incomplete`
  - `v3_acceptance_smoke_missing`

## 2026-07-01 - v3 Phase 32 Business Command Governance Instrumentation

### Completed

- Used the `codebase-design` skill guidance to keep governance command instrumentation behind one shared runtime
  interface instead of duplicating permission checks in each CLI command.
- Re-read the required v3 source documents before implementation:
  - `docs/README.md`
  - `docs/roadmap/major-version-roadmap.md`
  - `docs/roadmap/v3-clients-and-team-governance.md`
  - `docs/v2/README.md`
  - `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
  - `docs/v3/README.md`
  - `docs/development-progress.md`
- Re-read Phase 21 gap audit and Phase 26 client export-preview governance instrumentation docs before implementation.
- Added `docs/v3/phases/phase-32-business-command-governance-instrumentation/plan.md` before implementation.
- Added `docs/v3/phases/phase-32-business-command-governance-instrumentation/design-notes.md`.
- Accepted `docs/v3/phases/phase-32-business-command-governance-instrumentation/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 32 row.
- Added `threadvault governance instrumentation business-command` as the diagnostic entrypoint for normalized
  business-command instrumentation.
- Added CLI-level governance helpers that call `ArchiveStore.governance_business_command_instrumentation()`.
- Wired explicit governance options into sensitive command families:
  - direct export
  - export-target markdown/obsidian/skill
  - backup
  - restore
  - backup-history prune
  - restore-history prune
  - audit-history prune
  - client session
  - client warnings
  - retrieval query
  - retrieval hybrid
  - agent retrieve
- Preserved existing `client export-preview` governance instrumentation.
- Kept external model behavior as a preflight boundary only; no external model adapter execution was added.
- Added JSON schema:
  - `governance_business_command_instrumentation`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot guide, robot schemas, server policy readiness, centralized audit readiness, gap audit
  output, and older v3 tests that intentionally track phase count or blocker state.
- Added `tests/test_v332_business_command_governance_instrumentation.py`.
- Preserved local-first/privacy-first defaults and left accepted v2 retrieval, hybrid retrieval, vector indexing,
  summary pipeline, and agent-facing retrieval internals unchanged.

### Validation

- Completed schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote
    `governance_business_command_instrumentation.schema.json`
- Completed focused validation:
  - `py -3.12 -m pytest tests\test_v332_business_command_governance_instrumentation.py -q` -> 6 passed
  - `py -3.12 -m ruff check src\threadvault\cli.py src\threadvault\governance.py tests\test_v332_business_command_governance_instrumentation.py` -> passed
- Completed adjacent v3 validation:
  - `py -3.12 -m pytest tests\test_v319_server_policy_readiness.py tests\test_v320_centralized_audit_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v323_central_policy_store_readiness.py tests\test_v324_central_backup_readiness.py tests\test_v325_read_only_shared_server_prototype.py tests\test_v326_client_export_preview_governance_instrumentation.py tests\test_v327_local_tui_client_runtime.py tests\test_v328_identity_actor_binding_runtime.py tests\test_v329_central_policy_store_runtime.py tests\test_v330_centralized_audit_store_runtime.py tests\test_v331_centralized_backup_restore_policy_runtime.py tests\test_v332_business_command_governance_instrumentation.py -q` -> 63 passed
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 373 passed
- Completed gap-audit smoke:
  - `threadvault governance v3 gap-audit --json` -> passed with `accepted_phase_count = 32`,
    `current_phase = phase-32-business-command-governance-instrumentation`, `blocking_count = 1`, and
    `v3_complete = false`

### Bugs Found

- Initial Phase 32 code had advanced gap-audit state before the `governance instrumentation business-command` CLI was
  actually registered. Added the missing Typer subcommand and tests.
- Full validation found older v3 readiness and gap-audit tests that still expected Phase 31, one instrumented command,
  or the automatic instrumentation blocker. Updated them to distinguish accepted broad local instrumentation from
  remaining final v3 acceptance smoke.
- Gap-audit remaining-gap text still said centralized audit instrumentation was pending after Phase 32. Updated it to
  reflect accepted local business-command instrumentation while keeping shared enforcement claims out of scope.

### Next

- v3 Phase 32 is accepted as the broad local business-command governance instrumentation runtime.
- Continue v3 toward Phase 33 with the remaining blocker:
  - `v3_acceptance_smoke_missing`

## 2026-07-01 - v3 Phase 33 v3 Final Acceptance Smoke

### Completed

- Used the `codebase-design` skill guidance to make final v3 acceptance a small runtime interface instead of a
  hand-only checklist.
- Re-read the required v3 source documents before implementation:
  - `docs/README.md`
  - `docs/roadmap/major-version-roadmap.md`
  - `docs/roadmap/v3-clients-and-team-governance.md`
  - `docs/v2/README.md`
  - `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
  - `docs/v3/README.md`
  - `docs/development-progress.md`
- Re-read Phase 32 business-command governance instrumentation acceptance before implementation.
- Added `docs/v3/phases/phase-33-v3-final-acceptance-smoke/plan.md` before implementation.
- Added `docs/v3/phases/phase-33-v3-final-acceptance-smoke/design-notes.md`.
- Accepted `docs/v3/phases/phase-33-v3-final-acceptance-smoke/acceptance.md`.
- Updated `docs/v3/README.md` with the Phase 33 row.
- Added `threadvault governance v3 acceptance-smoke` as the final v3 acceptance smoke command.
- Added final smoke runtime coverage for:
  - local-first/server opt-in/cloud-disabled defaults
  - accepted v2 retrieval, hybrid retrieval, vector-disabled default, and agent retrieval
  - local richer client browse/search/export-preview and TUI runtime
  - optional read-only server prototype
  - raw transcript vs summary/search governance separation
  - denied sensitive side-effect blocking before execution
  - local preflight audit evidence
  - identity actor binding, central policy store, centralized audit store, and central backup policy runtimes
  - external model calls disabled by default
  - capabilities, robot guide, robot schemas, schema artifacts, v3 phase docs, and retired root report invariant
- Added JSON schema:
  - `governance_v3_acceptance_smoke`
- Regenerated schema artifacts under `docs/schemas/`.
- Updated capabilities, robot guide, robot schemas, and v3 completion gap audit.
- Added `tests/test_v333_v3_final_acceptance_smoke.py`.
- Updated older v3 tests that intentionally track current phase count, completion status, and final blocker state.
- Preserved local-first/privacy-first defaults and left accepted v2 retrieval, hybrid retrieval, vector indexing,
  summary pipeline, and agent-facing retrieval internals unchanged.

### Validation

- Completed schema generation:
  - `threadvault schemas write --out docs\schemas --json` -> passed and wrote
    `governance_v3_acceptance_smoke.schema.json`
- Completed focused validation:
  - `py -3.12 -m pytest tests\test_v333_v3_final_acceptance_smoke.py -q` -> 3 passed
  - `py -3.12 -m ruff check src\threadvault\store.py src\threadvault\cli.py src\threadvault\governance.py src\threadvault\schemas.py tests\test_v321_v3_completion_gap_audit.py tests\test_v333_v3_final_acceptance_smoke.py` -> passed
- Completed adjacent v3 validation:
  - `py -3.12 -m pytest tests\test_v319_server_policy_readiness.py tests\test_v320_centralized_audit_readiness.py tests\test_v321_v3_completion_gap_audit.py tests\test_v322_identity_actor_readiness.py tests\test_v323_central_policy_store_readiness.py tests\test_v324_central_backup_readiness.py tests\test_v325_read_only_shared_server_prototype.py tests\test_v326_client_export_preview_governance_instrumentation.py tests\test_v327_local_tui_client_runtime.py tests\test_v328_identity_actor_binding_runtime.py tests\test_v329_central_policy_store_runtime.py tests\test_v330_centralized_audit_store_runtime.py tests\test_v331_centralized_backup_restore_policy_runtime.py tests\test_v332_business_command_governance_instrumentation.py tests\test_v333_v3_final_acceptance_smoke.py -q` -> 70 passed
- Completed final verification:
  - `py -3.12 -m ruff check .` -> passed
  - `py -3.12 -m pytest` -> 376 passed
- Completed manual final smoke:
  - `threadvault import --db TEMP_DB --codex-home tests\fixtures\codex_home --json` -> passed
  - `threadvault governance v3 acceptance-smoke --db TEMP_DB --work-dir TEMP_WORK --query pytest --session sess-current --json` -> passed with `status = accepted`, `ok = true`, `required_check_count = 7`, `failed_check_count = 0`, and `criteria_satisfied_count = 5`
- Completed final gap-audit smoke:
  - `threadvault governance v3 gap-audit --json` -> passed with `overall_status = complete`, `v3_complete = true`,
    `accepted_phase_count = 33`, `current_phase = phase-33-v3-final-acceptance-smoke`, and `blocking_count = 0`
  - `Test-Path deep-research-report.md` -> `False`

### Bugs Found

- First manual smoke attempt used a non-imported temporary database and exposed an unhelpful retrieval traceback. The
  accepted test path imports fixture sessions before running the smoke.
- Focused validation found the vector status field lives under `config.enabled`, not `enabled`. Updated the smoke
  runtime evidence collection.
- Adjacent validation found older phase tests still expected Phase 32 and the final smoke blocker. Updated them to
  track the final accepted v3 state.

### Next

- v3 Phase 33 is accepted as the final v3 acceptance smoke.
- v3 is complete according to `threadvault governance v3 gap-audit --json`.
- Future work should be planned as opt-in hardening or a later version line:
  - production shared enforcement
  - external identity providers
  - desktop/IDE packaging
  - richer client shells

