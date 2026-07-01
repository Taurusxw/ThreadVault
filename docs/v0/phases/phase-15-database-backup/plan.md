# Phase 15 / v0.15: Database Backup

## Goal

Add a safe local SQLite backup command for ThreadVault archives. Users should be able to create a consistent database backup before import, reindex, vacuum, retention cleanup, or other maintenance work.

## Scope

- Add `threadvault backup`.
- Use SQLite's built-in `Connection.backup()` API instead of raw file copy.
- Support:
  - `threadvault backup --out backups --json`
  - `threadvault backup --out backups/threadvault-backup.db --json`
  - `threadvault backup --out backups/threadvault-backup.db --force --json`
- Default to refusing overwrite when the destination file exists.
- Include backup metadata in JSON output:
  - source db
  - destination path
  - bytes
  - schema version
  - source stats
  - overwritten flag
- Add `backup` JSON schema and capabilities entry.
- Do not add restore, compression, encryption, cloud sync, or scheduled automation in v0.15.

## Existing Project Lessons

- SQLite provides a mature online backup API; use it instead of hand-copying database files that may have WAL state.
- CASS-style agent commands should return structured JSON and be safe in automation.
- ccusage-style local history tooling benefits from backup-before-maintenance workflows.
- ThreadVault remains local-first and privacy-first: backups are local files only.

## Tasks

- Add a database helper using SQLite `backup()`.
- Add `ArchiveStore.backup(out, force=False)`.
- Add `threadvault backup --out PATH --force --json`.
- Add schema `backup`.
- Add capability/json output entries.
- Add tests for:
  - backup to directory creates timestamped `.db`
  - backup to explicit file
  - no overwrite without `--force`
  - force overwrite
  - backup can be opened and queried
  - schema validation
  - v0.15 docs exist
- Update README, development progress, external review, and research Markdown appendices.

## Acceptance Commands

```powershell
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault import --codex-home tests/fixtures/codex_home --db <tmp>/threadvault.db --json
threadvault backup --db <tmp>/threadvault.db --out <tmp>/backups --json
threadvault backup --db <tmp>/threadvault.db --out <tmp>/backup.db --json
threadvault backup --db <tmp>/threadvault.db --out <tmp>/backup.db --force --json
threadvault validate-json --schema backup --input <payload.json> --json
```

## Assumptions

- Restore workflows need separate design and are out of scope for v0.15.
- Backup files may contain local private session data; ThreadVault only writes them where the user requests.
- Existing destination files are user-owned and must not be overwritten unless `--force` is explicit.

