# ADR 0002: Hot/Cold Archive Storage

Status: accepted
Date: 2026-07-14

## Context

The local archive exceeded 5 GiB because raw compacted history, tool output, telemetry, embedded images, and repeated conversation bodies all lived in one SQLite file. Daily retrieval needs canonical conversation and a clean index; it does not need every bulky payload on every read.

## Decision

- Keep canonical human conversation, event identity, compact metadata, and `indexed_text` in the hot SQLite database.
- Store reversible bulky evidence as immutable SHA-256-addressed blobs in a sibling cold directory.
- Replace low-value telemetry with an auditable hash/size stub.
- Remove an `event_msg/agent_message` body only when it exactly matches a canonical assistant/developer response in the same session.
- Preserve unique messages and quarantine unknown payloads in cold storage.
- Use copy-on-write rebuilds with count, canonical conversation digest, doctor, FTS, and cold-reference acceptance gates.
- Provide Core (hot DB), Evidence (hot DB + cold blobs), and Forensic (Evidence + source JSONL) backup profiles.
- Expose one smart backup entrypoint that bootstraps Evidence, selects only the highest due changed tier, verifies before retention, reserves disk space, and keeps bounded automatic generations without touching manual backups.
- Garbage-collect cold data only by reference reachability and only after an explicit apply action.

## Consequences

Daily search uses a much smaller database and backups can match recovery needs. Routine users no longer need to choose a profile manually, while explicit profile commands remain available. Full evidence remains local and recoverable, but moving a live archive now requires moving both the DB and its cold directory unless only Core recovery is desired. Forensic completeness still depends on retaining or backing up source JSONL.
