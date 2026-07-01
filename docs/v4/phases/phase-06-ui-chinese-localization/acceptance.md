# v4 Phase 06 Acceptance: UI Chinese Localization

## Accepted Scope

Phase 06 accepts an additive Chinese browser UI for the v4 Personal Web UI:

- `/zh`
- `/assets/app.zh.js`
- `threadvault ui serve --lang en|zh`
- focused tests in `tests/test_v406_ui_chinese_localization.py`

## Acceptance Criteria

- English default entrypoint `/` remains English.
- English script `/assets/app.js` remains English.
- Chinese entrypoint `/zh` uses `lang="zh-CN"` and Chinese visible UI text.
- Chinese script `/assets/app.zh.js` contains localized view labels, controls, table headings, empty states, and safety
  hints.
- `--lang zh --open` opens `/zh`.
- Default `--open` still opens `/`.
- API paths, action ids, JSON fields, schemas, database behavior, config behavior, and safety checks remain unchanged.
- `deep-research-report.md` remains absent.

## Validation

Final validation is recorded in `docs/development-progress.md` for this phase.

## Non-Claims

Phase 06 does not replace the English UI, add a new backend, translate machine contracts, or introduce React/Vite/Node.
