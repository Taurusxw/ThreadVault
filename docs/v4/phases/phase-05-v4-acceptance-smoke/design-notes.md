# v4 Phase 05 Design Notes: v4 Acceptance Smoke

## Runtime Interface

Phase 05 adds `threadvault ui smoke --json` as the final Personal Web UI acceptance interface.

The smoke runtime lives in `threadvault.personal_ui` beside the local UI route and action handlers. This keeps the
acceptance path on the same module seam as the browser:

- `handle_api_get()` for health, overview, retrieval, and session detail routes.
- `handle_api_action()` for safe action execution, export preview, and dangerous-action rejection.
- `build_personal_ui_server()` for loopback bind verification.
- `ArchiveStore` for accepted v2 retrieval and v3 governance acceptance non-regression.

The command returns `personal_ui_smoke.v1`, a structured object with checks, criteria, local-first boundaries, and
diagnostics. Tests and agents can validate the whole phase through one stable contract instead of parsing CLI text.

## Safety Boundary

The smoke does not perform destructive writes. It verifies that dangerous actions reject without confirmation:

- `restore_apply`
- `vacuum`
- `reindex`
- `schema_write`

It also verifies that export preview reports `writes_files=false` and leaves the planned output directory absent.

## Non-Claims

Phase 05 does not add a desktop wrapper, login, team collaboration, cloud sync, public server default, external model
execution, React/Vite/Node build pipeline, or a parallel backend.

The smoke is an acceptance check for the v4 personal local Web UI, not a production uptime monitor.
