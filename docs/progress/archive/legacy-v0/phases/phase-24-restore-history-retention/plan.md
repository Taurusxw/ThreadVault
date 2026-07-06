# Phase 24 / v0.24: Restore History Retention

## Goal

Add safe retention pruning for local restore history JSONL files.

v0.23 introduced append-only restore history. v0.24 lets users keep the latest N valid restore records while preserving the same dry-run/apply safety posture used by audit and backup history pruning.

## Scope

- Add `threadvault restore-history prune --history PATH --keep N --json`.
- Default to dry-run and write nothing.
- `--apply` rewrites the JSONL file.
- Keep the latest N valid restore records.
- Preserve malformed/non-object history lines during apply and report warnings.
- Add `restore_history_prune` JSON schema.
- Do not delete backup files, restored databases, or Codex transcript files.
- Do not add config retention yet.

## Existing Project Lessons

- Reuse audit-history/backup-history prune interface: dry-run by default, explicit `--apply`.
- Restore history is one JSONL file, so pruning rewrites records rather than deleting artifact files.
- Malformed history lines may be useful evidence of manual edits or corruption; keep them unless a future explicit repair command is designed.

## Tasks

- Extend `restore_history.py` with `prune_restore_history(history_path, keep, apply=False)`.
- Add CLI command `restore-history prune`.
- Add schema `restore_history_prune`.
- Add capabilities entry.
- Add tests for:
  - dry-run writes nothing
  - apply keeps latest N valid records
  - malformed lines are preserved and warned
  - invalid keep rejection
  - schema validation
  - v0.24 docs exist
- Update README, development progress, external review, and research Markdown appendices.

## Acceptance Commands

```powershell
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault restore-history prune --history <history.jsonl> --keep 2 --json
threadvault restore-history prune --history <history.jsonl> --keep 2 --apply --json
threadvault validate-json --schema restore_history_prune --input <payload.json> --json
```

## Assumptions

- `keep` must be at least 1.
- Missing history file returns an empty successful plan.
- Apply creates parent directories only if a history path needs to be rewritten; missing files remain absent.

