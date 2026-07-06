# Phase 05 / v0.5: Quality Contracts and Maintenance

## Goal

Move ThreadVault from a working v0.4 CLI into a more maintainable tool that agents can call predictably and users can run against real Codex history with clearer diagnostics.

## Scope

- Keep the work local-first and privacy-first.
- Harden the CLI/data layer rather than adding UI, cloud sync, vector search, MCP, team features, or external LLM summaries.
- Continue treating Codex JSONL and state SQLite as unstable local facts behind adapters.

## Tasks

- Fix duplicate function-call pairing warnings in `CodexJsonlAdapter`.
- Add exact parser warning regression tests.
- Upgrade `capabilities` and `robot-docs schemas` with v0.5 JSON contract metadata.
- Ensure JSON-mode commands emit parseable JSON only.
- Add privacy allowlist config support without removing audit visibility.
- Make `privacy-scan` report `rules_version`, allowlisted counts, and effective finding counts.
- Expand `doctor` with schema object checks and maintenance suggestions.
- Add `self-test --json` for local fixture and database smoke checks.
- Update README, phase plan, external review, development progress, and research Markdown appendices.

## Acceptance Commands

```powershell
py -3.12 -m pytest
threadvault --help
threadvault capabilities --json
threadvault robot-docs schemas --json
threadvault ingest-sample --codex-home tests/fixtures/codex_home --dry-run --json
threadvault warnings --summary --json --db <tmp.db>
threadvault privacy-scan --session sess-privacy --db <tmp.db> --json
threadvault export --session sess-privacy --privacy-mode fail --db <tmp.db> --out <tmp-out> --json
threadvault reindex --fts-only --db <tmp.db> --json
threadvault doctor --db <tmp.db> --codex-home tests/fixtures/codex_home --json
```

## Assumptions

- Markdown remains the traceability source of truth.
- DOCX is not updated unless a formal Word deliverable is requested.
- External projects are used for interface and workflow inspiration only; no source code is copied.

