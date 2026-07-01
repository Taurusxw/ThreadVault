# v3 Phase 32 Design Notes: Business Command Governance Instrumentation

## One Runtime, Many Commands

The deep module is the governance instrumentation runtime. CLI commands should pass command, role, actor, target, and
audit context into one interface instead of duplicating permission and audit logic.

## Explicit But Automatic Once Requested

ThreadVault remains local-first. Governance instrumentation is explicit through `--governance-role` and optional config
or audit-log flags. Once requested, the business command path itself runs preflight before the business action and blocks
denied roles when governance is enabled.

## Existing Preflights Stay Authoritative

Phase 32 should not invent a second policy model. The runtime routes to the operation-specific preflight contracts from
Phases 13-18, then normalizes the result for command callers.

## Side Effects

Side-effecting commands must run instrumentation before writing files or mutating history. Read commands may execute
after allowed instrumentation and include the instrumentation payload in JSON output.

## External Model Boundary

There is no executable external model adapter enabled by default. Phase 32 can count and expose the external model
preflight boundary, but it must not claim external model execution has been implemented.

## Non-Claim

This phase accepts broad local command instrumentation, not production shared server enforcement. Final v3 completion
still requires a dedicated acceptance smoke.
