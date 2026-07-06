# v3 Phase 13 Plan: Export/Backup Governance Preflight

## Status

Planned on 2026-07-01.

## Goal

Add `threadvault governance preflight export-backup --json` as an explicit preflight interface for export and backup
workflows before any existing business command is instrumented for automatic permission checks or audit writes.

This phase gives richer clients and future optional server mode a safe way to ask whether an export or backup operation
would satisfy current governance expectations without writing files, creating backups, or changing default CLI behavior.

## Source Documents

This plan is based on:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/v3/phases/phase-10-governance-enforcement-gap-audit/gap-audit.md`
- `docs/v3/phases/phase-11-governance-enforcement-dry-run/acceptance.md`
- `docs/v3/phases/phase-12-governance-policy-readiness/acceptance.md`
- `docs/development-progress.md`

## In Scope

- Add a governance preflight command for export/backup command families.
- Add CLI command:
  - `threadvault governance preflight export-backup`
- Add JSON schema:
  - `governance_export_backup_preflight`
- Reuse Phase 10 command inventory to recognize export/backup commands:
  - `threadvault export`
  - `threadvault export-target markdown`
  - `threadvault export-target obsidian`
  - `threadvault export-target skill`
  - `threadvault backup`
- Reuse Phase 09 permission logic and Phase 11 enforcement dry-run logic.
- Report privacy and audit expectations for future execution.
- Support optional explicit audit logging for the preflight event itself.
- Regenerate packaged schema artifacts.
- Update capabilities and robot docs discovery.
- Add focused tests for allowed, blocked, out-of-scope command, optional audit, discovery, and docs.
- Update acceptance documentation and `docs/development-progress.md`.

## Out Of Scope

- Running `threadvault export`, `threadvault export-target ...`, or `threadvault backup`.
- Writing export files, manifests, vault files, skill files, or backup databases.
- Automatically enforcing permissions inside existing business commands.
- Automatically writing audit records from existing business commands.
- Implementing server runtime, centralized policy storage, identity providers, centralized audit, or cloud sync.
- Rewriting v2 retrieval, hybrid retrieval, vector, or agent-facing interfaces.

## Interface Shape

`governance_export_backup_preflight` includes:

- `contract_version`
- `request`
- `scope`
- `command_policy`
- `permission`
- `enforcement`
- `privacy`
- `audit`
- `execution`
- `diagnostics`

Expected CLI shape:

```powershell
threadvault governance preflight export-backup --command "threadvault export" --role reviewer --json
```

Optional audit logging:

```powershell
threadvault governance preflight export-backup --command "threadvault backup" --role reader --audit-log audit.jsonl --json
```

## Acceptance Criteria

- The preflight command validates against `governance_export_backup_preflight`.
- Export/backup commands resolve to the Phase 10 inventory.
- Non export/backup commands return structured `out_of_scope` diagnostics.
- The payload distinguishes `would_allow` from future `would_block_if_enforced`.
- Privacy expectations are visible for export/share operations.
- Audit expectations are visible for export/backup operations.
- Optional audit logging records only the preflight event.
- The payload always reports:
  - `business_command_executed = false`
  - `files_written = false`
  - `backup_created = false`
- Discovery surfaces advertise `governance_export_backup_preflight`.
- Existing business commands remain unmodified and unenforced.
- `deep-research-report.md` remains absent.
