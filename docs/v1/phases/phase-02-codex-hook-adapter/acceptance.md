# Phase 02 Acceptance: Codex Hook Adapter

## Scope

This acceptance covers the v1 Codex Hook adapter. It verifies that ThreadVault can receive Codex hook JSON on stdin, enqueue ingestion work, and return hook-compatible JSON without importing transcript content inside the hook process.

## Evidence

- `threadvault codex-hook ingest` reads hook JSON from stdin.
- Default hook stdout is valid JSON and contains only the hook response.
- `--diagnostic-json` emits ThreadVault diagnostic payloads for troubleshooting.
- Invalid stdin exits successfully and returns a hook continue response without enqueueing work.
- `threadvault codex-hook config --json` emits a sample `Stop` hook snippet.
- `capabilities --json` advertises the `codex-hook` command group and `codex_hook_adapter` feature flag.
- `schemas list --json` includes `codex_hook_ingest` and `codex_hook_config`.
- The hook command does not import sessions; queue processing remains explicit through `threadvault ingest-queue process --apply`.

## Validation Commands

```powershell
py -3.12 -m pytest tests\test_v102_codex_hook_adapter.py
py -3.12 -m pytest
py -3.12 -m ruff check .
threadvault codex-hook --help
threadvault codex-hook config --json
threadvault capabilities --json
threadvault schemas list --json
```

## Result

Passed on 2026-07-01.

- `py -3.12 -m pytest tests\test_v102_codex_hook_adapter.py` -> 9 passed
- `py -3.12 -m pytest` -> 153 passed
- `py -3.12 -m ruff check .` -> passed
- `threadvault codex-hook --help` -> passed and listed `ingest` and `config`
- `threadvault codex-hook config --json` -> passed and emitted a `Stop` hook snippet
- `threadvault capabilities --json` -> passed and advertised `codex-hook` plus `codex_hook_adapter: true`
- `threadvault schemas list --json` -> passed and listed `codex_hook_ingest` and `codex_hook_config`

The phase is accepted as the v1 Codex Hook adapter foundation. Automatic hook installation/trust and scheduled queue processing remain separate future work.
