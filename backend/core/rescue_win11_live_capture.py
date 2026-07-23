"""Windows 11 live setup capture contract (PI-RS-ASUS-LAB-CONTROL-006).

Primary evidence path: SETUP_LOGS volume during setup — not post-hang only.
"""

from __future__ import annotations

import json
import re
import secrets
import string
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = 1
CONTRACT_VERSION = 1
SETUP_LOGS_LABEL = "SETUP_LOGS"
SETUP_LOGS_TAG = "SETUP_LOGS.TAG"
FORBIDDEN_RUN_IDS = frozenset({"", "norunid", "unknown", "unknown-norunid"})


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def generate_win11_run_id(*, when: datetime | None = None) -> str:
    ts = (when or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    suffix = "".join(secrets.choice(string.hexdigits.lower()) for _ in range(8))
    return f"asus-win11-{ts}-{suffix}"


def validate_run_id(run_id: str) -> dict[str, Any]:
    rid = (run_id or "").strip()
    ok = bool(re.fullmatch(r"asus-win11-\d{8}T\d{6}Z-[0-9a-f]{8}", rid))
    if rid.lower() in FORBIDDEN_RUN_IDS or "norunid" in rid.lower():
        ok = False
    return {
        "ok": ok,
        "run_id": rid,
        "blocked_reason": None if ok else "invalid_or_forbidden_run_id",
    }


def run_directory_layout(run_root: Path) -> dict[str, Path]:
    parts = (
        "collector",
        "heartbeats",
        "winpe",
        "panther",
        "rollback",
        "setupdiag",
        "disk-layout",
        "firmware",
        "screenshots",
        "result",
    )
    return {name: run_root / name for name in parts}


def ensure_run_tree(run_root: Path) -> dict[str, str]:
    layout = run_directory_layout(run_root)
    for path in layout.values():
        path.mkdir(parents=True, exist_ok=True)
    return {k: str(v) for k, v in layout.items()}


def resolve_setup_logs_roots(candidates: Sequence[Path]) -> dict[str, Any]:
    """Find SETUP_LOGS by label tag file — never by drive letter alone."""
    found: list[dict[str, Any]] = []
    for root in candidates:
        tag = root / SETUP_LOGS_TAG
        label_ok = root.name.upper().startswith("SETUP_LOGS") or tag.is_file()
        if not label_ok and not (root / "setuphelfer").is_dir():
            continue
        if not root.is_dir():
            continue
        writable = False
        try:
            probe = root / f".setuphelfer-write-probe-{secrets.token_hex(4)}"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink(missing_ok=True)
            writable = True
        except OSError as exc:
            found.append(
                {
                    "path": str(root),
                    "writable": False,
                    "error": str(exc)[:200],
                }
            )
            continue
        found.append({"path": str(root), "writable": writable, "tag_present": tag.is_file()})
    ready = next((f for f in found if f.get("writable")), None)
    return {
        "schema_version": SCHEMA_VERSION,
        "label": SETUP_LOGS_LABEL,
        "candidates": found,
        "setup_capture_ready": bool(ready),
        "selected": ready,
    }


def build_heartbeat(
    *,
    run_id: str,
    collector_alive: bool = True,
    setup_process_seen: bool | None = None,
    sources_scanned: Sequence[str] | None = None,
    files_seen: int = 0,
    files_copied: int = 0,
    bytes_copied: int = 0,
    last_copy_error: str | None = None,
    setup_logs_volume_present: bool = True,
) -> dict[str, Any]:
    gate = validate_run_id(run_id)
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "run_id_valid": gate["ok"],
        "timestamp": utc_now(),
        "collector_alive": collector_alive,
        "setup_process_seen": setup_process_seen,
        "sources_scanned": list(sources_scanned or []),
        "files_seen": int(files_seen),
        "files_copied": int(files_copied),
        "bytes_copied": int(bytes_copied),
        "last_copy_error": last_copy_error,
        "setup_logs_volume_present": setup_logs_volume_present,
    }


def write_heartbeat(path: Path, heartbeat: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(heartbeat), indent=2) + "\n", encoding="utf-8")


def finalize_capture_status(
    *,
    run_id: str,
    panther_files: int,
    rollback_files: int,
    heartbeats: int,
) -> dict[str, Any]:
    gate = validate_run_id(run_id)
    if not gate["ok"]:
        return {
            "status": "blocked",
            "reason": "invalid_run_id",
            "run_id": run_id,
        }
    if panther_files > 0 or rollback_files > 0:
        status = "evidence_collected"
    elif heartbeats > 0:
        status = "insufficient_evidence"
    else:
        status = "collector_missing"
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "run_id": run_id,
        "status": status,
        "panther_files": panther_files,
        "rollback_files": rollback_files,
        "heartbeats": heartbeats,
        "definitive_freeze_root_cause_known": False,
    }


DEFAULT_SOURCE_GLOBS = (
    r"X:\Windows\Panther",
    r"X:\$WINDOWS.~BT\Sources\Panther",
    r"X:\$WINDOWS.~BT\Sources\Rollback",
    r"C:\$WINDOWS.~BT\Sources\Panther",
    r"C:\$WINDOWS.~BT\Sources\Rollback",
    r"C:\Windows\Panther",
)
