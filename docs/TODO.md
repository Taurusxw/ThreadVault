# TODO

## Current Follow-Up Items

| Priority | Item | Notes |
|---|---|---|
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
- Retired active Web UI runtime, schemas, and tests for the 1.0.0 native desktop release.
- Removed the remaining active Web UI launcher, readiness test, and retired discovery metadata for the 1.0.1 cleanup.
- Prepared the v1.0.0 release documentation and acceptance gate.
- Generated output policy: `.gitignore` excludes `threadvault-ui-output/`, `threadvault-ui-backups/`, `exports/`, `backups/`, `data/`, local database files, and `.env` files.
