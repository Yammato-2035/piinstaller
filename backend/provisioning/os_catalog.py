"""
Target-OS provisioning catalog loader — read-only.

PI-RS-HW-COMPAT-PROVISION-001 Phase 13 (catalog half).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

OS_CATALOG_VERSION = 1

_DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "provisioning"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def load_os_catalog(*, data_dir: Path | None = None) -> list[dict[str, Any]]:
    root = data_dir or _DEFAULT_DATA_DIR
    data = _load_json(root / "os_catalog.json")
    return list(data.get("entries") or [])


def validate_os_catalog_download_disabled(*, data_dir: Path | None = None) -> list[str]:
    """Hard safety check: every entry MUST have download_enabled == False in this
    phase. Returns violating image_ids (empty == safe)."""
    entries = load_os_catalog(data_dir=data_dir)
    return [e.get("image_id", "?") for e in entries if e.get("download_enabled") is not False]


def filter_by_architecture(entries: list[dict[str, Any]], architecture: str) -> list[dict[str, Any]]:
    return [e for e in entries if e.get("architecture") == architecture]


def filter_by_support_status(entries: list[dict[str, Any]], support_status: str) -> list[dict[str, Any]]:
    return [e for e in entries if e.get("support_status") == support_status]


def get_os_catalog_entry(image_id: str, *, data_dir: Path | None = None) -> dict[str, Any] | None:
    for entry in load_os_catalog(data_dir=data_dir):
        if entry.get("image_id") == image_id:
            return entry
    return None


def build_os_catalog_diagnostics(*, data_dir: Path | None = None) -> dict[str, Any]:
    entries = load_os_catalog(data_dir=data_dir)
    return {
        "catalog_version": OS_CATALOG_VERSION,
        "module": "provisioning.os_catalog",
        "entry_count": len(entries),
        "download_ever_enabled": len(validate_os_catalog_download_disabled(data_dir=data_dir)) > 0,
        "support_status_counts": {
            status: len(filter_by_support_status(entries, status))
            for status in ("verified", "experimental", "future", "blocked")
        },
    }


__all__ = [
    "OS_CATALOG_VERSION",
    "load_os_catalog",
    "validate_os_catalog_download_disabled",
    "filter_by_architecture",
    "filter_by_support_status",
    "get_os_catalog_entry",
    "build_os_catalog_diagnostics",
]
