# v3 Phase 08 Design Notes: Local Audit Log Workflow

## Explicit Before Automatic

This phase provides explicit audit commands before automatic instrumentation. Later phases can wire sensitive operations
to the same append helper, but Phase 08 should not alter existing command behavior.

## Append-Only JSONL

The local log is JSONL so records can be appended safely and inspected with ordinary local tools. The implementation
should never rewrite valid existing records during append. Listing may tolerate malformed lines and report them as
warnings.

## Privacy Boundary

Audit records should capture operation metadata, not raw transcript content. `target_id` and `metadata` are caller
provided, so clients should avoid placing secrets or raw transcript text there.

## Governance Boundary

This phase does not enforce roles or access levels. It gives later permission and server phases a durable local record
format and command contract to reuse.

## Local-First Boundary

The audit log is local-only by default. No server, cloud sync, or external model call is required.
