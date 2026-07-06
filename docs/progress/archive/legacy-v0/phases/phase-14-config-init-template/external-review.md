# Phase 14 / v0.14 External Review: Config Init Template

## Review Summary

v0.14 adds safe config initialization. The feature is intentionally small: write a valid starter `threadvault.toml`, refuse accidental overwrite, and validate the generated file through the same parser used by normal commands.

## Sources Reviewed

- CASS-style agent workflows: setup commands should provide JSON output and deterministic results.
- ccusage-style local history tooling: maintenance/setup commands should be explicit and avoid surprising filesystem changes.
- MeXenon/codex-session-export, ezyyeah/codex-export, and jinghan23/codex-export: repeatable local workflows benefit from documented config and export defaults.
- OpenAI Codex environment docs: ThreadVault should keep its config separate from Codex-owned local state roots.

## v0.14 Application

- Add `config init` under the existing config command group.
- Use `--force` as the only overwrite path.
- Reuse `diagnose_app_config()` to validate the generated template.
- Keep raw Codex transcripts and state databases untouched.
- Use TOML literal string guidance for Windows path regex examples.

## Risks

- Overwriting user config would be damaging. v0.14 refuses overwrite by default and returns a structured `config_exists` error.
- A bad template would break first-run setup. v0.14 validates the generated file in tests and command output.
- Examples can drift from parser behavior. v0.14 fixes the README Windows regex example and adds a regression test for it.

