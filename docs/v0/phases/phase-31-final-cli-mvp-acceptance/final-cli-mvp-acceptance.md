# ThreadVault v0.31 Final CLI MVP Acceptance

## Summary

Final CLI/data-layer acceptance passed.

This acceptance used only local fixture transcripts under `tests/fixtures/codex_home`; it did not scan or copy real private Codex transcripts. The command chain covered import, list, search, summarize, multi-format export, privacy scan/redaction, stats, doctor, self-test, reindex, backup, manifest verification, restore preflight, restore apply, and restore history.

## Result

- Overall: passed
- Fixture sessions imported: 4
- Events imported: 28
- Parse warnings recorded: 7
- Search hits for `pytest`: 3
- Summary evidence IDs: 6
- Privacy findings: 3
- Reindex count: `events=28`, `events_fts=28`
- Restore history records: 1

## Commands Covered

| Command Area | Result |
|---|---|
| `threadvault import --codex-home tests/fixtures/codex_home --db <tmp.db> --json` | passed |
| `threadvault list --db <tmp.db> --json` | passed |
| `threadvault search pytest --db <tmp.db> --json --fields minimal` | passed |
| `threadvault summarize --session sess-current --db <tmp.db> --json` | passed |
| `threadvault export --session sess-current --format md/json/jsonl/csv` | passed |
| `threadvault privacy-scan --session sess-privacy --json` | passed |
| `threadvault export --session sess-privacy --privacy-mode redact --json` | passed |
| `threadvault stats --db <tmp.db> --json` | passed |
| `threadvault doctor --db <tmp.db> --codex-home tests/fixtures/codex_home --json` | passed |
| `threadvault self-test --db <tmp.db> --json` | passed |
| `threadvault reindex --db <tmp.db> --fts-only --json` | passed |
| `threadvault backup --db <tmp.db> --out <tmp-backups> --json` | passed |
| `threadvault backup-verify --backup <backup.db> --manifest --json` | passed |
| `threadvault backup-manifest --backup <backup.db> --json` | passed |
| `threadvault restore-plan --backup <backup.db> --target-db <restored.db> --json` | passed |
| `threadvault restore --backup <backup.db> --target-db <restored.db> --apply --restore-history <history.jsonl> --json` | passed |
| `threadvault restore-history list --history <history.jsonl> --json` | passed |

## Schema Validation Covered

Representative JSON payloads were validated with `threadvault validate-json`:

- `search_minimal`
- `privacy_scan`
- `stats`
- `doctor`
- `backup`
- `backup_verify`
- `backup_manifest`
- `restore_plan`
- `restore`
- `restore_history_list`

## Evidence Details

The temporary acceptance workspace was:

```text
C:\Users\Administrator\AppData\Local\Temp\threadvault-v31-1ddcc8d2280b4342b00a7609840d0d07
```

The generated files included:

- `threadvault.db`
- exported `sess-current.md`
- exported `sess-current.json`
- exported `sess-current.jsonl`
- exported `sess-current.csv`
- redacted `sess-privacy.md`
- backup database and manifest
- restored database
- restore history JSONL
- saved JSON payloads used for schema validation

## Conclusion

The ThreadVault CLI/data-layer MVP passes final acceptance for the originally requested local-first Codex session archive scope. Deferred product lines remain out of scope for this acceptance: Web UI, TUI, desktop app, MCP server, REST API, vector database, cloud sync, team permissions, and external LLM automatic summarization.
