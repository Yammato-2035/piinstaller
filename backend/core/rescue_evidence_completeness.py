"""Evidence completeness gate for rescue auto-discovery (001D7)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_FILES = (
    "00-session.json",
    "06-storage.json",
    "10-network-hardware.json",
    "11-network-connectivity.json",
    "12-kernel-findings.json",
    "13-services.json",
    "14-payload-version.json",
    "15-privacy-summary.json",
    "16-discovery-summary.json",
    "state.json",
)


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def validate_session_evidence(session_dir: Path, *, expected_session_id: str = "", expected_boot_id: str = "") -> dict[str, Any]:
    missing = [name for name in REQUIRED_FILES if not (session_dir / name).is_file()]
    state = _load_json(session_dir / "state.json") or _load_json(session_dir / "00-session.json") or {}
    session_id = str(state.get("session_id") or "")
    boot_id = str(state.get("boot_id") or "")
    mismatches: list[str] = []
    if expected_session_id and session_id and session_id != expected_session_id:
        mismatches.append("session_id")
    if expected_boot_id and boot_id and boot_id != expected_boot_id:
        mismatches.append("boot_id")

    privacy = _load_json(session_dir / "15-privacy-summary.json") or {}
    secrets = bool(privacy.get("secret_detected"))
    pii = bool(privacy.get("pii_detected"))

    if missing or mismatches or secrets:
        status = "failed" if secrets or mismatches else "review_required"
    elif pii:
        status = "review_required"
    else:
        status = "complete"

    return {
        "status": status,
        "missing_files": missing,
        "session_mismatches": mismatches,
        "privacy_gate_passed": not secrets and not pii,
        "secret_gate_passed": not secrets,
        "session_id": session_id,
        "boot_id": boot_id,
        "session_dir": str(session_dir),
    }
