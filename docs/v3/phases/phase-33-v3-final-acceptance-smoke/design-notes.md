# v3 Phase 33 Design Notes: v3 Final Acceptance Smoke

## Acceptance As A Runtime Interface

The final smoke should be a small runtime interface, not only a checklist in prose. This keeps final v3 acceptance
testable by callers, tests, and future maintainers through the same seam.

## Evidence, Not New Product Surface

Phase 33 gathers evidence from accepted modules:

- v2 retrieval and agent-facing interfaces
- v3 client manifest, workflows, and local TUI runtime
- opt-in read-only server prototype
- governance preflights and business-command instrumentation
- identity, policy, audit, and backup/restore policy runtimes
- discovery and schema registries

It should add only the minimal smoke wrapper and final gap-audit status transition.

## Local-First Boundaries

The smoke must prove that local CLI use does not require server or cloud. Optional shared/server checks should run
in-process or as manifest/smoke calls without binding public network sockets.

## Shared Enforcement Non-Claim

The final v3 result can accept optional local/shared-readiness primitives and a read-only prototype. It must not claim
production-grade shared enforcement, authenticated external identity, or external model execution.

## Failure Shape

Each smoke check should report:

- code
- ok
- category
- evidence
- required
- message

This makes future regressions easier to locate without relying on a long hand-run transcript.
