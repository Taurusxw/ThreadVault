from __future__ import annotations

from pathlib import Path
from typing import Literal

from .app_config import load_app_config

RetentionSection = Literal["audit_history", "backup_history", "restore_history"]
KeepSource = Literal["cli", "config"]


_KEEP_ATTRS: dict[RetentionSection, str] = {
    "audit_history": "audit_history_keep",
    "backup_history": "backup_history_keep",
    "restore_history": "restore_history_keep",
}


def resolve_retention_keep(keep: int | None, config: Path | None, section: RetentionSection) -> tuple[int, KeepSource]:
    """Resolve retention keep count while preserving CLI-over-config precedence."""
    if keep is not None:
        return keep, "cli"
    app_config = load_app_config(config)
    config_keep = getattr(app_config, _KEEP_ATTRS[section])
    if config_keep is not None:
        return config_keep, "config"
    config_hint = f" in {config}" if config else " in threadvault.toml"
    raise ValueError(f"Provide --keep or configure [{section}].keep{config_hint}")
