# v3 Phase 14 Plan: Restore/Retention Governance Preflight

## Status

Planned on 2026-07-01.

## Goal

Add `threadvault governance preflight restore-retention --json` as an explicit preflight interface for restore and
retention workflows before any existing restore, prune, or delete command is instrumented for automatic permission checks
or audit writes.

This phase gives richer clients and future optional server mode a safe way to ask whether a restore or retention
operation would satisfy current governance expectations without applying restore, rewriting history, pruning records, or
deleting files.

## Source Documents

This plan is based on:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/v3/phases/phase-10-governance-enforcement-gap-audit/gap-audit.md`
- `docs/v3/phases/phase-12-governance-policy-readiness/acceptance.md`
- `docs/v3/phases/phase-13-export-backup-governance-preflight/acceptance.md`
- `docs/development-progress.md`

## In Scope

- Add a governance preflight command for restore/retention command families.
- Add CLI command:
  - `threadvault governance preflight restore-retention`
- Add JSON schema:
  - `governance_restore_retention_preflight`
- Reuse Phase 10 command inventory to recognize restore/retention commands:
  - `threadvault restore`
  - `threadvault restore-history prune`
  - `threadvault backup-history prune`
  - `threadvault audit-history prune`
- Reuse Phase 09 permission logic and Phase 11 enforcement dry-run logic.
- Report audit, recovery, and retention expectations for future execution.
- Support optional explicit audit logging for the preflight event itself.
- Regenerate packaged schema artifacts.
- Update capabilities and robot docs discovery.
- Add focused tests for allowed, blocked, out-of-scope command, optional audit, discovery, and docs.
- Update acceptance documentation and `docs/development-progress.md`.

## Out Of Scope

- Running `threadvault restore`, `restore-history prune`, `backup-history prune`, or `audit-history prune`.
- Restoring databases, rewriting JSONL history, pruning reports, deleting files, or applying retention.
- Automatically enforcing permissions inside existing business commands.
- Automatically writing audit records from existing business commands.
- Implementing server runtime, centralized policy storage, identity providers, centralized audit, or cloud sync.
- Rewriting v2 retrieval, hybrid retrieval, vector, or agent-facing interfaces.

## Interface Shape

`governance_restore_retention_preflight` includes:

- `contract_version`
- `request`
- `scope`
- `command_policy`
- `permission`
- `enforcement`
- `recovery`
- `audit`
- `execution`
- `diagnostics`

Expected CLI shape:

```powershell
threadvault governance preflight restore-retention --command "threadvault restore" --role maintainer --json
```

Optional audit logging:

```powershell
threadvault governance preflight restore-retention --command "threadvault audit-history prune" --role reader --audit-log audit.jsonl --json
```

## Acceptance Criteria

- The preflight command validates against `governance_restore_retention_preflight`.
- Restore/retention commands resolve to the Phase 10 inventory.
- Non restore/retention commands return structured `out_of_scope` diagnostics.
- The payload distinguishes `would_allow` from future `would_block_if_enforced`.
- Recovery and retention expectations are visible for future execution.
- Audit expectations are visible for restore/retention operations.
- Optional audit logging records only the preflight event.
- The payload always reports:
  - `business_command_executed = false`
  - `restore_applied = false`
  - `retention_applied = false`
  - `files_deleted = false`
- Discovery surfaces advertise `governance_restore_retention_preflight`.
- Existing business commands remain unmodified and unenforced.
- `deep-research-report.md` remains absent.
