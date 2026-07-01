# Phase 25 / v0.25: Restore History Retention Config

## Goal

Add local configuration support for restore history retention.

v0.24 added `restore-history prune --keep N`. v0.25 lets users configure a default `[restore_history] keep = N` in `threadvault.toml`, matching the existing audit and backup retention config patterns.

## Scope

- Add `[restore_history] keep = N` to `threadvault.toml`.
- Make `restore-history prune --keep` optional when config supplies `restore_history.keep`.
- Preserve precedence: CLI `--keep` overrides config.
- Add `--config PATH` to `restore-history prune`.
- Add `keep_source` to `restore_history_prune` JSON output.
- Update `config show`, `config doctor`, and config template to surface restore history retention.
- Do not add automatic pruning or scheduled cleanup.

## Existing Project Lessons

- Reuse `audit-history prune --config` and `backup-history prune --config` behavior.
- Keep all TOML parsing inside `threadvault.app_config`.
- Keep prune dry-run by default.
- Retention config should supply only defaults; it should not imply automatic deletion or rewriting.

## Tasks

- Extend `AppConfig` with `restore_history_keep`.
- Parse and validate `[restore_history].keep`.
- Update config summaries and diagnostics.
- Update `restore-history prune` to resolve keep from CLI or config.
- Add tests for config default, CLI override, missing keep, invalid config, config show, schema validation, and v0.25 docs.
- Update README, development progress, external review, and research Markdown appendices.

## Acceptance Commands

```powershell
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault restore-history prune --history <history.jsonl> --config <threadvault.toml> --json
threadvault restore-history prune --history <history.jsonl> --config <threadvault.toml> --keep 1 --json
threadvault validate-json --schema restore_history_prune --input <payload.json> --json
threadvault config show --config <threadvault.toml> --json
```

## Assumptions

- `restore_history.keep` must be an integer greater than or equal to 1.
- Restore history retention remains separate from audit and backup retention because these artifacts have different risk and storage profiles.
- `--apply` remains the only way to rewrite restore history.

