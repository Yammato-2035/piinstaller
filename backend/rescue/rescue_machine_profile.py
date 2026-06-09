"""Rescue machine profile — no raw serials, no WLAN secrets."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_SERIAL_KEYS = frozenset({"serial", "serial_number", "product_serial", "board_serial"})
_FORBIDDEN_PROFILE_KEYS = frozenset({"wifi_password", "psk", "password", "secret", "token"})


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def machine_id_from_dmi(fields: Mapping[str, str]) -> str:
    """Stable machine id without exposing raw serials in profile output."""
    parts: list[str] = []
    for key in ("sys_vendor", "product_name", "board_vendor", "board_name", "bios_vendor"):
        val = (fields.get(key) or "").strip()
        if val:
            parts.append(f"{key}={val}")
    serial = (fields.get("product_serial") or fields.get("board_serial") or "").strip()
    if serial:
        parts.append(f"serial_hash={hashlib.sha256(serial.encode()).hexdigest()[:16]}")
    blob = "|".join(parts) or "unknown"
    return hashlib.sha256(blob.encode()).hexdigest()


def build_machine_profile(
    *,
    dmi_fields: Mapping[str, str] | None = None,
    boot_mode: str = "uefi",
    secure_boot: str = "unknown",
    graphics_mode: str = "unknown",
    network: Mapping[str, Any] | None = None,
    rescue: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    dmi = dict(dmi_fields or {})
    vendor = (dmi.get("sys_vendor") or dmi.get("board_vendor") or "").strip()
    model = (dmi.get("product_name") or dmi.get("board_name") or "").strip()
    return {
        "schema_version": 1,
        "machine_id": machine_id_from_dmi(dmi),
        "vendor": vendor,
        "model": model,
        "boot_mode": boot_mode,
        "secure_boot": secure_boot,
        "graphics_mode": graphics_mode,
        "last_known_good_menu": "",
        "network": dict(
            network
            or {
                "last_status": "not_configured",
                "wifi_scan_supported": None,
                "ethernet_detected": None,
            }
        ),
        "rescue": dict(
            rescue
            or {
                "last_boot_status": "yellow",
                "last_medium_check": "",
                "last_ui_mode": "",
            }
        ),
        "updated_at": _now_iso(),
        "secrets_exposed": False,
    }


def validate_machine_profile(profile: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    blob = json.dumps(profile, default=str)
    for key in _FORBIDDEN_PROFILE_KEYS:
        if key in profile or re.search(rf'"{key}"\s*:', blob, re.I):
            errors.append(f"FORBIDDEN_KEY_{key.upper()}")
    for k, v in profile.items():
        if k.lower() in _SERIAL_KEYS and isinstance(v, str) and v.strip():
            errors.append("RAW_SERIAL_NOT_ALLOWED")
            break
    return errors


def load_machine_profile(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def save_machine_profile(profile: Mapping[str, Any], path: Path, *, best_effort: bool = True) -> dict[str, Any]:
    errors = validate_machine_profile(profile)
    result = {"written": False, "path": str(path), "errors": errors, "error": None}
    if errors:
        result["error"] = "validation_failed"
        if not best_effort:
            raise ValueError(errors[0])
        return result
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(dict(profile), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        result["written"] = True
    except OSError as exc:
        result["error"] = str(exc)
        if not best_effort:
            raise
    return result
