# ADR 0001: Keep The Active Runtime Personal-Only

- Status: Accepted
- Date: 2026-07-13
- Decision owners: ThreadVault maintainer

## Context

ThreadVault is used as one person's local Codex archive. The previous v3 work introduced governance diagnostics, identity/permission contracts, central policy/audit/backup previews, and a shared read-only HTTP server prototype. Those surfaces increased core module size and produced contradictory discovery state without serving the current product goal.

## Decision

The active 2.x runtime is personal-only:

- remove team mode, governance commands/contracts/config, and the shared HTTP server;
- keep the native Tkinter app as the primary local interface;
- keep MCP as a local read-only stdio interface over an existing database;
- retain personal safety gates: privacy scan, export preview, explicit confirmation, backup verification, and conservative restore;
- preserve v3/v4 historical records under `docs/progress/archive/` as evidence, not active capability claims.

## Consequences

- The removal is a breaking public-contract change and requires package version `2.0.0`.
- Core modules and discovery payloads become smaller and internally consistent.
- ThreadVault does not provide authenticated identity, team permissions, central policy/audit, or remote/shared service semantics.
- Reintroducing shared/team behavior requires an explicit new product decision and must not bypass the personal safety model.

## Rejected Alternatives

- Keep dormant governance behind flags: rejected because it preserves maintenance cost and ambiguous contracts.
- Keep only the shared HTTP prototype: rejected because local MCP stdio already covers the supported agent-integration need with a smaller privacy surface.
