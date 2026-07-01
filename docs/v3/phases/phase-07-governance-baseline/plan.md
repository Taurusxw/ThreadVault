# v3 Phase 07 Plan: Governance Baseline

## Status

Planned on 2026-07-01.

## Goal

Add an opt-in governance baseline through `threadvault governance status --json`.

This phase defines stable vocabulary and discovery surfaces for future team governance without turning ThreadVault into a
mandatory server or changing local CLI behavior. It prepares the product for later permissions and audit-log phases by
making governance state explicit and machine-readable.

## Source Documents

This plan is based on:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/v3/phases/phase-06-client-warning-detail-workflow/design-notes.md`
- `docs/development-progress.md`

## In Scope

- Add a `threadvault.governance` module with a small status interface.
- Add optional `[governance] enabled = true` app config support.
- Add `ArchiveStore.governance_status(...)`.
- Add CLI command group:
  - `threadvault governance status`
- Add JSON schema:
  - `governance_status`
- Regenerate packaged schema artifacts.
- Update capabilities, robot docs, and client manifest discovery.
- Add focused tests for default-off behavior, config opt-in behavior, discovery, and docs.
- Update `docs/v3/README.md` and `docs/development-progress.md`.

## Out Of Scope

- Enforcing permissions on existing commands.
- Writing audit records.
- Implementing server runtime.
- Adding cloud sync.
- Adding users, identity providers, or invitations.
- Changing local-first CLI defaults.

## Interface Shape

`governance_status` includes:

- `contract_version`
- `enabled`
- `mode`
- `access_levels`
- `roles`
- `sensitive_operations`
- `audit_requirements`
- `defaults`
- `diagnostics`

The payload should make future governance decisions discoverable while clearly reporting that enforcement and shared
server mode are not implemented in this phase.

## Acceptance Criteria

- Default governance status is disabled.
- `[governance] enabled = true` is an explicit opt-in and does not require a server.
- Access levels include raw transcript, summary/search, export, delete/retention, and restore.
- Sensitive operations include reads, search, export, delete/retention, restore, and external model calls.
- Discovery surfaces advertise `governance_status`.
- `deep-research-report.md` remains absent.
