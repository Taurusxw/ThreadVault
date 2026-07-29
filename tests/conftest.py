from __future__ import annotations

from pathlib import Path

import pytest

import threadvault.restore_history as restore_history_module


@pytest.fixture(autouse=True)
def isolate_local_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep tests away from the user's archive, Codex home, config, and restore history."""

    runtime_root = tmp_path / "threadvault-test-runtime"
    codex_home = runtime_root / "codex-home"
    (codex_home / "sessions").mkdir(parents=True)
    (codex_home / "archived_sessions").mkdir()
    monkeypatch.setenv("THREADVAULT_HOME", str(runtime_root / "project"))
    monkeypatch.setenv("THREADVAULT_DB", str(runtime_root / "archive" / "threadvault.db"))
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    monkeypatch.delenv("CODEX_SQLITE_HOME", raising=False)
    monkeypatch.setenv("APPDATA", str(runtime_root / "appdata"))
    monkeypatch.setattr(restore_history_module, "default_restore_history_path", lambda: tmp_path / "restore-history.jsonl")
