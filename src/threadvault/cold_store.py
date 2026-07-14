from __future__ import annotations

import hashlib
import os
import zlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ColdBlobRecord:
    blob_id: str
    relative_path: str
    codec: str
    kind: str
    original_bytes: int
    stored_bytes: int
    sha256: str


def default_cold_root(db_path: Path) -> Path:
    db_path = db_path.expanduser()
    return db_path.with_name(f"{db_path.stem}-cold")


def database_path(conn) -> Path:
    row = conn.execute("PRAGMA database_list").fetchone()
    if row is None:
        raise RuntimeError("SQLite main database path is unavailable.")
    value = row[2] if not hasattr(row, "keys") else row["file"]
    return Path(value).expanduser().resolve()


class ColdBlobStore:
    """Content-addressed immutable cold evidence behind a small local interface."""

    def __init__(self, root: Path):
        self.root = root.expanduser().resolve()

    def put(self, data: bytes, *, kind: str, compress: bool = True) -> ColdBlobRecord:
        digest = hashlib.sha256(data).hexdigest()
        encoded = zlib.compress(data, level=6) if compress else data
        codec = "zlib" if compress else "raw"
        suffix = ".zlib" if compress else ".bin"
        relative = Path("blobs") / digest[:2] / f"{digest}{suffix}"
        target = self.root / relative
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
            with temporary.open("wb") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
        return ColdBlobRecord(
            blob_id=digest,
            relative_path=relative.as_posix(),
            codec=codec,
            kind=kind,
            original_bytes=len(data),
            stored_bytes=target.stat().st_size,
            sha256=digest,
        )

    def read(self, relative_path: str, codec: str) -> bytes:
        path = self._resolve(relative_path)
        data = path.read_bytes()
        if codec == "zlib":
            return zlib.decompress(data)
        if codec == "raw":
            return data
        raise ValueError(f"Unsupported cold blob codec: {codec}")

    def verify(self, record: ColdBlobRecord) -> dict[str, object]:
        path = self._resolve(record.relative_path)
        result: dict[str, object] = {
            "blob_id": record.blob_id,
            "path": str(path),
            "exists": path.is_file(),
            "ok": False,
            "error": None,
        }
        if not path.is_file():
            result["error"] = "missing"
            return result
        try:
            data = self.read(record.relative_path, record.codec)
        except (OSError, ValueError, zlib.error) as exc:
            result["error"] = f"decode_failed:{type(exc).__name__}"
            return result
        actual = hashlib.sha256(data).hexdigest()
        if actual != record.sha256 or len(data) != record.original_bytes:
            result["error"] = "content_mismatch"
            return result
        result["ok"] = True
        return result

    def _resolve(self, relative_path: str) -> Path:
        candidate = (self.root / relative_path).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ValueError("Cold blob path escapes the configured root.")
        return candidate
