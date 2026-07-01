# Phase 23 / v0.23: Restore History

## Goal

Add a local restore history trail so applied restores can be audited later without inspecting shell logs.

v0.22 introduced write-capable restore. v0.23 records successful applied restores as local JSONL metadata and adds read commands for agents and users.

## Scope

- Add local JSONL restore history records for successful `restore --apply`.
- Default history path is under the ThreadVault app data directory.
- Add `--restore-history PATH` to `restore` for deterministic scripts/tests.
- Add `threadvault restore-history list --json`.
- Add `threadvault restore-history latest --json`.
- Record metadata only:
  - timestamp
  - backup path
  - target path
  - apply/overwrite/allow_missing_manifest flags
  - backup SHA256
  - target SHA256
  - pre-restore backup destination if any
  - restored schema version and stats
- Add `restore_history_list` and `restore_history_latest` schemas.
- Do not store raw transcript text or Codex JSONL payloads in history.

## Existing Project Lessons

- Reuse audit-history list/latest command shape.
- Use JSONL for append-only local audit trails.
- Reuse streaming SHA256 helper from `backup_manifest`.
- Keep restore execution and history persistence separated by a small module interface.

## Tasks

- Add `threadvault.restore_history` module:
  - `default_restore_history_path()`
  - `append_restore_history(payload, path=None)`
  - `list_restore_history(path=None)`
  - `latest_restore_history(path=None)`
- Update restore to append history only after successful apply.
- Add CLI group `restore-history`.
- Add schemas and refresh `docs/schemas`.
- Add tests for history writing, custom path, list/latest, dry-run not writing, schema validation, and v0.23 docs.
- Update README, development progress, external review, and research Markdown appendices.

## Acceptance Commands

```powershell
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault restore --backup <backup.db> --target-db <restore.db> --apply --restore-history <history.jsonl> --json
threadvault restore-history list --history <history.jsonl> --json
threadvault restore-history latest --history <history.jsonl> --json
threadvault validate-json --schema restore_history_list --input <payload.json> --json
```

## Assumptions

- Failed or dry-run restores are not appended to history.
- History contains local paths and checksums and should be treated as local/private metadata.
- Restore history is separate from SQLite archive contents to avoid mutating restored databases just to record operational metadata.

