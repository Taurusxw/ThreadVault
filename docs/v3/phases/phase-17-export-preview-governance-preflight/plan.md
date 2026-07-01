# v3 Phase 17 Plan: Export Preview Governance Preflight

## Status

Planned on 2026-07-01.

## Goal

Add `threadvault governance preflight export-preview --json` as an explicit preflight interface for client export-preview
workflows before `threadvault client export-preview` is instrumented for automatic permission checks or audit writes.

This phase gives richer clients and future optional server mode a safe way to ask whether an export preview would
satisfy current governance expectations without running the preview, scanning content, writing export artifacts, or
returning a manifest.

## Source Documents

This plan is based on:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/v3/phases/phase-10-governance-enforcement-gap-audit/gap-audit.md`
- `docs/v3/phases/phase-13-export-backup-governance-preflight/acceptance.md`
- `docs/v3/phases/phase-16-summary-search-governance-preflight/acceptance.md`
- `docs/development-progress.md`

## In Scope

- Add a governance preflight command for client export preview.
- Add CLI command:
  - `threadvault governance preflight export-preview`
- Add JSON schema:
  - `governance_export_preview_preflight`
- Reuse Phase 10 command inventory to recognize:
  - `threadvault client export-preview`
- Reuse Phase 09 permission logic and Phase 11 enforcement dry-run logic.
- Report export-preview, privacy-scan, local metadata, and audit expectations for future execution.
- Support optional explicit audit logging for the preflight event itself.
- Regenerate packaged schema artifacts.
- Update capabilities and robot docs discovery.
- Add focused tests for allowed, blocked, out-of-scope command, optional audit, discovery, and docs.
- Update acceptance documentation and `docs/development-progress.md`.

## Out Of Scope

- Running `threadvault client export-preview`.
- Returning export preview payloads, manifests, selected sessions, privacy findings, local paths, or raw metadata.
- Writing export artifacts.
- Automatically enforcing permissions inside existing client or export commands.
- Automatically writing audit records from existing client or export commands.
- Rewriting export-target modules or v2 retrieval, hybrid retrieval, vector, or agent-facing interfaces.
- Implementing server runtime, centralized policy storage, identity providers, centralized audit, or cloud sync.

## Interface Shape

`governance_export_preview_preflight` includes:

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
threadvault governance preflight export-preview --command "threadvault client export-preview" --role reviewer --json
```

Optional audit logging:

```powershell
threadvault governance preflight export-preview --command "threadvault client export-preview" --role reader --audit-log audit.jsonl --json
```

## Acceptance Criteria

- The preflight command validates against `governance_export_preview_preflight`.
- `threadvault client export-preview` resolves to the Phase 10 inventory.
- Non export-preview commands return structured `out_of_scope` diagnostics.
- The payload distinguishes `would_allow` from future `would_block_if_enforced`.
- Export-preview and privacy expectations are visible for future execution.
- Optional audit logging records only the preflight event.
- The payload always reports:
  - `business_command_executed = false`
  - `preview_generated = false`
  - `manifest_returned = false`
  - `files_written = false`
  - `local_metadata_returned = false`
- Discovery surfaces advertise `governance_export_preview_preflight`.
- Existing client and export commands remain unmodified and unenforced.
- `deep-research-report.md` remains absent.
