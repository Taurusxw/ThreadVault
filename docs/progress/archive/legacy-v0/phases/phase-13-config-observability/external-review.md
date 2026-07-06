# Phase 13 / v0.13 External Review: Config Observability

## Review Summary

v0.13 adds configuration observability. The goal is not a new storage backend or UI; it is a small diagnostics surface that helps humans and agents understand local ThreadVault configuration safely.

## Sources Reviewed

- CASS-style agent workflows: provide deterministic JSON diagnostics and avoid interactive prompts.
- ccusage-style local diagnostics: configuration and local history commands should be safe, repeatable, and scriptable.
- MeXenon/codex-session-export, ezyyeah/codex-export, and jinghan23/codex-export: local export tools need clear config and output behavior for repeated use.
- OpenAI Codex Hooks docs: transcript format is not stable, so ThreadVault diagnostics should not infer config from raw transcript shape.
- OpenAI Codex environment variable docs: `CODEX_HOME` and `CODEX_SQLITE_HOME` are Codex state locations; ThreadVault config stays separate in `threadvault.toml`.

## v0.13 Application

- Add `config show` for safe config summaries.
- Add `config doctor` for parse errors, invalid values, invalid regex, and actionable suggestions.
- Keep raw allowlist values hidden by default.
- Keep the implementation inside `app_config.py` so CLI remains thin.

## Risks

- Dumping config values could leak sensitive allowlist patterns or local paths. v0.13 defaults to counts and rule kinds only.
- Duplicating validation logic could cause drift. v0.13 reuses the same parser path where possible and wraps errors in diagnostics.
- Adding yet another command can clutter CLI help; grouping under `threadvault config` keeps the surface discoverable.

