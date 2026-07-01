# v3 Phase 08 Plan: Local Audit Log Workflow

## Status

Planned on 2026-07-01.

## Goal

Add an explicit local append-only audit log workflow through `threadvault governance audit append --json` and
`threadvault governance audit list --json`.

This phase gives sensitive operations a durable local evidence trail without forcing server mode, cloud sync, or
permission enforcement into existing local CLI commands.

## Source Documents

This plan is based on:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/v3/phases/phase-07-governance-baseline/design-notes.md`
- `docs/development-progress.md`

## In Scope

- Add append-only local audit log helpers.
- Add CLI commands:
  - `threadvault governance audit append`
  - `threadvault governance audit list`
- Add JSON schemas:
  - `governance_audit_append`
  - `governance_audit_list`
- Regenerate packaged schema artifacts.
- Update capabilities, robot docs, and governance discovery.
- Add focused tests for append/list behavior, malformed line tolerance, discovery, and docs.
- Update `docs/v3/README.md` and `docs/development-progress.md`.

## Out Of Scope

- Automatically writing audit records from existing commands.
- Enforcing permissions.
- Server runtime or centralized audit storage.
- Cloud sync.
- Identity providers, user invitations, or team membership.
- Storing raw transcript content in audit records.

## Interface Shape

`governance_audit_append` includes:

- `contract_version`
- `ok`
- `log`
- `record`
- `diagnostics`

`governance_audit_list` includes:

- `contract_version`
- `log`
- `records`
- `warnings`
- `diagnostics`

Audit records include:

- `record_version`
- `record_id`
- `timestamp`
- `operation`
- `actor`
- `status`
- `target`
- `metadata`
- `local_only`

## Acceptance Criteria

- Append creates a JSONL audit log when missing.
- Append preserves existing records and appends a new line.
- List returns records newest first or in documented stable order.
- Malformed JSONL lines are returned as warnings without hiding valid records.
- Audit workflow reports local-only, server-not-required defaults.
- Discovery surfaces advertise the audit schemas and commands.
- `deep-research-report.md` remains absent.
