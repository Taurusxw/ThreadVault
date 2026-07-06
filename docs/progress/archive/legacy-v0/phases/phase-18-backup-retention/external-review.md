# Phase 18 / v0.18 External Review: Backup Retention

## Review Summary

v0.18 adds backup retention. It follows the already validated audit-history prune pattern: dry-run by default, explicit `--apply` for deletion, and conservative discovery.

## Sources Reviewed

- ThreadVault audit-history prune: reuse dry-run/apply shape and JSON payload structure.
- CASS-style robot workflows: maintenance commands should be deterministic, non-interactive, and script-friendly.
- SQLite/local backup practice: delete only files that are confidently identified as valid backups.
- ThreadVault privacy model: backup files can contain private transcript content, so deletion must be explicit.

## v0.18 Application

- Add `backup-history prune`.
- Keep dry-run default.
- Delete only valid backups discovered by `backup-history list`.
- Keep malformed backup-like files as warnings.
- Do not implement restore or config-driven retention in this phase.

## Risks

- Deleting backups is sensitive. v0.18 requires `--apply` and scopes deletion to valid discovered backups.
- Invalid backup-like files may be important evidence of corruption. v0.18 does not delete them automatically.

