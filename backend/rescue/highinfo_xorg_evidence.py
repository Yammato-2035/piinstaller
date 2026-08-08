"""HIGHINFO Xorg/startx evidence record + SETUP_LOGS mirror helpers.

PI-RS-ASUS-HIGHINFO-PHYSICAL-009 — persist boot-scoped Xorg proof independently
of GUI success. Never attributes stale previous-boot artifacts to the current boot.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

HIGHINFO_XORG_EVIDENCE_VERSION = 1
DEFAULT_RELATIVE_RECORD = "boot/highinfo/xorg_probe_evidence.json"


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def classify_evidence_origin(
    *,
    artifact_boot_id: str | None,
    current_boot_id: str | None,
    artifact_stamp: str | None = None,
    current_stamp: str | None = None,
) -> str:
    """Return current_boot | stale_previous_boot | unknown_origin."""
    a = (artifact_boot_id or "").strip()
    c = (current_boot_id or "").strip()
    if a and c and a == c:
        return "current_boot"
    if a and c and a != c:
        return "stale_previous_boot"
    if artifact_stamp and current_stamp and artifact_stamp != current_stamp:
        return "stale_previous_boot"
    if a or artifact_stamp:
        return "unknown_origin"
    return "unknown_origin"


def build_highinfo_xorg_evidence_record(
    *,
    boot_id: str,
    run_id: str,
    startx_invoked: bool,
    startx_exit_code: int | None = None,
    xorg_log_found: bool = False,
    xorg_log_path: str | None = None,
    display_server: str = "xorg",
    evidence_mirrored: bool = False,
    mirrored_at: str | None = None,
    errors: Sequence[str] | None = None,
    warnings: Sequence[str] | None = None,
    reason: str | None = None,
    xorg_probe_status: str | None = None,
    profile: str = "ASUS-TUI-BASELINE-HIGHINFO",
) -> dict[str, Any]:
    """Build the boot-scoped HIGHINFO Xorg evidence contract."""
    errs = [str(e) for e in (errors or ()) if e]
    warns = [str(w) for w in (warnings or ()) if w]
    rec: dict[str, Any] = {
        "schema_version": HIGHINFO_XORG_EVIDENCE_VERSION,
        "schema": "highinfo-xorg-evidence.v1",
        "profile": profile,
        "boot_id": str(boot_id or "unknown"),
        "run_id": str(run_id or "unknown"),
        "startx_invoked": bool(startx_invoked),
        "startx_exit_code": startx_exit_code,
        "xorg_log_found": bool(xorg_log_found),
        "xorg_log_path": xorg_log_path,
        "display_server": display_server,
        "evidence_mirrored": bool(evidence_mirrored),
        "mirrored_at": mirrored_at,
        "errors": errs,
        "warnings": warns,
        "xorg_probe_status": xorg_probe_status,
        "finished_at": _now_iso(),
    }
    if not startx_invoked:
        rec["reason"] = reason or "startx_not_invoked"
        rec["xorg_log_found"] = False
        if xorg_log_path is None:
            rec["xorg_log_path"] = None
    elif reason:
        rec["reason"] = reason
    return rec


def resolve_setup_logs_evidence_roots(
    candidates: Sequence[str | Path] | None = None,
) -> list[Path]:
    """Return existing SETUP_LOGS (or esp-rw) evidence roots."""
    default = [
        Path("/run/setuphelfer/esp-rw/setuphelfer/evidence"),
        *sorted(Path("/media").glob("*/SETUP_LOGS*/setuphelfer/evidence")),
        *sorted(Path("/media").glob("*/SETUP_LOGS/setuphelfer/evidence")),
    ]
    roots: list[Path] = []
    for cand in candidates if candidates is not None else default:
        p = Path(cand)
        if p.is_dir():
            roots.append(p)
    return roots


def mirror_path_to_roots(
    src: Path,
    relative_dest: str,
    roots: Sequence[Path],
) -> dict[str, Any]:
    """Copy a file or directory into each evidence root under relative_dest."""
    copied: list[str] = []
    errors: list[str] = []
    if not src.exists():
        return {"copied": copied, "errors": [f"source_missing:{src}"], "mirrored": False}
    rel = relative_dest.lstrip("/")
    for root in roots:
        dest = root / rel
        try:
            if src.is_dir():
                dest.mkdir(parents=True, exist_ok=True)
                for child in src.iterdir():
                    target = dest / child.name
                    if child.is_dir():
                        if target.exists():
                            shutil.rmtree(target)
                        shutil.copytree(child, target)
                    else:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(child, target)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
            copied.append(str(dest))
        except OSError as exc:
            errors.append(f"{dest}:{exc}")
    return {"copied": copied, "errors": errors, "mirrored": bool(copied) and not errors}


def write_and_mirror_highinfo_xorg_evidence(
    record: Mapping[str, Any],
    *,
    local_path: Path,
    relative_dest: str = DEFAULT_RELATIVE_RECORD,
    setup_logs_roots: Sequence[Path] | None = None,
) -> dict[str, Any]:
    """Write local JSON record and mirror to SETUP_LOGS roots when available."""
    local_path = Path(local_path)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    body = dict(record)
    roots = list(setup_logs_roots) if setup_logs_roots is not None else resolve_setup_logs_evidence_roots()
    mirrored_at = None
    mirror_result: dict[str, Any] = {"copied": [], "errors": [], "mirrored": False}
    # Write local first without mirrored flag, then update after mirror.
    body["evidence_mirrored"] = False
    body["mirrored_at"] = None
    local_path.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if roots:
        mirrored_at = _now_iso()
        mirror_result = mirror_path_to_roots(local_path, relative_dest, roots)
        body["evidence_mirrored"] = bool(mirror_result.get("mirrored"))
        body["mirrored_at"] = mirrored_at if body["evidence_mirrored"] else None
        if mirror_result.get("errors"):
            errs = list(body.get("errors") or [])
            errs.extend(str(e) for e in mirror_result["errors"])
            body["errors"] = errs
        local_path.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        # Re-mirror updated record
        if body["evidence_mirrored"]:
            mirror_path_to_roots(local_path, relative_dest, roots)
    else:
        warns = list(body.get("warnings") or [])
        warns.append("setup_logs_evidence_root_unavailable")
        body["warnings"] = warns
        local_path.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return {
        "local_path": str(local_path),
        "record": body,
        "mirror": mirror_result,
        "roots": [str(r) for r in roots],
    }


__all__ = [
    "HIGHINFO_XORG_EVIDENCE_VERSION",
    "DEFAULT_RELATIVE_RECORD",
    "build_highinfo_xorg_evidence_record",
    "classify_evidence_origin",
    "resolve_setup_logs_evidence_roots",
    "mirror_path_to_roots",
    "write_and_mirror_highinfo_xorg_evidence",
]
