# Phase 10 / v0.10: Audit History Retention

## Goal

Add a safe retention workflow for audit report directories. Users should be able to preview which old anonymous reports would be removed, then explicitly apply deletion only when they are ready.

## Scope

- Keep ThreadVault local-first and privacy-first.
- Operate only on ThreadVault audit report files matching `threadvault-audit-*.json`.
- Default to dry-run. No file deletion occurs without `--apply`.
- Do not read Codex raw transcripts.
- Do not add UI, MCP, vector search, cloud sync, team features, or external LLM summaries.

## Tasks

- Add retention planning in `audit.py`:
  - sort valid reports using the same history ordering
  - keep latest N reports
  - return kept/deletable/malformed warnings
- Add `threadvault audit-history prune --dir DIR --keep N --json`.
- Add `--apply` for actual deletion.
- Add schema `audit_history_prune`.
- Add tests for dry-run, apply deletion, malformed report tolerance, and schema validation.
- Update README, development progress, external review, and research Markdown appendices.

## Acceptance Commands

```powershell
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault audit-history prune --dir <tmp-reports> --keep 2 --json
threadvault audit-history prune --dir <tmp-reports> --keep 2 --apply --json
threadvault schemas show audit_history_prune --json
```

## Assumptions

- `--keep` must be at least 1.
- Malformed report files are never deleted by prune in v0.10; users can inspect warnings and remove them manually.
- Deletion is limited to files selected from valid ThreadVault audit report discovery.

