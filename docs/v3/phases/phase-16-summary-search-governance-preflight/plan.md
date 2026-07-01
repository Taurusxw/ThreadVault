# v3 Phase 16 Plan: Summary/Search Governance Preflight

## Status

Planned on 2026-07-01.

## Goal

Add `threadvault governance preflight summary-search --json` as an explicit preflight interface for summary/search read
workflows before existing retrieval, agent, or client warning commands are instrumented for automatic permission checks
or audit writes.

This phase gives richer clients and future optional server mode a safe way to ask whether a non-raw read would satisfy
current governance expectations without executing search, returning snippets, returning warning details, or exposing
local metadata.

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
- `docs/v3/phases/phase-15-raw-read-governance-preflight/acceptance.md`
- `docs/development-progress.md`

## In Scope

- Add a governance preflight command for summary/search command families.
- Add CLI command:
  - `threadvault governance preflight summary-search`
- Add JSON schema:
  - `governance_summary_search_preflight`
- Reuse Phase 10 command inventory to recognize summary/search commands:
  - `threadvault client warnings`
  - `threadvault agent retrieve`
  - `threadvault retrieval query`
  - `threadvault retrieval hybrid`
- Reuse Phase 09 permission logic and Phase 11 enforcement dry-run logic.
- Report summary/search, local metadata, and audit expectations for future execution.
- Support optional explicit audit logging for the preflight event itself.
- Regenerate packaged schema artifacts.
- Update capabilities and robot docs discovery.
- Add focused tests for allowed, out-of-scope, unknown command, optional audit, discovery, and docs.
- Update acceptance documentation and `docs/development-progress.md`.

## Out Of Scope

- Running retrieval, hybrid retrieval, agent retrieval, or warning detail commands.
- Returning search results, snippets, evidence chunks, warning details, local paths, or raw metadata from the preflight.
- Automatically enforcing permissions inside existing retrieval, agent, or client commands.
- Automatically writing audit records from existing retrieval, agent, or client commands.
- Rewriting v2 retrieval, hybrid ranking, vector indexing, or agent-facing retrieval.
- Covering raw transcript reads, export/backup, restore/retention, export previews, external model calls, or server/cloud
  behavior.

## Interface Shape

`governance_summary_search_preflight` includes:

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
threadvault governance preflight summary-search --command "threadvault retrieval query" --role reader --json
```

Optional audit logging:

```powershell
threadvault governance preflight summary-search --command "threadvault agent retrieve" --role reviewer --audit-log audit.jsonl --json
```

## Acceptance Criteria

- The preflight command validates against `governance_summary_search_preflight`.
- Summary/search commands resolve to the Phase 10 inventory.
- Non summary/search commands return structured `out_of_scope` diagnostics.
- Unknown commands return structured `unknown_command` diagnostics.
- The payload distinguishes `would_allow` from future `would_block_if_enforced`.
- Summary/search and local metadata expectations are visible for future execution.
- Optional audit logging records only the preflight event.
- The payload always reports:
  - `business_command_executed = false`
  - `search_executed = false`
  - `retrieval_results_returned = false`
  - `warning_details_returned = false`
  - `local_metadata_returned = false`
- Discovery surfaces advertise `governance_summary_search_preflight`.
- Existing retrieval, agent, and client warning commands remain unmodified and unenforced.
- `deep-research-report.md` remains absent.
