# Phase 11 / v0.11 External Review: Audit Retention Config

## Review Summary

v0.11 adds config-driven retention defaults for audit report pruning. This follows mature CLI practice: keep automation-friendly defaults in a local config file, keep command-line flags as explicit overrides, and make destructive operations require an additional apply flag.

## Sources Reviewed

- OpenAI Codex Hooks docs: transcript paths and transcript formats remain implementation details, so ThreadVault should avoid relying on raw transcript shape for maintenance tasks.
- OpenAI Codex environment variable docs: `CODEX_HOME` and `CODEX_SQLITE_HOME` define Codex local state roots; ThreadVault config should stay separate and should not mutate Codex state.
- MeXenon/codex-session-export: local Codex export tools benefit from user-controlled filtering and repeatable output workflows.
- ezyyeah/codex-export: multi-format exports and directory outputs are expected to be scriptable, which creates a need for retention conventions.
- jinghan23/codex-export: CLI/Desktop compatibility reinforces the need to separate ThreadVault-generated artifacts from Codex-owned files.
- ccusage Codex guide: Codex log support is experimental, so maintenance commands should stay conservative and transparent.
- CASS-style robot commands: JSON output should be stable enough for agents and scripts.

## v0.11 Application

- Reuse the existing TOML config loader rather than creating a second config format.
- Add `[audit_history] keep = N` as a simple, mature convention.
- Keep `--keep` as a command-line override for one-off runs.
- Keep prune dry-run by default; `--apply` remains the only deletion trigger.
- Add `keep_source` in JSON output so scripts can tell whether retention came from CLI or config.

## Risks

- A broader config file inside a module named `privacy_config.py` is slightly awkward. v0.11 accepts that small naming debt to avoid unnecessary refactoring; a future phase can introduce an `app_config.py` compatibility wrapper.
- Invalid config values can break automated jobs. v0.11 intentionally fails clearly instead of guessing a fallback value.
- Retention must never target raw Codex transcripts. The existing report discovery function only selects valid ThreadVault audit report JSON files and continues to leave malformed files untouched.

