# ThreadVault v2.4.2 Release Acceptance

## Scope

This patch accepts deterministic CLI content assertions under GitHub Actions while keeping actual desktop-smoke and MCP integration checks in the native CI environment. The immutable v2.4.1 tag and release remain unchanged.

## Gates

- Source and installed metadata report `2.4.2`.
- The four previously failing forced-color CLI tests pass with `GITHUB_ACTIONS` removed only inside the isolated `CliRunner` fixture.
- Machine-readable JSON is ASCII-safe on restricted Windows stdout and remains parseable with unchanged Unicode values.
- Full Windows Python 3.11 and 3.12 CI jobs pass lint, branch coverage, isolated desktop smoke, and MCP manifest checks.
- Dependency check and release hygiene pass.

## Results

- Local reproduction with `GITHUB_ACTIONS=true`: four failures reproduced before the fixture fix; the same four tests pass after isolation.
- Full local CI-mode suite with Typer 0.27.0: `313 passed`, `79.33%` branch coverage; `pip check` and ruff passed.
- Restricted `cp1252` stdout desktop smoke: `desktop_smoke.v2`, `ok=true`, and the emitted JSON parsed successfully.
- Remote Windows matrix: [GitHub Actions run 30425979086](https://github.com/Taurusxw/ThreadVault/actions/runs/30425979086) succeeded.
- Python 3.11 job: completed successfully in 4m33s; coverage, desktop smoke, and MCP manifest all passed.
- Python 3.12 job: completed successfully in 9m37s; coverage, desktop smoke, and MCP manifest all passed.

## Status

completed
