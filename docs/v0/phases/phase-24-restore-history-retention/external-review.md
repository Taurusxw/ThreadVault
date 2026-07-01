# Phase 24 / v0.24 External Review: Restore History Retention

## Review Summary

v0.24 adds restore history retention. The mature behavior to reuse is ThreadVault's own audit-history and backup-history prune model: preview by default, explicit apply, and structured JSON output.

## Sources Reviewed

- ThreadVault `audit-history prune`: dry-run/apply retention shape.
- ThreadVault `backup-history prune`: conservative deletion and warning behavior.
- ThreadVault restore history JSONL: append-only local operational log.
- CASS-style robot workflows: deterministic maintenance JSON.

## v0.24 Application

- Add `restore-history prune`.
- Rewrite only the restore history JSONL file on `--apply`.
- Keep latest N valid records.
- Preserve malformed lines and return warnings.
- Do not touch backup databases or restored databases.

## Risks

- Rewriting a JSONL log can lose manual comments or malformed evidence. v0.24 preserves malformed/non-object lines on apply.
- Users may expect file deletion semantics from other prune commands. Docs must clarify this command prunes records inside one history file.
- Config-driven retention is left out until command behavior is stable.

