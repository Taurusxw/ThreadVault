# v3 Phase 03 Plan: Client Overview Workflow

## Status

Planned and executed on 2026-07-01.

## Goal

Add the first local client workflow payload: `threadvault client overview --json`.

The overview gives richer clients a browse/search/export starting point for their first screen. It returns recent
sessions, optional search results, safe action hints, and privacy diagnostics while reusing existing ThreadVault modules.

## Source Documents

This plan is based on:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/v3/phases/phase-01-client-interface-readiness-audit/design-notes.md`
- `docs/v3/phases/phase-02-client-manifest-entrypoint/design-notes.md`
- `docs/development-progress.md`

## In Scope

- Extend `threadvault.client_interface` with a client overview builder.
- Add `ArchiveStore.client_overview(...)`.
- Add CLI command:
  - `threadvault client overview`
- Add JSON schema:
  - `client_overview`
- Regenerate packaged schema artifacts under `docs/schemas/`.
- Update capabilities and robot docs discovery.
- Add focused tests for browse, search, local-debug, discovery, schemas, and v3 docs.
- Update `docs/v3/README.md` and `docs/development-progress.md`.

## Out Of Scope

- GUI rendering.
- Desktop shell packaging.
- VS Code/Cursor extension packaging.
- Web or TUI implementation.
- Server runtime.
- Team permissions.
- Rewriting retrieval, hybrid retrieval, vector indexing, export, or privacy scanning.

## Interface Shape

`client_overview` includes:

- `contract_version`
- `request`
- `sessions`
- `search`
- `actions`
- `privacy`
- `diagnostics`

If `--query` is omitted, the payload is a browse overview over recent sessions. If `--query` is provided, search results
come from the existing agent-facing retrieval interface.

## Privacy Rules

- Raw local paths are omitted by default.
- `--local-debug` is required to include raw session paths or agent result metadata.
- No external model calls are made.
- No server is required.

## Acceptance Criteria

- `threadvault client overview --json` validates against `client_overview`.
- Browse mode returns fixture sessions with no raw paths by default.
- Search mode returns agent retrieval results with evidence IDs and no metadata by default.
- `--local-debug` explicitly includes local debug metadata.
- Capabilities, robot docs, schema registry, and packaged schema files include `client_overview`.
- `deep-research-report.md` remains absent.

