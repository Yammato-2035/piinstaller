"""
Rescue stick persistence — canonical evidence directory on live medium (Phase R.3).

Read-only on internal disks; read-write only on recognized Setuphelfer rescue stick.
Falls back to RAM with explicit warning when stick persistence is not safe.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from core.storage_discovery import Runner, discover_findmnt_mounts_flat, discover_lsblk_json_tree

RESCUE_PERSISTENCE_VERSION = 3

EVIDENCE_DIR_NAME = "setuphelfer-evidence"
EVIDENCE_SUBDIRS = (
    "boot",
    "menu",
    "hardware",
    "network",
    "telemetry",
    "rescue-ui",
    "tests",
    "matrix",
    "summaries",
    "raw",
)

_STICK_LABELS = frozenset({"SETUPHELFER", "SETUPHELFER_RESCUE", "SETUPHELFER_RESCUE_LIVE"})
_LIVE_MEDIUM_PATH = Path("/run/live/medium")
_RAM_FALLBACK_ROOT = Path("/tmp/setuphelfer-evidence")
_WRITABLE_FSTYPES = frozenset({"vfat", "exfat", "ext2", "ext3", "ext4"})
_READONLY_FSTYPES = frozenset({"iso9660", "udf", "squashfs", "erofs"})
_MEDIA_RE = re.compile(r"^/media/[^/]+/SETUPHELFER", re.IGNORECASE)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalize_label(label: str) -> str:
    return (label or "").strip().upper().replace(" ", "_")


def _mount_options_readonly(options: str) -> bool:
    opts = (options or "").lower().split(",")
    return "ro" in opts and "rw" not in opts


def _is_plausible_stick_target(target: str) -> bool:
    t = (target or "").rstrip("/")
    if not t:
        return False
    if t == str(_LIVE_MEDIUM_PATH) or t.startswith(f"{_LIVE_MEDIUM_PATH}/"):
        return True
    return bool(_MEDIA_RE.match(t))


def _reject_internal_system_source(source: str, *, runner: Runner = None) -> bool:
    """True when source device is a system disk (must not be write target)."""
    src = (source or "").strip()
    if not src.startswith("/dev/"):
        return False
    try:
        from core.safe_device import list_classified_devices

        for dev in list_classified_devices(runner=runner):
            dev_id = str(getattr(dev, "id", "") or "")
            if not dev_id:
                continue
            if src == dev_id or src.startswith(dev_id.rstrip("0123456789")):
                if bool(getattr(dev, "is_system_disk", False)):
                    return True
    except Exception:
        pass
    return False


def _label_for_mount(target: str, *, runner: Runner = None) -> str:
    """Best-effort label lookup via lsblk mountpoints."""
    tgt = (target or "").rstrip("/")
    if not tgt:
        return ""
    data = discover_lsblk_json_tree(runner=runner)
    devices = data.get("blockdevices", []) or []

    def walk(nodes: list[dict[str, Any]]) -> str:
        for node in nodes:
            if not isinstance(node, dict):
                continue
            mps = node.get("mountpoints")
            mp = node.get("mountpoint")
            mounted = False
            if isinstance(mps, list) and any(str(x).rstrip("/") == tgt for x in mps if x):
                mounted = True
            elif mp and str(mp).rstrip("/") == tgt:
                mounted = True
            if mounted:
                return _normalize_label(str(node.get("label") or ""))
            children = node.get("children")
            if isinstance(children, list):
                found = walk(children)
                if found:
                    return found
        return ""

    if isinstance(devices, list):
        return walk(devices)
    return ""


def detect_rescue_stick_mount(*, runner: Runner = None) -> dict[str, Any]:
    """Detect live-medium or labeled Setuphelfer stick mount (read-only discovery)."""
    mounts = discover_findmnt_mounts_flat(runner=runner)
    candidates: list[dict[str, Any]] = []

    for fs in mounts:
        target = str(fs.get("target") or "").rstrip("/")
        source = str(fs.get("source") or "")
        fstype = str(fs.get("fstype") or "").lower()
        options = str(fs.get("options") or "")
        if not _is_plausible_stick_target(target):
            continue
        if _reject_internal_system_source(source, runner=runner):
            continue
        label = _label_for_mount(target, runner=runner)
        label_ok = not label or label in _STICK_LABELS or "SETUPHELFER" in label
        live_medium = target == str(_LIVE_MEDIUM_PATH) or target.startswith(f"{_LIVE_MEDIUM_PATH}/")
        media_setuphelfer = bool(_MEDIA_RE.match(target))
        recognized = live_medium or media_setuphelfer or label in _STICK_LABELS
        readonly_fs = fstype in _READONLY_FSTYPES or _mount_options_readonly(options)
        writable = (
            recognized
            and not readonly_fs
            and fstype in _WRITABLE_FSTYPES
            and not _mount_options_readonly(options)
        )
        score = 0
        if live_medium:
            score += 3
        if label in _STICK_LABELS:
            score += 2
        if media_setuphelfer:
            score += 2
        if writable:
            score += 1
        candidates.append(
            {
                "mount_point": target,
                "source": source,
                "fstype": fstype,
                "options": options,
                "label": label or None,
                "recognized": recognized,
                "label_ok": label_ok,
                "live_medium": live_medium,
                "readonly_medium": readonly_fs,
                "writable": writable,
                "score": score,
            }
        )

    candidates.sort(key=lambda c: int(c.get("score") or 0), reverse=True)
    best = candidates[0] if candidates else None

    if best and best.get("writable"):
        return {
            "detected": True,
            "mount_point": best["mount_point"],
            "writable_root": str(Path(best["mount_point"]) / EVIDENCE_DIR_NAME),
            "fallback": False,
            "warning": None,
            "candidates": candidates,
            "persistence_mode": "stick_rw",
        }

    warning_parts: list[str] = []
    if best and best.get("readonly_medium"):
        warning_parts.append("Live-Medium ist read-only (iso9660/udf/squashfs) — Evidence nur im RAM.")
    elif best and not best.get("recognized"):
        warning_parts.append("Stick-Mount nicht eindeutig als Setuphelfer erkannt — Evidence nur im RAM.")
    elif not best:
        warning_parts.append("Kein Live-Medium/Setuphelfer-Mount gefunden — Evidence nur im RAM.")
    else:
        warning_parts.append("Stick nicht beschreibbar — Evidence nur im RAM.")

    return {
        "detected": bool(best),
        "mount_point": best.get("mount_point") if best else None,
        "writable_root": str(_RAM_FALLBACK_ROOT),
        "fallback": True,
        "warning": " ".join(warning_parts),
        "candidates": candidates,
        "persistence_mode": "ram_fallback",
    }


def build_rescue_evidence_root(*, runner: Runner = None) -> dict[str, Any]:
    """Resolve canonical evidence root path and metadata."""
    det = detect_rescue_stick_mount(runner=runner)
    root = Path(str(det.get("writable_root") or _RAM_FALLBACK_ROOT))
    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "evidence_root": str(root),
        "evidence_dir_name": EVIDENCE_DIR_NAME,
        "fallback": bool(det.get("fallback")),
        "warning": det.get("warning"),
        "mount_point": det.get("mount_point"),
        "persistence_mode": det.get("persistence_mode"),
        "detection": det,
    }


def ensure_rescue_evidence_tree(*, runner: Runner = None) -> dict[str, Any]:
    """Create evidence subdirectories on stick or RAM fallback."""
    meta = build_rescue_evidence_root(runner=runner)
    root = Path(meta["evidence_root"])
    created: list[str] = []
    errors: list[str] = []
    for sub in EVIDENCE_SUBDIRS:
        path = root / sub
        try:
            path.mkdir(parents=True, exist_ok=True)
            created.append(str(path))
        except OSError as exc:
            errors.append(f"{sub}:{exc}")
    meta["created_dirs"] = created
    meta["errors"] = errors
    meta["tree_ready"] = len(errors) == 0
    return meta


def _resolve_write_path(subdir: str, filename: str, *, runner: Runner = None) -> tuple[Path, dict[str, Any]]:
    sub = (subdir or "raw").strip().strip("/")
    if sub not in EVIDENCE_SUBDIRS:
        sub = "raw"
    name = (filename or "evidence.json").strip()
    if not name or "/" in name or ".." in name:
        raise ValueError("invalid evidence filename")
    meta = ensure_rescue_evidence_tree(runner=runner)
    root = Path(meta["evidence_root"]).resolve()
    target = (root / sub / name).resolve()
    if not str(target).startswith(str(root)):
        raise ValueError("evidence path escapes root")
    return target, meta


def write_rescue_json_evidence(
    subdir: str,
    filename: str,
    payload: dict[str, Any] | list[Any],
    *,
    runner: Runner = None,
) -> dict[str, Any]:
    """Write JSON evidence file under /setuphelfer-evidence/<subdir>/ (stick or RAM)."""
    path, meta = _resolve_write_path(subdir, filename, runner=runner)
    body = {
        "schema_version": 1,
        "written_at": _utc_now(),
        "persistence": {
            "fallback": meta.get("fallback"),
            "warning": meta.get("warning"),
            "evidence_root": meta.get("evidence_root"),
        },
        "payload": payload,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "status": "ok",
        "path": str(path),
        "subdir": subdir,
        "filename": filename,
        "fallback": meta.get("fallback"),
        "warning": meta.get("warning"),
    }


def write_rescue_text_evidence(
    subdir: str,
    filename: str,
    text: str,
    *,
    runner: Runner = None,
) -> dict[str, Any]:
    """Write plain-text evidence under /setuphelfer-evidence/<subdir>/ (stick or RAM)."""
    path, meta = _resolve_write_path(subdir, filename, runner=runner)
    header = (
        f"# Setuphelfer Rescue Evidence\n"
        f"# written_at: {_utc_now()}\n"
        f"# fallback: {meta.get('fallback')}\n"
        f"# warning: {meta.get('warning') or 'none'}\n\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + (text or ""), encoding="utf-8")
    return {
        "status": "ok",
        "path": str(path),
        "subdir": subdir,
        "filename": filename,
        "fallback": meta.get("fallback"),
        "warning": meta.get("warning"),
    }


def write_rescue_summary(
    title: str,
    lines: list[str] | tuple[str, ...],
    *,
    runner: Runner = None,
) -> dict[str, Any]:
    """Write human-readable summary to summaries/ (md + json index)."""
    title_s = (title or "Rescue Summary").strip()
    body_lines = [str(x) for x in lines if str(x).strip()]
    md = "\n".join([f"# {title_s}", "", *body_lines, ""])
    md_result = write_rescue_text_evidence("summaries", "rescue_summary_latest.md", md, runner=runner)
    json_payload = {"title": title_s, "lines": body_lines, "generated_at": _utc_now()}
    json_result = write_rescue_json_evidence("summaries", "rescue_summary_latest.json", json_payload, runner=runner)
    return {"status": "ok", "markdown": md_result, "json": json_result}


def build_rescue_persistence_diagnostics() -> dict[str, Any]:
    return {
        "persistence_version": RESCUE_PERSISTENCE_VERSION,
        "module": "core.rescue_persistence",
        "evidence_dir_name": EVIDENCE_DIR_NAME,
        "evidence_subdirs": list(EVIDENCE_SUBDIRS),
        "stick_labels": sorted(_STICK_LABELS),
        "ram_fallback_root": str(_RAM_FALLBACK_ROOT),
        "live_medium_path": str(_LIVE_MEDIUM_PATH),
        "public_functions": [
            "detect_rescue_stick_mount",
            "build_rescue_evidence_root",
            "ensure_rescue_evidence_tree",
            "write_rescue_json_evidence",
            "write_rescue_text_evidence",
            "write_rescue_summary",
            "build_rescue_persistence_diagnostics",
        ],
        "writes_internal_disks": False,
        "read_only_discovery": True,
    }
