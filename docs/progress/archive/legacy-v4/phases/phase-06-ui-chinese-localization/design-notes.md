# v4 Phase 06 Design Notes: UI Chinese Localization

## Localization Interface

Phase 06 keeps the accepted English UI as the source baseline and adds a second static resource pair for Chinese:

- `INDEX_HTML_ZH`
- `APP_JS_ZH`

The server module remains deep at the existing Personal UI seam. Browser language selection changes only which static
HTML and JavaScript files are served; all behavior still crosses the same `/api/*` read routes and `/api/action`
registry.

## Boundary Decisions

- English remains default at `/` and `/assets/app.js`.
- Chinese lives at `/zh` and `/assets/app.zh.js`.
- CSS stays shared through `/assets/app.css`.
- `threadvault ui serve --lang en|zh` controls only the browser URL used by `--open`.
- Action ids such as `restore_apply`, API paths, JSON schema names, JSON fields, and CLI commands remain English for
  compatibility with existing tests, agents, and scripts.

## Safety Boundary

No safety behavior moved into the localized JavaScript. Dangerous actions still rely on the existing action registry
confirmation checks:

- `restore_apply`
- `vacuum`
- `reindex`
- `schema_write`

The Chinese UI can display localized warnings, but the backend remains the authority for confirmation and preview
requirements.

## Non-Claims

Phase 06 is not a full i18n framework. It does not add runtime language switching, translated machine contracts, a
frontend build step, a public server mode, accounts, cloud sync, or team collaboration.
