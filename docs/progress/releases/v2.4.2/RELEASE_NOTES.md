# ThreadVault v2.4.2 Release Notes

## Summary

ThreadVault `2.4.2` is a release-engineering hotfix for the v2.4.1 foolproof archive release. It makes CLI content tests independent of the ANSI styling that Rich forces when `GITHUB_ACTIONS=true`, so the Windows Python 3.11/3.12 matrix tests behavior rather than escape-code placement.

No archive schema, storage policy, Hook, MCP, desktop workflow, or JSON contract changes are included. All v2.4.1 source catch-up, backup completeness, Codex integration, desktop, and CI improvements remain intact.

## Upgrade

```powershell
py -3.12 -m pip install -e ".[dev]"
py -3.12 -m pip check
```

## Validation

- The four CLI content cases that failed only under GitHub's forced-color host flag pass with deterministic `CliRunner` environment isolation.
- Real `desktop smoke --json` and MCP manifest steps still run under the native GitHub Actions environment.
- Full Windows Python 3.11/3.12 release-matrix results are recorded in `ACCEPTANCE.md`.

## Compatibility

- Python 3.11 or newer.
- Database schema v8; no migration required.
