# v3 Phase 15 Plan: Raw Read Governance Preflight

## Status

Planned on 2026-07-01.

## Goal

Add `threadvault governance preflight raw-read --json` as an explicit preflight interface for raw transcript or
client session-detail reads before any existing client read command is instrumented for automatic permission checks or
audit writes.

This phase gives richer clients and future optional server mode a safe way to ask whether a raw transcript read would
satisfy current governance expectations without returning transcript content, local metadata, or session previews.

## Source Documents

This plan is based on:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/v3/phases/phase-10-governance-enforcement-gap-audit/gap-audit.md`
- `docs/v3/phases/phase-12-governance-policy-readiness/acceptance.md`
- `docs/v3/phases/phase-13-export-backup-governance-preflight/acceptance.md`
- `docs/v3/phases/phase-14-restore-retention-governance-preflight/acceptance.md`
- `docs/development-progress.md`

## In Scope

- Add a governance preflight command for raw transcript read command families.
- Add CLI command:
  - `threadvault governance preflight raw-read`
- Add JSON schema:
  - `governance_raw_read_preflight`
- Reuse Phase 10 command inventory to recognize raw-read commands:
  - `threadvault client session`
- Reuse Phase 09 permission logic and Phase 11 enforcement dry-run logic.
- Report raw transcript, local metadata, and audit expectations for future execution.
- Support optional explicit audit logging for the preflight event itself.
- Regenerate packaged schema artifacts.
- Update capabilities and robot docs discovery.
- Add focused tests for allowed, blocked, config-enabled, out-of-scope command, optional audit, discovery, and docs.
- Update acceptance documentation and `docs/development-progress.md`.

## Out Of Scope

- Running `threadvault client session`.
- Returning raw transcript content, event previews, local paths, or session metadata from the preflight.
- Automatically enforcing permissions inside existing client commands.
- Automatically writing audit records from existing client commands.
- Expanding to summary/search command families such as `threadvault retrieval query`, `threadvault retrieval hybrid`,
  `threadvault agent retrieve`, or `threadvault client warnings`.
- Implementing server runtime, centralized policy storage, identity providers, centralized audit, or cloud sync.
- Rewriting v2 retrieval, hybrid retrieval, vector, or agent-facing interfaces.

## Interface Shape

`governance_raw_read_preflight` includes:

- `contract_version`
- `request`
- `scope`
- `command_policy`
- `permission`
- `enforcement`
- `privacy`
- `audit`
- `execution`
- `diagnostics`

Expected CLI shape:

```powershell
threadvault governance preflight raw-read --command "threadvault client session" --role owner --json
```

Optional audit logging:

```powershell
threadvault governance preflight raw-read --command "threadvault client session" --role reader --audit-log audit.jsonl --json
```

## Acceptance Criteria

- The preflight command validates against `governance_raw_read_preflight`.
- Raw-read commands resolve to the Phase 10 inventory.
- Non raw-read commands return structured `out_of_scope` diagnostics.
- The payload distinguishes `would_allow` from future `would_block_if_enforced`.
- Raw transcript and local metadata expectations are visible for future execution.
- Optional audit logging records only the preflight event.
- The payload always reports:
  - `business_command_executed = false`
  - `raw_transcript_returned = false`
  - `event_preview_returned = false`
  - `local_metadata_returned = false`
- Discovery surfaces advertise `governance_raw_read_preflight`.
- Existing client commands remain unmodified and unenforced.
- `deep-research-report.md` remains absent.
