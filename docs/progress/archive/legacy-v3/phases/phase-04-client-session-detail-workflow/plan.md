# v3 Phase 04 Plan: Client Session Detail Workflow

## Status

Planned and executed on 2026-07-01.

## Goal

Add `threadvault client session --session SESSION_ID --json` so richer clients can move from overview cards into a safe
session detail view.

The detail payload includes session metadata, local rule summary, evidence IDs, limited event previews, action hints, and
privacy diagnostics. It must not become a raw transcript dump.

## Source Documents

This plan is based on:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/v3/phases/phase-03-client-overview-workflow/design-notes.md`
- `docs/development-progress.md`

## In Scope

- Extend `threadvault.client_interface` with a session detail payload builder.
- Add `ArchiveStore.client_session(...)`.
- Add CLI command:
  - `threadvault client session`
- Add JSON schema:
  - `client_session`
- Regenerate packaged schema artifacts.
- Update capabilities, robot docs, and client manifest discovery.
- Add focused tests for default privacy, local-debug opt-in, unknown-session handling, discovery, schemas, and docs.
- Update `docs/v3/README.md` and `docs/development-progress.md`.

## Out Of Scope

- Full transcript rendering.
- Export file writing.
- Desktop/IDE/Web/TUI implementation.
- Server runtime.
- Team permissions.
- New retrieval logic.

## Privacy Rules

- Default payload omits session `raw_path`.
- Default event previews omit `file_path`.
- `--local-debug` is required for raw path and event file path metadata.
- Event text is previewed and bounded by `--max-chars`.
- Number of returned events is bounded by `--event-limit`.

## Acceptance Criteria

- `client_session` validates against its JSON schema.
- Default detail payload includes summary evidence and event previews but no raw local paths.
- `--local-debug` explicitly includes raw path and event file path metadata.
- Unknown session IDs fail with a controlled CLI error.
- Discovery surfaces advertise `client_session`.
- `deep-research-report.md` remains absent.

