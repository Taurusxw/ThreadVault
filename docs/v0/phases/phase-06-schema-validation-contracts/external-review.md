# Phase 06 / v0.6 External Review: Schema Validation Contracts

## Review Summary

v0.6 turns agent-friendly JSON output into reusable validation contracts. The main borrowed pattern is mature schema validation instead of ad hoc checks.

## Sources Reviewed

- CASS: agent-oriented docs, JSON outputs, and robot-friendly validation expectations.
- MeXenon/codex-session-export: stable filters and review-oriented outputs that benefit from predictable downstream parsing.
- ezyyeah/codex-export: multi-format scriptability and export contracts.
- jinghan23/codex-export: CLI/Desktop session compatibility, reinforcing the need for explicit machine contracts.
- ccusage Codex guide: Codex data remains experimental, so ThreadVault contracts should describe normalized output rather than raw transcript shapes.
- OpenAI Codex docs: transcript/state formats remain local facts behind adapters; public ThreadVault schemas apply only to ThreadVault JSON outputs.

## v0.6 Application

- Use the mature `jsonschema` package for Draft 2020-12 validation.
- Add schema list/show/write commands for agents and scripts.
- Add `validate-json` so generated JSON can be checked without writing custom validators.
- Package schema files under `docs/schemas/` for offline consumption.

## Risks

- Schemas can become stale if output fields change without tests.
- Too-strict schemas may block compatible append-only output, so v0.6 keeps `additionalProperties: true`.
- Raw Codex transcript shapes are still not schema-stabilized; only normalized ThreadVault output is covered.

