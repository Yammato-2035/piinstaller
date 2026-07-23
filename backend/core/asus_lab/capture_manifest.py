"""Capture manifest entries for ASUS lab runs."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = 1


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest_entry(
    *,
    relative_path: str,
    category: str,
    collector: str,
    started_at: str,
    completed_at: str | None = None,
    exit_code: int = 0,
    size_bytes: int = 0,
    sha256: str | None = None,
    redaction_status: str = "not_required",
    errors: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "relative_path": relative_path,
        "category": category,
        "collector": collector,
        "started_at": started_at,
        "completed_at": completed_at or utc_now(),
        "exit_code": int(exit_code),
        "size_bytes": int(size_bytes),
        "sha256": sha256,
        "redaction_status": redaction_status,
        "errors": list(errors or []),
    }


def append_manifest(manifest_path: Path, entry: Mapping[str, Any]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    items: list[dict[str, Any]] = []
    if manifest_path.is_file():
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("entries"), list):
                items = list(data["entries"])
            elif isinstance(data, list):
                items = list(data)
        except (OSError, json.JSONDecodeError):
            items = []
    items.append(dict(entry))
    payload = {"schema_version": SCHEMA_VERSION, "entries": items, "updated_at": utc_now()}
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def record_artifact(
    run_root: Path,
    *,
    relative_path: str,
    category: str,
    collector: str,
    started_at: str,
    exit_code: int = 0,
    redaction_status: str = "not_required",
    errors: list[str] | None = None,
) -> dict[str, Any]:
    path = run_root / relative_path
    size = path.stat().st_size if path.is_file() else 0
    digest = sha256_file(path) if path.is_file() else None
    entry = manifest_entry(
        relative_path=relative_path,
        category=category,
        collector=collector,
        started_at=started_at,
        exit_code=exit_code,
        size_bytes=size,
        sha256=digest,
        redaction_status=redaction_status,
        errors=errors,
    )
    append_manifest(run_root / "manifest" / "capture_manifest.json", entry)
    return entry
