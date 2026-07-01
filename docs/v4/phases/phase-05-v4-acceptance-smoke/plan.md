# v4 Phase 05 Plan: v4 Acceptance Smoke

## Status

Planned after Phase 04.

## Goal

Add final v4 smoke validation for the Personal Web UI:

```powershell
threadvault ui smoke --json
```

The smoke should prove that the local UI server, core API routes, action safety rules, and v2/v3 non-regression
boundaries all hold together.

## Scope

- Add `threadvault ui smoke --db PATH --json`.
- Add JSON schemas:
  - `personal_ui_health`
  - `personal_ui_action`
  - `personal_ui_smoke`
- Add capability flags:
  - `personal_web_ui: true`
  - `personal_ui_desktop_wrapper: false`
  - `personal_ui_team_mode: false`
  - `personal_ui_cloud_sync: false`
- Add robot docs entries for:
  - `threadvault ui serve`
  - `threadvault ui smoke`
- Validate server and action behavior against fixture data.

## Smoke Criteria

- `threadvault ui serve --help` is available.
- UI server starts on `127.0.0.1`.
- `/api/health` returns ok.
- `/api/client/overview` lists fixture sessions.
- `/api/retrieve?q=pytest` returns results.
- `/api/client/session?session=sess-current` returns summary and event preview.
- `/api/action` can execute dry-run or safe actions.
- Export preview does not write files.
- Restore apply without confirmation is rejected.
- Cloud, public server, team, login, and external model behavior are not default paths.
- Accepted v2 retrieval and v3 governance acceptance do not regress.
- `deep-research-report.md` remains absent.

## Validation Plan

Focused tests:

- UI server health route.
- Overview route reuses `ArchiveStore.client_overview`.
- Retrieve route reuses `ArchiveStore.agent_retrieve`.
- Session route reuses `ArchiveStore.client_session`.
- Action registry rejects unknown actions.
- Dangerous actions require `confirm=true`.
- Export preview does not write files.
- Restore apply without confirm is blocked.
- Schema contracts validate.

Integration smoke:

```powershell
threadvault import --db TEMP_DB --codex-home tests\fixtures\codex_home --json
threadvault ui smoke --db TEMP_DB --json
```

Final verification:

```powershell
py -3.12 -m ruff check .
py -3.12 -m pytest
threadvault capabilities --json
threadvault ui smoke --json
Test-Path deep-research-report.md
```

## Acceptance Criteria

- `threadvault ui smoke --json` passes on fixture data.
- Public discovery surfaces advertise the v4 UI contracts.
- Local-first/privacy-first defaults are preserved.
- The v4 acceptance document records validation results and non-claims.

