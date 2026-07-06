# v3 Phase 29 Plan: Central Policy Store Runtime

## Status

Planned on 2026-07-01.

## Goal

Add a minimal opt-in local central policy store runtime for v3 team governance. The runtime should accept a versioned
local JSON policy document, validate its shape against ThreadVault's existing role/access vocabulary, resolve an actor's
policy roles and allowed access levels, and expose the result through a stable JSON contract.

This phase should close the `central_policy_store_missing` v3 blocker without claiming production shared enforcement,
centralized audit, centralized backup/restore, or broad automatic governance instrumentation.

## Source Documents

This plan is based on:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/v3/phases/phase-23-centralized-policy-store-readiness/plan.md`
- `docs/v3/phases/phase-23-centralized-policy-store-readiness/design-notes.md`
- `docs/v3/phases/phase-23-centralized-policy-store-readiness/acceptance.md`
- `docs/v3/phases/phase-28-identity-actor-binding-runtime/acceptance.md`
- `docs/development-progress.md`

## In Scope

- Add local config support for an optional central policy document path:
  - `[governance.policy] central_store = "path/to/policy.json"`
- Add governance runtime command:
  - `threadvault governance policy central-store`
- Add JSON schema:
  - `governance_central_policy_store`
- Accept a local JSON policy document with:
  - policy contract/version fields
  - policy id
  - policy version
  - provenance fields
  - role definitions mapped to existing access levels
  - actor-to-role bindings
- Validate:
  - file existence and JSON syntax
  - policy document contract/version presence
  - known role names
  - known access levels
  - actor bindings to known roles
  - policy provenance fields
- Resolve:
  - actor roles
  - allowed access levels
  - whether a requested operation is allowed
- Update central policy readiness, server policy readiness, backup readiness, and v3 gap audit to distinguish accepted
  local central policy storage from remaining shared enforcement blockers.
- Update capabilities, robot guide, robot schemas, and generated schema artifacts.
- Add focused tests for default missing policy, valid local policy, invalid policy, config-driven loading, discovery, and
  v3 gap audit state.
- Update acceptance documentation and `docs/development-progress.md`.

## Out Of Scope

- Remote server-backed policy storage.
- Database-backed policy persistence.
- Authenticated identity provider integration.
- Centralized audit store or tamper evidence.
- Centralized backup/restore policy implementation.
- Automatic enforcement across all business commands.
- Replacing local-first CLI defaults.
- Changing accepted v2 retrieval, hybrid retrieval, vector adapter, summary pipeline, or agent-facing interfaces.

## Interface Shape

Expected CLI shape:

```powershell
threadvault governance policy central-store --policy POLICY --actor ACTOR --operation OPERATION --json
```

`--policy` is optional when `[governance.policy] central_store` is configured. `--actor` and `--operation` are optional;
when omitted, the command validates and summarizes the policy document only.

Expected `governance_central_policy_store` payload sections:

- `contract_version`
- `request`
- `governance`
- `store`
- `policy`
- `validation`
- `provenance`
- `actor_resolution`
- `operation_resolution`
- `enforcement`
- `blockers`
- `diagnostics`

## Policy Document Shape

Minimal JSON policy document:

```json
{
  "contract_version": "threadvault_central_policy.v1",
  "policy_id": "team-local",
  "version": "2026-07-01.1",
  "provenance": {
    "author": "owner@example",
    "reviewed_by": ["reviewer@example"],
    "approved_by": ["owner@example"],
    "source": "local-file"
  },
  "roles": [
    {"name": "reader", "access_levels": ["summary_search"]},
    {"name": "reviewer", "access_levels": ["summary_search", "export"]}
  ],
  "actors": [
    {"id": "reviewer@example", "roles": ["reviewer"]}
  ]
}
```

## Acceptance Criteria

- The command validates against `governance_central_policy_store`.
- Missing policy defaults are reported as local-first and safe for local CLI use, not as a hard requirement.
- A valid policy document reports `store.available = true`, `policy.valid = true`, version/provenance fields, actor role
  resolution, and operation allow/deny when an operation is provided.
- Invalid policy documents return machine-readable validation errors without requiring server/cloud behavior.
- `governance policy central-readiness` reports central policy storage, local adapter, versioning, and provenance as
  implemented when a valid local central policy is configured.
- `governance v3 gap-audit` no longer lists `central_policy_store_missing` after the runtime is accepted, but still
  reports remaining blockers for centralized audit, centralized backup/restore, broad instrumentation, and final v3
  acceptance smoke.
- Discovery surfaces advertise the new schema and command.
- `deep-research-report.md` remains absent.
