# v4 Phase 03 Plan: Personal UI Workbench

## Status

Planned after Phase 02.

## Goal

Turn the static shell into a usable single-page local workbench. The UI should be plain, dense, and complete enough for
personal daily use.

## Scope

- Build a static HTML/CSS/JS workbench served by Phase 02.
- Use native browser controls: forms, buttons, selects, tables, textareas, and `details`/`summary`.
- Provide a left navigation, top search/status bar, main work area, and right JSON output panel.
- Make every API response inspectable in the JSON panel.

## Required Views

- Archive: session list, cwd/project filter, updated time, event count, warning count.
- Search: standard search, retrieval query, hybrid retrieval, and agent retrieve modes.
- Session: summary, event preview, evidence event IDs, export entrypoints.
- Export: export preview, privacy mode, markdown/obsidian/skill/session export actions.
- Privacy: privacy scan, warnings, and config/allowlist hints.
- Maintenance: stats, doctor, self-test, reindex, vacuum.
- Backup/Restore: backup, verify, history, restore plan, restore.
- Config: init, show, doctor.
- Schemas: list, show, validate, write.
- Governance: personal status, v3 gap audit, v3 acceptance smoke, advanced diagnostics.

## Non-Scope

- No marketing page.
- No complex visual design system.
- No React/Vite/Node.
- No desktop wrapper.
- No team/cloud/login behavior.

## UI Principles

- First screen is the workbench.
- Make task state explicit: pending, running, ok, blocked, failed.
- Keep raw JSON visible because ThreadVault's public contracts are JSON-first.
- Use plain, accessible controls over custom widgets.
- Advanced Governance diagnostics should be available but folded away from the personal default path.

## Acceptance Criteria

- The app loads from `threadvault ui serve`.
- Navigation can switch between all required view families.
- Search opens results and JSON.
- Session detail shows summary, event previews, and evidence IDs.
- Export preview is visible before export actions.
- Dangerous controls display confirmation requirements.
- Layout is usable at common desktop widths without overlapping controls.
