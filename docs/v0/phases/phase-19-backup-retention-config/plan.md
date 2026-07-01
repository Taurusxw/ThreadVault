# Phase 19 / v0.19: Backup Retention Config

## Goal

Add local configuration support for backup retention so `backup-history prune` can use the same safe, script-friendly retention workflow as `audit-history prune`.

v0.18 added explicit backup pruning with `--keep`. v0.19 lets users define a default in `threadvault.toml` while preserving CLI override and dry-run-by-default behavior.

## Scope

- Add `[backup_history] keep = N` to local ThreadVault config.
- Keep `--keep` optional when config supplies `backup_history.keep`.
- Preserve precedence: CLI `--keep` overrides config.
- Add `keep_source` to `backup_history_prune` JSON output.
- Update `config show`, `config doctor`, and config template to surface `backup_history.keep`.
- Add tests for config default, CLI override, missing keep, invalid config, schema validation, and docs.
- Do not add automatic pruning, scheduled jobs, compression, encryption, restore, or cloud sync.

## Existing Project Lessons

- Reuse the v0.11 `audit-history prune --config` interface and JSON shape.
- Reuse `threadvault.app_config` as the only TOML parsing module.
- Continue the CASS-style rule: JSON mode must be deterministic and non-interactive.
- Backups contain private local transcripts, so pruning must remain explicit and previewable.

## Tasks

- Extend `AppConfig` with `backup_history_keep`.
- Parse and validate `[backup_history].keep` with the same positive integer helper.
- Update config summaries and diagnostics to include backup retention.
- Add `--config` and optional `--keep` to `backup-history prune`.
- Add `_resolve_backup_history_keep()`.
- Update `backup_history_prune` schema with `keep_source`.
- Update README, development progress, external review, and research Markdown appendices.
- Refresh packaged schemas.

## Acceptance Commands

```powershell
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault backup-history prune --dir <tmp>/backups --config <threadvault.toml> --json
threadvault backup-history prune --dir <tmp>/backups --config <threadvault.toml> --keep 1 --json
threadvault validate-json --schema backup_history_prune --input <payload.json> --json
threadvault config show --config <threadvault.toml> --json
```

## Assumptions

- `backup_history.keep` must be an integer greater than or equal to 1.
- `backup_history.keep` is intentionally separate from `audit_history.keep`; audit reports and database backups have different storage costs and risk profiles.
- `--apply` remains the only way to delete files.

