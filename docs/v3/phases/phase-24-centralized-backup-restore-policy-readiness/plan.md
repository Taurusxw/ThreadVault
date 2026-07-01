# v3 Phase 24 Plan: Centralized Backup/Restore Policy Readiness

## Status

Planned on 2026-07-01.

## Goal

Add `threadvault governance backup central-readiness --json` as a readiness report for centralized backup, restore, and
retention policy before shared/team deployment or final v3 acceptance is claimed.

ThreadVault already has local backup, restore, backup manifest, restore plan, restore history, and local retention
capabilities. This phase records the remaining gap between those local workflows and shared/team backup policy.

## Source Documents

This plan is based on:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/v3/phases/phase-13-export-backup-governance-preflight/acceptance.md`
- `docs/v3/phases/phase-14-restore-retention-governance-preflight/acceptance.md`
- `docs/v3/phases/phase-20-centralized-audit-retention-readiness/acceptance.md`
- `docs/v3/phases/phase-21-v3-completion-gap-audit/gap-audit.md`
- `docs/v3/phases/phase-23-centralized-policy-store-readiness/acceptance.md`
- `docs/development-progress.md`

## In Scope

- Add governance readiness command:
  - `threadvault governance backup central-readiness`
- Add JSON schema:
  - `governance_central_backup_readiness`
- Report readiness categories for:
  - local backup/restore baseline
  - centralized backup repository
  - backup policy and retention policy
  - restore approval and review workflow
  - audit provenance
  - identity and central policy dependencies
  - recovery testing and migration
- Regenerate packaged schema artifacts.
- Update capabilities and robot docs discovery.
- Add focused tests for default not-ready state, config-enabled diagnostics, blockers, discovery/schema/docs, and
  local-first invariants.
- Update acceptance documentation and `docs/development-progress.md`.

## Out Of Scope

- Implementing a centralized backup repository.
- Implementing replication, remote object storage, cloud sync, or shared restore execution.
- Implementing retention approval, legal hold, restore approval, or disaster recovery workflows.
- Implementing identity providers, actor binding, centralized policy, or centralized audit storage.
- Changing existing local backup/restore commands or retention behavior.
- Changing retrieval, hybrid retrieval, vector indexing, summary pipeline, or agent-facing retrieval behavior.
- Requiring a server or cloud account for local CLI use.

## Interface Shape

`governance_central_backup_readiness` includes:

- `contract_version`
- `governance`
- `readiness`
- `local_backup`
- `central_backup`
- `policy`
- `restore`
- `retention`
- `audit`
- `dependencies`
- `recovery_testing`
- `blockers`
- `recommended_next_phases`
- `diagnostics`

Expected CLI shape:

```powershell
threadvault governance backup central-readiness --json
```

## Acceptance Criteria

- The command validates against `governance_central_backup_readiness`.
- Default output reports `overall_status = not_ready_for_centralized_backup_restore_policy`.
- Default output reports local backup/restore as available but centralized backup repository and shared policy as missing.
- The payload preserves `local_first = true`, `privacy_first = true`, `server_opt_in = true`, and `cloud_sync = false`.
- Required blockers include central backup repository, backup policy, retention policy, restore approval workflow, audit
  provenance, identity dependency, central policy dependency, recovery testing, and migration plan.
- Discovery surfaces advertise `governance_central_backup_readiness`.
- `deep-research-report.md` remains absent.
