# ThreadVault v1.0.0 Release Notes

## Summary

ThreadVault `1.0.0` makes the native Tkinter desktop app the primary local interface and completes the retirement of the browser Web UI from the active package.

This release remains local-first and privacy-first. It does not require a hosted server, browser runtime, WebView, Electron, React, Tauri, cloud sync, or external model calls.

## Highlights

- Promoted the package version to `1.0.0`.
- Kept `threadvault desktop launch` as the primary local UI command.
- Kept `threadvault desktop smoke --json` as the non-window desktop verification command.
- Removed the active `threadvault.personal_ui` runtime module.
- Removed active `personal_ui_health`, `personal_ui_action`, and `personal_ui_smoke` schema registrations and generated schema artifacts.
- Removed active Web UI runtime tests.
- Preserved historical Web UI evidence under `docs/progress/archive/legacy-v4/`.
- Kept former Web UI commands in retired metadata only.

## Upgrade Notes

Install or refresh the editable package:

```powershell
py -3.12 -m pip install -e ".[dev]"
```

Verify the version and primary desktop interface:

```powershell
py -3.12 -c "import importlib.metadata as m, threadvault; print(threadvault.__version__); print(m.version('threadvault'))"
threadvault capabilities --json
threadvault desktop smoke --json
```

## Compatibility Notes

- `threadvault ui serve` and `threadvault ui smoke` remain retired and are not active CLI commands.
- `threadvault.personal_ui` is no longer importable in the active package.
- `personal_ui_*` JSON schemas are no longer active contracts.
- Historical v4 Web UI docs are archive evidence, not live API guidance.

## Validation

Release validation is recorded in `docs/progress/releases/v1.0.0/ACCEPTANCE.md`.
