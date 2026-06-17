"""
SETUP_LOGS partition persistence — prefer writable vfat logs partition on rescue stick.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from core.mount_facade import discover_mounts_flat

SETUP_LOGS_LABEL = "SETUP_LOGS"
SETUP_LOGS_SUBDIR = "setuphelfer/evidence"
_RUN_FALLBACK = Path("/run/setuphelfer/evidence")
_LOCAL_FALLBACK = Path("/var/lib/setuphelfer-rescue/local/evidence")

_SETUP_LOGS_MOUNT_RE = re.compile(r"^/media/[^/]+/SETUP_LOGS$", re.IGNORECASE)
_SETUP_LOGS_RUN_RE = re.compile(r"^/run/media/[^/]+/SETUP_LOGS$", re.IGNORECASE)


def _normalize_label(label: str) -> str:
    return (label or "").strip().upper()


def detect_setup_logs_mount(*, runner: Any = None) -> dict[str, Any]:
    """Find SETUP_LOGS vfat mount for persistent rescue evidence."""
    mounts = discover_mounts_flat(runner=runner)
    candidates: list[dict[str, Any]] = []
    for fs in mounts:
        target = str(fs.get("target") or "").rstrip("/")
        if not target:
            continue
        label = _normalize_label(str(fs.get("label") or ""))
        fstype = str(fs.get("fstype") or "").lower()
        options = str(fs.get("options") or "").lower()
        is_setup_logs = (
            label == SETUP_LOGS_LABEL
            or bool(_SETUP_LOGS_MOUNT_RE.match(target))
            or bool(_SETUP_LOGS_RUN_RE.match(target))
        )
        if not is_setup_logs:
            continue
        readonly = "ro" in options.split(",") and "rw" not in options.split(",")
        writable = fstype in ("vfat", "exfat", "ext4") and not readonly
        candidates.append(
            {
                "mount_point": target,
                "source": fs.get("source"),
                "fstype": fstype,
                "writable": writable,
                "label": label or SETUP_LOGS_LABEL,
            }
        )
    candidates.sort(key=lambda c: (0 if c.get("writable") else 1, c.get("mount_point") or ""))
    best = candidates[0] if candidates else None
    if best and best.get("writable"):
        root = Path(str(best["mount_point"])) / SETUP_LOGS_SUBDIR
        return {
            "detected": True,
            "mount_point": best["mount_point"],
            "evidence_root": str(root),
            "persistent": True,
            "non_persistent": False,
            "warning": None,
            "persistence_mode": "setup_logs",
        }
    return {
        "detected": False,
        "mount_point": None,
        "evidence_root": str(_RUN_FALLBACK),
        "persistent": False,
        "non_persistent": True,
        "warning": "SETUP_LOGS nicht beschreibbar — Evidence nur unter /run (nicht persistent).",
        "persistence_mode": "run_fallback",
    }


def resolve_rescue_evidence_root(*, runner: Any = None) -> dict[str, Any]:
    """Prefer SETUP_LOGS, then setuphelfer-evidence on ESP, then /run fallback."""
    logs = detect_setup_logs_mount(runner=runner)
    if logs.get("persistent"):
        return logs
    from core.rescue_persistence import build_rescue_evidence_root

    stick = build_rescue_evidence_root(runner=runner)
    if not stick.get("fallback"):
        return {
            "detected": True,
            "mount_point": stick.get("mount_point"),
            "evidence_root": stick.get("evidence_root"),
            "persistent": True,
            "non_persistent": False,
            "warning": stick.get("warning"),
            "persistence_mode": stick.get("persistence_mode"),
        }
    return logs
