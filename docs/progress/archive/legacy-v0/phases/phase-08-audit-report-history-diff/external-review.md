# Phase 08 / v0.8 External Review: Audit Report History Diff

## Review Summary

v0.8 borrows from mature health-report and usage-diff workflows: persist machine-readable snapshots, compare aggregate counters, and keep raw data out of diagnostic artifacts.

## Sources Reviewed

- CASS: health and triage reports that agents can consume without an interactive UI.
- ccusage: local usage/log analysis patterns where experimental data sources need trend monitoring.
- MeXenon/codex-session-export: project/session review flows that benefit from stable exported artifacts.
- ezyyeah/codex-export: scriptable export formats and explicit user-controlled output paths.
- jinghan23/codex-export: CLI/Desktop state awareness, reinforcing local-only report generation.
- OpenAI Codex docs: transcript/state formats remain unstable, so reports track normalized parser health rather than raw transcript semantics.

## v0.8 Application

- Add timestamped anonymous JSON audit reports.
- Add report diff over aggregate warning/classification counters.
- Add schema contracts for audit reports and diffs.
- Keep persisted reports privacy-safe by default.

## Risks

- Aggregate trend data can still reveal broad usage shape.
- Reports with `--include-paths` may contain local paths; this remains explicit opt-in.
- Diffs are aggregate-only and should not be interpreted as semantic transcript quality.

