# Rules

This document records ThreadVault project rules that supplement the global Codex rules and `AGENTS.md`.

## Code Rules

- Keep the existing Python package layout under `src/threadvault`.
- Prefer small changes that reuse `ArchiveStore`, CLI helpers, schema contracts, and personal safety helpers.
- Do not duplicate parser, database, export, retrieval, or privacy logic in UI/client code.
- Treat the native Tkinter desktop app as the primary 2.x local interface.
- Do not reintroduce `threadvault ui serve`, browser launchers, Web UI fallback metadata, or browser-first workflows unless explicitly requested.
- Keep `threadvault.personal_ui` and active `personal_ui_*` schemas out of the runtime; use `docs/progress/archive/legacy-v4/` for historical evidence.
- Keep team mode, central governance contracts, `threadvault.governance`, and `threadvault.shared_server` out of the active runtime; use `docs/progress/archive/legacy-v3/` for historical evidence.
- Do not introduce a frontend framework or build pipeline.
- Preserve local-first and privacy-first defaults.
- Keep confirmation and preview gates enforced by backend safety rules; frontend UI should make the same gates clear to users.
- Use existing JSON contracts and schema helpers for machine-facing payloads.

## Data And Privacy Rules

- Treat raw transcript files, archive databases, backups, exports, audit logs, and QA screenshots as potentially private.
- Treat `threadvault-cold` and Evidence/Forensic backups as private transcript evidence.
- Never prune cold data by age alone. Determine reachability from event payload references, preview the reclaimable set, then require explicit `--apply`.
- Automatic backup retention may delete only superseded files below `storage-backups/auto`; it must never delete manual backups or unique live archive content, and every new backup must verify before retention runs.
- Smart backup must reserve free disk space and fail closed when the selected profile cannot fit; it must not silently downgrade the required recovery tier.
- Never rebuild the live archive in place. Use a separate target and validate counts, canonical conversation digest, doctor, FTS, and cold references before switching paths.
- Do not upload or transmit raw session data by default.
- Keep the archive database separate from generated export folders.
- Do not make external model calls the default summary path.
- Do not enable vector indexing by default; it is config-gated derived data.
- Do not present the personal safety gates as team permissions, authenticated identity, or central policy enforcement.

## UI Safety Rules

- Native desktop UI work should go through `desktop_data.py` and existing store/client contracts instead of reading SQLite directly.
- Keep backup policy in `ArchiveStore.storage_auto_backup`; the desktop Backup Center may present it but must not recreate tier, disk, verification, or retention logic.
- Archived Web UI history must not become the default daily entrypoint again.
- Desktop export writes must require a matching immutable preview plan plus explicit native confirmation; CLI export remains an explicit write command.
- Desktop export parameter changes must invalidate the current immutable preview plan before any write can proceed.
- Desktop restore must default to a new collision-free target and refuse overwrite.
- Restore, vacuum, reindex, and schema write operations must require explicit confirmation.
- Prune operations must stay dry-run by default and require confirmation/apply for destructive cleanup.
- Running actions must show progress feedback.
- Completed actions must show a stable completed state and must not keep loading spinners active.
- Locked write buttons should explain why they are locked instead of silently doing nothing.
- CLI JSON should preserve stable machine fields; user-facing summaries belong in the native desktop app.

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
- Use patch bumps for narrow fixes, minor bumps for additive user-visible capability, and major bumps for intentional public-contract removal or milestone lines.
- Every version bump must have a dated `docs/CHANGELOG.md` entry and a round record under `docs/progress/rounds/`.
- Historical milestone lines are preserved as v0 through v4 records under `docs/progress/archive/legacy-v*`; do not recreate old active version directories.

## Validation Rules

- Run focused tests for the changed surface.
- For UI changes, include rendered behavior validation when practical.
- For archived Web UI history, do not revive JavaScript/localization checks unless the user explicitly reopens that legacy line.
- For schema contract changes, regenerate and validate schema artifacts.
- Be honest about commands that were not run or checks that remain risky.
