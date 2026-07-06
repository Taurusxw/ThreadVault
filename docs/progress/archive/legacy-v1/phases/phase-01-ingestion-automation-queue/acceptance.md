# Phase 01 Acceptance: Ingestion Automation Queue

## Scope

This acceptance covers the first v1 ingestion automation foundation. It verifies that queue requests can be recorded without importing transcripts, inspected later, and explicitly processed through the existing import path.

## Evidence

- `threadvault ingest-queue enqueue` records pending ingestion work.
- `threadvault ingest-queue list` reports queued work.
- `threadvault ingest-queue process` is dry-run by default.
- `threadvault ingest-queue process --apply` imports fixture Codex sessions through the existing importer.
- `capabilities --json` advertises the new command group and `ingestion_queue` feature flag.
- `schemas list --json` includes `ingestion_enqueue`, `ingestion_queue_list`, and `ingestion_process`.
- `docs/v1/README.md` and this phase plan preserve v1 traceability.

## Validation Commands

```powershell
py -3.12 -m pytest tests\test_v101_ingestion_queue.py
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault ingest-queue --help
threadvault capabilities --json
threadvault schemas list --json
```

## Result

Passed on 2026-07-01.

- `py -3.12 -m pytest tests\test_v101_ingestion_queue.py` -> 6 passed
- `py -3.12 -m pytest` -> 144 passed
- `py -3.12 -m ruff check .` -> passed
- `threadvault ingest-queue --help` -> passed and listed `enqueue`, `list`, and `process`
- `threadvault capabilities --json` -> passed and advertised `ingest-queue` plus `ingestion_queue: true`
- `threadvault schemas list --json` -> passed and listed the three ingestion queue schemas

The phase is accepted as the v1 ingestion automation queue foundation. Hook installation and event-specific Hook payload adapters remain separate future work.
