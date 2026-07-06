# v3 Phase 06 Plan: Client Warning Detail Workflow

## Status

Planned on 2026-07-01.

## Goal

Add `threadvault client warnings --json` so richer clients can show structured parser warning and privacy finding
details for a session without reading raw transcripts or duplicating warning/privacy logic.

This phase completes the local client remediation loop started by `client session` and `client export-preview`: a user can
see that a session has issues, inspect why, and decide whether to re-ingest, redact, configure an allowlist, or avoid
exporting.

## Source Documents

This plan is based on:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/v3/phases/phase-05-client-export-preview-workflow/design-notes.md`
- `docs/development-progress.md`

## In Scope

- Add a read-only client warning detail payload.
- Reuse existing warning persistence and privacy scan behavior.
- Add `ArchiveStore.client_warnings(...)`.
- Add CLI command:
  - `threadvault client warnings`
- Add JSON schema:
  - `client_warnings`
- Regenerate packaged schema artifacts.
- Update capabilities, robot docs, and client manifest discovery.
- Add focused tests for warning detail, privacy findings, discovery, and local metadata defaults.
- Update `docs/v3/README.md` and `docs/development-progress.md`.

## Out Of Scope

- Regenerating parser warnings.
- Changing privacy rules or allowlist semantics.
- Writing redacted exports.
- GUI implementation.
- Server runtime.
- Team permissions or centralized audit enforcement.

## Interface Shape

`client_warnings` includes:

- `contract_version`
- `request`
- `session`
- `warnings`
- `privacy`
- `actions`
- `diagnostics`

The `actions` block should point clients toward existing safe next steps such as `privacy-scan`, `config show`, and
`client export-preview`. It should not perform remediation automatically.

## Acceptance Criteria

- Session warnings validate against `client_warnings`.
- Privacy findings are summarized for sessions that contain sensitive content.
- Default output does not expose raw local file paths.
- Explicit local debug mode may include local metadata and must mark that choice in `privacy.raw_paths_included`.
- Discovery surfaces advertise `client_warnings`.
- `deep-research-report.md` remains absent.
