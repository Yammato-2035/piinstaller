"""Rescue stick payload version (1.10.0.x track, separate from project_version)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PAYLOAD_VERSION_FILE = _REPO_ROOT / "config" / "rescue_payload_version.json"
_PREVIOUS_DEFAULT = "1.10.0.14"
_CURRENT_DEFAULT = "1.10.0.15"


@lru_cache(maxsize=1)
def load_rescue_payload_version_config() -> dict[str, Any]:
    if not _PAYLOAD_VERSION_FILE.is_file():
        return {
            "rescue_payload_version": _CURRENT_DEFAULT,
            "previous_rescue_payload_version": _PREVIOUS_DEFAULT,
        }
    data = json.loads(_PAYLOAD_VERSION_FILE.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("invalid_rescue_payload_version_config")
    return data


def rescue_payload_version() -> str:
    value = str(load_rescue_payload_version_config().get("rescue_payload_version", "")).strip()
    return value or _CURRENT_DEFAULT


def previous_rescue_payload_version() -> str:
    value = str(load_rescue_payload_version_config().get("previous_rescue_payload_version", "")).strip()
    return value or _PREVIOUS_DEFAULT
