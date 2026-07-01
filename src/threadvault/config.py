from __future__ import annotations

import os
from pathlib import Path

APP_DIR_NAME = "threadvault"
DB_FILE_NAME = "threadvault.db"


def default_codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()


def default_data_dir() -> Path:
    if os.name == "nt":
        root = os.environ.get("LOCALAPPDATA")
        if root:
            return Path(root) / APP_DIR_NAME
    return Path.home() / ".local" / "share" / APP_DIR_NAME


def default_db_path() -> Path:
    return default_data_dir() / DB_FILE_NAME


def discover_session_dirs(codex_home: Path | None = None) -> list[Path]:
    home = (codex_home or default_codex_home()).expanduser()
    return [home / "sessions", home / "archived_sessions"]
