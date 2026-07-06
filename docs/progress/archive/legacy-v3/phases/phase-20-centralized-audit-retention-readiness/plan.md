# v3 Phase 20 Plan: Centralized Audit Retention Readiness

## Status

Planned on 2026-07-01.

## Goal

Add `threadvault governance audit centralized-readiness --json` as a readiness report for centralized audit retention
before any shared audit store, server runtime, or automatic audit instrumentation is implemented.

This phase makes the gap between local JSONL audit logs and shared/server audit retention explicit and machine-readable.
It helps future server/team work know what remains before audit evidence can be trusted across actors and deployments.

## Source Documents

This plan is based on:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/v3/phases/phase-08-local-audit-log-workflow/acceptance.md`
- `docs/v3/phases/phase-19-server-policy-readiness/acceptance.md`
- `docs/development-progress.md`

## In Scope

- Add a governance readiness command for centralized audit retention.
- Add CLI command:
  - `threadvault governance audit centralized-readiness`
- Add JSON schema:
  - `governance_centralized_audit_readiness`
- Report readiness categories for:
  - local JSONL audit availability
  - centralized audit store
  - actor identity binding
  - append-only integrity
  - retention policy
  - query/review workflow
  - backup/export of audit evidence
  - automatic audit instrumentation
- Reuse existing app config and governance readiness facts.
- Regenerate packaged schema artifacts.
- Update capabilities and robot docs discovery.
- Add focused tests for default not-ready state, config-enabled diagnostics, discovery/schema/docs, and invariants.
- Update acceptance documentation and `docs/development-progress.md`.

## Out Of Scope

- Implementing centralized audit storage.
- Implementing server runtime, identity providers, or actor binding.
- Migrating local JSONL audit records.
- Enforcing append-only storage across machines.
- Automatically writing audit records from existing business commands.
- Changing local-first CLI defaults.
- Changing retrieval, hybrid retrieval, vector indexing, summary pipeline, or agent-facing retrieval behavior.

## Interface Shape

`governance_centralized_audit_readiness` includes:

- `contract_version`
- `governance`
- `readiness`
- `local_audit`
- `centralized_audit`
- `identity`
- `integrity`
- `retention`
- `review`
- `backup_export`
- `instrumentation`
- `blockers`
- `recommended_next_phases`
- `diagnostics`

Expected CLI shape:

```powershell
threadvault governance audit centralized-readiness --json
```

## Acceptance Criteria

- The command validates against `governance_centralized_audit_readiness`.
- Default output reports `overall_status = not_ready_for_centralized_audit`.
- Default output reports local JSONL audit as available but centralized audit store as unavailable.
- Required blockers include central audit store, actor binding, append-only integrity, retention policy, review workflow,
  backup/export policy, and automatic audit instrumentation.
- The payload preserves `local_first = true`, `privacy_first = true`, `server_opt_in = true`, and `cloud_sync = false`.
- Discovery surfaces advertise `governance_centralized_audit_readiness`.
- Existing audit append/list commands remain local-only and unchanged.
- `deep-research-report.md` remains absent.
