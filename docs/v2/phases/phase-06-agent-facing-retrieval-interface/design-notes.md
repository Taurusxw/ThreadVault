# Phase 06 Design Notes: Agent-Facing Retrieval Interface

## Design Decision

Phase 06 implements an agent-facing retrieval interface as a local CLI/module contract instead of a full MCP server runtime.

The roadmap asks for "MCP or agent-facing retrieval interface." A deep module plus JSON CLI commands satisfies the agent-facing part now and gives a later MCP adapter a clean seam to call. Starting with an MCP server process would introduce deployment, lifecycle, and client-registration complexity before the retrieval interface itself is proven.

## Deep Module Shape

`threadvault.agent_interface` is the new module. Its interface is intentionally small:

- Build a manifest.
- Run a retrieval request.

The implementation can hide:

- Whether results came from FTS-only retrieval or hybrid retrieval.
- How vector status is checked.
- How result metadata is sanitized.
- Which underlying schema names matter to agents.
- How diagnostics are normalized.

This keeps the CLI shallow and makes a future MCP adapter straightforward: call the same module rather than duplicating CLI behavior.

## Mode Strategy

The default agent mode is `hybrid`.

Reasons:

- Hybrid already degrades to FTS-only when vector search is disabled, absent, or empty.
- Agents usually want the best available ranked evidence, not a specific storage implementation.
- FTS remains explicit through `--mode fts` for clients that need the simpler retrieval contract.

`vector` is not a standalone agent mode in this phase because direct vector querying lacks the same fallback guarantees and would force clients to understand vector config state.

## Privacy Strategy

Default agent output should be useful but conservative:

- Include stable IDs, source, score, text, evidence event IDs, and ranking diagnostics.
- Omit raw local path fields by default.
- Include mode/config/index diagnostics at a high level.
- Add `--local-debug` for local-only inspection of metadata already exposed by lower-level commands.

This follows the v2 roadmap requirement that agent-facing interfaces do not expose private raw paths or transcript content unless the user explicitly requests local debug mode.

## Relationship To Existing Interfaces

The new interface does not replace:

- `threadvault retrieval query`
- `threadvault retrieval hybrid`
- `threadvault vector status`
- `threadvault robot-docs`
- `threadvault capabilities`

Instead, it composes them into a smaller agent-oriented entrypoint.

## Deferred Work

- MCP server adapter that maps MCP tool calls to `threadvault.agent_interface`.
- Richer request body input from JSON files or stdin.
- More advanced result redaction policies.
- Agent query templates or saved profiles.
- External embedding providers.

## Compatibility Notes

- No database schema changes.
- No package version bump.
- No change to existing retrieval or hybrid contract versions.
- New contracts are additive.
- The root `deep-research-report.md` remains retired.
