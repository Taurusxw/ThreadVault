# v4 Phase 02 Design Notes: Local UI Server

## Module Interface

Phase 02 adds `threadvault.personal_ui` as the local personal Web UI server module. The module keeps the HTTP server
small and routes all archive behavior through existing interfaces:

- `ArchiveStore.client_overview`
- `ArchiveStore.client_session`
- `ArchiveStore.client_warnings`
- `ArchiveStore.agent_retrieve`
- `capabilities()`

The server exposes in-process handler functions (`handle_api_get` and `handle_api_action`) so tests can exercise the
interface without binding a socket. The socket-bound part is limited to stdlib request handling.

## Static Assets

The initial HTML/CSS/JS is intentionally minimal. It proves that the server can return a usable shell and a JSON panel,
but it does not claim Phase 03 workbench completeness.

## Action Entry Point

`POST /api/action` exists in Phase 02, but only rejects missing or unknown actions with a structured `personal_ui_action`
payload. Full action registry coverage is deferred to Phase 04.

This keeps the interface shape stable without pretending dangerous write actions are implemented.

## Safety Boundaries

- Default host is `127.0.0.1`.
- `ui serve` warns when a non-loopback host is explicitly selected.
- No account login, cloud sync, team enforcement, or external model call path is added.
- No React, Vite, Node, or frontend build step is introduced.
- The server calls Python interfaces directly and does not shell out to `threadvault`.

## Deferred To Later Phases

- Phase 03: full workbench navigation and page workflows.
- Phase 04: complete action registry and confirmation/preview enforcement for all actions.
- Phase 05: `threadvault ui smoke --json`.

