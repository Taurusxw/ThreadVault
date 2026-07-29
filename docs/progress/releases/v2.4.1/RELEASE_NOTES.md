# ThreadVault v2.4.1 Release Notes

## Summary

ThreadVault `2.4.1` closes the daily-archive loop. Smart backup now checks and catches up Codex sources before it writes a backup, Hook and MCP integration can be installed and diagnosed together, and the native desktop workbench shows the real source/integration state instead of assuming the archive is current.

## Highlights

### Foolproof source catch-up

- Added `threadvault storage sync` to compare active and archived Codex transcripts with import provenance.
- Targets only missing, changed, stale-parser, or newly touched sources.
- Keeps local source paths out of normal JSON unless explicitly requested.
- Refreshes observation time for unchanged files without duplicating sessions or events.

### Backup completeness guard

- `storage auto --apply` catches up sources before choosing Core, Evidence, or Forensic.
- A catch-up failure blocks backup creation rather than producing a verified but known-stale archive.
- Existing disk reserve, post-create verification, 3/2/1 automatic retention, and manual-backup protection remain intact.

### One-command Codex integration

- Added dry-run-first `threadvault codex status` and `threadvault codex install`.
- Installs and checks the exact user Stop hook and read-only `threadvault` MCP entry together.
- Pins the active virtual-environment executable and archive database.
- Preserves unrelated hooks and `notify`; MCP config is restored if Codex registration fails.
- Reports source freshness, observed Hook coverage, recommended actions, Hook review, and restart requirements.

### Native desktop workbench

- Added source backlog and Hook/MCP coverage to Backup Center and Codex Integration.
- Added a confirmed one-click integration installer.
- Preserved the v2.4.1 unified Tk styling, friendly session tables, stable in-place refresh, confirmed export, safe restore targets, and background operations.
- Fixed a real empty-window startup regression caused by treating Treeviews as Entry-style inputs.

### Release engineering

- Added Windows GitHub Actions for Python 3.11 and 3.12.
- Added ruff, 70% branch-coverage, isolated desktop smoke, and MCP manifest gates.
- Added regression coverage for source freshness, combined Codex setup, backup-before-catch-up ordering, Windows file handles, and live Tk initial refresh.

## Upgrade

```powershell
py -3.12 -m pip install -e ".[dev]"
threadvault codex install --db data\threadvault.db --json
threadvault codex install --db data\threadvault.db --apply --json
threadvault storage sync --db data\threadvault.db --apply --json
threadvault codex status --db data\threadvault.db --json
```

Review `/hooks` if Codex requests trust for the exact command, then restart Codex after a newly created or changed MCP registration.

## Compatibility And Privacy

- Python 3.11 or newer; native Tkinter desktop remains the primary local UI.
- Database schema remains v8; no destructive migration is required.
- MCP remains local, stdio, and read-only.
- Transcripts, databases, cold blobs, backups, exports, and screenshots remain private ignored artifacts.
- Team mode, a shared HTTP server, cloud sync, external models, and a frontend build pipeline remain outside the active 2.x product.

## Validation

See `docs/progress/releases/v2.4.1/ACCEPTANCE.md`.
