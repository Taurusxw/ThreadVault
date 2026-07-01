# v3 Phase 23 Plan: Centralized Policy Store Readiness

## Status

Planned on 2026-07-01.

## Goal

Add `threadvault governance policy central-readiness --json` as a readiness report for centralized policy storage,
policy adapters, policy versioning, provenance, migration, rollback, and identity dependency before shared/team policy
enforcement is claimed.

Phase 21 and Phase 22 identify centralized policy storage as a blocker for optional shared/server enforcement. This phase
makes that blocker explicit and machine-readable without implementing a central store or changing local CLI defaults.

## Source Documents

This plan is based on:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/v3/phases/phase-19-server-policy-readiness/acceptance.md`
- `docs/v3/phases/phase-21-v3-completion-gap-audit/gap-audit.md`
- `docs/v3/phases/phase-22-identity-actor-binding-readiness/acceptance.md`
- `docs/development-progress.md`

## In Scope

- Add governance readiness command:
  - `threadvault governance policy central-readiness`
- Add JSON schema:
  - `governance_central_policy_readiness`
- Report readiness categories for:
  - central policy store
  - policy adapter interface
  - policy document/versioning
  - policy provenance and review
  - policy migration and rollback
  - identity/actor dependency
  - local fallback policy
- Regenerate packaged schema artifacts.
- Update capabilities and robot docs discovery.
- Add focused tests for default not-ready state, config-enabled diagnostics, blockers, discovery/schema/docs, and
  local-first invariants.
- Update acceptance documentation and `docs/development-progress.md`.

## Out Of Scope

- Implementing a centralized policy store.
- Implementing a policy adapter, server runtime, or policy loader.
- Implementing identity providers, actor binding, or team role directories.
- Replacing local static governance vocabulary.
- Automatically enforcing centralized policy for existing business commands.
- Changing retrieval, hybrid retrieval, vector indexing, summary pipeline, or agent-facing retrieval behavior.
- Requiring a server or cloud account for local CLI use.

## Interface Shape

`governance_central_policy_readiness` includes:

- `contract_version`
- `governance`
- `readiness`
- `local_policy`
- `central_policy`
- `adapter`
- `versioning`
- `provenance`
- `migration`
- `identity_dependency`
- `fallback`
- `blockers`
- `recommended_next_phases`
- `diagnostics`

Expected CLI shape:

```powershell
threadvault governance policy central-readiness --json
```

## Acceptance Criteria

- The command validates against `governance_central_policy_readiness`.
- Default output reports `overall_status = not_ready_for_central_policy_store`.
- Default output reports local governance role vocabulary as available but centralized policy store and adapter as missing.
- The payload preserves `local_first = true`, `privacy_first = true`, `server_opt_in = true`, and `cloud_sync = false`.
- Required blockers include central policy store, policy adapter, policy versioning, policy provenance, policy migration,
  rollback, identity/actor binding dependency, and automatic enforcement integration.
- Discovery surfaces advertise `governance_central_policy_readiness`.
- `deep-research-report.md` remains absent.
