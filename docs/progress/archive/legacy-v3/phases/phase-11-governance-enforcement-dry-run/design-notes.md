# v3 Phase 11 Design Notes: Governance Enforcement Dry Run

## Dry Run Before Apply

Phase 11 intentionally stops at dry-run enforcement checks. This gives richer clients, future server mode, and operators a
stable way to ask what would happen before any existing command is wired to block or audit automatically.

## Inventory As Policy Seed

The Phase 10 inventory remains the source for command-to-operation mapping. This avoids scattering command sensitivity
knowledge across CLI handlers.

## Permission Logic Reuse

The dry-run check should reuse the existing role and operation vocabulary from Phase 09. It may call the same permission
decision implementation, but it reports the result as a future enforcement preview.

## Local-First Boundary

The new command is a governance planning tool. It must not require server mode, cloud sync, or external model calls. It
must not rewrite v2 retrieval or bypass privacy-first client/export behavior.

## Audit Boundary

Optional audit logging records the dry-run check itself. It does not imply that the checked command was executed or that
ThreadVault has automatic audit instrumentation for that command.
