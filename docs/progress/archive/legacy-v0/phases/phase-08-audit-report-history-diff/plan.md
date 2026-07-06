# Phase 08 / v0.8: Audit Report History Diff

## Goal

Make anonymous Codex corpus audits durable and comparable over time. Users should be able to write a privacy-safe audit report, validate it, and compare two reports to see whether parse warnings, classifications, and corpus counts improved or regressed.

## Scope

- Keep ThreadVault local-first and privacy-first.
- Only write anonymous audit reports by default.
- Keep raw transcript text, raw absolute paths, and raw session IDs out of persisted reports unless a user explicitly opts into `--include-paths`.
- Do not add UI, MCP, vector search, cloud sync, team features, or external LLM summaries.

## Tasks

- Extend `audit-corpus` with `--out DIR` to write timestamped JSON reports.
- Add `threadvault audit-diff --before FILE --after FILE --json`.
- Add audit report metadata:
  - `report_version`
  - `generated_at`
  - `source`
  - `limit`
  - `privacy_note`
- Add diff fields:
  - file/event/warning deltas
  - parseable ratio delta
  - warning code deltas
  - classification deltas
  - regression flags when warnings increase or parseable ratio falls.
- Add JSON Schemas:
  - `corpus_audit_report`
  - `corpus_audit_diff`
- Add tests for report writing, privacy-safe persisted output, diff behavior, and schema validation.
- Update README, progress log, external review, and research Markdown appendices.

## Acceptance Commands

```powershell
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault audit-corpus --codex-home tests/fixtures/codex_home --out <tmp-reports> --json
threadvault validate-json --schema corpus_audit_report --input <report.json> --json
threadvault audit-diff --before <report-a.json> --after <report-b.json> --json
threadvault schemas show corpus_audit_diff --json
```

## Assumptions

- Timestamped report filenames are sufficient for v0.8; no database table is added yet.
- Report diff compares aggregate fields only and never needs raw transcript content.
- Reports with `include_paths: true` are allowed but visibly marked; default reports remain anonymous.

