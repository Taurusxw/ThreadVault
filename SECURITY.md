# Security Policy

ThreadVault is a local-first archive and retrieval tool for Codex session transcripts. It is designed to keep transcript data, archive databases, backups, and generated exports on the user's machine by default.

## Supported Versions

Security reports should target the current public release line:

| Version | Supported |
|---|---|
| `0.34.x` | Yes |

## Reporting A Vulnerability

Please report security issues privately through GitHub Security Advisories for this repository when available. If advisories are unavailable, open a minimal GitHub issue that does not include secrets, raw transcript content, database files, local paths, or private logs.

Include:

- A short description of the issue.
- Affected command, API, UI action, or MCP tool.
- Minimal reproduction steps using synthetic data.
- Whether the issue can expose raw transcripts, local paths, generated exports, backups, or credentials.

Do not attach real `data/*.db`, backup files, `threadvault-ui-output/`, `.codex` transcripts, `.env` files, or generated vault exports.

## Local Data Boundary

ThreadVault intentionally ignores local archive databases, generated exports, backups, environment files, and cache/build artifacts. Treat any file produced by export, backup, restore, UI QA, or MCP preview workflows as private until reviewed.
