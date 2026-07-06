# Phase 27 / v0.27 External Review: Retention Schema Contract

## Review Summary

v0.27 tightens existing JSON schemas rather than adding user-facing features. The reference point is ThreadVault's own v0.5/v0.6 contract work and CASS-style robot output, where fields intended for agents should have precise schemas.

## Sources Reviewed

- ThreadVault v0.5 JSON contract: append-only field policy and robot-friendly JSON outputs.
- ThreadVault v0.6 schema commands: packaged JSON schema files and `validate-json`.
- ThreadVault v0.11/v0.19/v0.25 retention config phases: `keep_source` runtime values.
- ThreadVault v0.26 retention helper: centralized `cli|config` keep-source behavior.
- CASS-style robot workflows: stable low-ambiguity fields for automation.

## v0.27 Application

- Require `keep_source` consistently across audit, backup, and restore history prune schemas.
- Restrict `keep_source` to `cli` or `config` everywhere.
- Add tests at the schema seam, not in individual CLI commands.
- Refresh packaged schemas for downstream tools.

## Risks

- Schema tightening can reject previously accepted synthetic payloads. This is acceptable because runtime output already follows the stricter contract.
- Overly broad schemas are easier for humans but less useful for agents; v0.27 favors machine validation for public JSON outputs.

## Source Reuse Boundary

No external source code is copied. The phase reuses ThreadVault's schema infrastructure and borrows only contract design lessons from reviewed systems.

