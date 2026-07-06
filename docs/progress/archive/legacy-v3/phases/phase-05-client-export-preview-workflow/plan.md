# v3 Phase 05 Plan: Client Export Preview Workflow

## Status

Planned and executed on 2026-07-01.

## Goal

Add `threadvault client export-preview --json` so richer clients can inspect planned export files, privacy mode, skipped
items, and evidence coverage before invoking file-writing export commands.

The preview must be read-only and must reuse the existing export target module instead of duplicating export behavior in
the client layer.

## Source Documents

This plan is based on:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/v3/phases/phase-04-client-session-detail-workflow/design-notes.md`
- `docs/development-progress.md`

## In Scope

- Add a read-only export preview function to the export target module.
- Add `ArchiveStore.client_export_preview(...)`.
- Add CLI command:
  - `threadvault client export-preview`
- Add JSON schema:
  - `client_export_preview`
- Regenerate packaged schema artifacts.
- Update capabilities, robot docs, and client manifest discovery.
- Add focused tests proving preview does not write output files.
- Update `docs/v3/README.md` and `docs/development-progress.md`.

## Out Of Scope

- Writing export files.
- Replacing `export-target` execution commands.
- GUI implementation.
- Server runtime.
- Team permissions.
- New privacy rules.

## Interface Shape

`client_export_preview` includes:

- `contract_version`
- `request`
- `selection`
- `planned_files`
- `skipped`
- `privacy`
- `evidence`
- `actions`
- `diagnostics`

The `actions.execute` field points to the real `export-target` command a client can run after user confirmation.

## Acceptance Criteria

- Session preview validates against `client_export_preview`.
- Project preview validates and lists selected sessions.
- `privacy_mode = fail` reports blocked high-risk sessions without writing export files.
- Preview output includes planned file paths and evidence IDs.
- Output directories are not created by preview.
- Discovery surfaces advertise `client_export_preview`.
- `deep-research-report.md` remains absent.

