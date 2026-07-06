# Phase 01 / v1.0 Foundation: Ingestion Automation Queue

## Goal

Create the first v1 `Ingestion Automation` module: a small, Hook-safe queue interface that records local Codex ingest work without running heavy imports inside a Hook process.

This phase begins the v1 personal knowledge layer while preserving the completed `v0.31.0` CLI/data-layer behavior. It does not attempt the whole v1 product in one step. The specific outcome is a reliable queue/process workflow that future Codex Hooks, scheduled scans, and knowledge exports can build on.

## Source Context

Required context read before this plan:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v1-personal-knowledge-layer.md`
- `docs/v0/README.md`
- `docs/development-progress.md`
- `src/threadvault/cli.py`
- `src/threadvault/importer.py`
- `src/threadvault/store.py`
- `src/threadvault/database.py`
- `src/threadvault/schemas.py`
- `codebase-design` skill guidance for deep modules

## Product Boundary

v1 centers on automatic local accumulation plus durable knowledge outputs. This phase only handles the automatic-ingest foundation.

In scope:

- A persistent local queue for ingestion requests.
- Hook-safe request recording.
- Processing queued requests by calling the existing import path.
- Status/listing visibility for users and agents.
- JSON outputs and schema contracts for the new workflow.
- Tests proving queue behavior and CLI behavior.

Out of scope:

- Obsidian vault export.
- Batch export manifests.
- Codex Skill generation.
- Vector search or embeddings.
- MCP, REST, desktop, TUI, or server mode.
- Background daemon installation.
- External LLM summaries.
- Running full transcript imports directly inside a Hook command.

## Architecture Decision

### Module

Add a new `threadvault.ingestion` module.

The module's external interface should be small:

- `enqueue_ingestion(conn, request) -> dict`
- `list_ingestion_queue(conn, status=None, limit=...) -> dict`
- `process_ingestion_queue(conn, codex_home=None, limit=..., apply=False) -> dict`

The implementation may contain dataclasses and helpers internally, but callers should not need to know table details, timestamp generation, deduplication rules, or status transitions.

### Seam

The seam lives between Hook/CLI triggers and the existing import machinery.

Hook-like callers should only enqueue work. The processing command owns expensive import execution and may call the existing importer through the current `ArchiveStore.import_codex()` path or equivalent lower-level function.

### Storage

Use SQLite in the existing ThreadVault database rather than a separate queue file. This keeps queue state co-located with the archive and makes backup/restore behavior naturally include pending work metadata.

Add a table such as `ingestion_queue` through `init_db()` migration:

- `request_id`
- `source`
- `codex_home`
- `reason`
- `status`
- `created_at`
- `updated_at`
- `processed_at`
- `attempts`
- `message`

Statuses:

- `pending`
- `processing`
- `completed`
- `failed`
- `skipped`

Deduplication:

- For this first phase, deduplicate active requests by `(source, codex_home, reason)` while status is `pending` or `processing`.
- If a matching active request exists, return that request with `enqueued: false` and status `skipped` in the command payload.
- Completed and failed historical requests remain visible and do not block new work.

### Processing

`process_ingestion_queue(..., apply=False)` is dry-run by default.

Dry-run behavior:

- Lists pending requests that would be processed.
- Does not call import.
- Does not mutate request status.

Apply behavior:

- Marks each selected pending request as `processing`.
- Runs the existing Codex import path for the request's `codex_home`.
- Marks request `completed` when import returns without raising, even if import stats contain per-file failures.
- Marks request `failed` if the import command itself raises.
- Records import stats or error text in `message`.

The first phase processes requests sequentially. Concurrency control is intentionally minimal because v1 does not yet include a daemon or background worker.

## CLI Shape

Add a new Typer group:

```powershell
threadvault ingest-queue enqueue --source hook --codex-home C:\Users\you\.codex --reason session-stop --json
threadvault ingest-queue list --json
threadvault ingest-queue process --json
threadvault ingest-queue process --apply --json
```

Command behavior:

- `enqueue` initializes the database if needed and records a pending request.
- `list` shows queued request metadata without exposing raw transcript content.
- `process` is dry-run by default and requires `--apply` to run imports.
- Every command supports `--db`.
- Every command supports `--json`.

Human output can be compact Rich tables. JSON is the test and automation surface.

## JSON Contracts

Add schemas:

- `ingestion_enqueue`
- `ingestion_queue_list`
- `ingestion_process`

Required top-level fields:

`ingestion_enqueue`:

- `ok`
- `enqueued`
- `request`

`ingestion_queue_list`:

- `requests`
- `count`

`ingestion_process`:

- `ok`
- `apply`
- `processed`
- `requests`

The schemas should remain append-only and permissive through `additionalProperties: true`, matching existing v0 contract style.

## Capabilities

Update `capabilities()` and `robot_schemas()` so agents can discover:

- the new `ingest-queue` command group;
- the new JSON outputs;
- the new schemas;
- a feature flag such as `ingestion_queue: true`.

Do not change existing schema contract versions unless the project later decides to version the v1 JSON contract separately. This phase should extend the current additive contract.

## Documentation Updates

Create/update:

- `docs/v1/README.md`
- `docs/v1/phases/phase-01-ingestion-automation-queue/plan.md`
- `docs/development-progress.md`

Update only short navigation references elsewhere if needed:

- `docs/README.md`
- root `README.md` if a short v1 active-development pointer is useful

Do not recreate or update `deep-research-report.md`. Do not modify the root DOCX.

## Test Plan

Add focused tests, likely in `tests/test_v101_ingestion_queue.py`:

- enqueue creates a pending request;
- enqueue deduplicates active matching requests;
- list returns queued requests;
- process dry-run does not import or mutate status;
- process `--apply` imports fixture Codex sessions through existing importer;
- queue JSON outputs validate against new schemas;
- traceability docs exist for the v1 phase.

Regression checks:

```powershell
py -3.12 -m pytest tests\test_v101_ingestion_queue.py
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault ingest-queue --help
threadvault capabilities --json
threadvault schemas list --json
```

## Acceptance Criteria

- A user or Hook can enqueue ingestion work without scanning or importing transcripts.
- A user can inspect queued ingestion requests.
- A user can dry-run queued work.
- A user can explicitly process queued work and update the archive.
- Existing v0 CLI commands and tests continue to pass.
- New JSON outputs are schema-valid.
- Documentation makes the phase recoverable from `docs/README.md`, `docs/roadmap/`, `docs/v1/`, and `docs/development-progress.md`.

## Open Assumptions

- Queue entries may include local paths such as `codex_home`; this is local/private metadata, similar to backup manifests and restore history.
- Hook integration itself can be added in a later phase once the queue/process interface is stable.
- Queue retention/pruning is not needed in this first phase; completed/failed request cleanup can be designed after real usage patterns appear.
