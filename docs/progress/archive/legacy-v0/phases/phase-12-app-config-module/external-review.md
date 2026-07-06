# Phase 12 / v0.12 External Review: App Config Module

## Review Summary

v0.12 is a maintenance phase. It does not add a large feature; it removes naming debt from the configuration module so future local settings can evolve without confusing privacy-specific code with app-wide configuration.

## Sources Reviewed

- OpenAI Codex Hooks docs: transcript formats are not stable. ThreadVault should keep raw Codex shape isolated and keep its own configuration independent.
- OpenAI Codex environment variable docs: `CODEX_HOME` and `CODEX_SQLITE_HOME` identify Codex local state roots. ThreadVault's `threadvault.toml` should remain a separate local app config file and must not mutate Codex-owned state.
- CASS-style CLI patterns: compatibility matters for agent-facing tools; stable imports and JSON contracts should evolve by addition or thin compatibility wrappers.
- ccusage Codex guide: experimental Codex log support reinforces keeping implementation details behind adapters and stable local config.
- MeXenon/codex-session-export, ezyyeah/codex-export, and jinghan23/codex-export: local export tools benefit from repeatable CLI workflows and user-owned configuration.

## v0.12 Application

- Add `app_config.py` as the canonical module.
- Keep `privacy_config.py` as a thin compatibility wrapper.
- Avoid a breaking CLI rename for `--privacy-config`.
- Keep TOML schema unchanged for users:
  - `[privacy].allowlist`
  - `[audit_history].keep`

## Risks

- Introducing a new module can create duplicate logic if done carelessly. v0.12 keeps one implementation in `app_config.py` and re-exports from `privacy_config.py`.
- Renaming user-facing CLI flags would break scripts. v0.12 avoids that; a future version can add aliases only if there is a clear migration plan.

