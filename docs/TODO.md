# TODO

## Current Follow-Up Items

| Priority | Item | Notes |
|---|---|---|
| Medium | Stabilize browser QA around JavaScript confirmation dialogs | Browser plugin automation can be interrupted by native confirm dialogs; independent Chrome/Playwright may be better for full visual QA. |
| Medium | Replace broad Chinese `.replace(...)` localization | Current additive Chinese asset generation is tested but fragile because broad replacements can mutate identifiers. Prefer a structured translation table. |
| Medium | Add safe "open export directory" UX | Users need a clearer bridge from "导出已写入" to the actual folder. Design as local-only and avoid unsafe arbitrary path opening. |
| Low | Expand visual QA checklist into standard release artifact | Keep under `docs/progress/releases/` only when preparing a release. |

## Completed In Current Rounds

- Session detail preview mapping.
- Export preview state gate.
- Chinese UI localization hardening.
- JavaScript asset syntax checks.
- Local export and backup write verification.
- Completed-state spinner fix.
- Basic/pro mode documentation.
- Archive database vs export directory explanation.
- Full knowledge graph expansion.
- Standard documentation completeness pass.
- Legacy documentation migration to `docs/progress/archive/` after user confirmation.
- Generated output policy: `.gitignore` excludes `threadvault-ui-output/`, `threadvault-ui-backups/`, `exports/`, `backups/`, `data/`, local database files, and `.env` files.
