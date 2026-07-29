# 2026-07-29 Round 001: Foolproof archive integration

## Status

Implementation, live catch-up/backup, automated validation, rendered Windows review, and release preparation completed.

## Goal

Make daily Codex archiving self-maintaining: detect missed conversations automatically, catch the database up before backup, install Hook and MCP integration in one safe action, and expose the real state clearly in the native desktop app.

## Frozen Completion Contract

1. Confirm current Codex Hook and MCP behavior against official documentation.
2. Detect source/database freshness without exposing local paths by default.
3. Import only stale transcripts and block smart backup if catch-up fails.
4. Provide one dry-run-first command and one confirmed desktop action for Hook plus MCP setup.
5. Add CI coverage for Windows, supported Python versions, desktop smoke, and MCP discovery.
6. Update bilingual usage, architecture, contracts, schemas, progress, and release records.
7. Prove the result with full tests, a live archive catch-up, a verified backup, rendered desktop QA, and public-release hygiene checks.

## Implementation

- Added `source_sync.py` with a read-only freshness contract and targeted apply path for missing, changed, stale-parser, and newly touched transcripts.
- Added targeted file imports in `importer.py`; same-hash skips now refresh import observation time without duplicating archive content.
- Upgraded smart backup to `smart-backup.v2`: source catch-up runs before tier selection, and any import failure blocks backup creation.
- Added `threadvault storage sync --json/--apply` and JSON Schema coverage.
- Added `codex_integration.py` plus `threadvault codex status/install`; the installer pins the active ThreadVault executable and database, preserves unrelated hooks, uses the Codex CLI for MCP registration, and rolls back config on failure.
- Added desktop source-freshness status and a confirmed “一键安装联动” action.
- Fixed a rendered-startup regression caused by applying Entry-style state configuration to Treeview widgets.
- Explicitly closed read-only SQLite connections in backup lifecycle paths so Windows retention can remove superseded files.
- Added a Windows CI matrix for Python 3.11/3.12, ruff, 70% branch coverage, isolated desktop smoke, and MCP manifest validation.

## Architecture Decision

`store.py`, `cli.py`, and the desktop controller are existing hotspots. New freshness and Codex-configuration responsibilities were therefore placed in deep modules (`source_sync.py` and `codex_integration.py`); store/CLI/desktop layers remain shallow delegates and presentation adapters. This round freezes those hotspot responsibilities rather than adding another embedded subsystem.

## Live Acceptance

- Installed the exact user-level ThreadVault Stop hook and registered the `threadvault` read-only MCP server in Codex's shared configuration.
- The first targeted catch-up imported 62 stale files and 108,951 events; a second pass caught two files that changed during the run and imported 9,531 more events. Smart backup then caught one more active transcript with 5,313 events. A final four-file validation pass imported another 10,455 events without failed files and left the live archive at 404 sessions / 939,614 events with equal FTS counts.
- The verified Evidence backup contained a 1.390 GB database, passed SQLite integrity and SHA verification, and had zero missing or invalid cold references across 98,699 blobs (3.679 GB stored).
- Automatic retention completed with two Evidence generations and one Core generation retained; manual backups remained outside deletion scope.
- Rendered Windows QA showed real session titles/projects, source backlog, daily 03:15 schedule, disk state, one-click backup, exact Hook/MCP state, and the integration action. The initial empty-window regression was reproduced, fixed, and covered by a live Tk test.

## Verification

Final automated results and exact counts are recorded in `docs/progress/releases/v2.4.1/ACCEPTANCE.md`.

## Documentation

Updated English and Chinese README files, the detailed Chinese manual, architecture, API/contracts, database behavior, MCP integration, knowledge graph, development workflow, changelog, progress, TODO, document indexes, generated schemas, this round, and v2.4.1 release records.

## Residual Risks

- Codex owns non-managed Hook trust review. ThreadVault can verify the exact configured command and observe completed queue records, but cannot programmatically declare the Hook trusted.
- A new or changed MCP registration is loaded only after Codex restarts.
- The currently active Codex transcript can appear pending between messages; the Stop hook or next catch-up closes that gap.
- A full NVDA narration pass and official MCP Inspector run remain non-blocking follow-ups.

## Status

completed
