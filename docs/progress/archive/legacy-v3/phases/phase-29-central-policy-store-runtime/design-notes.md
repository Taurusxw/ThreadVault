# v3 Phase 29 Design Notes: Central Policy Store Runtime

## Local File First

The first accepted central policy store is a local JSON file. This is deliberately smaller than a server/database store,
but it gives v3 a real versioned policy document, provenance fields, and actor-to-role resolution without breaking
local-first defaults.

## Store Runtime Is Not Team Enforcement

Loading and resolving a central policy document is a prerequisite for shared enforcement. It does not mean existing
business commands automatically enforce that policy, and it does not make the optional read-only server team-ready.

## Policy Vocabulary Reuses Existing Governance Terms

The policy document must use existing ThreadVault role names and access levels. That keeps Phase 29 aligned with the
accepted governance preflight contracts instead of introducing a second policy language.

## Deep Module Seam

The runtime should sit behind a small governance interface that accepts config, optional policy path, actor, and
operation. CLI, store methods, readiness reports, schemas, and future server adapters should reuse this interface
instead of duplicating parsing and validation.

## Opt-In Boundaries

The config path is optional and governance remains disabled by default. Missing central policy must not block ordinary
local CLI workflows.
