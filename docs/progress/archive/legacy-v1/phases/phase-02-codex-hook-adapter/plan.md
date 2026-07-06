# Phase 02 / v1.0 Foundation: Codex Hook Adapter

## Goal

Add a Codex Hook-safe adapter that can receive Codex lifecycle hook payloads, enqueue ThreadVault ingestion work, and return a valid hook response without scanning or importing transcripts inside the hook process.

Phase 01 created the persistent ingestion queue. Phase 02 turns that queue into a practical Codex integration point while keeping the same v1 boundary: Hook event capture is lightweight; heavy import work stays in `threadvault ingest-queue process --apply`.

## Source Context

Required context read before this plan:

- `docs/README.md`
- `docs/roadmap/major-version-roadmap.md`
- `docs/roadmap/v1-personal-knowledge-layer.md`
- `docs/v1/README.md`
- `docs/v1/phases/phase-01-ingestion-automation-queue/plan.md`
- `docs/v1/phases/phase-01-ingestion-automation-queue/acceptance.md`
- `docs/v0/README.md`
- `docs/development-progress.md`
- `src/threadvault/ingestion.py`
- `src/threadvault/cli.py`
- `src/threadvault/store.py`
- `src/threadvault/schemas.py`
- `codebase-design` skill guidance for module/interface design
- OpenAI Codex Hooks documentation: `https://developers.openai.com/codex/hooks`

## Official Hook Constraints Used

The Codex Hooks documentation establishes these design constraints:

- Command hooks receive one JSON object on stdin.
- Shared input fields include `session_id`, `transcript_path`, `cwd`, `hook_event_name`, and `model`.
- `Stop` is a turn-scoped event and can be used when a conversation turn stops.
- `Stop` expects JSON on stdout when the hook exits `0`; plain text output is invalid.
- Hook command definitions can live in `hooks.json` or inline `[hooks]` config.
- Practical locations include `~/.codex/hooks.json` and `<repo>/.codex/hooks.json`.
- Multiple matching hooks can run; one hook should not assume it is the only hook.
- Hooks must be reviewed and trusted before non-managed command hooks run.

## Product Boundary

In scope:

- A `Codex Hook Adapter` module that parses hook payload JSON and enqueues ingestion work.
- A CLI command that reads hook JSON from stdin.
- A default hook-compatible stdout shape for Codex.
- An explicit diagnostic JSON mode for tests and troubleshooting.
- A command that emits a sample `hooks.json` snippet for a `Stop` hook.
- JSON schemas for diagnostic outputs.
- Tests for hook-safe behavior, queue integration, schema validation, and docs traceability.

Out of scope:

- Editing `~/.codex/hooks.json` automatically.
- Trusting hooks inside Codex.
- Running imports in the hook process.
- Parsing or copying transcript content from `transcript_path`.
- Blocking Codex turns, adding continuation prompts, or enforcing policy decisions.
- Background daemon installation.
- Obsidian export, Codex Skill generation, vector search, MCP, REST, desktop, or cloud/team features.

## Architecture Decision

### Module

Add a new `threadvault.codex_hooks` module.

External interface:

- `handle_codex_hook_payload(conn, payload, *, codex_home=None, source="codex-hook") -> dict`
- `build_codex_hook_config(command: str, *, timeout=10, status_message=...) -> dict`
- `hook_continue_response() -> dict`

The module should hide:

- event name normalization;
- safe codex home inference;
- queue request construction;
- invalid payload handling;
- hook-compatible response shape.

### Seam

The seam lives between Codex Hook stdin/stdout and ThreadVault ingestion automation.

Codex Hook callers should not need to know how ThreadVault deduplicates queue requests or how later imports run. ThreadVault queue/process callers should not need to know Codex Hook stdout rules.

### Hook Behavior

Default command behavior:

- Read stdin as JSON.
- If valid, enqueue a request into `ingestion_queue`.
- Infer `codex_home` from `transcript_path` when it points under a `sessions` or `archived_sessions` directory.
- If inference is not possible, leave `codex_home` as `None` so later processing uses ThreadVault's default Codex home.
- Return only hook-compatible JSON on stdout.
- Exit `0` even when payload parsing fails, so ThreadVault does not break Codex sessions.

Diagnostic mode:

- With an explicit option, emit ThreadVault diagnostic JSON instead of hook stdout.
- Include whether a request was enqueued, the normalized hook event, inferred codex home, and the hook response.
- Do not include raw transcript content.

### Reason Mapping

Queue `reason` should use the normalized hook event:

- `codex-hook:Stop`
- `codex-hook:SessionStart`
- etc.

For v1 Phase 02, the generated sample config should use `Stop`.

## CLI Shape

Add a new Typer group:

```powershell
threadvault codex-hook ingest
threadvault codex-hook ingest --diagnostic-json
threadvault codex-hook config --json
```

Hook command example:

```powershell
threadvault codex-hook ingest --db E:\Codex\ThreadVault\data\threadvault.db
```

Generated `hooks.json` shape should be compatible with the official three-level structure:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "threadvault codex-hook ingest",
            "timeout": 10,
            "statusMessage": "Queueing ThreadVault ingestion"
          }
        ]
      }
    ]
  }
}
```

The config command only prints a snippet. It must not write user or repo Codex config files.

## JSON Contracts

Add schemas:

- `codex_hook_ingest`
- `codex_hook_config`

`codex_hook_ingest` required fields:

- `ok`
- `hook_event_name`
- `codex_home`
- `enqueue`
- `hook_response`

`codex_hook_config` required fields:

- `hooks`

The default hook stdout should not be validated against ThreadVault schemas because it is a Codex hook response, not a ThreadVault diagnostic payload.

## Capabilities

Update `capabilities()` and `robot_schemas()` so agents can discover:

- the new `codex-hook` command group;
- diagnostic JSON outputs;
- the new schemas;
- a feature flag such as `codex_hook_adapter: true`.

Do not change the Python package version in this phase.

## Documentation Updates

Create/update:

- `docs/v1/README.md`
- `docs/v1/phases/phase-02-codex-hook-adapter/plan.md`
- `docs/v1/phases/phase-02-codex-hook-adapter/acceptance.md`
- `docs/development-progress.md`
- `docs/THREADVAULT_USAGE_MANUAL.md`

Optional short navigation updates:

- root `README.md`, only if a compact v1 pointer is useful.

Do not recreate or update `deep-research-report.md`. Do not modify the root DOCX.

## Test Plan

Add focused tests, likely in `tests/test_v102_codex_hook_adapter.py`:

- module handler enqueues from a valid `Stop` payload;
- handler infers `codex_home` from `transcript_path`;
- default CLI stdout is hook-compatible JSON and does not expose ThreadVault diagnostics;
- diagnostic mode validates against `codex_hook_ingest`;
- invalid stdin still returns hook-compatible continue JSON and does not enqueue;
- config command emits a `Stop` hook snippet that points at `threadvault codex-hook ingest`;
- capabilities and schema registry include the new hook adapter entries;
- traceability docs exist.

Regression checks:

```powershell
py -3.12 -m pytest tests\test_v102_codex_hook_adapter.py
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault codex-hook --help
threadvault codex-hook config --json
threadvault capabilities --json
threadvault schemas list --json
```

## Acceptance Criteria

- Codex can call `threadvault codex-hook ingest` with a hook JSON payload on stdin and receive valid JSON on stdout.
- The hook command enqueues ingestion work and does not import transcripts.
- Invalid hook input cannot break the Codex turn.
- A user can generate a sample `hooks.json` snippet for `Stop`.
- Existing v0 and v1 Phase 01 commands remain compatible.
- New diagnostic JSON outputs are schema-valid.
- Documentation makes the phase recoverable from `docs/README.md`, `docs/roadmap/`, `docs/v1/`, and `docs/development-progress.md`.

## Open Assumptions

- `Stop` is the first recommended event because it is turn-scoped and matches v1's goal of accumulating Codex activity after work happens.
- Hook config installation and trust review should remain manual for now; automatic writes to Codex config would need separate user confirmation and cross-platform safety design.
- The hook adapter may store local `codex_home` metadata in ThreadVault's local database, consistent with existing backup and restore metadata behavior.
