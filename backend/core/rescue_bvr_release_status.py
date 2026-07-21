"""Release-safe read-only Rescue BVR status (PI-RS-BVR-GUI-VT-PROGRESS-002)."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.rescue_bvr_dcc_status import (
    SUPPORTED_LOCALES,
    evaluate_i18n_status,
    load_physical_result,
    map_overall_status,
)
from core.rescue_canonical_bvr_progress import (
    gui_status_from_canonical,
    read_progress_for_display,
)

_HOME_PATH_RE = re.compile(r"/home/[^/\s]+")
_SECRETISH = re.compile(r"(token|secret|password|api[_-]?key|authorization)", re.I)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _redact_text(value: str) -> str:
    text = _HOME_PATH_RE.sub("/home/<redacted>", value or "")
    if _SECRETISH.search(text):
        return "<redacted>"
    return text


def _traffic_light(value: str) -> str:
    s = (value or "").lower()
    if s in {"green", "passed", "visible", "match", "complete"}:
        return "green"
    if s in {"yellow", "passed_with_gui_fallback", "fallback", "partial", "incomplete"}:
        return "yellow"
    if s in {"red", "failed", "mismatch", "missing"}:
        return "red"
    return "unknown"


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _payload_version(repo_root: Path) -> str:
    for cand in (
        repo_root / "config/rescue_payload_version.json",
        Path("/opt/setuphelfer/config/rescue_payload_version.json"),
        Path("/opt/setuphelfer-rescue/config/rescue_payload_version.json"),
    ):
        data = _read_json(cand) or {}
        ver = str(data.get("rescue_payload_version") or "").strip()
        if ver:
            return ver
    return ""


def _product_version(repo_root: Path) -> str:
    for cand in (
        repo_root / "config/version.json",
        Path("/opt/setuphelfer/config/version.json"),
    ):
        data = _read_json(cand) or {}
        ver = str(data.get("project_version") or "").strip()
        if ver:
            return ver
    return ""


def build_release_rescue_bvr_status(
    *,
    repo_root: Path,
    version_drift_status: str = "unknown",
    deploy_drift_status: str = "unknown",
) -> dict[str, Any]:
    """Sanitized, least-privilege status for release runtime (no developer capability)."""
    physical = load_physical_result(repo_root) or {}
    progress = read_progress_for_display()
    gui_payload = gui_status_from_canonical(progress)
    i18n_status, locales, _missing = evaluate_i18n_status(repo_root)

    overall = str(physical.get("overall_status") or "")
    if not overall:
        if progress.get("terminal") and str(progress.get("status") or "") == "passed":
            overall = "passed"
        elif progress.get("terminal"):
            overall = str(progress.get("status") or "unknown")
        else:
            overall = "unknown"

    gui_block = progress.get("gui") if isinstance(progress.get("gui"), dict) else {}
    gui_status = str(gui_block.get("status") or "")
    if not gui_status:
        if physical.get("gui_visible") is True:
            gui_status = "visible"
        elif physical.get("watchdog_fallback") or overall == "passed_with_gui_fallback":
            gui_status = "fallback"
        elif physical.get("gui_failure_code"):
            gui_status = "failed"
        else:
            gui_status = "unknown"

    bvr = progress.get("bvr") if isinstance(progress.get("bvr"), dict) else {}
    if not any(bvr.values()) and physical:
        bvr = {
            "backup": "passed" if overall in {"passed", "passed_with_gui_fallback"} else "unknown",
            "verify": "passed" if overall in {"passed", "passed_with_gui_fallback"} else "unknown",
            "restore": "passed" if overall in {"passed", "passed_with_gui_fallback"} else "unknown",
            "manifest": "match" if overall in {"passed", "passed_with_gui_fallback"} else "unknown",
        }

    evidence_available = bool(physical.get("evidence_imported")) or (
        (repo_root / "docs/evidence/rescue/bvr-gui-vt-progress-002").is_dir()
    )

    error_code = physical.get("gui_failure_code") or None
    if isinstance(error_code, str):
        error_code = _redact_text(error_code)

    mapped = map_overall_status(
        bvr_core_status="passed" if overall in {"passed", "passed_with_gui_fallback"} else (
            "failed" if overall == "failed" else "unknown"
        ),
        gui_status=gui_status if gui_status != "unknown" else "unknown",
        evidence_status="complete" if evidence_available else "missing",
    )
    if overall and overall != "unknown":
        mapped = overall

    status_top = "ok"
    if mapped in {"failed"}:
        status_top = "failed"
    elif mapped in {"passed_with_gui_fallback", "passed_with_progress_warning", "review_required"}:
        status_top = "review_required"
    elif mapped in {"unknown", "implemented_pending_physical_retest"}:
        status_top = "unknown"

    next_key = "maintain_green"
    if gui_status == "fallback":
        next_key = "investigate_gui_fallback"
    elif mapped == "implemented_pending_physical_retest":
        next_key = "run_physical_msi_retest"
    elif mapped == "failed":
        next_key = "collect_evidence_and_triage"
    elif status_top == "unknown":
        next_key = "collect_physical_msi_evidence"

    return {
        "status": status_top,
        "product_version": _product_version(repo_root),
        "payload_version": _payload_version(repo_root) or str(physical.get("payload_version") or ""),
        "last_run_id": _redact_text(str(physical.get("run_id") or progress.get("run_id") or "")),
        "last_run_status": mapped,
        "bvr": {
            "backup": str(bvr.get("backup") or "unknown"),
            "verify": str(bvr.get("verify") or "unknown"),
            "restore": str(bvr.get("restore") or "unknown"),
            "manifest": str(bvr.get("manifest") or "unknown"),
        },
        "gui": {
            "status": gui_status,
            "error_code": error_code,
            "vt": gui_block.get("active_vt"),
        },
        "progress": {
            "phase": str(progress.get("phase") or gui_payload.get("phase") or "unknown"),
            "sequence": int(progress.get("sequence") or gui_payload.get("sequence") or 0),
            "terminal": bool(progress.get("terminal")),
        },
        "locales": list(locales or SUPPORTED_LOCALES),
        "i18n_status": i18n_status,
        "version_drift": _traffic_light(version_drift_status),
        "deploy_drift": _traffic_light(deploy_drift_status),
        "evidence_available": evidence_available,
        "updated_at": str(progress.get("updated_at") or _utc_now()),
        "next_action_key": next_key,
        "read_only": True,
        "developer_capability_required": False,
    }
