# v3 Phase 02 Acceptance: Client Manifest Entrypoint

## Status

Accepted on 2026-07-01.

## Scope

This acceptance covers the first v3 client-facing entrypoint:

- `threadvault client manifest --json`
- `threadvault.client_interface`
- `client_interface_manifest` JSON schema
- discovery updates for capabilities, robot docs, schema registry, and packaged schema artifacts

## Acceptance Evidence

The Phase 02 manifest confirms:

- client families include:
  - `desktop`
  - `ide`
  - `web`
  - `tui`
  - `server`
- server mode is optional, deferred, and not required by default.
- clients are pointed to existing discovery, retrieval, export, vector, and schema entrypoints.
- defaults keep:
  - `local_first = true`
  - `server_required = false`
  - `cloud_sync = false`
  - `external_model_calls = false`
  - `raw_paths_in_default_output = false`
  - `vector_enabled_by_default = false`
- integration policy tells clients not to re-parse Codex transcripts and not to bypass privacy scanning for export.
- governance remains planned rather than silently enabled.

## Validation

Focused validation:

```powershell
py -3.12 -m pytest tests\test_v302_client_manifest.py
py -3.12 -m ruff check src\threadvault\client_interface.py src\threadvault\store.py src\threadvault\cli.py src\threadvault\schemas.py tests\test_v302_client_manifest.py
```

Results:

- `tests\test_v302_client_manifest.py` -> passed.
- Focused ruff -> passed.

Adjacent validation:

```powershell
py -3.12 -m pytest tests\test_v206_agent_interface.py tests\test_v207_v2_acceptance.py tests\test_v301_client_interface_readiness.py tests\test_v302_client_manifest.py
```

Result:

- Adjacent interface validation -> passed.

Manual smoke:

```powershell
threadvault client manifest --json
threadvault schemas list --json
threadvault capabilities --json
Test-Path deep-research-report.md
```

Results:

- `threadvault client manifest --json` -> passed.
- `threadvault schemas list --json` -> passed and listed `client_interface_manifest`.
- `threadvault capabilities --json` -> passed and listed `client` plus `client manifest`.
- `Test-Path deep-research-report.md` -> `False`.

## Result

ThreadVault now has a v3 client-facing manifest that future desktop, IDE, Web, TUI, and optional server clients can use
for capability discovery without duplicating parser or retrieval logic.

## Deferred To Later v3 Phases

- Implement a richer local client.
- Design optional server transport for the same manifest.
- Add team permissions and shared audit enforcement.

