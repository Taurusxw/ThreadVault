# v4 Phase 06 Plan: UI Chinese Localization

## Status

Planned after Phase 05.

## Goal

Add an independent Chinese browser UI for the v4 Personal Web UI without replacing the accepted English UI baseline.

English remains the default entrypoint:

- `/`
- `/assets/app.js`
- `threadvault ui serve --open`

Chinese is additive:

- `/zh`
- `/assets/app.zh.js`
- `threadvault ui serve --lang zh --open`

## Scope

- Add Chinese static resources in `threadvault.personal_ui`:
  - `INDEX_HTML_ZH`
  - `APP_JS_ZH`
- Reuse the existing CSS at `/assets/app.css`.
- Reuse existing `/api/*` read routes and `/api/action`.
- Add `threadvault ui serve --lang en|zh`, defaulting to `en`.
- Make `--lang` affect only the URL opened by `--open`.
- Add focused tests for English baseline preservation, Chinese route serving, and CLI behavior.
- Add this phase's traceability docs and update the v4 phase index plus development progress.

## Out Of Scope

- No React, Vite, Node, i18n framework, or frontend build pipeline.
- No translated JSON schema names, JSON fields, action ids, API paths, or CLI command names.
- No parallel backend or new business rules.
- No change to host, port, database, config, safety confirmation, or smoke behavior.

## Validation Plan

Focused validation:

```powershell
py -3.12 -m pytest tests\test_v406_ui_chinese_localization.py -q
```

Adjacent v4 validation:

```powershell
py -3.12 -m pytest tests\test_v402_local_ui_server.py tests\test_v403_personal_ui_workbench.py tests\test_v404_ui_action_coverage.py tests\test_v405_v4_acceptance_smoke.py tests\test_v406_ui_chinese_localization.py -q
```

Final verification:

```powershell
py -3.12 -m ruff check .
py -3.12 -m pytest
threadvault ui smoke --json
threadvault ui serve --help
Test-Path deep-research-report.md
```

## Acceptance Criteria

- English UI resources still contain the accepted English title and navigation.
- `/zh` returns Chinese HTML with `lang="zh-CN"`.
- `/assets/app.zh.js` returns Chinese visible UI strings.
- `/` and `/assets/app.js` remain English.
- `threadvault ui serve --help` shows `--lang` with default `en`.
- `--lang zh --open` opens `/zh`; default `--open` opens `/`.
- Existing v4 local-first and privacy-first safety boundaries still pass.
