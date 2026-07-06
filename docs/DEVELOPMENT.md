# Development

This document records the current local development workflow for ThreadVault.

## Environment

- Python 3.11 or newer is supported.
- The current Windows development command examples use Python 3.12 through the `py` launcher.
- The project is installed in editable mode for local development.
- The personal Web UI is served by Python stdlib HTTP code in `personal_ui.py`; there is no required Node/Vite/React build pipeline.

## Install

```powershell
cd <repo-root>
py -3.12 -m pip install -e ".[dev]"
```

Use the console script:

```powershell
threadvault --help
```

Do not use `py -3.12 -m threadvault`; the package does not define `threadvault.__main__`.

## Common Checks

Run these before finishing broad code changes:

```powershell
py -3.12 -m ruff check .
py -3.12 -m pytest
```

Focused checks for personal UI work:

```powershell
py -3.12 -m pytest tests/test_v402_local_ui_server.py tests/test_v403_personal_ui_workbench.py tests/test_v404_ui_action_coverage.py tests/test_v405_v4_acceptance_smoke.py tests/test_v406_ui_chinese_localization.py -q
```

Focused checks for documentation-only changes:

```powershell
py -3.12 -m pytest tests/test_v401_personal_ui_readiness.py tests/test_v403_personal_ui_workbench.py -q
```

Useful smoke checks:

```powershell
threadvault capabilities --json
threadvault robot-docs schemas --json
threadvault mcp manifest --json
threadvault ui smoke --json
```

## Local Personal UI

Start the Chinese personal UI locally with the launcher:

```powershell
.\启动ThreadVault中文界面.cmd
```

Or start it through the CLI:

```powershell
threadvault ui serve --lang zh --host 127.0.0.1 --port 8766 --open
```

Health check:

```powershell
Invoke-WebRequest -Uri http://127.0.0.1:8766/api/health -UseBasicParsing
```

Expected paths:

- `paths.db_path`: the archive database, usually `<repo-root>\data\threadvault.db` in this checkout.
- `paths.default_export_dir`: the UI default export folder, currently resolved from `threadvault-ui-output`.

Archive DB override order is `--db`, `THREADVAULT_DB`, `[storage].archive_db`, then the project-local `data/threadvault.db`.

## JavaScript Asset Checks

The UI JavaScript is embedded in Python strings and served as static assets. When changing UI JS or Chinese localization:

1. Serve or extract both English and Chinese JS assets.
2. Run:

```powershell
node --check <served-app.js>
node --check <served-app.zh.js>
```

3. Run the localization tests:

```powershell
py -3.12 -m pytest tests/test_v406_ui_chinese_localization.py -q
```

## Browser QA

For non-trivial UI behavior, verify the rendered app, not only Python tests.

Minimum UI smoke path:

1. Open `http://127.0.0.1:8766/zh`.
2. Confirm the top bar shows both the archive DB path and export folder path.
3. Switch between ordinary and pro mode.
4. Search or open a recent session.
5. Generate an export preview.
6. Confirm the matching write action unlocks.
7. Write an export and verify the completion activity stops spinning.
8. Confirm console errors are absent or explained.

Screenshots and generated QA exports may contain private data. Keep them local and do not treat them as public artifacts.

## Documentation Workflow

For each development round:

- Update `docs/CHANGELOG.md` when user-visible behavior or documented capabilities change.
- Update `docs/PROGRESS.md` when current status, validation, or risks change.
- Add or update one file in `docs/progress/rounds/`.
- Update `docs/DOC_INDEX.md` when documentation files are added, moved, or retired.
- Update `CONTEXT.md` when domain terminology changes.
- Update `docs/KNOWLEDGE_GRAPH.md` when an entity, relationship, write path, or safety boundary changes.

Legacy `docs/v0` through `docs/v4` records were migrated after user confirmation to `docs/progress/archive/legacy-v0` through `docs/progress/archive/legacy-v4`. Do not recreate the old directories for new work.

## Output Directories

Local generated directories such as these may contain private data:

```text
threadvault-ui-output/
threadvault-ui-backups/
```

Before committing or sharing, inspect whether they are intended artifacts or local QA output.

## Git Hygiene

- Do not revert unrelated user changes.
- Keep changes scoped to the current task.
- Prefer focused tests matching the changed surface.
- Do not stage generated private outputs unless explicitly requested.
