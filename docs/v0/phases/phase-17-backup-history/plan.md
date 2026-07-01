# Phase 17 / v0.17: Backup History

## Goal

Add backup directory history commands so users and agents can list local ThreadVault backup files, find the latest backup, and verify the latest backup without manually copying filenames.

v0.15 added backup creation, and v0.16 added backup verification. v0.17 makes backup directories easier to work with.

## Scope

- Add `threadvault backup-history list --dir DIR --json`.
- Add `threadvault backup-history latest --dir DIR --json`.
- Add `threadvault backup-history verify-latest --dir DIR --json`.
- Discover ThreadVault backup files matching `threadvault-backup-*.db` plus explicit `.db` files that pass basic ThreadVault backup verification when useful.
- Do not delete, prune, restore, compress, encrypt, or upload backups.
- Keep outputs local and machine-readable.

## Existing Project Lessons

- Reuse the proven `audit-history list/latest/diff-latest` command shape.
- CASS-style agent workflows benefit from commands that avoid manual filename copying.
- Backup workflows should remain conservative: discover and verify first, restore later only after separate design.

## Tasks

- Add a `backup_history.py` module:
  - `list_backup_files(dir)`
  - `latest_backup_file(dir)`
  - `verify_latest_backup(dir)`
- Add CLI group `backup-history`.
- Add JSON schemas:
  - `backup_history_list`
  - `backup_history_latest`
  - `backup_history_verify_latest`
- Add capabilities/json output entries.
- Add tests for:
  - list/latest sorting
  - verify-latest success
  - empty directory error
  - malformed/non-SQLite backup warning handling
  - schema validation
  - v0.17 docs exist
- Update README, development progress, external review, and research Markdown appendices.

## Acceptance Commands

```powershell
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault backup --db <tmp>/threadvault.db --out <tmp>/backups --json
threadvault backup-history list --dir <tmp>/backups --json
threadvault backup-history latest --dir <tmp>/backups --json
threadvault backup-history verify-latest --dir <tmp>/backups --json
threadvault validate-json --schema backup_history_list --input <payload.json> --json
```

## Assumptions

- `threadvault-backup-*.db` is the canonical backup history filename pattern.
- Explicit one-off backup files can still be verified directly with `backup-verify`.
- Backup deletion/pruning belongs in a later phase after retention rules are designed.

