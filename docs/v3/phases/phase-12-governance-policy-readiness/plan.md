# v3 Phase 12 Plan: Governance Policy Readiness

## Status

Planned on 2026-07-01.

## Goal

Add `threadvault governance policy readiness --json` to report whether ThreadVault is ready to enable team governance
policy enforcement, and which prerequisites remain incomplete.

This phase creates a machine-readable policy readiness manifest before any existing business command is changed to
enforce permissions or write automatic audit records.

## Source Documents

This plan is based on:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/v3/phases/phase-10-governance-enforcement-gap-audit/gap-audit.md`
- `docs/v3/phases/phase-11-governance-enforcement-dry-run/acceptance.md`
- `docs/development-progress.md`

## In Scope

- Add a policy readiness JSON manifest for future governance enforcement.
- Add CLI command:
  - `threadvault governance policy readiness`
- Add JSON schema:
  - `governance_policy_readiness`
- Summarize readiness across:
  - local-first and privacy-first defaults
  - audit log support
  - permission preflight support
  - enforcement gap inventory
  - enforcement dry-run support
  - server identity and policy store readiness
  - command instrumentation readiness
  - centralized audit readiness
  - backup/restore and retention readiness
- Regenerate packaged schema artifacts.
- Update capabilities and robot docs discovery.
- Add focused tests for readiness state, blocker list, defaults, discovery, and docs.
- Update acceptance documentation and `docs/development-progress.md`.

## Out Of Scope

- Enforcing permissions in export, retrieval, backup, restore, client, or retention commands.
- Automatically writing audit records from existing business commands.
- Implementing server runtime, identity provider integration, team membership, or centralized policy storage.
- Implementing cloud sync.
- Rewriting v2 retrieval, hybrid retrieval, vector, or agent-facing interfaces.

## Interface Shape

`governance_policy_readiness` includes:

- `contract_version`
- `governance`
- `readiness`
- `capabilities`
- `command_categories`
- `blockers`
- `recommended_next_phases`
- `diagnostics`

Expected CLI shape:

```powershell
threadvault governance policy readiness --json
```

## Acceptance Criteria

- The readiness command validates against `governance_policy_readiness`.
- The payload reports local-first defaults are preserved.
- Implemented prerequisites include audit log, permission preflight, enforcement gap audit, and enforcement dry-run.
- Incomplete prerequisites include at least server identity, centralized policy storage, command instrumentation, and
  centralized audit.
- The payload states team enforcement is not ready and current command enforcement remains disabled.
- Discovery surfaces advertise `governance_policy_readiness`.
- Existing business commands remain unmodified and unenforced.
- `deep-research-report.md` remains absent.
