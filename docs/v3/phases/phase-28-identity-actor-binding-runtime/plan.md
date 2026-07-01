# Phase 28 - Identity Actor Binding Runtime

## Status

Planned on 2026-07-01.

## Context

Phase 27 accepted the first local richer client runtime. The current v3 completion gap audit still reports
`identity_actor_binding_missing` as a blocking governance gap. Phase 22 documented identity and actor binding readiness,
but intentionally did not implement an identity provider, actor binding, role mapping, request attribution, or
authenticated actor provenance.

This phase implements the smallest useful actor binding runtime: an opt-in local static identity map in
`threadvault.toml`, a command that resolves an actor to governance roles, and optional local audit evidence for the
binding decision. This is enough to remove the "missing" identity blocker while keeping shared enforcement and centralized
audit claims out of scope.

## Required Reading

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/development-progress.md`
- `docs/v3/phases/phase-22-identity-actor-binding-readiness/plan.md`
- `docs/v3/phases/phase-22-identity-actor-binding-readiness/design-notes.md`
- `docs/v3/phases/phase-22-identity-actor-binding-readiness/acceptance.md`

## Goals

- Add a local actor binding runtime command:
  - `threadvault governance identity bind`
- Extend local config with an optional static actor map:
  - `[governance.identity]`
  - `actors = [{ id = "...", roles = ["reviewer"], display = "...", source = "local-static" }]`
- Return a stable JSON contract:
  - `governance_identity_actor_binding`
- Support request attribution fields:
  - command, operation, target type, target id, client id
- Optionally write a local audit record with actor binding metadata.
- Update identity readiness, server policy readiness, central policy readiness, central audit readiness, central backup
  readiness, and v3 completion gap audit to recognize the accepted local actor binding runtime.

## Non-Goals

- Adding external SSO, OAuth, LDAP, or a cloud identity provider.
- Enforcing team policy for every business command.
- Claiming shared deployment readiness.
- Implementing centralized policy storage or centralized audit storage.
- Changing v2 retrieval, hybrid retrieval, vector adapter, or agent-facing interfaces.

## Interface Shape

Command:

```powershell
threadvault governance identity bind --actor ACTOR --config threadvault.toml --json
```

Optional fields:

- `--command COMMAND`
- `--operation OPERATION`
- `--target-type TYPE`
- `--target-id ID`
- `--client-id CLIENT`
- `--audit-log LOG`

The payload includes:

- `contract_version`
- `request`
- `governance`
- `identity_provider`
- `actor`
- `binding`
- `role_mapping`
- `request_attribution`
- `audit`
- `diagnostics`

## Acceptance Criteria

- Missing config preserves local-first defaults and returns an unbound local-static identity result without requiring a
  server.
- Configured actors resolve to roles from the existing governance role vocabulary.
- Unknown configured actors return `bound = false` and do not grant roles.
- Invalid configured roles are reported without crashing unrelated local CLI behavior.
- Optional audit writes a local JSONL record with actor, roles, source, command/operation, and target metadata.
- Discovery advertises the command, schema, and feature flag.
- `threadvault governance v3 gap-audit --json` reports:
  - `accepted_phase_count = 28`
  - `current_phase = phase-28-identity-actor-binding-runtime`
  - no `identity_actor_binding_missing` blocker
  - `team_identity_and_policy.status = identity_binding_accepted_policy_pending`
  - `v3_complete = false`
- `deep-research-report.md` remains absent.

## Validation Plan

- Schema generation:
  - `threadvault schemas write --out docs\schemas --json`
- Focused tests:
  - `py -3.12 -m pytest tests\test_v328_identity_actor_binding_runtime.py -q`
- Adjacent validation:
  - identity readiness
  - v3 completion gap audit
  - server policy readiness
  - centralized policy/audit/backup readiness
  - capabilities/schema contract
- Final verification:
  - `py -3.12 -m ruff check .`
  - `py -3.12 -m pytest`
  - manual smoke commands
  - `Test-Path deep-research-report.md`
