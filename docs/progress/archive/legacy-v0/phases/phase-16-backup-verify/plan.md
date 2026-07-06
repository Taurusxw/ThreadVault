# Phase 16 / v0.16: Backup Verify

## Goal

Add a local `threadvault backup-verify` command that checks whether a backup database is readable and structurally healthy before any future restore workflow exists.

v0.15 added backup creation. v0.16 adds verification so users and agents can trust backup artifacts before maintenance or migration work.

## Scope

- Add `threadvault backup-verify --backup PATH --json`.
- Verify:
  - file exists
  - SQLite can open it read-only
  - `PRAGMA integrity_check` returns `ok`
  - ThreadVault schema version is readable
  - required tables/indexes/triggers are present through existing database doctor logic
  - basic stats can be read
- Return structured JSON and nonzero exit for invalid backups.
- Add `backup_verify` JSON schema and capabilities entry.
- Do not implement restore, compression, encryption, cloud sync, or scheduled automation.

## Existing Project Lessons

- SQLite provides `PRAGMA integrity_check`; use mature built-in validation instead of inventing a checker.
- CASS-style robot workflows need parseable diagnostics for both success and failure.
- Backup/restore workflows should be staged: verify first, restore later after overwrite rules are designed.
- ThreadVault remains local-first and privacy-first; verification reads only the user-specified local database.

## Tasks

- Add `verify_database_backup(path)` to `database.py`.
- Add `ArchiveStore.verify_backup(path)`.
- Add `threadvault backup-verify`.
- Add schema `backup_verify`.
- Add capabilities/json output entries.
- Add tests for:
  - valid backup
  - missing backup
  - non-SQLite file
  - schema validation
  - v0.16 docs exist
- Update README, development progress, external review, and research Markdown appendices.

## Acceptance Commands

```powershell
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault import --codex-home tests/fixtures/codex_home --db <tmp>/threadvault.db --json
threadvault backup --db <tmp>/threadvault.db --out <tmp>/backup.db --json
threadvault backup-verify --backup <tmp>/backup.db --json
threadvault backup-verify --backup <tmp>/bad.db --json
threadvault validate-json --schema backup_verify --input <payload.json> --json
```

## Assumptions

- Verification may read stats from the backup; stats do not expose raw transcript text.
- Restore remains out of scope until overwrite, provenance, and validation rules are designed separately.

