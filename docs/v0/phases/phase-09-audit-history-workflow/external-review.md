# Phase 09 / v0.9 External Review: Audit History Workflow

## Review Summary

v0.9 borrows from mature CLI history workflows: report directories should be discoverable, sortable, and comparable without requiring users or agents to hand-manage filenames.

## Sources Reviewed

- CASS: robot-friendly health commands and non-interactive diagnostics.
- ccusage: local historical usage/log workflows and trends over time.
- ezyyeah/codex-export: scriptable output directories and repeatable command-line export patterns.
- MeXenon/codex-session-export: review-oriented export organization.
- jinghan23/codex-export: local Codex CLI/Desktop awareness, reinforcing local-only history tooling.
- OpenAI Codex docs: raw transcript format remains unstable, so history commands operate on ThreadVault audit reports rather than Codex raw files.

## v0.9 Application

- Add `audit-history list/latest/diff-latest`.
- Tolerate malformed report files and surface warnings in JSON output.
- Keep output machine-readable and schema-described.

## Risks

- Report directories may contain user-created files; discovery must only match ThreadVault audit report names.
- Latest ordering should use report metadata when possible, with path ordering as a fallback.
- `diff-latest` is aggregate-only and should not be treated as semantic session comparison.

