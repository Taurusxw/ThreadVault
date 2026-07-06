# v4 Phase 01 Plan: Personal UI Readiness

## Status

Accepted for implementation on 2026-07-01.

## Required Context Read

This phase starts after reading:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/v3/README.md`
- `docs/v3/phases/phase-33-v3-final-acceptance-smoke/acceptance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/THREADVAULT_USAGE_MANUAL.md`
- `docs/development-progress.md`

`docs/v4/README.md` did not exist at phase start, so creating it is the first required v4 action.

## Goal

Create the v4 documentation entrypoint and readiness record for ThreadVault Personal Web UI. This phase does not build
the HTTP server yet. It fixes the product boundary, safety boundary, and capability coverage matrix that later UI phases
must satisfy.

## Scope

- Create `docs/v4/README.md`.
- Create this Phase 01 plan before implementation.
- Create `design-notes.md` for local personal UI scope and module seams.
- Create `coverage-matrix.md` mapping required UI actions to existing ThreadVault interfaces.
- Create `acceptance.md` after implementation.
- Add a focused documentation regression test.
- Update `docs/development-progress.md`.

## Non-Scope

- No Web server implementation.
- No new CLI command in this phase.
- No action registry implementation in this phase.
- No React, Vite, Node, bundled frontend dependency, login, cloud sync, team collaboration, or public server behavior.
- No parser, SQLite retrieval, vector, summary, export, privacy, backup, restore, or governance rewrite.

## Existing Interfaces To Reuse

- `ArchiveStore` remains the backend module behind the future UI actions.
- v1 surfaces:
  - `threadvault ingest-queue enqueue/list/process`
  - `threadvault codex-hook ingest/config`
  - `threadvault export-target markdown/obsidian/skill`
- v2 surfaces:
  - `threadvault retrieval query`
  - `threadvault retrieval hybrid`
  - `threadvault summary-pipeline chunks`
  - `threadvault vector status/index/query`
  - `threadvault agent manifest/retrieve`
- v3 surfaces:
  - `threadvault client manifest/overview/tui/session/export-preview/warnings`
  - `threadvault governance status`
  - `threadvault governance preflight ...`
  - `threadvault governance instrumentation business-command`
  - `threadvault governance v3 gap-audit`
  - `threadvault governance v3 acceptance-smoke`

## Implementation Steps

1. Inspect existing CLI, store, client, governance, and schema surfaces.
2. Create the v4 README with development rules, product boundaries, architecture boundaries, and safety boundaries.
3. Create Phase 01 design notes.
4. Create Phase 01 coverage matrix for all required personal UI features.
5. Create Phase 01 acceptance.
6. Add `tests/test_v401_personal_ui_readiness.py`.
7. Run focused tests and smoke commands.
8. Update `docs/development-progress.md` with validation evidence and next steps.

## Acceptance Criteria

- `docs/v4/README.md` exists and names v4 as Personal Web UI.
- Phase 01 has `plan.md`, `design-notes.md`, `coverage-matrix.md`, and `acceptance.md`.
- Coverage matrix includes every required v4 UI capability family from the objective.
- Safety boundaries mention localhost default, explicit confirmation for dangerous writes, export preview, dry-run prune,
  backup target visibility, and disabled cloud/external/team defaults.
- Focused test verifies the v4 docs and no retired `deep-research-report.md` file.
- `docs/development-progress.md` records this round.

