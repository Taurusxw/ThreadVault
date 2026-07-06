# v4 Phase 04 Plan: UI Action Coverage

## Status

Planned after Phase 03.

## Goal

Implement the complete UI action registry and wire every required Personal Web UI capability to existing ThreadVault
modules.

## Scope

- Add a centralized action registry behind `POST /api/action`.
- Cover every action family in the Phase 01 coverage matrix.
- Normalize action results, errors, confirmation failures, and JSON payload display.
- Preserve existing v1/v2/v3 behavior and contracts.

## Initial Action Names

```text
init
import
ingest_queue_enqueue
ingest_queue_list
ingest_queue_process
summarize
privacy_scan
export_session
export_target_markdown
export_target_obsidian
export_target_skill
config_init
config_show
config_doctor
reindex
vacuum
backup
backup_verify
restore_plan
restore_apply
schema_list
schema_show
schema_write
validate_json
vector_status
vector_index
vector_query
governance_status
governance_v3_gap_audit
governance_v3_acceptance_smoke
governance_preflight
governance_instrumentation
```

This list can expand during implementation, but each addition must map to an existing ThreadVault module or accepted
contract.

## Dangerous Operation Rules

- `restore_apply` requires `confirm=true`.
- `vacuum` requires `confirm=true`.
- `reindex` requires `confirm=true`.
- `schema_write` requires `confirm=true`.
- `export_*` actions require preview availability before execution.
- `backup` can execute directly but must show the target path.
- Prune/delete apply actions default to dry-run and require confirmation for apply.

## Non-Scope

- No new parser.
- No new retrieval engine.
- No new export implementation.
- No alternate privacy scanner.
- No default external model calls, cloud sync, public server, or team enforcement.

## Acceptance Criteria

- Unknown actions are rejected with structured JSON.
- All required action families have registry entries or documented deferrals.
- Dangerous actions are blocked without confirmation.
- Export preview remains no-write.
- Focused tests cover each safety rule and representative successful actions.
- Capabilities and robot docs are updated if the registry becomes a public interface in this phase.

