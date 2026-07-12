# ThreadVault v1.0.1 Release Notes

## Summary

ThreadVault `1.0.1` completes the active-tree cleanup after the native desktop `1.0.0` release. The native Tkinter app is now the only active local UI path advertised by current launchers, tests, capabilities, robot docs, and user documentation.

Historical Web UI evidence remains preserved under `docs/progress/archive/legacy-v4/`.

## Highlights

- Removed the obsolete `启动ThreadVault中文界面.cmd` launcher.
- Removed the legacy Web UI readiness test from the active suite.
- Removed retired Web UI commands, feature flags, and interface records from capability and robot-guide discovery.
- Kept `threadvault desktop launch` as the primary local UI command.
- Kept `threadvault desktop smoke --json` as the non-window desktop verification command.
- Updated active documentation to describe the native desktop app as the only current local UI path.

## Upgrade Notes

Install or refresh the editable package:

```powershell
py -3.12 -m pip install -e ".[dev]"
```

Verify the version and primary interface:

```powershell
py -3.12 -c "import importlib.metadata as m, threadvault; print(threadvault.__version__); print(m.version('threadvault'))"
threadvault capabilities --json
threadvault desktop smoke --json
```

## Compatibility Notes

- The deleted Chinese Web UI launcher is no longer available as a redirect to the desktop launcher; use `启动ThreadVault桌面版.cmd` or `threadvault desktop launch` directly.
- Consumers should no longer expect retired Web UI keys in `capabilities()` or `robot_guide()` output.
- Historical v4 Web UI records remain archive evidence, not live API guidance.

## Validation

Release validation is recorded in `docs/progress/releases/v1.0.1/ACCEPTANCE.md`.
