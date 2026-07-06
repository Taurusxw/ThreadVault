# Phase 31 / v0.31: Final CLI MVP Acceptance

## Goal

Run and archive a final end-to-end acceptance pass for the ThreadVault CLI/data-layer MVP.

v0.30 concluded that the CLI/data-layer line is effectively complete. v0.31 proves that conclusion with a single current-environment smoke chain covering import, search, summarize, export, privacy, schema validation, doctor/self-test, backup, restore, and restore history.

## Scope

- Run a temporary-workspace acceptance chain using `tests/fixtures/codex_home`.
- Validate representative JSON outputs with `threadvault validate-json`.
- Confirm export files are created for Markdown, JSON, JSONL, and CSV.
- Confirm privacy scan and redact export work.
- Confirm backup, manifest, restore-plan, restore, and restore-history list work.
- Record the acceptance result under `docs/v0/phases/phase-31-final-cli-mvp-acceptance/`.
- Update README, development progress, and research appendices.

## Existing Project Lessons

- Reuse ThreadVault's own CLI and schemas as the acceptance harness.
- Reuse SQLite backup/restore safety gates instead of inventing a separate verifier.
- Follow CASS-style machine-verifiable readiness: the acceptance artifact should be a JSON summary plus a readable Markdown report.

## Tasks

- Create `docs/v0/phases/phase-31-final-cli-mvp-acceptance/final-cli-mvp-acceptance.md`.
- Run acceptance smoke commands in a temp directory.
- Save the command summary and results in the acceptance report.
- Run full pytest and ruff.
- Clean generated caches.
- If all evidence passes, the CLI/data-layer objective can be marked complete.

## Acceptance Commands

```powershell
threadvault import --codex-home tests/fixtures/codex_home --db <tmp.db> --json
threadvault list --db <tmp.db> --json
threadvault search pytest --db <tmp.db> --json --fields minimal
threadvault summarize --session sess-current --db <tmp.db> --json
threadvault export --session sess-current --db <tmp.db> --out <tmp-out> --format md --json
threadvault export --session sess-current --db <tmp.db> --out <tmp-out> --format json --json
threadvault export --session sess-current --db <tmp.db> --out <tmp-out> --format jsonl --json
threadvault export --session sess-current --db <tmp.db> --out <tmp-out> --format csv --json
threadvault privacy-scan --session sess-privacy --db <tmp.db> --json
threadvault export --session sess-privacy --db <tmp.db> --out <tmp-out> --privacy-mode redact --json
threadvault stats --db <tmp.db> --json
threadvault doctor --db <tmp.db> --codex-home tests/fixtures/codex_home --json
threadvault self-test --db <tmp.db> --json
threadvault reindex --db <tmp.db> --fts-only --json
threadvault backup --db <tmp.db> --out <tmp-backups> --json
threadvault backup-verify --backup <backup.db> --manifest --json
threadvault restore-plan --backup <backup.db> --target-db <restored.db> --json
threadvault restore --backup <backup.db> --target-db <restored.db> --apply --restore-history <history.jsonl> --json
threadvault restore-history list --history <history.jsonl> --json
py -3.12 -m pytest
py -3.12 -m ruff check .
```

## Assumptions

- This final acceptance is for the CLI/data-layer scope, not deferred UI/cloud/vector/MCP work.
- DOCX synchronization remains separate unless explicitly requested.
- The long-running goal can be completed after this pass if all evidence succeeds and no required work remains in the CLI/data-layer scope.


