# Phase 03 / v2.2: Summary Evidence Chunk Selection

## Summary

This phase adds the v2.2 bridge between the existing evidence-backed summary work and future optional semantic retrieval. The roadmap says vector retrieval should not embed every raw event by default. Instead, ThreadVault should prefer turn summaries, session summaries, project summary blocks, and high-value evidence chunks.

Phase 03 implements that selection layer without creating embeddings, adding a vector database, calling an external model, or changing the archive schema. The output is a stable JSON contract that future vector adapters can consume.

## Source Of Truth Read Before This Phase

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v2-retrieval-and-interfaces.md`
- `docs/v2/README.md`
- `docs/development-progress.md`
- Existing code:
  - `src/threadvault/summarizer.py`
  - `src/threadvault/export_targets.py`
  - `src/threadvault/database.py`
  - `src/threadvault/retrieval.py`

The active v2 roadmap is `docs/roadmap/v2-retrieval-and-interfaces.md`. The older goal text mentions `docs/roadmap/v2-personal-knowledge-layer.md` and `docs/v0-v1/`; those paths do not exist in the current repository. Phase 03 continues to use the current `docs/v0/`, `docs/v1/`, and `docs/v2/` structure.

## Current Baseline

- `threadvault.retrieval` provides an FTS-backed query interface and diagnostics.
- `threadvault.summarizer` builds local deterministic `Summary` objects with evidence event IDs.
- `export-target obsidian` and `export-target skill` already write selected evidence pages.
- There is no reusable chunk-selection interface for future embeddings.
- There is no JSON schema for selected summary/evidence chunks.

## Goals

- Add a `Summary Pipeline` module that selects durable chunks for future retrieval adapters.
- Produce deterministic chunk IDs and stable JSON.
- Select only high-value material:
  - session summary chunks.
  - turn summary chunks.
  - evidence chunks linked to summary/evidence event IDs.
- Preserve event traceability through `evidence_event_ids`.
- Support explicit session selection and project selection.
- Add CLI access for agents and future tools.
- Add schema discovery and generated schema artifacts.
- Keep all work local and deterministic.

## Non-Goals

- Do not compute embeddings.
- Do not add a vector database.
- Do not add semantic search mode.
- Do not add hybrid ranking.
- Do not call external LLMs or embedding providers.
- Do not vectorize all raw events.
- Do not change SQLite schema, package version, backup manifest version, restore records, or global JSON contract version.
- Do not change existing `summarize`, `search`, or `retrieval query` contracts.

## Public Interface Plan

### Summary Pipeline Module

Add a new module:

```python
threadvault.summary_pipeline
```

Tentative interface:

```python
SummaryChunkRequest(
    session_ids: list[str],
    project: str | None,
    max_chunks_per_session: int,
    max_chars: int,
)

build_summary_chunks(conn, request) -> dict
```

The module owns:

- archive selection for session/project inputs.
- summary construction through existing `build_summary`.
- chunk ID generation.
- chunk text shaping.
- evidence event ID propagation.
- chunk-selection diagnostics.

### Chunk Contract

Add a schema named:

- `summary_chunks`

Top-level payload:

- `contract_version`
- `selection`
- `chunks`
- `skipped`
- `diagnostics`

Each chunk:

- `chunk_id`
- `chunk_type`
- `session_id`
- `turn_index`
- `text`
- `text_chars`
- `evidence_event_ids`
- `metadata`

Chunk types in this phase:

- `session_summary`
- `turn_summary`
- `evidence`

### CLI

Add a command group:

```powershell
threadvault summary-pipeline chunks --session SESSION_ID --json
threadvault summary-pipeline chunks --project E:\Codex\ThreadVault --json
```

Options:

- repeated `--session`
- optional `--project`
- `--max-chunks-per-session`
- `--max-chars`
- `--json`

At least one `--session` or `--project` is required.

### Capabilities And Robot Docs

Advertise:

- command: `summary-pipeline`
- JSON output: `summary-pipeline chunks`
- feature flag: `summary_evidence_chunks: true`
- schema: `summary_chunks`
- pipeline contract version.

## Selection Rules

The first implementation should be deterministic and conservative:

1. Build one `session_summary` chunk from the existing `Summary` object.
2. Build turn-level chunks from events grouped by `turn_index`.
3. Build evidence chunks from summary evidence event IDs and obvious high-value events:
   - user messages.
   - function calls.
   - function call outputs containing problem/failure text.
   - assistant final messages.
4. Stop at `max_chunks_per_session`.
5. Trim chunk text at `max_chars`.
6. Do not include raw event payload JSON.
7. Do not include all raw events by default.

## Architecture Notes

This is a deep module phase:

- Callers learn one interface: `build_summary_chunks`.
- The implementation hides session selection, event grouping, summary shaping, evidence selection, and trimming.
- Future vector adapters should consume the output instead of duplicating chunk-selection logic.

## Acceptance Criteria

- `threadvault summary-pipeline chunks --session sess-current --json` emits a stable object payload.
- Payload validates against `summary_chunks`.
- Payload includes at least one `session_summary` chunk and evidence-backed chunks for fixture data.
- Every emitted chunk has at least one evidence event ID.
- `--project` selection works with fixture project cwd.
- Unknown session IDs are reported in `skipped`.
- `capabilities --json` advertises the command, JSON output, and feature flag.
- `robot-docs guide --json` advertises the summary pipeline schema.
- Existing retrieval and search tests still pass.

## Validation Plan

```powershell
py -3.12 -m pytest tests\test_v203_summary_evidence_chunks.py
threadvault schemas write --out docs\schemas --json
py -3.12 -m ruff check .
py -3.12 -m pytest
threadvault summary-pipeline chunks --session sess-current --json
threadvault summary-pipeline chunks --project E:\Codex\ThreadVault --json
threadvault capabilities --json
threadvault schemas list --json
threadvault summary-pipeline --help
threadvault summary-pipeline chunks --help
Test-Path deep-research-report.md
py -3.12 -c "import threadvault, importlib.metadata as m; print(threadvault.__version__); print(m.version('threadvault'))"
```

## Risks

- If this module exports too much raw event text, it could undermine the roadmap's decision not to vectorize all raw events. The implementation should trim text and select only high-value events.
- If vector-specific fields are added now, the interface may overfit an adapter that does not exist yet. This phase should emit provider-neutral chunks only.
- If selection is spread across export targets, future retrieval adapters will duplicate logic. The module should be the reusable seam.

## Next Phase

After this phase, v2 can add a local vector adapter behind an explicit configuration gate. That later phase should consume `summary_chunks` output instead of scanning raw events directly.
