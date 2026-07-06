# ThreadVault v1.0.0 Release Acceptance

## Scope

This release accepts ThreadVault `1.0.0` as the native desktop primary local-interface release.

Included:

- Native Tkinter desktop app as the primary local interface.
- Desktop smoke command.
- Web UI command retirement.
- Active Web UI runtime/schema/test removal.
- MCP stdio read-only integration.
- Existing local archive, retrieval, export, privacy, backup/restore, and governance surfaces.

Excluded:

- Git history rewriting.
- Hosted server deployment.
- Cloud sync.
- External model calls by default.
- Reintroducing browser-first workflows.

## Acceptance Gates

- Package metadata reports `1.0.0`.
- Capabilities and robot docs report `native_desktop` as primary.
- `threadvault ui serve` and `threadvault ui smoke` are absent from active CLI help.
- `threadvault.personal_ui` is absent from the active package.
- `personal_ui_health`, `personal_ui_action`, and `personal_ui_smoke` are absent from active schema discovery.
- Desktop smoke passes without opening a browser or server.
- Release docs exist under `docs/progress/releases/v1.0.0/`.

## Validation

```powershell
py -3.12 -m py_compile src\threadvault\store.py src\threadvault\schemas.py src\threadvault\cli.py src\threadvault\desktop_data.py src\threadvault\desktop_app.py
py -3.12 -m pytest tests\test_v28_capabilities_schema_contract.py tests\test_v401_personal_ui_readiness.py tests\test_v407_desktop_app.py tests\test_v105_codex_skill_target.py -q
py -3.12 -m ruff check src\threadvault\store.py src\threadvault\schemas.py src\threadvault\cli.py src\threadvault\desktop_data.py src\threadvault\desktop_app.py tests\test_v28_capabilities_schema_contract.py tests\test_v401_personal_ui_readiness.py tests\test_v407_desktop_app.py tests\test_v105_codex_skill_target.py
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault capabilities --json
threadvault robot-docs guide --json
threadvault schemas list --json
threadvault desktop smoke --json
py -3.12 -c "import importlib.metadata as m, importlib.util, threadvault; print(threadvault.__version__); print(m.version('threadvault')); print(importlib.util.find_spec('threadvault.personal_ui'))"
git diff --check
```

Results:

- `py_compile` passed for touched runtime modules.
- Focused release tests passed: `28 passed`.
- Focused ruff passed.
- Full test suite passed: `400 passed in 58.78s`.
- Full ruff passed.
- `threadvault capabilities --json` passed and reported `contract_version = 1.0`, `primary_local_interface = native_desktop`, and retired Web UI archive metadata.
- `threadvault robot-docs guide --json` passed and reported the removed Web UI runtime under `retired_interfaces.personal_web_ui`.
- `threadvault schemas list --json` passed and omitted `personal_ui_health`, `personal_ui_action`, and `personal_ui_smoke`.
- `threadvault desktop smoke --json` passed with `ok = true`, `browser_required = false`, and `server_required = false`.
- Version metadata reported `threadvault.__version__ = 1.0.0`, installed metadata `1.0.0`, and `threadvault.personal_ui` import spec `None`.
- CLI help confirmed there is no active `ui` command.
- `git diff --check` passed; Git only reported Windows line-ending normalization warnings.

Environment notes:

- `py -3.12 -m pip install -e ".[dev]"` built `threadvault-1.0.0` but initially failed while replacing `Scripts\threadvault.exe` because Windows reported the file was in use. A subsequent direct `threadvault capabilities --json` and `threadvault desktop smoke --json` both passed.
- `py -3.12 -m pip check` failed due existing unrelated environment issues: invalid `~hreadvault` distribution warning and missing dependencies for Selenium/Trio/wsproto. ThreadVault's own required dependencies were present.

## Residual Risks

- Historical Git commits may still contain a legacy DOCX planning artifact; this release does not rewrite history.
- Local generated output, database, backup, audit, and export directories may contain private data and should stay local.
- Some low-frequency write workflows remain CLI-first until the native UI has complete confirmation and target-path gates.

## Status

completed
