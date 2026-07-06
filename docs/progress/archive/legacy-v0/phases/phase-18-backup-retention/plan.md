# Phase 18 / v0.18: Backup Retention

## Goal

Add a safe backup retention workflow for directories containing canonical ThreadVault backup files. Users should be able to preview which old verified backups would be removed, then explicitly apply deletion when ready.

v0.17 added backup-history list/latest/verify-latest. v0.18 adds prune with the same conservative pattern used by audit-history.

## Scope

- Add `threadvault backup-history prune --dir DIR --keep N --json`.
- Add explicit `--apply` to delete old backups.
- Default to dry-run.
- Delete only valid backups discovered by `backup-history list`.
- Preserve malformed or non-SQLite backup-like files as warnings; do not delete them automatically.
- Add `backup_history_prune` JSON schema and capabilities entry.
- Do not implement restore, cloud sync, encryption, compression, or backup pruning config yet.

## Existing Project Lessons

- Reuse the proven `audit-history prune` dry-run/apply pattern.
- CASS-style maintenance commands should produce deterministic JSON and avoid prompts.
- Backups may contain private transcript content; deletion must be explicit and scoped.

## Tasks

- Add `prune_backup_history(dir, keep, apply=False)`.
- Add CLI command `backup-history prune`.
- Add schema `backup_history_prune`.
- Add tests for:
  - dry-run does not delete
  - `--apply` deletes only valid old backups
  - invalid backup-like files are warnings and not deleted
  - schema validation
  - v0.18 docs exist
- Update README, development progress, external review, and research Markdown appendices.

## Acceptance Commands

```powershell
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault backup-history prune --dir <tmp>/backups --keep 2 --json
threadvault backup-history prune --dir <tmp>/backups --keep 2 --apply --json
threadvault validate-json --schema backup_history_prune --input <payload.json> --json
```

## Assumptions

- `--keep` must be at least 1.
- Backup retention config can be designed later, after CLI behavior is stable.
- Invalid backup files should remain untouched for manual inspection.

