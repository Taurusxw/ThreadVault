# Phase 07 / v0.7 External Review: Real Corpus Anonymous Audit

## Review Summary

v0.7 applies privacy-first diagnostics to real Codex corpus sampling. The key borrowed pattern is to separate machine-useful telemetry from sensitive raw content.

## Sources Reviewed

- ccusage Codex guide: treats Codex log support as experimental, so diagnostics should emphasize warning distributions and compatibility rather than raw assumptions.
- CASS: health/triage style outputs that are useful to agents without dumping large private payloads.
- MeXenon/codex-session-export: project/session filters and review ergonomics, useful when local debugging explicitly opts into paths.
- ezyyeah/codex-export: scriptable exports and include/exclude ideas, reinforcing explicit user-controlled disclosure.
- jinghan23/codex-export: CLI/Desktop awareness and `state_5.sqlite` context, reinforcing the need to avoid over-sharing local paths by default.
- OpenAI Codex docs: transcript/state are local and format-unstable; ThreadVault diagnostics should summarize adapter health without publishing raw transcripts.

## v0.7 Application

- Default real corpus sampling hides raw paths and session IDs.
- `--include-paths` is an explicit local debugging opt-in.
- Add aggregate warning/classification telemetry for real corpus compatibility decisions.
- Keep schemas focused on normalized ThreadVault outputs rather than Codex raw formats.

## Risks

- Anonymous per-run IDs are not stable across commands, so they should not be used for durable references.
- Users may still opt into paths with `--include-paths`; docs must describe this clearly.
- Aggregate warning codes can reveal workflow shape, but they are much safer than raw transcript content.

