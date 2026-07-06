# Phase 25 / v0.25 External Review: Restore History Retention Config

## Review Summary

v0.25 adds restore history retention config. This reuses ThreadVault's existing local TOML configuration model rather than creating another config format.

## Sources Reviewed

- ThreadVault v0.11 audit retention config: `--keep` optional with `[audit_history].keep`.
- ThreadVault v0.19 backup retention config: separate section and `keep_source` metadata.
- ThreadVault v0.24 restore history prune: dry-run/apply rewrite semantics.
- CASS-style robot workflows: deterministic JSON output and explicit provenance fields.

## v0.25 Application

- Add `[restore_history] keep = N`.
- Preserve CLI precedence.
- Add `keep_source` to prune JSON.
- Keep `--apply` as the only write trigger.
- Keep config parsing in `app_config`.

## Risks

- Users may interpret config as automatic cleanup. Documentation must state it only supplies a default for prune.
- Restore history includes private local paths and checksums. Config-driven retention must remain explicit through the command.
- A shared keep value for all history types would be simpler but less accurate; v0.25 keeps a dedicated section.

