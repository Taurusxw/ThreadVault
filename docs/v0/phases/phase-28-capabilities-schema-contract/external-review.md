# Phase 28 / v0.28 External Review: Capabilities Schema Contract

## Review Summary

v0.28 tightens the `capabilities --json` contract. The main reference is CASS-style robot/health entrypoints: agent-facing discovery commands should describe stable fields precisely enough for automation. ThreadVault already has schema infrastructure, so this phase reuses that instead of introducing a new manifest format.

## Sources Reviewed

- ThreadVault v0.5 robot-friendly JSON contract and `capabilities --json`.
- ThreadVault v0.6 schema commands and `validate-json`.
- ThreadVault v0.27 retention schema tightening.
- CASS-style robot workflows: machine callers depend on complete discovery metadata.
- `codebase-design` skill: keep schema contract knowledge centralized.

## v0.28 Application

- Require all stable fields already emitted by `capabilities --json`.
- Add missing schema properties for export profiles, privacy modes, search fields, and stability policy.
- Update `robot-docs schemas --json` so the field summary aligns with the real capabilities object.
- Validate real capabilities output against the capabilities schema in tests.

## Risks

- Required schema fields should only be added for fields runtime already emits. v0.28 does not require speculative future fields.
- `capabilities` should remain a discovery surface, not a replacement for detailed command docs.
- Schema tightening should not change command behavior.

## Source Reuse Boundary

No external source code is copied. This phase reuses ThreadVault's schema system and borrows only interface-shape lessons from mature robot-friendly CLIs.

