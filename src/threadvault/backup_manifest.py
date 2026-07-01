from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

MANIFEST_VERSION = "0.20"


def manifest_path_for_backup(backup: Path) -> Path:
    return backup.with_name(f"{backup.name}.manifest.json")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_backup_manifest(backup_payload: dict[str, Any]) -> dict[str, Any]:
    backup = Path(backup_payload["destination"]).expanduser()
    manifest_path = manifest_path_for_backup(backup)
    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "backup": str(backup),
        "backup_sha256": sha256_file(backup),
        "backup_bytes": backup.stat().st_size,
        "source_db": backup_payload["source_db"],
        "source_db_sha256": _sha256_if_exists(Path(backup_payload["source_db"]).expanduser()),
        "schema_version": backup_payload["schema_version"],
        "stats": backup_payload["stats"],
        "privacy_note": "Manifest contains local paths and checksums, but no raw transcript content.",
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "path": str(manifest_path),
        "written": True,
        "manifest": manifest,
    }


def verify_backup_manifest(backup: Path) -> dict[str, Any]:
    backup = backup.expanduser()
    manifest_path = manifest_path_for_backup(backup)
    result: dict[str, Any] = {
        "backup": str(backup),
        "manifest": str(manifest_path),
        "exists": manifest_path.exists(),
        "ok": False,
        "errors": [],
        "manifest_data": None,
    }
    if not manifest_path.exists():
        result["errors"].append({"code": "manifest_missing", "message": "Backup manifest file does not exist."})
        return result
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result["errors"].append({"code": "manifest_invalid_json", "message": str(exc)})
        return result
    if not isinstance(data, dict):
        result["errors"].append({"code": "manifest_not_object", "message": "Backup manifest must be a JSON object."})
        return result
    result["manifest_data"] = data
    if data.get("manifest_version") != MANIFEST_VERSION:
        result["errors"].append({
            "code": "manifest_version_mismatch",
            "message": f"Expected manifest_version {MANIFEST_VERSION}, found {data.get('manifest_version')}.",
        })
    recorded_backup = data.get("backup")
    if recorded_backup and Path(str(recorded_backup)).expanduser() != backup:
        result["errors"].append({
            "code": "manifest_backup_path_mismatch",
            "message": "Manifest backup path does not match requested backup.",
        })
    if not backup.exists():
        result["errors"].append({"code": "backup_missing", "message": "Backup file does not exist."})
    else:
        actual_bytes = backup.stat().st_size
        if data.get("backup_bytes") != actual_bytes:
            result["errors"].append({
                "code": "backup_bytes_mismatch",
                "message": f"Expected {data.get('backup_bytes')}, found {actual_bytes}.",
            })
        actual_sha = sha256_file(backup)
        if data.get("backup_sha256") != actual_sha:
            result["errors"].append({"code": "backup_sha256_mismatch", "message": "Backup SHA256 does not match manifest."})
    result["ok"] = not result["errors"]
    return result


def _sha256_if_exists(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return sha256_file(path)
