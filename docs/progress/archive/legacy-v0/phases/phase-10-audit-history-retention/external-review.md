# Phase 10 / v0.10 External Review: Audit History Retention

## Review Summary

v0.10 adds retention management with a conservative dry-run/apply pattern. This follows mature CLI maintenance behavior: preview destructive actions first, require explicit confirmation flags to mutate files, and scope deletion tightly.

## Sources Reviewed

- CASS: machine-friendly maintenance commands should produce structured output and avoid interactive prompts by default.
- ccusage: local history/log tools need pruning workflows as reports accumulate.
- ezyyeah/codex-export: output directories should remain script-manageable.
- MeXenon/codex-session-export: export artifacts should be reviewable and user-controlled.
- OpenAI Codex local-state constraints: ThreadVault should prune only its own reports, never Codex raw transcripts.

## v0.10 Application

- Add `audit-history prune --keep N` as dry-run by default.
- Add `--apply` for actual deletion.
- Never delete malformed report files automatically.
- Add JSON schema coverage for prune output.

## Risks

- Any deletion feature can surprise users; default dry-run and explicit `--apply` reduce this risk.
- Overly broad globbing could delete unrelated files, so pruning only uses discovered valid audit reports.

