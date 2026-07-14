# ThreadVault v2.4.0 Release Notes

## Summary

ThreadVault `2.4.0` is the first public release of the personal-only 2.x line. It turns the local Codex archive into a complete daily workflow: targeted automatic ingestion, read-only MCP retrieval, compact hot/cold storage, verified smart backups, and a foolproof native desktop interface.

This release intentionally removes the former active team-governance/shared-server direction and keeps those records only as historical evidence. The supported product is one person's local archive, native desktop app, CLI, and read-only MCP server.

## Highlights

### Personal-only architecture

- Removed active team mode, central governance/identity/policy contracts, and the shared HTTP server prototype.
- Preserved privacy scanning, export preview, explicit confirmation, backup verification, conservative restore, and read-only MCP safety gates.
- Split MCP transport, validation, and read-only execution into focused modules.

### Automatic Codex archiving and MCP

- Added a dry-run-first, idempotent Codex `Stop` hook installer that preserves unrelated hooks.
- Imports only the transcript named by each hook event instead of rescanning the full Codex home.
- Added current `world_state`, `inter_agent_communication_metadata`, compacted-event, and collaborative-session compatibility.
- Kept the MCP stdio server read-only, with capabilities, statistics, diagnostics, retrieval, session detail, and export preview tools.

### Hot/cold storage and minimal backups

- Added schema v8 storage metadata and immutable SHA-256-addressed cold blobs.
- Kept canonical human conversation and the clean FTS index in the hot SQLite database.
- Externalized large reversible evidence, compacted history, patches, metadata payloads, and image assets.
- Removed exact duplicate assistant bodies while retaining canonical conversation content.
- Added copy-on-write rebuild, deep verification, reference-aware cold pruning, and Core/Evidence/Forensic backup profiles.

### Foolproof smart backups

- Added `threadvault storage auto` as the normal single backup entrypoint.
- Selects at most one due changed tier: bootstrap/weekly Evidence, daily Core, or monthly Forensic after sufficient history.
- Skips unchanged archives, verifies every created backup, and blocks before violating the disk reserve.
- Retains only the newest 3 Core, 2 Evidence, and 1 Forensic automatic generations without touching manual backups.

### Native desktop workflow

- Added friendly title/project/time session tables with warning badges while hiding internal thread identifiers.
- Added a first-class Backup Center with last run, automatic schedule, next run, disk estimate, selected tier, retention, and one-click smart backup.
- Completed the export flow: privacy-aware preview, immutable parameter binding, explicit confirmation, actual file write, and manifest.
- Defaulted restore to a collision-free new database target and kept overwrite refusal.
- Added automatic health diagnosis, secondary maintenance controls, scrollbars, path pickers, keyboard shortcuts, visible focus, and Chinese labels.

### Documentation

- Added separate switchable English and Simplified Chinese project manuals: `README.md` and `README.zh-CN.md`.
- Updated architecture, API, database, MCP integration, rules, knowledge graph, development, usage, changelog, progress, and document-index references.

## Upgrade Notes

Refresh the editable environment:

```powershell
py -3.12 -m pip install -e ".[dev]"
py -3.12 -m pip check
```

Verify the active interface and contracts:

```powershell
threadvault capabilities --json
threadvault desktop smoke --json
threadvault mcp manifest --json
threadvault doctor --json
```

For a first 2.x setup, run one backfill, install the targeted hook, and register MCP using absolute paths as shown in the README. Existing 1.x users should note:

- `threadvault.personal_ui`, browser launch commands, active team/governance commands, and the shared server are no longer supported runtime surfaces.
- The active archive schema is v8. Back up first; use `storage rebuild --target-db ...` when converting a large legacy hot database into the compact hot/cold layout.
- MCP remains read-only and ingestion remains a separate Codex hook workflow.
- Existing long-running Codex MCP processes should be restarted after upgrade so they load the 2.4.0 package.

## Privacy And Storage Notes

- Raw transcripts, `data/`, archive databases, cold blobs, automatic/manual backups, restore history, and generated exports remain private local artifacts and are excluded from Git.
- Evidence and Forensic backups may contain reversible tool output and local paths.
- `storage prune` remains dry-run-first and deletes only unreachable cold content when explicitly applied.
- Desktop and CLI exports must still be reviewed before sharing outside the machine.

## Compatibility

- Python: 3.11 or newer.
- Primary local UI: native Tkinter desktop.
- Primary agent integration: local read-only MCP stdio.
- Database: schema v8.
- No browser, shared HTTP server, cloud sync, external model, or frontend build pipeline is required.

## Validation

Release validation is recorded in `docs/progress/releases/v2.4.0/ACCEPTANCE.md`.
