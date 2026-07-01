# Phase 27 - Local TUI Client Runtime

## Status

Planned on 2026-07-01.

## Context

v3 Phase 26 accepted the first automatic governance instrumentation slice for `threadvault client export-preview`.
The current v3 completion gap audit still reports `richer_client_runtime_not_accepted`: the client-facing JSON workflows
exist, but no concrete desktop, IDE, Web, or TUI runtime has been accepted.

This phase accepts the smallest useful richer client runtime: a local TUI command that browses, searches, and previews
exports through the existing client-facing interfaces. It keeps the runtime local-first and serverless by default.

## Required Reading

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/development-progress.md`

## Goals

- Add a concrete local richer client runtime command:
  - `threadvault client tui`
- Reuse existing client-facing interfaces:
  - `ArchiveStore.client_overview`
  - `ArchiveStore.client_export_preview`
  - v2 agent retrieval through `client_overview --query`
- Emit a stable JSON contract for automation:
  - `client_tui_runtime`
- Render a readable local TUI view when `--json` is not requested.
- Preserve local-first and privacy-first defaults:
  - no server required
  - no cloud sync
  - no external model calls
  - no raw local paths in default output
- Update v3 completion gap audit so the richer-client runtime blocker is removed.

## Non-Goals

- Building an Electron desktop shell, browser UI, or VS Code/Cursor extension.
- Adding a mandatory server or cloud dependency.
- Rewriting retrieval, hybrid ranking, vector indexing, or agent-facing retrieval.
- Writing export files from the TUI runtime. Export remains a preview unless the user runs the returned execute command.
- Adding broad governance instrumentation beyond the accepted `client export-preview` slice.

## Interface Shape

`threadvault client tui` accepts:

- `--query QUERY` for search inside the runtime overview.
- `--cwd CWD` to scope browsing/searching to a project.
- `--limit N` for session/search result count.
- `--export-preview-session SESSION_ID` for read-only export preview.
- `--out OUT` and `--profile PROFILE` for export preview planning.
- `--local-debug` for explicit raw local metadata opt-in.
- `--json` for the machine-readable payload.

The payload includes:

- `contract_version`
- `runtime`
- `request`
- `screen`
- `overview`
- optional `export_preview`
- `actions`
- `privacy`
- `diagnostics`

## Design Rules

- Place runtime orchestration in a dedicated module, not directly in the CLI command body.
- Keep the module interface small and test it through `ArchiveStore.client_tui_runtime`.
- Treat Rich rendering as presentation only; the JSON payload is the contract.
- Use existing client and agent interfaces rather than parsing Codex JSONL files.

## Acceptance Criteria

- `threadvault client tui --json` returns `client_tui_runtime.v1` and validates against the schema.
- Query mode reuses the v2 agent-facing retrieval path through client overview and reports hybrid diagnostics.
- Export preview mode includes a `client_export_preview` payload and does not write files.
- Default output is human-readable and includes sessions/search/export preview sections when relevant.
- Discovery advertises the runtime in capabilities, robot guide, robot schemas, schema artifacts, and client manifest.
- `threadvault governance v3 gap-audit --json` reports:
  - `accepted_phase_count = 27`
  - `current_phase = phase-27-local-tui-client-runtime`
  - no `richer_client_runtime_not_accepted` blocker
  - `richer_client_runtime` marked accepted
  - `v3_complete = false`
- `deep-research-report.md` remains absent.

## Validation Plan

- Focused tests:
  - `py -3.12 -m pytest tests\test_v327_local_tui_client_runtime.py -q`
- Adjacent tests:
  - client overview/export preview
  - v3 completion gap audit
  - capabilities/schema contract
- Schema generation:
  - `threadvault schemas write --out docs\schemas --json`
- Final verification:
  - `py -3.12 -m ruff check .`
  - `py -3.12 -m pytest`
  - manual JSON and non-JSON TUI smokes
  - `Test-Path deep-research-report.md`
