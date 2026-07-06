from __future__ import annotations

import os
import tomllib
from pathlib import Path

APP_DIR_NAME = "threadvault"
DB_FILE_NAME = "threadvault.db"
ENV_DB_PATH = "THREADVAULT_DB"
ENV_PROJECT_HOME = "THREADVAULT_HOME"


def default_codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()


def default_project_root() -> Path:
    env_root = os.environ.get(ENV_PROJECT_HOME)
    if env_root:
        return Path(env_root).expanduser()
    cwd = Path.cwd()
    if (cwd / "pyproject.toml").exists() and (cwd / "src" / "threadvault").exists():
        return cwd
    source_root = Path(__file__).resolve().parents[2]
    if (source_root / "pyproject.toml").exists() and (source_root / "src" / "threadvault").exists():
        return source_root
    return cwd


def default_data_dir() -> Path:
    return default_project_root() / "data"


def default_config_path() -> Path:
    if os.name == "nt":
        root = os.environ.get("APPDATA")
        if root:
            return Path(root) / APP_DIR_NAME / "threadvault.toml"
    return Path.home() / ".config" / APP_DIR_NAME / "threadvault.toml"


def default_db_path(config_path: Path | None = None) -> Path:
    env_path = os.environ.get(ENV_DB_PATH)
    if env_path:
        return Path(env_path).expanduser()
    configured_path = configured_db_path(config_path)
    if configured_path is not None:
        return configured_path
    return default_data_dir() / DB_FILE_NAME


def configured_db_path(config_path: Path | None = None) -> Path | None:
    path = (config_path or default_config_path()).expanduser()
    if not path.exists():
        return None
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    value = data.get("storage", {}).get("archive_db")
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("storage.archive_db must be a string path")
    if not value.strip():
        return None
    return Path(value).expanduser()


def discover_session_dirs(codex_home: Path | None = None) -> list[Path]:
    home = (codex_home or default_codex_home()).expanduser()
    return [home / "sessions", home / "archived_sessions"]
