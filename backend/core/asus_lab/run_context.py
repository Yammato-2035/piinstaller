"""Run context and Run-ID generation for ASUS lab automation."""

from __future__ import annotations

import re
import secrets
import string
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1

RUN_TYPES = frozenset(
    {
        "hw-discovery",
        "win11-live-capture",
        "bios-baseline",
        "bios-change",
        "bios-postcheck",
        "disk-restore",
        "efi-change",
        "secure-boot-change",
        "full-lab-capture",
    }
)

_PREFIX = {
    "hw-discovery": "asus-hw",
    "win11-live-capture": "asus-win11",
    "bios-baseline": "asus-bios",
    "bios-change": "asus-bios",
    "bios-postcheck": "asus-bios",
    "disk-restore": "asus-disk",
    "efi-change": "asus-efi",
    "secure-boot-change": "asus-sb",
    "full-lab-capture": "asus-full",
}

FORBIDDEN = frozenset({"", "norunid", "unknown", "unknown-norunid"})
_RUN_RE = re.compile(r"^asus-(hw|win11|bios|disk|efi|sb|full)-\d{8}T\d{6}Z-[0-9a-f]{8}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def generate_run_id(run_type: str, *, when: datetime | None = None) -> str:
    if run_type not in RUN_TYPES:
        raise ValueError("invalid_run_type")
    ts = (when or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    suffix = "".join(secrets.choice(string.hexdigits.lower()) for _ in range(8))
    return f"{_PREFIX[run_type]}-{ts}-{suffix}"


def validate_run_id(run_id: str) -> dict[str, Any]:
    rid = (run_id or "").strip()
    ok = bool(_RUN_RE.fullmatch(rid)) and rid.lower() not in FORBIDDEN and "norunid" not in rid.lower()
    return {"ok": ok, "run_id": rid, "blocked_reason": None if ok else "invalid_or_forbidden_run_id"}


def create_run_directory(base: Path, run_id: str) -> Path:
    gate = validate_run_id(run_id)
    if not gate["ok"]:
        raise ValueError(gate["blocked_reason"])
    run_root = base / run_id
    if run_root.exists():
        raise FileExistsError("run_directory_exists")
    tmp = base / f".{run_id}.tmp-{secrets.token_hex(4)}"
    tmp.mkdir(parents=True, exist_ok=False)
    for name in (
        "manifest",
        "system",
        "firmware",
        "disks",
        "windows",
        "network",
        "graphics",
        "heartbeats",
        "bios",
        "result",
        "redaction",
    ):
        (tmp / name).mkdir(parents=True, exist_ok=True)
    tmp.rename(run_root)
    return run_root


def build_run_context(
    *,
    run_type: str,
    boot_id: str,
    machine_id: str,
    payload_version: str,
    run_id: str | None = None,
) -> dict[str, Any]:
    rid = run_id or generate_run_id(run_type)
    gate = validate_run_id(rid)
    if not gate["ok"]:
        raise ValueError(gate["blocked_reason"])
    return {
        "schema_version": SCHEMA_VERSION,
        "run_type": run_type,
        "run_id": rid,
        "boot_id": boot_id,
        "machine_id": machine_id,
        "payload_version": payload_version,
        "created_at": utc_now(),
        "profile_id": "ASUS_ROG_GABRIEL_LAB",
        "bitlocker_mutation": False,
    }
