# Phase 22 / v0.22 External Review: Safe Restore

## Review Summary

v0.22 introduces the first write-capable restore command. The mature pattern to follow is backup tooling that separates plan/apply, verifies source artifacts before writes, backs up existing targets before overwrite, and verifies results after writes.

## Sources Reviewed

- Python standard library `shutil.copy2`: reliable local file copy with metadata preservation for a verified backup file.
- SQLite backup API already used by ThreadVault: reuse for pre-restore backup of existing target databases.
- ThreadVault v0.21 `restore-plan`: preflight source of truth for target risk and backup/manifest status.
- ThreadVault v0.15-v0.20 backup/verify/manifest commands: provenance and health checks.
- CASS-style robot workflows: deterministic JSON outputs and explicit action modes.

## v0.22 Application

- `restore` is dry-run by default.
- `--apply` is required for writes.
- Existing targets require both `--overwrite` and `--pre-restore-backup-dir`.
- Backup and manifest checks must pass before apply, with explicit legacy opt-in for missing manifests.
- After apply, the restored target is verified and diagnosed.

## Risks

- Restore can overwrite valuable local data. v0.22 requires explicit overwrite and a pre-restore backup.
- Manifests were introduced after backups existed. Missing manifests can be allowed only with a visible flag.
- Raw file copy of an arbitrary live database is risky, but here the source is a verified backup artifact, not a live database.

