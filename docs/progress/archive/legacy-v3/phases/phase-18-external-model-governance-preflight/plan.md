# v3 Phase 18 Plan: External Model Governance Preflight

## Status

Planned on 2026-07-01.

## Goal

Add `threadvault governance preflight external-model --json` as an explicit preflight interface for future external model
adapter calls before any external summarization, embedding, or enrichment adapter is implemented or wired into business
commands.

This phase makes the opt-in boundary concrete: clients and future server mode can ask what governance would require for
an external model call without sending prompts, transcript text, embeddings, metadata, or any outbound payload.

## Source Documents

This plan is based on:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v3-clients-and-team-governance.md`
- `docs/v2/README.md`
- `docs/v2/phases/phase-07-v2-acceptance-smoke/v2-acceptance.md`
- `docs/v3/README.md`
- `docs/v3/phases/phase-10-governance-enforcement-gap-audit/gap-audit.md`
- `docs/v3/phases/phase-12-governance-policy-readiness/acceptance.md`
- `docs/v3/phases/phase-17-export-preview-governance-preflight/acceptance.md`
- `docs/development-progress.md`

## In Scope

- Add a governance preflight command for future external model adapter calls.
- Add CLI command:
  - `threadvault governance preflight external-model`
- Add JSON schema:
  - `governance_external_model_preflight`
- Reuse Phase 10 command inventory to recognize:
  - `external model adapters`
- Reuse Phase 09 permission logic and Phase 11 enforcement dry-run logic.
- Report outbound data, redaction, evidence-validation, consent, audit, and opt-in expectations for future execution.
- Support optional explicit audit logging for the preflight event itself.
- Regenerate packaged schema artifacts.
- Update capabilities and robot docs discovery.
- Add focused tests for allowed, blocked, unknown/out-of-scope command, optional audit, discovery, and docs.
- Update acceptance documentation and `docs/development-progress.md`.

## Out Of Scope

- Implementing external LLM, embedding, summarization, or enrichment adapters.
- Calling network services or sending any outbound payload.
- Returning model responses, embeddings, generated summaries, or provider metadata.
- Automatically enforcing permissions inside existing business commands.
- Automatically writing audit records from existing business commands.
- Changing retrieval, hybrid retrieval, vector indexing, summary pipeline, or agent-facing retrieval behavior.
- Implementing server runtime, centralized policy storage, identity providers, centralized audit, or cloud sync.

## Interface Shape

`governance_external_model_preflight` includes:

- `contract_version`
- `request`
- `scope`
- `command_policy`
- `permission`
- `enforcement`
- `outbound_policy`
- `audit`
- `execution`
- `diagnostics`

Expected CLI shape:

```powershell
threadvault governance preflight external-model --command "external model adapters" --role reviewer --json
```

Optional audit logging:

```powershell
threadvault governance preflight external-model --command "external model adapters" --role reader --audit-log audit.jsonl --json
```

## Acceptance Criteria

- The preflight command validates against `governance_external_model_preflight`.
- `external model adapters` resolves to the Phase 10 inventory.
- Unknown or out-of-scope commands return structured diagnostics.
- The payload distinguishes `would_allow` from future `would_block_if_enforced`.
- Outbound-data, redaction, evidence-validation, consent, and audit expectations are visible for future execution.
- Optional audit logging records only the preflight event.
- The payload always reports:
  - `business_command_executed = false`
  - `external_call_executed = false`
  - `payload_sent = false`
  - `model_response_returned = false`
  - `provider_metadata_returned = false`
- Discovery surfaces advertise `governance_external_model_preflight`.
- Existing commands remain unmodified and unenforced.
- `deep-research-report.md` remains absent.
