# v3 Phase 30 Plan: Centralized Audit Store Runtime

## Status

Planned on 2026-07-01.

## Goal

Add a minimal opt-in local centralized audit store runtime for v3 team governance. The runtime should write, list, and
verify identity-bound audit records in a single append-only JSONL store with hash-chain tamper evidence.

This phase should close the `centralized_audit_store_missing` v3 blocker without claiming remote/server audit storage,
centralized backup/restore policy, broad automatic audit instrumentation, or final v3 acceptance.

## Source Documents

This plan is based on:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/v3/phases/phase-20-centralized-audit-retention-readiness/plan.md`
- `docs/v3/phases/phase-20-centralized-audit-retention-readiness/design-notes.md`
- `docs/v3/phases/phase-20-centralized-audit-retention-readiness/acceptance.md`
- `docs/v3/phases/phase-28-identity-actor-binding-runtime/acceptance.md`
- `docs/v3/phases/phase-29-central-policy-store-runtime/acceptance.md`
- `docs/development-progress.md`

## In Scope

- Add local config support for an optional centralized audit store path:
  - `[governance.audit] central_store = "path/to/audit.jsonl"`
- Add governance runtime command:
  - `threadvault governance audit centralized-store`
- Add JSON schema:
  - `governance_centralized_audit_store`
- Support actions:
  - `append`
  - `list`
  - `verify`
- Append centralized audit records with:
  - record id
  - timestamp
  - operation
  - actor
  - status
  - target
  - metadata
  - actor provenance fields
  - previous record hash
  - current record hash
- Verify:
  - JSONL parseability
  - required fields
  - previous-hash continuity
  - record hash correctness
- Query/list:
  - newest records by limit
  - optional actor filter
  - optional operation filter
- Update centralized audit readiness, server policy readiness, central backup readiness, and v3 gap audit to distinguish
  accepted local centralized audit storage from remaining retention, backup, and instrumentation blockers.
- Update capabilities, robot guide, robot schemas, and generated schema artifacts.
- Add focused tests for missing/default store, append/list/verify, tamper detection, config-driven store, discovery, and
  v3 gap audit state.
- Update acceptance documentation and `docs/development-progress.md`.

## Out Of Scope

- Remote or server-backed centralized audit storage.
- Database-backed shared audit persistence.
- Cryptographic signatures or external key management.
- Retention/legal-hold/prune approval enforcement.
- Centralized audit backup/export policy.
- Automatic audit instrumentation across every business command.
- Replacing local JSONL audit append/list commands.
- Changing local-first CLI defaults.
- Changing accepted v2 retrieval, hybrid retrieval, vector adapter, summary pipeline, or agent-facing interfaces.

## Interface Shape

Expected CLI shape:

```powershell
threadvault governance audit centralized-store --action append --store STORE --operation OP --actor ACTOR --status STATUS --target-type TYPE --target-id ID --json
threadvault governance audit centralized-store --action list --store STORE --json
threadvault governance audit centralized-store --action verify --store STORE --json
```

`--store` is optional when `[governance.audit] central_store` is configured. `--actor` and `--operation` are optional
filters for `list`.

Expected `governance_centralized_audit_store` payload sections:

- `contract_version`
- `request`
- `governance`
- `store`
- `append`
- `query`
- `verification`
- `records`
- `warnings`
- `blockers`
- `diagnostics`

## Acceptance Criteria

- The command validates against `governance_centralized_audit_store`.
- Missing store defaults are reported as local-first and safe for local CLI use.
- Append writes hash-chained centralized audit records and returns the appended record.
- List returns valid records and supports actor/operation filters.
- Verify detects tampering or broken hash-chain continuity.
- `governance audit centralized-readiness` reports centralized audit store, query workflow, and tamper evidence as
  implemented after the runtime is accepted, while retention, backup/export policy, and broad instrumentation remain
  not ready.
- `governance v3 gap-audit` no longer lists `centralized_audit_store_missing`, but still reports remaining blockers for
  centralized backup/restore, broad instrumentation, and final v3 acceptance smoke.
- Discovery surfaces advertise the new schema and command.
- `deep-research-report.md` remains absent.
