# Contributing

Thank you for helping improve ThreadVault.

## Development Setup

Use Python 3.11 or newer:

```powershell
py -3.12 -m pip install -e ".[dev]"
```

Run the main checks before submitting changes:

```powershell
py -3.12 -m ruff check .
py -3.12 -m pytest
```

## Project Rules

Before making changes, read:

- `AGENTS.md`
- `CONTEXT.md`
- `docs/RULES.md`
- `docs/DEVELOPMENT.md`
- `docs/DOC_INDEX.md`

Keep ThreadVault local-first and privacy-first. Do not commit real Codex transcripts, local archive databases, generated exports, backups, `.env` files, or personal workspace output.

## Pull Request Expectations

- Keep changes scoped and explain user-visible behavior.
- Add or update tests for code changes.
- Update docs when commands, config, schemas, MCP tools, UI behavior, or safety boundaries change.
- For versioned runtime changes, update `pyproject.toml`, `src/threadvault/__init__.py`, `README.md`, `docs/CHANGELOG.md`, and the relevant progress record.
- For documentation-only changes, say explicitly when no package version bump is needed.

## Privacy Test Data

Use synthetic fixtures only. If a test needs a secret-looking value, use fake values such as `api_key=supersecrettoken123` and assert that export/privacy behavior handles it correctly.
