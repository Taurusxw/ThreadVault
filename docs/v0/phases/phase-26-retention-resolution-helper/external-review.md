# Phase 26 / v0.26 External Review: Retention Resolution Helper

## Review Summary

v0.26 is a maintenance phase. The main reference is ThreadVault's own mature retention commands from v0.11, v0.19, and v0.25, plus the CASS-style preference for deterministic JSON provenance fields.

## Sources Reviewed

- ThreadVault v0.11 audit retention config: CLI/config precedence and `keep_source`.
- ThreadVault v0.19 backup retention config: same precedence rule applied to backup files.
- ThreadVault v0.25 restore history retention config: same precedence rule applied to restore history JSONL.
- CASS-style robot workflows: stable machine-readable output and explicit source metadata.
- `codebase-design` skill: extract a module only when it hides repeated complexity behind a small interface.

## v0.26 Application

- Extract only retention keep resolution, not the prune implementations.
- Preserve existing command names, options, exit behavior, and JSON fields.
- Keep config parsing inside `app_config`.
- Keep `keep_source` stable for agents and scripts.

## Risks

- Over-generalizing retention could hide artifact-specific safety rules. v0.26 avoids this by centralizing only keep resolution.
- Error messages are part of CLI ergonomics and tests; helper must preserve exact wording.
- A new helper should improve locality without creating an extra public interface users must learn.

## Source Reuse Boundary

No external source code is copied. This phase reuses ThreadVault's own established behavior and borrows only interface-design principles from reviewed projects.

