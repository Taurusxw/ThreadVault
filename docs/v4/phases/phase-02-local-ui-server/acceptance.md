# v4 Phase 02 Acceptance: Local UI Server

## Status

Accepted on 2026-07-01.

## Scope

Phase 02 accepts the first local Personal Web UI runtime:

- `src/threadvault/personal_ui.py`
- `threadvault ui serve --host 127.0.0.1 --port 8766 --open`
- minimal static HTML/CSS/JS shell
- read JSON routes for health, capabilities, overview, session, warnings, and retrieve
- structured `POST /api/action` rejection for unknown actions
- discovery/schema updates for the new public interface

## Routes

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

## Validation

Focused validation:

```powershell
py -3.12 -m pytest tests\test_v402_local_ui_server.py -q
py -3.12 -m ruff check src\threadvault\personal_ui.py src\threadvault\cli.py src\threadvault\store.py src\threadvault\schemas.py tests\test_v402_local_ui_server.py
threadvault schemas write --out docs\schemas --json
threadvault ui serve --help
threadvault capabilities --json
threadvault robot-docs guide --json
threadvault robot-docs schemas --json
Test-Path deep-research-report.md
```

Final results are recorded in `docs/development-progress.md`.

## Final Result

ThreadVault has a local stdlib Web UI server foundation. It is not yet the complete workbench or final action registry,
but the public command, routes, safety defaults, schemas, and tests are in place for Phase 03 and Phase 04.

## Non-Claims Preserved

- No `threadvault ui smoke --json` yet; that remains Phase 05.
- No complete workbench navigation yet; that remains Phase 03.
- No full action coverage yet; that remains Phase 04.
- No cloud sync, team mode, login, public server default, external model execution, React, Vite, or Node dependency.

