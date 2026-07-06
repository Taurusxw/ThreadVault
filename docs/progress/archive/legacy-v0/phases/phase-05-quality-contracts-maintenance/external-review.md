# Phase 05 / v0.5 External Review: Quality Contracts and Maintenance

## Review Summary

v0.5 keeps the v0.4 rule: borrow mature interface patterns and validation ideas, not external source code. The focus is quality gates, stable machine output, privacy maintenance, and diagnostics.

## Sources Reviewed

- MeXenon/codex-session-export: project view, session filtering, Last N turns, output truncation, and Markdown review workflows.
- ezyyeah/codex-export: multi-format export, include/exclude filters, and script-friendly conversion expectations.
- jinghan23/codex-export: Codex CLI plus Desktop session coverage and `state_5.sqlite` awareness.
- ccusage Codex guide: Codex log parsing is experimental and must be treated as format-unstable.
- CASS: robot/JSON command style, minimal fields, health/triage style diagnostics, and agent-readable docs.
- OpenAI Codex docs: hooks expose transcript paths but transcript content is not a stable interface; `CODEX_HOME` and `CODEX_SQLITE_HOME` are local state roots; archive/unarchive/delete affect transcript lifecycle.

## v0.5 Application

- Keep `CodexJsonlAdapter` as the parser adapter and fix warning diagnostics in one place.
- Preserve CASS-style low-token `search --fields minimal` and add JSON schema-style robot docs.
- Preserve ezyyeah-style multi-format export but make privacy findings configurable and auditable.
- Expand `doctor` rather than adding speculative repair automation.

## Verification Notes

- The OpenAI Codex manual helper was attempted with a Windows temp cache but returned HTTP 403 in this environment. The implementation therefore relies on already reviewed official Codex pages and local code/tests for this phase.

## Risks

- Codex transcript and state schemas may continue changing.
- Privacy allowlists can hide true positives if configured too broadly.
- JSON contracts are now more stable, so future field removal should be treated as a compatibility break.

