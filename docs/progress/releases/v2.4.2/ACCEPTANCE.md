# ThreadVault v2.4.2 Release Acceptance

## Scope

This patch accepts deterministic CLI content assertions under GitHub Actions while keeping actual desktop-smoke and MCP integration checks in the native CI environment. The immutable v2.4.1 tag and release remain unchanged.

## Gates

- Source and installed metadata report `2.4.2`.
- The four previously failing forced-color CLI tests pass with `GITHUB_ACTIONS` removed only inside the isolated `CliRunner` fixture.
- Full Windows Python 3.11 and 3.12 CI jobs pass lint, branch coverage, isolated desktop smoke, and MCP manifest checks.
- Dependency check and release hygiene pass.

## Results

- Local reproduction with `GITHUB_ACTIONS=true`: four failures reproduced before the fixture fix; the same four tests pass after isolation.
- Full local CI-mode suite with Typer 0.27.0: `312 passed`, `79.27%` branch coverage; `pip check` and ruff passed.
- Remote matrix: pending final green run.

## Status

pending remote CI
