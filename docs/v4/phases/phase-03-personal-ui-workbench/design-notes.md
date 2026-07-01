# v4 Phase 03 Design Notes: Personal UI Workbench

## Summary

Phase 03 expands the Phase 02 static shell into a native single-page workbench. The implementation remains inside
`src/threadvault/personal_ui.py` and keeps the HTTP surface from Phase 02: static assets plus read routes and the
placeholder `/api/action` entrypoint.

## Interface Shape

The workbench is intentionally a local browser client over existing ThreadVault interfaces:

- `/api/health` reports local-first and privacy-first defaults.
- `/api/client/overview` powers Archive.
- `/api/retrieve` powers Search through the existing agent retrieval interface.
- `/api/client/session` powers Session detail.
- `/api/client/warnings` powers Privacy and warning inspection.
- `/api/action` remains the single future write-action seam.

No parser, SQLite retrieval, privacy scan, export, backup, restore, schema, or governance business logic is duplicated in
the UI JavaScript.

## Layout Decision

The page uses a dense workbench layout:

- left navigation for required view families
- sticky top search/status bar
- main work area for forms, tables, and details
- right raw JSON output panel

This favors daily local operation over a marketing-style page. The UI uses native forms, tables, buttons, selects,
textarea, and `details`/`summary`. There is no React, Vite, Node, or frontend build step.

## Phase 04 Deferrals

Phase 03 exposes all required capability families, but write-heavy controls are placeholders until Phase 04 implements
the action registry. The UI labels dangerous flows with the required safety rules:

- export actions require preview before writing
- `restore_apply` requires `confirm=true`
- `reindex` requires `confirm=true`
- `vacuum` requires `confirm=true`
- `schema_write` requires `confirm=true`
- backup must display the target path before execution

The placeholder buttons call `/api/action`, which still rejects unknown actions with a structured
`personal_ui_action` response. This makes the future registry seam visible without creating a parallel backend.

## Non-Claims

Phase 03 does not claim:

- complete UI action coverage
- `threadvault ui smoke --json`
- desktop packaging
- login, team collaboration, cloud sync, public server defaults, or external model execution

Those boundaries remain assigned to later phases or out of v4 personal scope.
