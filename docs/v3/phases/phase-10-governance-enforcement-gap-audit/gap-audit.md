# v3 Phase 10 Gap Audit: Governance Enforcement

## Status

Accepted on 2026-07-01.

## Audit Question

Which existing ThreadVault commands should later call permission preflight and audit append before v3 can claim team
governance enforcement?

## Final Conclusion

The highest-priority future enforcement areas are:

- raw transcript or raw local metadata reads.
- export and share workflows.
- delete, prune, retention, backup, and restore workflows.
- external model calls if such adapters are added later.

Phase 10 records the inventory but does not enable enforcement.

The machine-readable command inventory is exposed as `governance_enforcement_gaps.v1` through:

```powershell
threadvault governance enforcement gaps --json
```

The command reported 16 command surfaces. Every record explicitly reports:

- `current_state.automatic_preflight = false`
- `current_state.automatic_audit = false`
- `current_state.enforced = false`

## Command Conclusions

| Command | Operation | Access Level | Audit Required | Future Phase |
|---|---|---|---|---|
| `threadvault client session` | `read_raw_transcript` | `raw_transcript` | Yes | `governance_enforcement_raw_read` |
| `threadvault client warnings` | `read_summary_search` | `summary_search` | No | `governance_enforcement_client_read` |
| `threadvault agent retrieve` | `read_summary_search` | `summary_search` | No | `governance_enforcement_search` |
| `threadvault retrieval query` | `read_summary_search` | `summary_search` | No | `governance_enforcement_search` |
| `threadvault retrieval hybrid` | `read_summary_search` | `summary_search` | No | `governance_enforcement_search` |
| `threadvault export` | `export_archive` | `export` | Yes | `governance_enforcement_export` |
| `threadvault export-target markdown` | `export_archive` | `export` | Yes | `governance_enforcement_export` |
| `threadvault export-target obsidian` | `export_archive` | `export` | Yes | `governance_enforcement_export` |
| `threadvault export-target skill` | `export_archive` | `export` | Yes | `governance_enforcement_export` |
| `threadvault client export-preview` | `export_archive` | `export` | No | `governance_enforcement_export_preview` |
| `threadvault backup` | `export_archive` | `export` | Yes | `governance_enforcement_backup_restore` |
| `threadvault restore` | `restore_backup` | `restore` | Yes | `governance_enforcement_backup_restore` |
| `threadvault restore-history prune` | `delete_or_prune` | `delete_retention` | Yes | `governance_enforcement_retention` |
| `threadvault backup-history prune` | `delete_or_prune` | `delete_retention` | Yes | `governance_enforcement_retention` |
| `threadvault audit-history prune` | `delete_or_prune` | `delete_retention` | Yes | `governance_enforcement_retention` |
| `external model adapters` | `external_model_call` | `export` | Yes | `external_model_policy_adapter` |

## Deferred Decisions

- Permission enforcement remains a later opt-in governance phase.
- Automatic audit writes remain deferred until command-level enforcement decisions are documented.
- External model calls remain disabled by default; the inventory only records the policy seam future adapters must use.
- v2 retrieval, hybrid retrieval, vector adapter, and agent-facing retrieval were not rewritten.
