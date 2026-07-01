# Phase 04 / v0.4: Real Corpus and Privacy Hardening

## Goal

Make ThreadVault safer against real Codex history: harden JSONL adaptation, add privacy-safe corpus sampling, support redaction/fail export modes, and preserve phase traceability.

## Scope

- Keep local-first SQLite/FTS5.
- Do not upload or fixture real private transcripts.
- Keep external LLM summaries, vector search, UI, MCP, and cloud sync out of scope.

## Tasks

- Introduce `CodexJsonlAdapter` as the parser implementation seam.
- Add record classification and call pairing warnings.
- Add `ingest-sample --dry-run --json`.
- Add `warnings --summary --json` and parse health in `doctor --json`.
- Add privacy severity, redaction, fail mode, and `privacy-scan`.
- Add evidence coverage to rule summaries.
- Update README, research Markdown, development progress, and external review.

## Acceptance Commands

```powershell
py -3.12 -m pytest
threadvault --help
threadvault ingest-sample --codex-home tests/fixtures/codex_home --dry-run --json
threadvault privacy-scan --session sess-current --db <tmp.db> --json
threadvault export --session sess-current --privacy-mode redact --db <tmp.db> --out <tmp-out> --json
```

## Assumptions

- Markdown is the source of truth for phase traceability.
- DOCX is not updated unless explicitly requested.
- Real corpus diagnostics report statistics and warning metadata only.

