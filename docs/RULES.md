# Rules

This document records ThreadVault project rules that supplement the global Codex rules and `AGENTS.md`.

## Code Rules

- Keep the existing Python package layout under `src/threadvault`.
- Prefer small changes that reuse `ArchiveStore`, CLI helpers, schema contracts, and governance helpers.
- Do not duplicate parser, database, export, retrieval, or privacy logic in UI/client code.
- Do not introduce a frontend framework or build pipeline for the personal UI unless explicitly requested.
- Preserve local-first and privacy-first defaults.
- Keep confirmation and preview gates enforced by backend safety rules; frontend UI should make the same gates clear to users.
- Use existing JSON contracts and schema helpers for machine-facing payloads.

## Data And Privacy Rules

- Treat raw transcript files, archive databases, backups, exports, audit logs, and QA screenshots as potentially private.
- Do not upload or transmit raw session data by default.
- Keep the archive database separate from generated export folders.
- Do not make external model calls the default summary path.
- Do not enable vector indexing by default; it is config-gated derived data.
- Do not imply team/cloud enforcement is active just because governance diagnostics exist.

## UI Safety Rules

- Export writes must require a matching preview state before `preview_accepted` is sent.
- Restore, vacuum, reindex, and schema write operations must require explicit confirmation.
- Prune operations must stay dry-run by default and require confirmation/apply for destructive cleanup.
- Running actions must show progress feedback.
- Completed actions must show a stable completed state and must not keep loading spinners active.
- Locked write buttons should explain why they are locked instead of silently doing nothing.
- The right-side JSON panel should preserve raw machine output; user-facing summaries belong in the main UI.
- Basic mode should keep the daily workflow simple; pro mode can expose advanced controls.

## Documentation Rules

- Keep standard documents listed in `docs/DOC_INDEX.md` current.
- New development traces belong under `docs/progress/rounds/`.
- Use `CONTEXT.md` for canonical terminology.
- Use `docs/KNOWLEDGE_GRAPH.md` for domain relationships, write paths, and safety boundaries.
- Do not create new lowercase `plan.md`, `design-notes.md`, `acceptance.md`, or similar active files.
- Existing lowercase phase files under `docs/progress/archive/legacy-v*` are preserved archive records.
- Do not recreate `docs/v0` through `docs/v4` or `docs/development-progress.md`.

## Versioning Rules

- The active package version lives in `pyproject.toml`, `src/threadvault/__init__.py`, and the README current-version line.
- Substantive optimization or development changes may advance the package version in the same round.
- Use patch bumps for narrow fixes, minor bumps for user-visible capability or runtime-contract improvements, and reserve major version changes for planned milestone lines.
- Every version bump must have a dated `docs/CHANGELOG.md` entry and a round record under `docs/progress/rounds/`.
- Historical milestone lines are preserved as v0 through v4 records under `docs/progress/archive/legacy-v*`; do not recreate old active version directories.

## Validation Rules

- Run focused tests for the changed surface.
- For UI changes, include rendered behavior validation when practical.
- For JavaScript/localization changes, run `node --check` against served English and Chinese JS assets when practical.
- For schema contract changes, regenerate and validate schema artifacts.
- Be honest about commands that were not run or checks that remain risky.
