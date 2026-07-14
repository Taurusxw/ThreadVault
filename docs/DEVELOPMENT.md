# Development

This document records the current local development workflow for ThreadVault.

## Environment

- Python 3.11 or newer is supported.
- The current Windows development command examples use Python 3.12 through the `py` launcher.
- The project is installed in editable mode for local development.
- Use the project `.venv` so unrelated global Python packages do not affect validation.
- The primary local UI is the Python stdlib Tkinter desktop app in `desktop_app.py`.
- The former personal Web UI CLI entrypoints, launcher, runtime module, active schemas, tests, and active discovery metadata are removed from the package; v4 records remain under `docs/progress/archive/legacy-v4/`.

## Install

```powershell
cd <repo-root>
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pip check
```

Use the console script:

```powershell
threadvault --help
```

Do not use `py -3.12 -m threadvault`; the package does not define `threadvault.__main__`.

## Common Checks

Run these before finishing broad code changes:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest
```

Focused checks for native desktop work:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_v407_desktop_app.py -q
.\.venv\Scripts\threadvault.exe desktop smoke --json
```

Useful smoke checks:

```powershell
threadvault capabilities --json
threadvault robot-docs schemas --json
threadvault mcp manifest --json
threadvault desktop smoke --json
```

Codex integration checks:

```powershell
threadvault codex-hook config --db data\threadvault.db --json
threadvault codex-hook install --db data\threadvault.db --json
codex mcp list
```

The hook installer is dry-run-first. For a real installation, pass an absolute `.venv\Scripts\threadvault.exe` command plus `--apply`; then review/trust the user hook through Codex `/hooks`. Do not replace Codex's existing `notify` command. Applied hooks use the turn's `transcript_path` and must remain targeted rather than scanning the entire Codex home.

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

## Native UI QA

For non-trivial UI behavior, verify the rendered app, not only Python tests.

Minimum UI smoke path:

1. Run `threadvault desktop smoke --json`.
2. Launch `threadvault desktop launch` or `.\启动ThreadVault桌面版.cmd`.
3. Confirm recent sessions show title, project, time, event count, and warning badge without exposing UUIDs as the main label.
4. Open Backup Center and confirm status, automatic schedule, next run, disk estimate, and one-click action are visible.
5. Generate an export preview; verify “确认导出” is disabled before a valid preview and invalidated after any export parameter changes.
6. Confirm restore defaults to a new database filename and write-like actions still require native confirmation.
7. Open Health and verify the read-only summary loads automatically while maintenance remains visually secondary.

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
## Storage And Schema Validation

For storage/schema work run:

```powershell
py -3.12 -m pytest tests/test_v220_storage_lifecycle.py -q
py -3.12 -m pytest tests/test_v230_smart_backup.py -q
threadvault storage verify --db data\threadvault.db --deep --json
threadvault storage auto --db data\threadvault.db --json
threadvault doctor --db data\threadvault.db --json
```

Do not test a migration by rewriting the live archive. Create a verified SQLite snapshot, rebuild to a separate DB/cold root, compare counts and canonical conversation digest, then activate with a reversible rename.
