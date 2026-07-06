# Phase 15 / v0.15 External Review: Database Backup

## Review Summary

v0.15 adds local SQLite database backup. This is a maintenance feature, not a new sync or cloud workflow. It should be boring, safe, and scriptable.

## Sources Reviewed

- SQLite backup API: use the built-in backup mechanism for a consistent copy instead of raw file copying.
- CASS-style robot commands: maintenance commands should expose deterministic JSON payloads and predictable exit codes.
- ccusage-style local tools: local usage/history databases need simple backup points before pruning or rebuilding.
- MeXenon/codex-session-export, ezyyeah/codex-export, and jinghan23/codex-export: local artifacts should remain user-controlled and script-manageable.
- OpenAI Codex local state guidance: ThreadVault backups are for ThreadVault's own SQLite archive, not Codex-owned transcripts or state databases.

## v0.15 Application

- Add `threadvault backup`.
- Use SQLite `Connection.backup()`.
- Refuse overwrite by default.
- Return source/destination/stats metadata in JSON.
- Keep restore, encryption, compression, and cloud upload out of scope.

## Risks

- Backups may contain private transcript content. v0.15 only writes to explicit local destinations and documents the privacy boundary.
- Raw file copy could miss WAL state. v0.15 avoids that by using SQLite's backup API.
- Restore is more dangerous than backup. v0.15 intentionally does not implement restore.

