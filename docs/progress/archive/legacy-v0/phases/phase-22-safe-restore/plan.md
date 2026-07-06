# Phase 22 / v0.22: Safe Restore

## Goal

Implement the first real restore command while preserving ThreadVault's local-first and safety-first posture.

v0.21 added read-only `restore-plan`. v0.22 adds `restore`, but keeps it dry-run by default and requires explicit flags for any write or overwrite.

## Scope

- Add `threadvault restore --backup BACKUP --target-db TARGET --json`.
- Default mode is dry-run and writes nothing.
- `--apply` is required to copy/restore the backup to the target.
- Backup database verification must pass before apply.
- Manifest verification must pass before apply unless `--allow-missing-manifest` is used for legacy backups.
- If target exists:
  - restore fails unless `--overwrite` is explicit
  - apply requires `--pre-restore-backup-dir DIR`
  - current target is backed up before overwrite using existing SQLite backup API
- If target parent does not exist:
  - dry-run reports it
  - apply creates parent directories
- Restore implementation copies the already verified SQLite backup file to the target using standard library file copy.
- After apply, verify restored target and run database doctor.
- Add `restore` JSON schema and capabilities entry.

## Existing Project Lessons

- Reuse `restore-plan` for preflight.
- Reuse `backup_database()` for pre-restore backups of existing targets.
- Reuse `verify_database_backup()` and `verify_backup_manifest()`.
- Keep overwrite behavior as explicit as `backup --force` and prune `--apply`.
- Do not modify Codex original JSONL/session files.

## Tasks

- Add `threadvault.restore` module with a deep `restore_backup()` interface.
- Add `ArchiveStore.restore()`.
- Add CLI command `restore`.
- Add `restore` schema and refresh packaged schema files.
- Add tests for:
  - dry-run writes nothing
  - apply to new target writes and verifies restored DB
  - target exists without overwrite fails
  - overwrite requires pre-restore backup dir
  - overwrite creates pre-restore backup
  - missing manifest blocks apply unless `--allow-missing-manifest`
  - schema validation and v0.22 docs
- Update README, development progress, external review, and research Markdown appendices.

## Acceptance Commands

```powershell
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault restore --backup <backup.db> --target-db <restore.db> --json
threadvault restore --backup <backup.db> --target-db <restore.db> --apply --json
threadvault validate-json --schema restore --input <payload.json> --json
threadvault schemas show restore --json
```

## Assumptions

- Restore targets are ThreadVault SQLite archive databases, not Codex original transcript files.
- `--overwrite` without `--pre-restore-backup-dir` is not allowed on apply.
- Missing manifests are legacy-compatible only when `--allow-missing-manifest` is explicit.

