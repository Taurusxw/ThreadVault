# Phase 11 / v0.11: Audit Retention Config

## Goal

Make audit report retention easier to automate by allowing `threadvault.toml` to define a default audit history keep count. The CLI remains explicit and safe: `--keep` overrides config, pruning stays dry-run unless `--apply` is passed, and no raw Codex transcript data is touched.

## Scope

- Keep ThreadVault local-first and privacy-first.
- Extend the existing local config file instead of introducing a new settings system.
- Support:
  - `[audit_history] keep = 20`
  - `threadvault audit-history prune --dir reports --config threadvault.toml --json`
  - `--keep N` as the highest-priority override.
- Fail clearly when neither `--keep` nor config provides a valid keep count.
- Do not add Web UI, TUI, MCP server, vector database, cloud sync, team features, or external LLM summaries.

## Existing Project Lessons

- CASS-style agent commands should be deterministic, machine-readable, and non-interactive.
- ezyyeah/codex-export and MeXenon/codex-session-export show that export/report directories become long-lived local artifacts and need predictable scriptable maintenance.
- ccusage treats local usage histories as append-only logs with explicit maintenance commands.
- OpenAI Codex docs continue to frame Codex local state/transcripts as implementation details that may change, so ThreadVault retention must only manage ThreadVault-generated audit reports.

## Tasks

- Add `audit_history.keep` parsing to the existing TOML config loader.
- Validate that configured keep is an integer greater than or equal to 1.
- Update `audit-history prune`:
  - make `--keep` optional
  - add `--config PATH`
  - use CLI keep first, config keep second
  - include `keep_source` in JSON output for traceability
- Add tests for config default, CLI override, missing keep, invalid config, and v0.11 docs.
- Update README, development progress, external review, and research Markdown appendices.

## Acceptance Commands

```powershell
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault audit-history prune --dir <tmp-reports> --config threadvault.toml --json
threadvault audit-history prune --dir <tmp-reports> --config threadvault.toml --keep 5 --json
threadvault audit-history prune --dir <tmp-reports> --config threadvault.toml --apply --json
threadvault --help
```

## Assumptions

- Markdown remains the source of truth for phase traceability; DOCX is not updated unless a formal Word deliverable is requested.
- `threadvault.toml` can hold more than privacy settings. A future phase may rename `privacy_config.py` to a broader app config module, but v0.11 avoids large churn.
- Invalid config should fail loudly rather than silently pruning with an unintended default.

