# v3 Phase 19 Plan: Server Policy Readiness

## Status

Planned on 2026-07-01.

## Goal

Add `threadvault governance server policy-readiness --json` as a server/team governance readiness report before any
automatic command instrumentation, server runtime, centralized policy store, or shared enforcement mode is implemented.

This phase makes the remaining team-governance blockers explicit and machine-readable: identity, actor binding, role
mapping, centralized policy storage, policy versioning, centralized audit, backup/restore policy, and opt-in server
mode.

## Source Documents

This plan is based on:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/v3/phases/phase-12-governance-policy-readiness/acceptance.md`
- `docs/v3/phases/phase-18-external-model-governance-preflight/acceptance.md`
- `docs/development-progress.md`

## In Scope

- Add a governance readiness command for optional server/team policy prerequisites.
- Add CLI command:
  - `threadvault governance server policy-readiness`
- Add JSON schema:
  - `governance_server_policy_readiness`
- Report readiness categories for:
  - server opt-in and local-first defaults
  - identity and actor binding
  - role mapping
  - centralized policy storage
  - policy versioning
  - automatic command preflight and audit instrumentation
  - centralized audit retention
  - centralized backup/restore and retention policy
  - outbound external model policy
- Reuse existing app config and governance status/readiness facts.
- Regenerate packaged schema artifacts.
- Update capabilities and robot docs discovery.
- Add focused tests for default not-ready state, config-enabled diagnostics, discovery/schema/docs, and invariants.
- Update acceptance documentation and `docs/development-progress.md`.

## Out Of Scope

- Starting or implementing a server process.
- Implementing authentication, SSO, tokens, policy databases, or centralized audit stores.
- Enforcing permissions inside existing business commands.
- Changing local-first CLI defaults.
- Changing retrieval, hybrid retrieval, vector indexing, summary pipeline, or agent-facing retrieval behavior.
- Implementing cloud sync or external model adapters.

## Interface Shape

`governance_server_policy_readiness` includes:

- `contract_version`
- `governance`
- `readiness`
- `server`
- `policy`
- `identity`
- `instrumentation`
- `audit`
- `backup_restore`
- `outbound_policy`
- `blockers`
- `recommended_next_phases`
- `diagnostics`

Expected CLI shape:

```powershell
threadvault governance server policy-readiness --json
```

## Acceptance Criteria

- The command validates against `governance_server_policy_readiness`.
- Default output reports `overall_status = not_ready_for_shared_enforcement`.
- Default output reports server/team capabilities as opt-in and disabled by default.
- Required blockers include identity, role mapping, centralized policy storage, policy versioning, automatic
  instrumentation, centralized audit retention, centralized backup/restore policy, and outbound external model policy.
- The payload preserves `local_first = true`, `privacy_first = true`, `server_opt_in = true`, and `cloud_sync = false`.
- Discovery surfaces advertise `governance_server_policy_readiness`.
- Existing commands remain unmodified and unenforced.
- `deep-research-report.md` remains absent.
