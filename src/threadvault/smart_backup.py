from __future__ import annotations

import json
import os
import shutil
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .archive_lifecycle import archive_storage_state, backup_storage_profile, verify_storage_backup
from .source_sync import sync_codex_sources

SMART_BACKUP_CONTRACT_VERSION = "smart-backup.v2"
CORE_INTERVAL = timedelta(days=1)
EVIDENCE_INTERVAL = timedelta(days=7)
FORENSIC_INTERVAL = timedelta(days=30)
DISK_RESERVE_BYTES = 5 * 1024**3
AUTO_KEEP = {"core": 3, "evidence": 2, "forensic": 1}
PROFILE_COVERAGE = {
    "core": {"core", "evidence", "forensic"},
    "evidence": {"evidence", "forensic"},
    "forensic": {"forensic"},
}


@dataclass(frozen=True)
class BackupRecord:
    profile: str
    generated_at: datetime
    manifest_path: Path
    database_path: Path
    payload: dict[str, Any]


def run_smart_backup(
    db_path: Path,
    *,
    out_root: Path | None = None,
    cold_root: Path | None = None,
    codex_home: Path | None = None,
    apply: bool = False,
    include_forensic: bool = True,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Choose, create, verify, and retain one appropriate backup profile."""
    db_path = db_path.expanduser().resolve()
    root = (out_root or db_path.parent / "storage-backups").expanduser().resolve()
    current_time = (now or datetime.now(UTC)).astimezone(UTC)
    history = _load_history(root)
    source_sync = sync_codex_sources(
        db_path,
        codex_home=codex_home,
        apply=apply,
    )
    state = archive_storage_state(
        db_path,
        cold_root=cold_root,
        codex_home=codex_home,
        include_source=include_forensic,
    )
    if apply and not source_sync["ok"]:
        decision: dict[str, str | None] = {"action": "blocked", "profile": None, "reason": "source_sync_failed"}
    elif not apply and source_sync["pending_files"]:
        decision = {"action": "sync", "profile": None, "reason": "source_sync_required"}
    else:
        decision = _choose_profile(history, state, current_time, include_forensic=include_forensic)
    estimate = _estimate_required_bytes(decision["profile"], state, root)
    disk = _disk_state(root, estimate)
    base = {
        "contract_version": SMART_BACKUP_CONTRACT_VERSION,
        "ok": True,
        "applied": apply,
        "action": decision["action"],
        "profile": decision["profile"],
        "reason": decision["reason"],
        "db_path": str(db_path),
        "out_root": str(root),
        "policy": {
            "core_days": CORE_INTERVAL.days,
            "evidence_days": EVIDENCE_INTERVAL.days,
            "forensic_days": FORENSIC_INTERVAL.days,
            "keep": AUTO_KEEP,
            "forensic_enabled": include_forensic,
        },
        "source_sync": source_sync,
        "archive_state": state,
        "latest": _latest_summary(history),
        "disk": disk,
        "backup": None,
        "verification": None,
        "retention": None,
    }
    if decision["action"] == "blocked":
        return {**base, "ok": False}
    if decision["action"] == "sync":
        return base
    if decision["action"] == "skip":
        if apply:
            auto_root = root / "auto"
            auto_root.mkdir(parents=True, exist_ok=True)
            _write_last_run(auto_root, base)
        return base
    if not disk["enough"]:
        return {**base, "ok": False, "action": "blocked", "reason": "insufficient_disk_space"}
    if not apply:
        return base

    auto_root = root / "auto"
    auto_root.mkdir(parents=True, exist_ok=True)
    lock_path = auto_root / ".smart-backup.lock"
    try:
        with _exclusive_lock(lock_path, current_time):
            profile = decision["profile"]
            assert profile is not None
            backup = backup_storage_profile(
                db_path,
                auto_root / profile,
                profile=profile,
                cold_root=cold_root,
                codex_home=codex_home,
            )
            if not backup["ok"]:
                result = {**base, "ok": False, "action": "failed", "backup": backup}
                _write_last_run(auto_root, result)
                return result
            verification = verify_storage_backup(
                Path(backup["manifest"]),
                deep=profile in {"evidence", "forensic"},
            )
            if not verification["ok"]:
                result = {
                    **base,
                    "ok": False,
                    "action": "failed_verification",
                    "backup": backup,
                    "verification": verification,
                }
                _write_last_run(auto_root, result)
                return result
            retention = _prune_auto_history(auto_root, apply=True)
            result = {
                **base,
                "action": "created",
                "backup": backup,
                "verification": verification,
                "retention": retention,
            }
            _write_last_run(auto_root, result)
            return result
    except FileExistsError:
        return {**base, "ok": False, "action": "blocked", "reason": "backup_already_running"}


def _choose_profile(
    history: list[BackupRecord],
    current: dict[str, Any],
    now: datetime,
    *,
    include_forensic: bool,
) -> dict[str, str | None]:
    if not history:
        return {"action": "backup", "profile": "evidence", "reason": "bootstrap_evidence"}
    oldest = min(record.generated_at for record in history)
    forensic = _latest_covering(history, "forensic")
    if (
        include_forensic
        and now - oldest >= FORENSIC_INTERVAL
        and (forensic is None or now - forensic.generated_at >= FORENSIC_INTERVAL)
        and _changed_since(forensic, current, "forensic")
    ):
        return {"action": "backup", "profile": "forensic", "reason": "monthly_forensic_due"}
    evidence = _latest_covering(history, "evidence")
    if (
        (evidence is None or now - evidence.generated_at >= EVIDENCE_INTERVAL)
        and _changed_since(evidence, current, "evidence")
    ):
        return {"action": "backup", "profile": "evidence", "reason": "weekly_evidence_due"}
    core = _latest_covering(history, "core")
    if (
        (core is None or now - core.generated_at >= CORE_INTERVAL)
        and _changed_since(core, current, "core")
    ):
        return {"action": "backup", "profile": "core", "reason": "daily_core_due"}
    return {"action": "skip", "profile": None, "reason": "fresh_or_unchanged"}


def _changed_since(record: BackupRecord | None, current: dict[str, Any], coverage: str) -> bool:
    if record is None:
        return True
    previous = record.payload.get("archive_state")
    if not isinstance(previous, dict):
        return True
    current_db = current["database"]
    previous_db = previous.get("database") or {}
    db_keys = ("sessions", "events", "warnings", "updated_at")
    if any(current_db.get(key) != previous_db.get(key) for key in db_keys):
        return True
    if coverage in {"evidence", "forensic"}:
        current_cold = current["cold"]
        previous_cold = previous.get("cold") or {}
        if any(current_cold.get(key) != previous_cold.get(key) for key in ("blobs", "original_bytes", "stored_bytes")):
            return True
    if coverage == "forensic":
        return current.get("source") != previous.get("source")
    return False


def _load_history(root: Path) -> list[BackupRecord]:
    records: list[BackupRecord] = []
    if not root.is_dir():
        return records
    for manifest_path in root.rglob("*.storage-manifest.json"):
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            profile = payload["profile"]
            database_path = Path(payload["database"]["path"]).expanduser().resolve()
            generated_at = _parse_timestamp(payload["generated_at"])
            if profile not in AUTO_KEEP or not database_path.is_file():
                continue
            if database_path.stat().st_size != int(payload["database"]["bytes"]):
                continue
            records.append(BackupRecord(profile, generated_at, manifest_path.resolve(), database_path, payload))
        except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
            continue
    return sorted(records, key=lambda record: record.generated_at)


def _latest_covering(history: list[BackupRecord], profile: str) -> BackupRecord | None:
    eligible = [record for record in history if record.profile in PROFILE_COVERAGE[profile]]
    return eligible[-1] if eligible else None


def _latest_summary(history: list[BackupRecord]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for profile in AUTO_KEEP:
        record = _latest_covering(history, profile)
        result[profile] = None if record is None else {
            "profile": record.profile,
            "generated_at": record.generated_at.isoformat().replace("+00:00", "Z"),
            "manifest": str(record.manifest_path),
        }
    return result


def _estimate_required_bytes(profile: str | None, state: dict[str, Any], root: Path) -> int:
    if profile is None:
        return 0
    required = int(state["database"]["bytes"] * 1.1)
    if profile in {"evidence", "forensic"}:
        existing_cold = root / "auto" / profile / "cold"
        if not existing_cold.is_dir():
            required += int(state["cold"]["stored_bytes"] * 1.1)
    if profile == "forensic" and state.get("source"):
        required += int(state["source"]["bytes"] * 1.1)
    return required


def _disk_state(root: Path, required: int) -> dict[str, Any]:
    probe = root
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    usage = shutil.disk_usage(probe)
    return {
        "free_bytes": usage.free,
        "required_bytes": required,
        "reserve_bytes": DISK_RESERVE_BYTES,
        "enough": usage.free >= required + DISK_RESERVE_BYTES,
    }


def _prune_auto_history(auto_root: Path, *, apply: bool) -> dict[str, Any]:
    deleted: list[str] = []
    deleted_bytes = 0
    kept: dict[str, list[str]] = {}
    for profile, keep in AUTO_KEEP.items():
        profile_root = (auto_root / profile).resolve()
        records = [
            record for record in _load_history(profile_root)
            if record.profile == profile and profile_root in record.manifest_path.parents
        ]
        retained = records[-keep:]
        deletable = records[: max(0, len(records) - keep)]
        kept[profile] = [str(record.manifest_path) for record in retained]
        if apply:
            for record in deletable:
                for path in _record_files(record, profile_root):
                    if path.is_file():
                        deleted_bytes += path.stat().st_size
                        path.unlink()
                        deleted.append(str(path))
            _prune_shared_evidence(profile_root, retained, deleted, apply=apply)
    return {
        "ok": True,
        "applied": apply,
        "keep": AUTO_KEEP,
        "kept": kept,
        "deleted": deleted,
        "deleted_bytes": deleted_bytes,
    }


def _record_files(record: BackupRecord, root: Path) -> list[Path]:
    files = [record.manifest_path]
    database = record.database_path.resolve()
    if database == root or root in database.parents:
        files.extend([database, database.with_name(f"{database.name}.manifest.json")])
    return files


def _prune_shared_evidence(
    profile_root: Path,
    retained: list[BackupRecord],
    deleted: list[str],
    *,
    apply: bool,
) -> None:
    if not retained or not apply:
        return
    cold_refs: set[str] = set()
    forensic_refs: set[str] = set()
    for record in retained:
        try:
            with closing(sqlite3.connect(f"file:{record.database_path.as_posix()}?mode=ro", uri=True)) as conn:
                cold_refs.update(row[0] for row in conn.execute("SELECT relative_path FROM cold_blobs"))
        except sqlite3.Error:
            return
        forensic_refs.update(item["relative_path"] for item in record.payload.get("forensic", []) if "relative_path" in item)
    _remove_unreferenced_files(profile_root / "cold", cold_refs, deleted)
    _remove_unreferenced_files(
        profile_root / "forensic",
        {value.removeprefix("forensic/") for value in forensic_refs},
        deleted,
    )


def _remove_unreferenced_files(root: Path, references: set[str], deleted: list[str]) -> None:
    if not root.is_dir():
        return
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative not in references:
            path.unlink()
            deleted.append(str(path))


class _exclusive_lock:
    def __init__(self, path: Path, now: datetime):
        self.path = path
        self.now = now
        self.fd: int | None = None

    def __enter__(self) -> None:
        if self.path.exists() and self.now.timestamp() - self.path.stat().st_mtime > 6 * 3600:
            self.path.unlink(missing_ok=True)
        self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(self.fd, str(os.getpid()).encode("ascii"))

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self.fd is not None:
            os.close(self.fd)
        self.path.unlink(missing_ok=True)


def _write_last_run(auto_root: Path, payload: dict[str, Any]) -> None:
    path = auto_root / "last-run.json"
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
