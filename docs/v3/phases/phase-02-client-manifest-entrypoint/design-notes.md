# v3 Phase 02 Design Notes: Client Manifest Entrypoint

## Summary

The first v3 client-facing implementation is a manifest, not a UI shell. This gives every later client the same
capability map and keeps the implementation safely on top of accepted v2 interfaces.

## Chosen Interface

`threadvault.client_interface.client_manifest(...)` builds a pure discovery payload from:

- loaded local config.
- `capabilities()`.
- `robot_guide()`.

It does not read the archive database and does not inspect raw Codex transcript files.

## Why This Is Not A Retrieval Facade

Phase 01 rejected a shallow client facade because `threadvault.agent_interface` is already the deep module for search.
Phase 02 keeps that decision: the new manifest tells clients to use `agent retrieve`, `retrieval hybrid`, `export-target`,
and `vector status`; it does not wrap or replace those commands.

## Client Families

The manifest names five families:

- `desktop`
- `ide`
- `web`
- `tui`
- `server`

Only `server` is marked as opt-in and deferred. The other families are planned local clients that can start from CLI JSON
or `ArchiveStore` without requiring shared infrastructure.

## Privacy Defaults

The manifest reports:

- `local_first = true`
- `server_required = false`
- `cloud_sync = false`
- `external_model_calls = false`
- `raw_paths_in_default_output = false`
- `vector_enabled_by_default = false`

These are client-facing assertions, so Phase 02 tests lock them down.

## Deferred Decisions

- Which richer client comes first after the manifest.
- Whether a future desktop/IDE implementation should call CLI JSON or a Python `ArchiveStore` adapter directly.
- How optional server mode will expose this manifest over HTTP while preserving local defaults.
- How team permissions and shared audit should be represented in a future governance manifest.

