# Development

This document records the current local development workflow for ThreadVault.

## Environment

- Python 3.11 or newer is supported.
- The current Windows development command examples use Python 3.12 through the `py` launcher.
- The project is installed in editable mode for local development.
- The primary local UI is the Python stdlib Tkinter desktop app in `desktop_app.py`.
- The former personal Web UI CLI entrypoints, runtime module, active schemas, and tests are retired from the 1.0.0 package; v4 records remain under `docs/progress/archive/legacy-v4/`.

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

Focused checks for native desktop work:

```powershell
py -3.12 -m pytest tests/test_v407_desktop_app.py -q
threadvault desktop smoke --json
```

Focused checks for documentation-only changes:

```powershell
py -3.12 -m pytest tests/test_v401_personal_ui_readiness.py -q
```

Useful smoke checks:

```powershell
threadvault capabilities --json
threadvault robot-docs schemas --json
threadvault mcp manifest --json
threadvault desktop smoke --json
```

## Local Desktop UI

Start the primary native desktop UI with the launcher:

```powershell
.\启动ThreadVault桌面版.cmd
```

Or start it through the CLI:

```powershell
threadvault desktop launch
```

Non-window smoke check:

```powershell
threadvault desktop smoke --json
```

## Retired Web UI

The browser UI is no longer an active local interface. The old Chinese launcher redirects to the desktop launcher and must not start `ui serve`:

```powershell
.\启动ThreadVault中文界面.cmd
```

`threadvault ui serve` and `threadvault ui smoke` should stay absent from `threadvault --help`, capabilities, and robot recommended commands.

The retired Web UI runtime module and active `personal_ui_*` JSON schemas are intentionally absent from the 1.0.0 package.

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
