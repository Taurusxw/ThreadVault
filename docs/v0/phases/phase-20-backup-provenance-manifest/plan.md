# Phase 20 / v0.20: Backup Provenance Manifest

## Goal

Add local provenance metadata for ThreadVault SQLite backups so future restore work has verifiable evidence before any overwrite-capable command exists.

v0.15-v0.19 created backup, verify, history, prune, and retention config. v0.20 adds a small sidecar manifest next to backup files and read-only manifest verification.

## Scope

- Write a JSON sidecar manifest for successful `threadvault backup` by default.
- Manifest path: `<backup>.manifest.json`.
- Manifest includes version, generated timestamp, backup path, backup SHA256, bytes, schema version, stats, source database path, and source database SHA256 when available.
- Add `--no-manifest` to `backup` for scripts that only want the `.db`.
- Add `threadvault backup-manifest --backup PATH --json` to read and verify the sidecar manifest.
- Extend `backup-verify --manifest` to include manifest verification in the existing verification payload.
- Add `backup_manifest` JSON schema and capabilities entry.
- Do not implement restore, automatic overwrite, encryption, compression, or cloud sync.

## Existing Project Lessons

- Reuse Python `hashlib.sha256` streaming file hashing instead of loading whole databases.
- Reuse existing `backup-verify` read-only checks and JSON contract discipline.
- Keep provenance in a sidecar file rather than changing the SQLite schema inside backup files.
- Keep CASS-style machine-readable outputs: JSON only on stdout in `--json` mode.

## Tasks

- Add `threadvault.backup_manifest` module:
  - `manifest_path_for_backup(path)`
  - `write_backup_manifest(backup_payload)`
  - `verify_backup_manifest(backup)`
- Update `ArchiveStore.backup()` to optionally write manifest.
- Add `ArchiveStore.verify_backup_manifest()`.
- Update CLI:
  - `backup --no-manifest`
  - `backup-verify --manifest`
  - `backup-manifest --backup PATH --json`
- Update schemas and packaged schema files.
- Add tests for manifest writing, no-manifest mode, mismatch detection, schema validation, and v0.20 docs.
- Update README, development progress, external review, and research Markdown appendices.

## Acceptance Commands

```powershell
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault backup --db <tmp>/threadvault.db --out <tmp>/backups --json
threadvault backup-manifest --backup <tmp>/backups/threadvault-backup-*.db --json
threadvault backup-verify --backup <tmp>/backups/threadvault-backup-*.db --manifest --json
threadvault validate-json --schema backup_manifest --input <payload.json> --json
```

## Assumptions

- Manifest verification is read-only.
- Missing manifest is a structured error for `backup-manifest` and an attached manifest check for `backup-verify --manifest`.
- Backup files may contain private data; manifest intentionally avoids raw session content.

