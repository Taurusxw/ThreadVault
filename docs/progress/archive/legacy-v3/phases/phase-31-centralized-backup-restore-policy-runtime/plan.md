# v3 Phase 31 Plan: Centralized Backup/Restore Policy Runtime

## Status

Planned on 2026-07-01.

## Goal

Close the `centralized_backup_restore_policy_missing` v3 blocker by adding a minimal opt-in local centralized
backup/restore policy runtime.

This phase should turn the Phase 24 readiness report into an executable policy interface that can validate a local
policy document and preview backup, restore, retention, legal-hold, recovery-test, and migration decisions. It must not
claim remote replication, cloud sync, or production shared restore execution.

## Source Documents

This plan is based on:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/v3/phases/phase-24-centralized-backup-restore-policy-readiness/plan.md`
- `docs/v3/phases/phase-24-centralized-backup-restore-policy-readiness/design-notes.md`
- `docs/v3/phases/phase-24-centralized-backup-restore-policy-readiness/acceptance.md`
- `docs/v3/phases/phase-28-identity-actor-binding-runtime/acceptance.md`
- `docs/v3/phases/phase-29-central-policy-store-runtime/acceptance.md`
- `docs/v3/phases/phase-30-centralized-audit-store-runtime/acceptance.md`
- `docs/development-progress.md`

## In Scope

- Add config support for a local centralized backup/restore policy document:
  - `[governance.backup] policy = "path/to/backup-policy.json"`
- Add governance runtime command:
  - `threadvault governance backup policy --json`
- Add JSON schema:
  - `governance_central_backup_policy`
- Validate a local policy document with:
  - contract version
  - policy id and version
  - provenance and approval metadata
  - backup scope and cadence
  - repository shape
  - retention rules
  - restore approval rules
  - legal hold rules
  - recovery testing expectations
  - migration rules from local backup/restore history
- Preview one requested operation against the policy:
  - `backup_archive`
  - `restore_backup`
  - `delete_or_prune`
  - `recovery_test`
  - `migrate_local_history`
- Update `governance backup central-readiness` so a valid policy clears the centralized backup/restore policy blocker
  while preserving remaining automatic instrumentation and final acceptance blockers.
- Update server policy readiness and v3 completion gap audit to recognize the accepted local policy runtime.
- Regenerate packaged schema artifacts.
- Add focused tests for default local-first behavior, valid policy decisions, invalid policy diagnostics, readiness/gap
  changes, discovery/schema/docs, and `deep-research-report.md` absence.
- Update acceptance documentation and `docs/development-progress.md`.

## Out Of Scope

- Implementing remote object storage, cloud sync, replication workers, or a shared backup repository service.
- Executing backup, restore, or prune commands automatically from the policy command.
- Adding production-grade legal hold enforcement or destructive retention execution.
- Adding broad command instrumentation; that remains the next blocker after this phase.
- Making server/cloud/team behavior mandatory.
- Changing accepted v2 retrieval, hybrid retrieval, vector indexing, summary pipeline, or agent-facing retrieval behavior.

## Interface Shape

Expected config:

```toml
[governance.backup]
policy = "central-backup-policy.json"
```

Expected command:

```powershell
threadvault governance backup policy --policy POLICY --operation restore_backup --actor maintainer@example --json
```

The runtime payload should include:

- `contract_version`
- `governance`
- `request`
- `policy`
- `validation`
- `provenance`
- `repository`
- `backup`
- `restore`
- `retention`
- `legal_hold`
- `recovery_testing`
- `migration`
- `operation_resolution`
- `audit`
- `enforcement`
- `blockers`
- `diagnostics`

## Acceptance Criteria

- Default config remains local-first, privacy-first, server-optional, and cloud-disabled.
- Missing policy returns a structured payload and does not claim central backup readiness.
- A valid local policy document validates against `governance_central_backup_policy`.
- A valid local policy can preview allow/block decisions for backup, restore, retention, recovery-test, and migration
  operations without executing side effects.
- `governance backup central-readiness --config CONFIG --json` reports centralized backup/restore policy accepted when
  the policy is valid.
- `governance v3 gap-audit --json` removes `centralized_backup_restore_policy_missing`, increments accepted phase
  count, and keeps v3 incomplete until automatic instrumentation and final acceptance smoke are done.
- Discovery surfaces advertise the new command, feature flag, robot guide entry, robot schema entry, and generated
  schema artifact.
- `deep-research-report.md` remains absent.
