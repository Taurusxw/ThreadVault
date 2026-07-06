# Phase 31 / v0.31 External Review: Final CLI MVP Acceptance

## Review Summary

v0.31 is the final CLI MVP acceptance pass. The useful external pattern is CASS-style machine-verifiable readiness: prove the tool works through its own command-line surfaces and JSON contracts.

## Sources Reviewed

- ThreadVault v0.30 completion gap audit.
- ThreadVault `capabilities --json`, `schemas`, `validate-json`, `doctor`, and `self-test`.
- CASS-style health/triage and robot-friendly command contracts.
- MeXenon/ezyyeah export tooling as reference for local export expectations.
- SQLite backup/restore best practice already used in ThreadVault.

## v0.31 Application

- Use one end-to-end CLI chain as the acceptance evidence.
- Validate representative machine outputs with existing schemas.
- Include backup and restore because they are now part of the maintenance surface.
- Keep the acceptance report local and Markdown-based.

## Risks

- Acceptance should not silently include real private Codex transcripts. v0.31 uses `tests/fixtures/codex_home`.
- A green smoke run does not prove future UI/cloud/vector work; those remain deferred.
- DOCX synchronization is a separate formal-delivery step if requested.

## Source Reuse Boundary

No external source code is copied. This phase reuses ThreadVault's own CLI and schema infrastructure as the verifier.

