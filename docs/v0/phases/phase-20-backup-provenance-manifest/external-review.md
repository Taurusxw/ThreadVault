# Phase 20 / v0.20 External Review: Backup Provenance Manifest

## Review Summary

v0.20 adds backup provenance manifests. The strongest existing pattern is local backup tooling: create an immutable-ish sidecar with checksums, then verify it before higher-risk workflows such as restore.

## Sources Reviewed

- Python/SQLite backup practice: ThreadVault already uses SQLite `Connection.backup()` instead of raw copying.
- ThreadVault `backup-verify`: read-only integrity checks are established and should be reused.
- ThreadVault audit/backup history: timestamped artifacts and JSON schemas are already used for local maintenance workflows.
- CASS-style robot workflows: diagnostics should be deterministic, non-interactive, and JSON-valid.
- Existing Codex export tools: they focus on local transcript/export artifacts, reinforcing local-first provenance over cloud state.

## v0.20 Application

- Add sidecar `<backup>.manifest.json` for successful backups.
- Include checksums and stats but no raw transcript content.
- Add read-only manifest verification.
- Integrate manifest verification into `backup-verify --manifest`.
- Keep restore out of scope.

## Risks

- Manifests contain local paths. This is acceptable because they are written only next to user-requested local backup files, but docs must warn they are local provenance artifacts.
- A manifest can become stale if a backup is moved or modified. v0.20 reports structured mismatch errors instead of trying to repair automatically.
- Checksumming large databases can take time. v0.20 uses streaming SHA256 and keeps the interface explicit.

