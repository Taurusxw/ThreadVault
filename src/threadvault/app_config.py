from __future__ import annotations

import os
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import APP_DIR_NAME


@dataclass(frozen=True)
class AllowlistRule:
    kind: str | None = None
    text: str | None = None
    pattern: re.Pattern[str] | None = None


@dataclass(frozen=True)
class AppConfig:
    source_path: Path | None = None
    allowlist: list[AllowlistRule] = field(default_factory=list)
    audit_history_keep: int | None = None
    backup_history_keep: int | None = None
    restore_history_keep: int | None = None
    vector_enabled: bool = False
    vector_adapter: str = "local-hash"
    vector_dimensions: int = 64
    governance_enabled: bool = False
    governance_identity_actors: list[dict[str, Any]] = field(default_factory=list)
    governance_policy_central_store: Path | None = None
    governance_audit_central_store: Path | None = None
    governance_backup_policy: Path | None = None


PrivacyConfig = AppConfig


def default_config_path() -> Path:
    if os.name == "nt":
        root = os.environ.get("APPDATA")
        if root:
            return Path(root) / APP_DIR_NAME / "threadvault.toml"
    return Path.home() / ".config" / APP_DIR_NAME / "threadvault.toml"


def load_app_config(path: Path | None = None) -> AppConfig:
    config_path = (path or default_config_path()).expanduser()
    if not config_path.exists():
        return AppConfig(source_path=None)
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    raw_rules = data.get("privacy", {}).get("allowlist", [])
    allowlist: list[AllowlistRule] = []
    for item in raw_rules:
        if not isinstance(item, dict):
            continue
        kind = _str_or_none(item.get("kind"))
        text = _str_or_none(item.get("text"))
        pattern_text = _str_or_none(item.get("pattern"))
        pattern = None
        if pattern_text:
            pattern = re.compile(pattern_text)
        allowlist.append(AllowlistRule(kind=kind, text=text, pattern=pattern))
    audit_history_keep = _positive_int_or_none(data.get("audit_history", {}).get("keep"), "audit_history.keep")
    backup_history_keep = _positive_int_or_none(data.get("backup_history", {}).get("keep"), "backup_history.keep")
    restore_history_keep = _positive_int_or_none(data.get("restore_history", {}).get("keep"), "restore_history.keep")
    vector_config = data.get("retrieval", {}).get("vector", {})
    vector_enabled = _bool_or_default(vector_config.get("enabled"), False, "retrieval.vector.enabled")
    vector_adapter = _str_or_default(vector_config.get("adapter"), "local-hash")
    if vector_adapter != "local-hash":
        raise ValueError("retrieval.vector.adapter must be local-hash")
    vector_dimensions = _positive_int_or_default(vector_config.get("dimensions"), 64, "retrieval.vector.dimensions")
    governance_config = data.get("governance", {})
    governance_enabled = _bool_or_default(governance_config.get("enabled"), False, "governance.enabled")
    governance_identity_actors = _identity_actors(governance_config.get("identity", {}).get("actors", []))
    governance_policy_central_store = _optional_path_or_none(
        governance_config.get("policy", {}).get("central_store"),
        "governance.policy.central_store",
    )
    governance_audit_central_store = _optional_path_or_none(
        governance_config.get("audit", {}).get("central_store"),
        "governance.audit.central_store",
    )
    governance_backup_policy = _optional_path_or_none(
        governance_config.get("backup", {}).get("policy"),
        "governance.backup.policy",
    )
    return AppConfig(
        source_path=config_path,
        allowlist=allowlist,
        audit_history_keep=audit_history_keep,
        backup_history_keep=backup_history_keep,
        restore_history_keep=restore_history_keep,
        vector_enabled=vector_enabled,
        vector_adapter=vector_adapter,
        vector_dimensions=vector_dimensions,
        governance_enabled=governance_enabled,
        governance_identity_actors=governance_identity_actors,
        governance_policy_central_store=governance_policy_central_store,
        governance_audit_central_store=governance_audit_central_store,
        governance_backup_policy=governance_backup_policy,
    )


def load_privacy_config(path: Path | None = None) -> PrivacyConfig:
    return load_app_config(path)


def default_config_template() -> str:
    return """# ThreadVault local configuration.
# This file is local-only. ThreadVault does not upload Codex transcripts or config data.

[privacy]
# Allowlist entries reduce false positives in privacy scanning.
# Keep this empty until you have a specific local false positive.
# For Windows path regex patterns, prefer TOML literal strings:
#   { kind = "windows_abs_path", pattern = '^E:\\\\Codex\\\\' }
allowlist = []

[audit_history]
# Number of latest valid anonymous audit reports to keep when prune uses config.
keep = 20

[backup_history]
# Number of latest valid local SQLite backups to keep when prune uses config.
keep = 10

[restore_history]
# Number of latest valid restore history records to keep when prune uses config.
keep = 20

[retrieval.vector]
# Local vector indexing is derived data and is disabled by default.
# Enable only when you want local deterministic vectors built from Summary Pipeline chunks.
enabled = false
adapter = "local-hash"
dimensions = 64

[governance]
# Governance is disabled by default. Enabling it makes local governance intent visible,
# but does not require a server, enable cloud sync, or enforce permissions yet.
enabled = false

[governance.identity]
# Optional local static actor map for v3 team-governance previews.
# This is local-only and does not enable shared enforcement by itself.
actors = []

[governance.policy]
# Optional local central policy document for v3 team-governance previews.
# This is local-only and does not enable shared enforcement by itself.
central_store = ""

[governance.audit]
# Optional local centralized audit JSONL store for v3 team-governance previews.
# This is local-only and does not enable shared enforcement by itself.
central_store = ""

[governance.backup]
# Optional local centralized backup/restore policy document for v3 team-governance previews.
# This is local-only and does not enable shared backup, restore, or retention execution by itself.
policy = ""
"""


def init_app_config(path: Path | None = None, force: bool = False) -> dict[str, Any]:
    config_path = _resolve_config_path(path)
    existed = config_path.exists()
    if existed and not force:
        return {
            **_base_config_payload(path, config_path),
            "ok": False,
            "created": False,
            "overwritten": False,
            "existed": True,
            "force": force,
            "error": "config_exists",
            "doctor": diagnose_app_config(path),
        }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(default_config_template(), encoding="utf-8")
    doctor = diagnose_app_config(path)
    return {
        **_base_config_payload(path, config_path),
        "ok": doctor["ok"],
        "created": not existed,
        "overwritten": existed,
        "existed": existed,
        "force": force,
        "error": None if doctor["ok"] else "generated_config_invalid",
        "doctor": doctor,
    }


def describe_app_config(path: Path | None = None, include_values: bool = False) -> dict[str, Any]:
    config_path = _resolve_config_path(path)
    payload = _base_config_payload(path, config_path)
    if not config_path.exists():
        return {
            **payload,
            "loaded": False,
            "loaded_path": None,
            "sections": [],
            "privacy": {"allowlist_count": 0, "allowlist_kinds": [], "allowlist_rules": [] if include_values else None},
            "audit_history": {"keep": None},
            "backup_history": {"keep": None},
            "restore_history": {"keep": None},
            "retrieval": {"vector": {"enabled": False, "adapter": "local-hash", "dimensions": 64}},
            "governance": {"enabled": False},
        }
    config = load_app_config(path)
    return {
        **payload,
        "loaded": True,
        "loaded_path": str(config.source_path) if config.source_path else None,
        "sections": _configured_sections(config_path),
        "privacy": _privacy_summary(config, include_values=include_values),
        "audit_history": {"keep": config.audit_history_keep},
        "backup_history": {"keep": config.backup_history_keep},
        "restore_history": {"keep": config.restore_history_keep},
        "retrieval": _retrieval_summary(config),
        "governance": _governance_summary(config),
    }


def diagnose_app_config(path: Path | None = None) -> dict[str, Any]:
    config_path = _resolve_config_path(path)
    payload = _base_config_payload(path, config_path)
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    suggestions: list[str] = []
    summary: dict[str, Any] | None = None
    if not config_path.exists():
        warnings.append({"code": "config_missing", "message": "Config file does not exist; built-in defaults will be used."})
        suggestions.append("Create threadvault.toml when privacy allowlist or audit history defaults are needed.")
        summary = describe_app_config(path)
    else:
        try:
            summary = describe_app_config(path)
        except tomllib.TOMLDecodeError as exc:
            errors.append({"code": "invalid_toml", "message": str(exc)})
            suggestions.append("Fix TOML syntax before running commands that depend on local config.")
        except re.error as exc:
            errors.append({"code": "invalid_privacy_allowlist_regex", "message": str(exc)})
            suggestions.append("Use valid Python regular expressions; for Windows paths prefer TOML literal strings.")
        except ValueError as exc:
            errors.append({"code": "invalid_config_value", "message": str(exc)})
            suggestions.append(
                "Fix invalid config values such as audit_history.keep, backup_history.keep, restore_history.keep, "
                "retrieval.vector, governance.enabled, governance.identity.actors, or governance backup/policy paths."
            )
    return {
        **payload,
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "suggestions": suggestions,
        "summary": summary,
    }


def _str_or_none(value) -> str | None:
    if value is None:
        return None
    return str(value)


def _identity_actors(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("governance.identity.actors must be an array")
    actors: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError(f"governance.identity.actors[{index}] must be an object")
        actor_id = _str_or_none(item.get("id"))
        if not actor_id:
            raise ValueError(f"governance.identity.actors[{index}].id is required")
        raw_roles = item.get("roles", [])
        if not isinstance(raw_roles, list) or any(not isinstance(role, str) for role in raw_roles):
            raise ValueError(f"governance.identity.actors[{index}].roles must be an array of strings")
        actors.append(
            {
                "id": actor_id,
                "display": _str_or_none(item.get("display")),
                "roles": list(raw_roles),
                "source": _str_or_none(item.get("source")) or "local-static",
            }
        )
    return actors


def _positive_int_or_none(value, name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer greater than or equal to 1")
    if value < 1:
        raise ValueError(f"{name} must be greater than or equal to 1")
    return value


def _positive_int_or_default(value, default: int, name: str) -> int:
    if value is None:
        return default
    result = _positive_int_or_none(value, name)
    assert result is not None
    return result


def _bool_or_default(value, default: bool, name: str) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be true or false")
    return value


def _str_or_default(value, default: str) -> str:
    if value is None:
        return default
    return str(value)


def _optional_path_or_none(value: Any, name: str) -> Path | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string path")
    if not value.strip():
        return None
    return Path(value).expanduser()


def _resolve_config_path(path: Path | None) -> Path:
    return (path or default_config_path()).expanduser()


def _base_config_payload(requested_path: Path | None, resolved_path: Path) -> dict[str, Any]:
    return {
        "requested_path": str(requested_path) if requested_path else None,
        "default_path": str(default_config_path()),
        "resolved_path": str(resolved_path),
        "exists": resolved_path.exists(),
    }


def _configured_sections(path: Path) -> list[str]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return sorted(key for key, value in data.items() if isinstance(value, dict))


def _privacy_summary(config: AppConfig, include_values: bool = False) -> dict[str, Any]:
    rules = []
    for rule in config.allowlist:
        item: dict[str, Any] = {
            "kind": rule.kind,
            "has_text": rule.text is not None,
            "has_pattern": rule.pattern is not None,
        }
        if include_values:
            item["text"] = rule.text
            item["pattern"] = rule.pattern.pattern if rule.pattern is not None else None
        rules.append(item)
    kinds = sorted({rule.kind for rule in config.allowlist if rule.kind is not None})
    return {
        "allowlist_count": len(config.allowlist),
        "allowlist_kinds": kinds,
        "allowlist_rules": rules if include_values else None,
    }


def _retrieval_summary(config: AppConfig) -> dict[str, Any]:
    return {
        "vector": {
            "enabled": config.vector_enabled,
            "adapter": config.vector_adapter,
            "dimensions": config.vector_dimensions,
        }
    }


def _governance_summary(config: AppConfig) -> dict[str, Any]:
    return {
        "enabled": config.governance_enabled,
        "identity": {
            "actor_count": len(config.governance_identity_actors),
            "actors": [
                {
                    "id": actor["id"],
                    "display": actor.get("display"),
                    "roles": actor["roles"],
                    "source": actor["source"],
                }
                for actor in config.governance_identity_actors
            ],
        },
        "policy": {
            "central_store": str(config.governance_policy_central_store) if config.governance_policy_central_store else None,
            "central_store_configured": config.governance_policy_central_store is not None,
        },
        "audit": {
            "central_store": str(config.governance_audit_central_store) if config.governance_audit_central_store else None,
            "central_store_configured": config.governance_audit_central_store is not None,
        },
        "backup": {
            "policy": str(config.governance_backup_policy) if config.governance_backup_policy else None,
            "policy_configured": config.governance_backup_policy is not None,
        },
    }
