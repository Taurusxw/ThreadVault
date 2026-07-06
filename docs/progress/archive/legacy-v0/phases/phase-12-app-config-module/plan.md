# Phase 12 / v0.12: App Config Module

## Goal

Promote ThreadVault's local TOML configuration from a privacy-only module to a general app config module, while preserving the existing `privacy_config` import path for compatibility.

v0.11 added `[audit_history] keep = N` to `threadvault.toml`, which made `privacy_config.py` responsible for non-privacy settings. v0.12 fixes that naming debt before the config surface grows.

## Scope

- Add `threadvault.app_config` as the canonical config module.
- Keep `threadvault.privacy_config` as a compatibility wrapper.
- Preserve the existing `threadvault.toml` format:
  - `[privacy].allowlist`
  - `[audit_history].keep`
- Keep CLI flags and JSON contracts compatible.
- Do not mutate Codex-owned state, `CODEX_HOME`, `CODEX_SQLITE_HOME`, raw transcripts, or `state_5.sqlite`.
- Do not add Web UI, TUI, MCP server, vector database, cloud sync, team features, or external LLM summaries.

## Existing Project Lessons

- CASS-style agent tools benefit from stable contracts and compatible evolution.
- ccusage warns that Codex data formats can change, so configuration should stay ThreadVault-owned instead of depending on Codex raw state.
- MeXenon, ezyyeah, and jinghan23 focus on local exports and repeatable CLI workflows; a stable local config module supports that direction.
- OpenAI Codex docs describe `CODEX_HOME` and `CODEX_SQLITE_HOME` as Codex local state roots and warn that transcript formats are not stable; ThreadVault config remains separate in `threadvault.toml`.

## Tasks

- Create `src/threadvault/app_config.py`.
- Move TOML loading, allowlist parsing, and audit retention parsing into `app_config.py`.
- Keep `PrivacyConfig` as an alias to the broader `AppConfig` for compatibility.
- Update internal imports to use `app_config`.
- Leave `privacy_config.py` as a thin re-export module.
- Add tests proving:
  - `load_app_config` parses privacy allowlist and audit history keep.
  - old `load_privacy_config` imports still work.
  - privacy scan/export behavior remains compatible.
  - v0.12 docs exist.
- Update README, development progress, external review, and research Markdown appendices.

## Acceptance Commands

```powershell
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault audit-history prune --dir <tmp-reports> --config threadvault.toml --json
threadvault privacy-scan --session <session-id> --privacy-config threadvault.toml --db <tmp.db> --json
threadvault --help
```

## Assumptions

- The public CLI option `--privacy-config` stays for privacy-specific commands to avoid a breaking CLI rename.
- Internal code should prefer `app_config`; `privacy_config` remains as a compatibility shim.
- DOCX is not updated unless a formal Word deliverable is explicitly requested.

