# v4 Phase 05 Acceptance: v4 Acceptance Smoke

## Accepted Scope

Phase 05 accepts the Personal Web UI by adding:

- `threadvault ui smoke --json`
- `personal_ui_smoke.v1`
- `docs/schemas/personal_ui_smoke.schema.json`
- capabilities and robot docs discovery for the smoke command and schema
- focused runtime and CLI tests

## Acceptance Criteria

- `threadvault ui serve` remains available and defaults to `127.0.0.1:8766`.
- The UI server can bind on loopback.
- `/api/health` returns ok with local-first defaults.
- `/api/client/overview` lists imported fixture sessions.
- `/api/retrieve?q=pytest` returns retrieval results.
- `/api/client/session?session=sess-current` returns summary and event previews.
- `/api/action` executes safe read actions.
- Export preview does not write files.
- Dangerous actions reject without `confirm=true`.
- Cloud sync, public server, team mode, login, and external model calls remain non-default.
- Accepted v2 retrieval and v3 governance acceptance smoke do not regress.
- Public discovery and schema artifacts are present.
- `deep-research-report.md` remains absent.

## Validation

Final validation is recorded in `docs/development-progress.md` for this phase.

## Non-Claims

Phase 05 does not make the Personal UI a public server, a multi-user team app, a desktop packaged app, or a cloud-synced
product. It closes the v4 local personal Web UI acceptance loop over the existing ThreadVault modules.
