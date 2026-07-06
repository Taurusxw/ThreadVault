# Phase 19 / v0.19 External Review: Backup Retention Config

## Review Summary

v0.19 adds backup retention configuration. The mature behavior to reuse is internal: v0.11 already established `audit-history prune --config`, CLI override precedence, `keep_source`, and safe dry-run defaults.

## Sources Reviewed

- ThreadVault `audit-history prune`: proven local config retention shape.
- ThreadVault `app_config`: canonical TOML parsing module after v0.12.
- CASS-style robot workflows: maintenance commands should be deterministic, non-interactive, and JSON-valid.
- SQLite/local backup practice: retention should not modify databases while deciding what to delete.
- OpenAI Codex docs/manual route: Codex local state and transcript formats should be treated as local, unstable implementation details; ThreadVault config must not write into Codex state.

## v0.19 Application

- Add `[backup_history] keep = N`.
- Let `backup-history prune` accept `--config`.
- Keep CLI `--keep` as the highest-precedence explicit value.
- Return `keep_source` as `cli` or `config`.
- Keep dry-run default and explicit `--apply`.

## Risks

- Sharing one retention number between audits and backups would be convenient but unsafe; backups may be larger and more sensitive. v0.19 keeps separate config sections.
- Configured deletion can feel automatic. The command still only deletes with explicit `--apply`.
- Invalid config must fail loudly before pruning.

