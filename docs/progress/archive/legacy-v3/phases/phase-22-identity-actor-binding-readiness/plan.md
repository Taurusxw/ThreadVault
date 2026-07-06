# v3 Phase 22 Plan: Identity Actor Binding Readiness

## Status

Planned on 2026-07-01.

## Goal

Add `threadvault governance identity actor-readiness --json` as a readiness report for identity providers, actor
binding, role mapping, request attribution, and audit actor provenance before any shared/server enforcement is claimed.

Phase 21 identified identity and actor binding as a blocker for optional shared/server deployment, centralized policy,
centralized audit, automatic instrumentation, and final v3 acceptance. This phase makes that blocker explicit and
machine-readable.

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
- `docs/v3/phases/phase-21-v3-completion-gap-audit/acceptance.md`
- `docs/development-progress.md`

## In Scope

- Add governance readiness command:
  - `threadvault governance identity actor-readiness`
- Add JSON schema:
  - `governance_identity_actor_readiness`
- Report readiness categories for:
  - identity provider
  - actor binding
  - role mapping
  - request attribution
  - audit actor provenance
  - session/client context
  - fallback/local actor behavior
- Regenerate packaged schema artifacts.
- Update capabilities and robot docs discovery.
- Add focused tests for default not-ready state, config-enabled diagnostics, blockers, discovery/schema/docs, and
  local-first invariants.
- Update acceptance documentation and `docs/development-progress.md`.

## Out Of Scope

- Implementing an identity provider.
- Implementing authentication, authorization middleware, server request context, or token validation.
- Implementing team role directories or role sync.
- Automatically binding actors to existing business commands.
- Changing local audit append/list behavior.
- Changing retrieval, hybrid retrieval, vector indexing, summary pipeline, or agent-facing retrieval behavior.
- Requiring a server or cloud account for local CLI use.

## Interface Shape

`governance_identity_actor_readiness` includes:

- `contract_version`
- `governance`
- `readiness`
- `identity_provider`
- `actor_binding`
- `role_mapping`
- `request_attribution`
- `audit_provenance`
- `local_fallback`
- `blockers`
- `recommended_next_phases`
- `diagnostics`

Expected CLI shape:

```powershell
threadvault governance identity actor-readiness --json
```

## Acceptance Criteria

- The command validates against `governance_identity_actor_readiness`.
- Default output reports `overall_status = not_ready_for_identity_binding`.
- Default output reports identity provider, actor binding, role mapping, request attribution, and audit actor provenance
  as not implemented.
- The payload preserves `local_first = true`, `privacy_first = true`, `server_opt_in = true`, and `cloud_sync = false`.
- The payload reports local/manual actor labels as available but insufficient for shared enforcement.
- Discovery surfaces advertise `governance_identity_actor_readiness`.
- `deep-research-report.md` remains absent.
