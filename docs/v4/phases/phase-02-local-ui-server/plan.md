# v4 Phase 02 Plan: Local UI Server

## Status

Planned after Phase 01.

## Goal

Add the local Personal Web UI server runtime and CLI entrypoint:

```powershell
threadvault ui serve --host 127.0.0.1 --port 8766 --open
```

The server should be a small Python stdlib HTTP server that serves static files and exposes JSON endpoints over existing
ThreadVault modules.

## Scope

- Add `src/threadvault/personal_ui.py`.
- Add `threadvault ui serve --host 127.0.0.1 --port 8766 --open --db PATH --config PATH`.
- Serve a minimal single-page HTML shell plus CSS and JavaScript assets.
- Add read endpoints:
  - `GET /`
  - `GET /assets/app.css`
  - `GET /assets/app.js`
  - `GET /api/health`
  - `GET /api/capabilities`
  - `GET /api/client/overview`
  - `GET /api/client/session?session=...`
  - `GET /api/client/warnings?session=...`
  - `GET /api/retrieve?q=...`
- Add `POST /api/action` as the single action entrypoint.

## Non-Scope

- No complete workbench UI yet.
- No exhaustive action coverage yet.
- No public server default.
- No login, account system, cloud sync, external model calls, team enforcement, React, Vite, or Node.
- No shelling out to `threadvault` commands for business behavior.

## Interface Shape

`POST /api/action` should accept:

```json
{
  "action": "import",
  "params": {},
  "confirm": true
}
```

The handler should call a Python action interface, not create one HTTP route per CLI command. That keeps the HTTP server
shallow and gives later phases one deep action registry seam.

## Safety Requirements

- Default bind host is `127.0.0.1`.
- Public binding is never the default.
- `/api/action` must reject unknown actions.
- Dangerous write actions must be blocked unless `confirm=true`.
- Export execution must be preview-first.
- Backup actions must show the target path.
- Cloud/team/external model defaults stay disabled.

## Acceptance Criteria

- `threadvault ui serve --help` works.
- The server starts on `127.0.0.1` with a configurable port.
- `/api/health` returns JSON with local-first and server safety metadata.
- `/api/capabilities` reuses `capabilities()`.
- Overview, session, warnings, and retrieve routes reuse `ArchiveStore` methods.
- Focused tests cover server routes without requiring browser automation.

