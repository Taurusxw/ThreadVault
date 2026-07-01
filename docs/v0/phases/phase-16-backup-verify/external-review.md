# Phase 16 / v0.16 External Review: Backup Verify

## Review Summary

v0.16 adds backup verification. It deliberately stops short of restore. The safe sequence is: create backup, verify backup, only later design restore with overwrite and provenance safeguards.

## Sources Reviewed

- SQLite `PRAGMA integrity_check`: mature built-in database integrity validation.
- SQLite read-only URI mode: useful for verification commands that should not mutate backup files.
- CASS-style diagnostics: machine-readable success and failure payloads are important for agent workflows.
- ccusage-style local maintenance tooling: verify local artifacts before destructive operations.
- OpenAI Codex local state guidance: ThreadVault backup verification should read only ThreadVault archive backups, not Codex-owned state.

## v0.16 Application

- Add `backup-verify`.
- Open backup files read-only.
- Run integrity and existing ThreadVault schema checks.
- Return structured JSON on both success and failure.
- Keep restore out of scope.

## Risks

- A verification command must not mutate backup files. v0.16 uses SQLite read-only URI mode.
- Integrity checks can prove database structure, not semantic completeness of a user's archive. v0.16 reports stats and schema health but does not claim restore readiness beyond those checks.

