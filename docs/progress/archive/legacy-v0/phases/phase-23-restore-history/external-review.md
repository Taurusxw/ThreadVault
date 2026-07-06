# Phase 23 / v0.23 External Review: Restore History

## Review Summary

v0.23 records restore history. The mature pattern to reuse is append-only local operational logs with machine-readable list/latest commands, similar to ThreadVault's audit-history workflows.

## Sources Reviewed

- ThreadVault audit-history: list/latest command shape and local artifact discovery.
- ThreadVault restore: applied restore payload already contains source, target, verification, and pre-restore backup metadata.
- CASS-style robot workflows: deterministic JSON outputs for agents.
- Existing Codex export tools: local artifact management and privacy-first behavior.

## v0.23 Application

- Append one JSON object per successful applied restore.
- Keep history separate from the SQLite database.
- Add list/latest commands.
- Do not append dry-run or failed restore attempts.
- Keep raw transcript/session content out of history.

## Risks

- History includes local file paths and checksums. Documentation must call it private local metadata.
- JSONL can contain malformed lines if edited manually. Listing should return warnings and continue.
- Logging restore events must not make restore itself brittle; if history writing fails, the structured error should be visible.

