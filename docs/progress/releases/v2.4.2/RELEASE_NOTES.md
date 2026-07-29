# ThreadVault v2.4.2 Release Notes

## Summary

ThreadVault `2.4.2` is a compatibility hotfix for the v2.4.1 foolproof archive release. It bounds Typer below 0.27 because the newly released Typer 0.27.0 changed CLI behavior on Python 3.11, one of ThreadVault's declared supported runtimes.

No archive schema, storage policy, Hook, MCP, desktop workflow, or JSON contract changes are included. All v2.4.1 source catch-up, backup completeness, Codex integration, desktop, and CI improvements remain intact.

## Upgrade

```powershell
py -3.12 -m pip install -e ".[dev]"
py -3.12 -m pip check
```

## Validation

- The four CLI cases that failed with Typer 0.27.0 on Python 3.11 pass with the bounded dependency.
- Full Windows Python 3.11/3.12 release-matrix results are recorded in `ACCEPTANCE.md`.

## Compatibility

- Python 3.11 or newer.
- Typer `>=0.12,<0.27`.
- Database schema v8; no migration required.
