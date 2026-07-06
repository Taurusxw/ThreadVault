# Phase 29 / v0.29 External Review: Doctor Schema Contract

## Review Summary

v0.29 tightens the `doctor --json` contract. The key reference is CASS-style health/triage output: agent-friendly diagnostic commands should have a stable schema so automation can distinguish healthy, degraded, and actionable states.

## Sources Reviewed

- ThreadVault v0.5 doctor fields: schema objects, maintenance suggestions, parse health.
- ThreadVault v0.6 schema commands and `validate-json`.
- ThreadVault v0.28 capabilities schema contract.
- CASS-style health/triage commands: machine-verifiable diagnostic payloads.
- `codebase-design` skill: centralize interface facts in the schema module.

## v0.29 Application

- Require stable top-level doctor fields already emitted by runtime.
- Keep nested diagnostic structures permissive enough for future additive fields.
- Validate real `doctor --json` output against the doctor schema in tests.
- Refresh packaged schemas for downstream agents.

## Risks

- Doctor output intentionally includes local paths and environment metadata. This remains local-only and should not be treated as share-safe.
- Overly strict nested schemas would make future doctor improvements harder. v0.29 only tightens stable top-level fields.
- Schema tightening should not change doctor runtime behavior.

## Source Reuse Boundary

No external source code is copied. This phase reuses ThreadVault's schema system and borrows only diagnostic contract principles from mature robot-friendly tooling.

