# Phase 14 / v0.14: Config Init Template

## Goal

Add a safe `threadvault config init` command that writes a starter `threadvault.toml` template. Users should be able to create a valid local config without copying examples by hand, and agents should be able to initialize config paths deterministically.

v0.13 made config observable through `config show` and `config doctor`; v0.14 adds the missing creation path.

## Scope

- Add a template generator in `app_config.py`.
- Add `threadvault config init --config PATH --json`.
- Default to no overwrite when the target exists.
- Add explicit `--force` for overwrite.
- Validate the generated template with the existing config parser.
- Keep the generated template local-only and privacy-preserving.
- Fix README examples to use TOML literal strings for Windows path regex patterns.
- Do not read or mutate Codex-owned state, `CODEX_HOME`, `CODEX_SQLITE_HOME`, transcripts, or `state_5.sqlite`.
- Do not add Web UI, TUI, MCP server, vector database, cloud sync, team features, or external LLM summaries.

## Existing Project Lessons

- CASS-style CLIs expose deterministic machine-readable setup and diagnostics.
- ccusage-style local tools should keep maintenance commands explicit and safe.
- MeXenon, ezyyeah, and jinghan23 emphasize repeatable local export workflows; a reproducible config template supports that.
- OpenAI Codex docs keep Codex state separate from user tooling; ThreadVault config init should write only ThreadVault-owned `threadvault.toml`.

## Tasks

- Add `default_config_template()` to `app_config.py`.
- Add `init_app_config(path=None, force=False)` returning a structured payload.
- Include generated template sections:
  - `[privacy] allowlist = []`
  - `[audit_history] keep = 20`
  - comments documenting TOML literal strings for Windows regex patterns.
- Add `threadvault config init`.
- Add JSON output fields:
  - `ok`
  - `path`
  - `created`
  - `overwritten`
  - `existed`
  - `force`
  - `doctor`
- Add `config_init` JSON schema.
- Add tests for create, existing-without-force, force overwrite, generated config doctor, schema validation, README literal-string example, and v0.14 docs.
- Update README, development progress, external review, and research Markdown appendices.

## Acceptance Commands

```powershell
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault config init --config <tmp>/threadvault.toml --json
threadvault config doctor --config <tmp>/threadvault.toml --json
threadvault config init --config <tmp>/threadvault.toml --json
threadvault config init --config <tmp>/threadvault.toml --force --json
threadvault validate-json --schema config_init --input <payload.json> --json
```

## Assumptions

- Default audit history retention in the template can be `20`, matching the documented example.
- Existing config files are user-owned and must not be overwritten unless `--force` is explicit.
- DOCX is not updated unless a formal Word deliverable is explicitly requested.

