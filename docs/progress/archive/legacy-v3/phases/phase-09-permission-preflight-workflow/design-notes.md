# v3 Phase 09 Design Notes: Permission Preflight Workflow

## Preflight Before Enforcement

This phase adds explicit permission checks before command enforcement. Existing local CLI commands must continue to work
without governance checks unless a later phase documents and implements enforcement.

## Disabled Means Not Enforced

When governance is disabled, the check still computes `would_allow`, but it does not enforce denial. This preserves the
local-first default while making future team-mode behavior visible.

## Role Vocabulary Reuse

The role and access vocabulary comes from Phase 07. Permission checks should not invent a parallel model.

## Audit Integration

Permission checks can optionally write to the Phase 08 local audit log. This validates that audit records can capture
governance decisions without making all commands write audit records yet.

## Deferred Work

Identity, server-side policy, central audit storage, and automatic command instrumentation remain deferred.
