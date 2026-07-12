# ThreadVault v1.0.1 Release Acceptance

## Scope

This release accepts ThreadVault `1.0.1` as the Web UI residue cleanup patch for the native desktop `1.0.x` line.

Included:

- Removal of the remaining old Web UI launcher and active readiness test.
- Removal of retired Web UI metadata from current discovery contracts.
- Native desktop-only active UI documentation.
- Preservation of historical Web UI evidence under the legacy archive.

Excluded:

- Git history rewriting.
- Deletion of local generated/private output directories.
- Hosted server deployment or cloud sync.
- Reintroduction of browser-first workflows.

## Acceptance Gates

- Package metadata reports `1.0.1`.
- Capabilities and robot docs report `native_desktop` as primary.
- Active discovery omits retired Web UI commands, flags, and interface records.
- The obsolete Chinese Web UI launcher and readiness test are absent.
- `threadvault.personal_ui` remains absent from the active package.
- Desktop smoke passes without opening a browser or server.
- Full pytest and ruff validation pass.
- Release docs exist under `docs/progress/releases/v1.0.1/`.

## Validation

```powershell
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault capabilities --json
threadvault robot-docs guide --json
threadvault desktop smoke --json
py -3.12 -c "import importlib.metadata as m, importlib.util, threadvault; print(threadvault.__version__); print(m.version('threadvault')); print(importlib.util.find_spec('threadvault.personal_ui'))"
git diff --check
```

Results:

- Full pytest passed: `396 passed`.
- Full ruff passed.
- Capabilities and robot docs reported `native_desktop` without Web UI retired metadata.
- Desktop smoke returned `ok = true`, `browser_required = false`, and `server_required = false`.
- Source and installed package metadata reported `1.0.1`.
- `threadvault.personal_ui` import spec was `None`.
- `git diff --check` passed with only Windows line-ending normalization warnings.

## Residual Risks

- Historical docs and Git history still mention the retired Web UI by design.
- Local generated output, database, backup, audit, and export directories may contain private data and remain outside this release.
- Consumers that depended on retired discovery keys must migrate to the native desktop interface metadata.

## Status

completed
