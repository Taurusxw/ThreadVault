# ThreadVault v2.4.2 Release Acceptance

## Scope

This patch accepts the Typer `<0.27` compatibility bound required to keep ThreadVault's Python 3.11 CLI behavior stable. The immutable v2.4.1 tag and release remain unchanged.

## Gates

- Source and installed metadata report `2.4.2`.
- The four previously failing Python 3.11 CLI tests pass under the resolved Typer 0.26.8 runtime.
- Full Windows Python 3.11 and 3.12 CI jobs pass lint, branch coverage, isolated desktop smoke, and MCP manifest checks.
- Dependency check and release hygiene pass.

## Results

- Local compatibility regression: `4 passed`; Typer resolved to `0.26.8`; `pip check` and ruff passed.
- Remote matrix: pending final green run.

## Status

pending remote CI
