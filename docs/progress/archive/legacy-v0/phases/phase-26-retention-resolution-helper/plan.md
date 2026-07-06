# Phase 26 / v0.26: Retention Resolution Helper

## Goal

Reduce retention configuration drift across audit, backup, and restore history prune commands.

v0.25 made restore history retention configurable. At that point audit, backup, and restore pruning all had the same CLI/config precedence rule, error behavior, and `keep_source` contract. v0.26 extracts that repeated decision into a small internal helper while preserving the public CLI surface.

## Scope

- Add one internal helper for resolving `--keep` versus `threadvault.toml` retention defaults.
- Preserve command behavior:
  - explicit `--keep` wins and returns `keep_source=cli`;
  - config default returns `keep_source=config`;
  - missing keep/config raises `Provide --keep or configure [section].keep...`;
  - invalid config errors still come from `app_config`.
- Update audit, backup, and restore history prune commands to use the helper.
- Add direct helper tests plus existing CLI contract tests.
- Do not change schemas except regenerating packaged schema files if needed.
- Do not add automatic pruning, background cleanup, or new public commands.

## Existing Project Lessons

- Reuse the `app_config` module as the only TOML parser.
- Keep prune commands dry-run by default.
- Keep `keep_source` stable for agent-friendly JSON consumers.
- Follow `codebase-design`: introduce a module only because three real call sites already vary by section name and attribute but share one rule.

## Tasks

- Add a small `retention.py` module with a `resolve_retention_keep()` function.
- Replace `_resolve_audit_history_keep()`, `_resolve_backup_history_keep()`, and `_resolve_restore_history_keep()` with thin calls or remove them.
- Add tests for helper behavior across audit, backup, and restore sections.
- Ensure existing v0.11/v0.19/v0.25 CLI tests still pass.
- Update README, development progress, external review, and research Markdown appendices.

## Acceptance Commands

```powershell
py -3.12 -m pytest tests\test_v26_retention.py tests\test_v11_audit_config.py tests\test_v19_backup_config.py tests\test_v25_restore_history_config.py
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault audit-history prune --dir <reports> --config <threadvault.toml> --json
threadvault backup-history prune --dir <backups> --config <threadvault.toml> --json
threadvault restore-history prune --history <history.jsonl> --config <threadvault.toml> --json
```

## Assumptions

- A generic helper is justified only for keep resolution, not for pruning itself; audit reports, backup files, and restore history JSONL have different pruning implementations.
- The public JSON contract remains additive and unchanged.
- Config remains local-only and private.

