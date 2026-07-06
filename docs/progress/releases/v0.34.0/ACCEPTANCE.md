# ThreadVault v0.34.0 Release Acceptance

## Scope

This release accepts the current `0.34.0` runtime and documentation state for public GitHub release.

Included:

- MCP stdio server runtime.
- MCP manifest and schema.
- MCP integration guide.
- Community and security files.
- Local artifact ignore guardrails.
- Migrated progress archive structure.

Excluded:

- Generated local export output.
- Local backups.
- Local SQLite archive databases.
- Real Codex transcript files.
- Git history rewriting.

## Validation

```powershell
threadvault mcp manifest --json
py -3.12 -m ruff check .
py -3.12 -m pytest
git diff --check
```

Results:

- `threadvault mcp manifest --json` passed and emitted `threadvault_mcp_manifest.v1` for version `0.34.0`.
- `py -3.12 -m ruff check .` passed.
- `py -3.12 -m pytest` passed: `421 passed in 76.39s`.
- `git diff --check` passed; only Windows line-ending warnings were reported.
- `.gitignore` verification confirmed local output, backup, database, export, and `.env` files are ignored.
- Secret scan hits were classified as synthetic fixtures, scanner source code, or documentation guidance, not real credentials.

## Public Release Checks

- MIT license exists and is detected by GitHub.
- Repository visibility is public.
- `SECURITY.md` exists.
- `CONTRIBUTING.md` exists.
- `.env.example` exists.
- `.gitignore` excludes local databases, generated exports, backups, and environment files.
- MCP export preview remains read-only.

## Residual Risks

- Historical Git commits may still contain a legacy DOCX planning artifact. This release removes it from the current tree but does not rewrite history.
- Historical archive records may intentionally contain local example paths as evidence. They should be treated as documentation examples, not secrets.
- ZCode configuration UI details may change; `docs/MCP_INTEGRATION.md` documents stable stdio command intent instead of guessing UI names.

## Status

completed
