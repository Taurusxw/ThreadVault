# Phase 02 Design Notes: Retrieval Contracts And Diagnostics

## Decision: Add A New v2 Retrieval Object Contract

`threadvault search --json` remains an array because that is the established v0/v1 machine contract:

```json
[
  {"event_id": 1, "session_id": "sess-current"}
]
```

The v2 retrieval interface needs richer metadata:

- which mode was requested.
- which mode was used.
- which engine produced the results.
- whether fallback behavior occurred.
- whether the local FTS index appears healthy.
- what filters shaped the result set.

Adding those fields directly to `search --json` would break the old array contract. Therefore Phase 02 adds:

```powershell
threadvault retrieval query QUERY --json
threadvault retrieval diagnose --json
```

## Decision: Diagnostics Belong In The Retrieval Module

The CLI should not infer retrieval internals. The `Retrieval` module already owns:

- mode validation.
- FTS adapter selection.
- quoted retry fallback for awkward input.
- result construction.

So the same module should also own the diagnostics that explain those behaviors. This keeps future MCP, REST, and GUI clients from re-implementing command-specific explanations.

## Decision: Report Index Health Without Raw Local Paths

The diagnostics can report:

- event count.
- FTS row count.
- whether counts match.

They should not report raw transcript paths or raw event payloads. That keeps the v2 interface useful for agents while preserving the local-first/privacy-first posture.

## Deferred Scope

The following are deliberately deferred:

- semantic mode.
- vector adapter.
- hybrid ranking.
- embedding configuration.
- MCP server.
- REST server.
- desktop or IDE clients.

The diagnostics shape should leave room for those future modes, but Phase 02 must not pretend they exist.
