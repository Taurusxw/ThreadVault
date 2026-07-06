from __future__ import annotations

from pathlib import Path

from threadvault.schemas import get_schema, validate_payload

RETENTION_SCHEMAS = ("audit_history_prune", "backup_history_prune", "restore_history_prune")


def valid_payload(schema_name: str, keep_source: str = "config") -> dict:
    if schema_name == "restore_history_prune":
        return {
            "history": "restore-history.jsonl",
            "records": [],
            "warnings": [],
            "invalid_lines": [],
            "ok": True,
            "apply": False,
            "keep": 2,
            "keep_source": keep_source,
            "kept": [],
            "deletable": [],
            "rewritten": False,
        }
    key = "reports" if schema_name == "audit_history_prune" else "backups"
    return {
        "dir": "history",
        key: [],
        "warnings": [],
        "ok": True,
        "apply": False,
        "keep": 2,
        "keep_source": keep_source,
        "kept": [],
        "deletable": [],
        "deleted": [],
    }


def test_retention_prune_schemas_require_keep_source_enum() -> None:
    for schema_name in RETENTION_SCHEMAS:
        schema = get_schema(schema_name)
        assert "keep_source" in schema["required"]
        assert schema["properties"]["keep_source"]["enum"] == ["cli", "config"]


def test_retention_prune_schemas_accept_runtime_keep_sources() -> None:
    for schema_name in RETENTION_SCHEMAS:
        assert validate_payload(schema_name, valid_payload(schema_name, "cli"))["ok"] is True
        assert validate_payload(schema_name, valid_payload(schema_name, "config"))["ok"] is True


def test_retention_prune_schemas_reject_unknown_keep_source() -> None:
    for schema_name in RETENTION_SCHEMAS:
        result = validate_payload(schema_name, valid_payload(schema_name, "default"))
        assert result["ok"] is False
        assert result["errors"]


def test_v27_docs_exist() -> None:
    for path in [
        Path("docs/progress/archive/legacy-v0/phases/phase-27-retention-schema-contract/plan.md"),
        Path("docs/progress/archive/legacy-v0/phases/phase-27-retention-schema-contract/external-review.md"),
    ]:
        assert path.exists(), f"missing {path}"
