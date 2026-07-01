# Phase 21 / v0.21: Restore Plan Preflight

## Goal

Add a read-only restore preflight command that tells users and agents whether a backup appears safe enough to restore, without actually restoring or overwriting anything.

v0.20 added backup provenance manifests. v0.21 uses that evidence to produce a restore plan before any destructive restore command exists.

## Scope

- Add `threadvault restore-plan --backup BACKUP --target-db TARGET --json`.
- Verify the backup database with existing read-only `backup-verify` logic.
- Verify the backup manifest when present; expose missing manifest as a warning, not a hard failure.
- Report target path status:
  - exists or missing
  - parent directory exists or missing
  - target equals backup
  - target has existing file that would require future explicit overwrite
- Return recommended next actions.
- Add `restore_plan` JSON schema and capabilities entry.
- Do not copy, overwrite, restore, move, or delete any database file.

## Existing Project Lessons

- Reuse v0.16 backup verification and v0.20 manifest verification.
- Reuse the JSON contract/schema pipeline from v0.6.
- Follow the dry-run/explicit-apply safety posture from audit/backup prune.
- Keep the module deep: `build_restore_plan(backup, target_db)` hides the verification and path-risk details behind one small interface.

## Tasks

- Add `threadvault.restore_plan` module.
- Add `ArchiveStore.restore_plan()`.
- Add CLI command `restore-plan`.
- Add `restore_plan` schema and refresh packaged schema files.
- Add tests for:
  - valid backup with manifest
  - valid backup without manifest warning
  - target path already exists warning
  - target equals backup error
  - schema validation
  - v0.21 docs exist
- Update README, development progress, external review, and research Markdown appendices.

## Acceptance Commands

```powershell
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault restore-plan --backup <backup.db> --target-db <restore.db> --json
threadvault validate-json --schema restore_plan --input <payload.json> --json
threadvault schemas show restore_plan --json
```

## Assumptions

- Missing manifest should warn because older backups created before v0.20 are still valid SQLite backups.
- `target-db == backup` is always an error.
- Existing target files are warnings in the plan; a future restore command must require explicit overwrite and should create a pre-restore backup first.

