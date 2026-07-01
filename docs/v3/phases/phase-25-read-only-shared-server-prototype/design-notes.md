# v3 Phase 25 Design Notes: Read-Only Shared Server Prototype

## Interface Placement

The new module seam is `threadvault.shared_server`. The interface is intentionally small:

- build a route manifest
- handle one read-only request in process
- build a stdlib HTTP server for explicit runtime use

This keeps server behavior behind one module while allowing tests to verify route behavior without running a long-lived
process.

## Dependency Decision

The current project dependencies do not include FastAPI, Starlette, Uvicorn, or another web framework. Phase 25 therefore
uses Python stdlib HTTP server primitives for the prototype instead of introducing a new mandatory runtime dependency.

This is a prototype boundary, not a long-term framework decision. A later phase may replace the runtime adapter if the
server grows beyond a narrow read-only surface.

## Read-Only Route Boundary

The accepted route surface is limited to:

- `/health`
- `/manifest`
- `/client/manifest`
- `/client/overview`
- `/agent/retrieve`
- `/governance/status`
- `/governance/server/policy-readiness`

No route writes files, appends audit records, exports archives, restores backups, mutates retention history, or calls
external models.

## Opt-In Boundary

The server is not available by default and is not required for local CLI workflows. The manifest and smoke commands are
safe discovery/read-only commands. The runtime start command requires explicit `--enable` before binding a socket.

## Deferred Items

- Identity and actor binding remain readiness-only after Phase 25.
- Central policy, audit, and backup stores remain readiness-only after Phase 25.
- Automatic governance instrumentation remains a later phase.
- Final v3 acceptance smoke remains a later phase.
