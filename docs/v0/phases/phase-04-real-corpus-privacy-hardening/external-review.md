# Phase 04 / v0.4 External Review: Real Corpus and Privacy Hardening

## Review Summary

v0.4 continues borrowing interface ideas from existing projects, not source code.

## Borrowed Patterns

- MeXenon/codex-session-export: practical session filtering and Markdown review workflows.
- ezyyeah/codex-export: multi-format export expectations.
- jinghan23/codex-export: CLI plus Desktop history awareness.
- ccusage: explicit caution that Codex local formats are experimental.
- CASS: agent-friendly JSON contracts and low-token command outputs.
- OpenAI Codex docs: transcripts and hooks are useful local facts but not a stable API.

## v0.4 Application

- Add parser adapter instead of spreading raw transcript assumptions.
- Add privacy-first dry-run corpus sampling.
- Add redact/fail export modes before any sharing-oriented workflows.
- Keep JSON outputs append-only for agent consumers.

## Risks

- Codex transcript and state schemas can change.
- Privacy regexes are defensive but incomplete.
- Rule summaries remain local and deterministic, not semantic or exhaustive.

