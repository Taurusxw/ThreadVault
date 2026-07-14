# ThreadVault v2.4.0 Release Acceptance

## Scope

This release accepts the complete personal-only 2.4.0 baseline: automatic ingestion, current Codex parser compatibility, read-only MCP, schema-v8 hot/cold storage, smart backups, and the native desktop workflow.

Included:

- Active v2.0 through v2.4 code, tests, schemas, docs, ADRs, rounds, and release records.
- Standalone English and Simplified Chinese project manuals with reciprocal language links.
- Package version `2.4.0`, tag `v2.4.0`, and GitHub Release notes.

Excluded:

- Local databases, cold blobs, transcript JSONL files, backups, exports, environment files, and screenshots.
- Hosted services, cloud sync, team mode, central governance, and browser-first workflows.
- History rewriting or deletion of archived v0-v4 documentation evidence.

## Acceptance Gates

- Source and installed package metadata report `2.4.0`.
- Full pytest and full-project ruff pass.
- `pip check` reports no broken requirements.
- Capabilities validate against the packaged JSON Schema.
- Desktop smoke returns `desktop_smoke.v2`, `ok=true`, and no browser/server requirement.
- MCP manifest reports version 2.4.0 and only read-only tools.
- Live doctor reports schema v8, matching events/FTS counts, and no required maintenance.
- Rendered Windows QA covers friendly sessions, Backup Center, export gating, and automatic health diagnosis.
- README language links and documented local paths resolve correctly.
- Secret/private-path/risky-artifact scans find no release-blocking tracked material.
- `git diff --check` passes apart from expected Windows line-ending notices.

## Validation Commands

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\threadvault.exe desktop smoke --db data\threadvault.db --json
.\.venv\Scripts\threadvault.exe mcp manifest --json
.\.venv\Scripts\threadvault.exe doctor --db data\threadvault.db --json
git diff --check
```

## Results

- Full pytest: `295 passed`.
- Full ruff: passed.
- Dependency check: no broken requirements.
- Source and installed metadata: `2.4.0`.
- Capabilities JSON Schema: valid.
- Desktop smoke: `desktop_smoke.v2`, `ok=true`.
- MCP manifest: version 2.4.0, six read-only tools.
- Live doctor: schema v8; 342 sessions; 835,177 events; seven known incomplete-call warnings; FTS 835,177/835,177; no maintenance suggestion.
- Rendered Windows QA: passed for the primary desktop workflows.
- English and Simplified Chinese README files: reciprocal links resolve, Markdown fence counts are balanced, and referenced local documentation exists.
- Public-release hygiene: the public repository remains MIT-licensed; no release-blocking secret, machine-specific active-document path, risky tracked artifact, or oversized untracked file was found.

## Residual Risks

- Tkinter's Windows accessibility tree exposes panes more reliably than all child control names. Keyboard focus, visible labels, and shortcuts are present; a full NVDA narration pass remains a non-blocking follow-up.
- A safe “open export directory” action is not included; the app displays the output and manifest paths instead.
- Historical documentation intentionally contains retired architecture and old-version terminology.

## Status

completed
