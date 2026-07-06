# Phase 28 Design Notes - Identity Actor Binding Runtime

## Decision

Implement a local static actor binding runtime before centralized policy or audit storage.

This gives v3 a real actor-to-role resolution interface while preserving local-first defaults. The local static map is not
a final team identity provider, but it is a concrete adapter-shaped runtime that future server, policy, and audit modules
can call.

## Module Interface

The public interface is intentionally narrow:

- resolve an actor against local config;
- validate mapped roles against the existing governance role vocabulary;
- return request attribution and provenance;
- optionally write local audit evidence.

The implementation stays in the governance module for now because it directly depends on existing roles, audit records,
and governance diagnostics. A future central identity adapter can replace the static config source behind the same payload
shape.

## Config Shape

The local config remains optional:

```toml
[governance]
enabled = true

[governance.identity]
actors = [
  { id = "reviewer@example", display = "Reviewer", roles = ["reviewer"], source = "local-static" },
]
```

No config means no actor binding is available, but the CLI remains safe and usable.

## Boundary

This phase should remove the "identity actor binding missing" blocker, but it must not claim:

- central policy readiness;
- central audit readiness;
- shared deployment readiness;
- broad command instrumentation readiness.

The accepted local actor binding runtime is a prerequisite for those later phases.

## Privacy And Local-First Defaults

Actor maps are local config. ThreadVault does not upload actor identifiers or require a server. JSON output may include
the actor id requested by the user; it does not expose raw transcript content or local file paths.
