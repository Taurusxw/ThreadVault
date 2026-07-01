# Phase 13 / v0.13: Config Observability

## Goal

Add machine-friendly configuration inspection commands so users and agents can verify which `threadvault.toml` is being used, whether it parses, and which local settings are effective without reading or dumping sensitive configuration contents.

v0.12 created `threadvault.app_config` as the canonical config module. v0.13 builds on that module by adding a small config diagnostics interface and CLI commands.

## Scope

- Add `threadvault config show --json`.
- Add `threadvault config doctor --json`.
- Keep config inspection local-only.
- Do not print raw allowlist text/pattern values by default.
- Do not read or mutate Codex-owned state, `CODEX_HOME`, `CODEX_SQLITE_HOME`, transcripts, or `state_5.sqlite`.
- Do not add Web UI, TUI, MCP server, vector database, cloud sync, team features, or external LLM summaries.

## Existing Project Lessons

- CASS-style robot commands should expose deterministic JSON for agent workflows.
- ccusage-style diagnostics should be safe to run repeatedly on local history/config without mutation.
- MeXenon, ezyyeah, and jinghan23 reinforce scriptable local tooling and clear CLI workflows.
- OpenAI Codex docs treat Codex local state/transcripts as Codex-owned and potentially unstable; ThreadVault config should remain a separate user-owned file.

## Tasks

- Extend `app_config.py` with:
  - `describe_app_config(path=None, include_values=False)`
  - `diagnose_app_config(path=None)`
- Include in `show` output:
  - requested path
  - resolved default path
  - loaded path
  - exists flag
  - configured sections
  - privacy allowlist count and rule kinds
  - audit history keep value
- Include in `doctor` output:
  - ok flag
  - errors/warnings
  - suggestions
  - same safe summary as `show`
- Add CLI subcommands:
  - `threadvault config show --config PATH --json`
  - `threadvault config doctor --config PATH --json`
- Add tests for missing config, valid config, invalid TOML, invalid regex, invalid keep, JSON-only output, and v0.13 docs.
- Update README, development progress, external review, and research Markdown appendices.

## Acceptance Commands

```powershell
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault config show --json
threadvault config show --config threadvault.toml --json
threadvault config doctor --config threadvault.toml --json
threadvault --help
```

## Assumptions

- `config show` defaults to safe summaries and does not expose raw allowlist text or regex values.
- A future explicit `--include-values` option can be added if users need full local debugging output.
- JSON contract for config commands starts as v0.13 additive contract.

