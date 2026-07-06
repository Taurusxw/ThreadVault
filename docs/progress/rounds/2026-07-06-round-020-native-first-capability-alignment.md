# 2026-07-06 Round 020 - Native-First Capability Alignment

## Status

completed

## Goal

Move ThreadVault closer to the 1.0.0 local-native application line by making native desktop the discoverable primary interface and demoting the browser Web UI to legacy fallback in runtime metadata and active docs.

## Background

The native desktop app and launcher already exist, but capabilities, robot docs, project rules, and some active documentation still treated the browser Web UI as a first-class daily path. That contradicted the 1.0.0 direction: smallest local app, fastest startup path, minimal UI, no browser dependency, and modular code suitable for future interfaces.

## Scope

- Runtime capability discovery and robot docs.
- Project rules and active documentation.
- Focused discovery/desktop tests.
- Package version metadata.

Out of scope:

- Deleting `personal_ui.py`.
- Removing `threadvault ui serve` or `threadvault ui smoke`.
- Final `1.0.0` release bump.

## Implementation Steps

1. Added a capabilities `interface_policy` declaring `native_desktop` as the primary local interface.
2. Bumped the base capabilities/robot schema contract marker from `0.6` to `0.7`.
3. Added native desktop and legacy Web UI status flags to feature discovery.
4. Moved Web UI commands from robot-doc recommended commands into `legacy_fallback_commands`.
5. Updated CLI help text to label Web UI commands as legacy fallback while keeping compatibility.
6. Updated tests to prove native-first discovery and legacy fallback status.
7. Updated active project docs and package version metadata.

## Key Decisions

- Keep the Web UI command surface available for compatibility/debugging until a later release gate explicitly removes or archives it.
- Use `desktop_data.py` as the desktop-facing seam so the Tkinter UI remains thin and future interfaces can reuse store/client contracts.
- Bump to `0.48.0`, not `1.0.0`, because full Web UI removal/parity closure is not yet complete.

## Change List

- `src/threadvault/store.py`
- `src/threadvault/schemas.py`
- `src/threadvault/cli.py`
- `src/threadvault/__init__.py`
- `pyproject.toml`
- `docs/schemas/capabilities.schema.json`
- `tests/test_v28_capabilities_schema_contract.py`
- `tests/test_v402_local_ui_server.py`
- `tests/test_v407_desktop_app.py`
- `AGENTS.md`
- `README.md`
- `docs/RULES.md`
- `docs/DEVELOPMENT.md`
- `docs/API.md`
- `docs/ARCHITECTURE.md`
- `docs/KNOWLEDGE_GRAPH.md`
- `docs/THREADVAULT_USAGE_MANUAL.md`
- `docs/CHANGELOG.md`
- `docs/DOC_INDEX.md`
- `docs/PROGRESS.md`
- `docs/TODO.md`

## Tests And Verification

```powershell
py -3.12 -m pytest tests\test_v28_capabilities_schema_contract.py tests\test_v401_personal_ui_readiness.py tests\test_v402_local_ui_server.py tests\test_v403_personal_ui_workbench.py tests\test_v406_ui_chinese_localization.py tests\test_v407_desktop_app.py tests\test_v105_codex_skill_target.py -q
py -3.12 -m ruff check src\threadvault\store.py src\threadvault\schemas.py src\threadvault\cli.py tests\test_v28_capabilities_schema_contract.py tests\test_v402_local_ui_server.py tests\test_v407_desktop_app.py
threadvault capabilities --json
threadvault robot-docs guide --json
py -3.12 -c "import importlib.metadata as m, threadvault; print(threadvault.__version__); print(m.version('threadvault'))"
```

Result: `51 passed`; focused ruff passed; CLI smoke confirmed native desktop primary discovery and Web UI legacy fallback commands; source and installed metadata both report `0.48.0`.

Note: `py -3.12 -m pip install -e ".[dev]"` reported a Windows lock on `threadvault.exe` during script replacement, but the final metadata check still reports `0.48.0` for both source and installed package metadata.

## Documentation Updates

- README current version and native-first status.
- Project AGENTS and rules to mark native desktop as primary for 1.0.0.
- Architecture, API, development, knowledge graph, and usage docs.
- Changelog, progress overview, TODO, and document index.

## Risks And Follow-Up

- Web UI code, schemas, tests, and commands still exist as a legacy fallback.
- Final 1.0.0 completion still needs a parity/removal decision for `personal_ui.py`, `ui serve`, `ui smoke`, and Web UI-only tests.
- Governance/audit write operations and overwrite restore remain command-based unless a later native confirmation design admits them into the desktop UI.

## Next Step

Perform the final 1.0.0 Web UI retirement audit: identify which Web UI surfaces can be deleted, which must stay as CLI/contracts, and which tests/docs should move to legacy archive evidence.
