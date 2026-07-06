# ThreadVault v0.34.0 Release Notes

## Summary

ThreadVault `0.34.0` adds a read-only MCP stdio server so Codex, OpenCode, ZCode, and other MCP-capable local agents can retrieve local archive context without parsing transcript files themselves.

This release keeps ThreadVault local-first and privacy-first. The first MCP tool set does not write files and does not call external models.

## Highlights

- Added `threadvault mcp manifest --json`.
- Added `threadvault mcp serve`.
- Added read-only MCP tools:
  - `threadvault_capabilities`
  - `threadvault_stats`
  - `threadvault_doctor`
  - `threadvault_retrieve`
  - `threadvault_session`
  - `threadvault_export_preview`
- Added the `mcp_manifest` JSON Schema.
- Added `docs/MCP_INTEGRATION.md` with Codex, OpenCode, ZCode, Obsidian, and AI self-configuration guidance.
- Kept export write flows behind explicit CLI/UI actions; MCP export preview does not write Markdown, Obsidian, or Skill files.

## Open Source Release Notes

- Repository license: MIT.
- Added `SECURITY.md`.
- Added `CONTRIBUTING.md`.
- Added `.env.example`.
- Added `.gitignore` guardrails for local databases, exports, backups, and environment files.

## Safety Boundary

Do not publish local artifacts such as:

- `data/*.db`
- `threadvault-ui-output/`
- `threadvault-ui-backups/`
- `.env` or `.env.*`
- real Codex transcript files
- generated Obsidian vault exports or Skill candidates before review

## Upgrade Notes

Install or refresh the editable package:

```powershell
py -3.12 -m pip install -e ".[dev]"
```

Verify the MCP manifest:

```powershell
threadvault mcp manifest --json
```

## Validation

Release validation is recorded in `docs/progress/releases/v0.34.0/ACCEPTANCE.md`.
