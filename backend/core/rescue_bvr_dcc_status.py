"""Rescue BVR + GUI status for Development Control Center (PI-RS-BVR-GUI-DCC-001)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SUPPORTED_LOCALES = ("de-DE", "en-US", "fr-FR", "nl-NL")
BASELINE_RUN_ID = "e2e-rescue-msi-20260721-232222-ba58c7a7"
TASK_ID = "PI-RS-BVR-GUI-DCC-001"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _traffic(status: str) -> str:
    s = (status or "").lower()
    if s in {"green", "passed", "visible", "complete", "available"}:
        return "green"
    if s in {"yellow", "passed_with_gui_fallback", "fallback", "active", "partial", "incomplete"}:
        return "yellow"
    if s in {"red", "failed", "missing"}:
        return "red"
    return "gray"


def load_baseline_bvr(repo_root: Path) -> dict[str, Any] | None:
    return _read_json(repo_root / "docs/evidence/rescue/bvr-gui-dcc-001/baseline_bvr_result.json")


def load_physical_result(repo_root: Path) -> dict[str, Any] | None:
    return _read_json(repo_root / "docs/evidence/rescue/bvr-gui-dcc-001/physical_msi_result.json")


def evaluate_i18n_status(repo_root: Path) -> tuple[str, list[str], list[str]]:
    locales_dir = repo_root / "scripts/rescue-live/image/locales"
    present: list[str] = []
    missing: list[str] = []
    keysets: dict[str, set[str]] = {}
    for loc in SUPPORTED_LOCALES:
        path = locales_dir / f"{loc}.json"
        if not path.is_file():
            missing.append(loc)
            continue
        data = _read_json(path) or {}
        keysets[loc] = set(data.keys())
        present.append(loc)
    if missing:
        return "incomplete", present, missing
    if not keysets:
        return "unknown", present, missing
    ref = next(iter(keysets.values()))
    if any(keys != ref for keys in keysets.values()):
        return "incomplete", present, ["keyset_mismatch"]
    return "complete", present, missing


def map_overall_status(
    *,
    bvr_core_status: str,
    gui_status: str,
    evidence_status: str,
) -> str:
    if bvr_core_status == "failed":
        return "failed"
    if evidence_status == "missing" and gui_status == "unknown":
        return "unknown"
    if bvr_core_status == "passed" and gui_status == "visible" and evidence_status == "complete":
        return "passed"
    if bvr_core_status == "passed" and gui_status in {"fallback", "failed"}:
        return "passed_with_gui_fallback"
    if bvr_core_status == "passed" and gui_status == "unknown":
        return "implemented_pending_physical_retest"
    return "review_required"


def build_rescue_bvr_dcc_status(
    *,
    repo_root: Path,
    workspace_branch: str = "",
    workspace_commit: str = "",
    origin_main_commit: str = "",
    runtime_commit: str = "",
    runtime_version: str = "",
    payload_version: str = "",
    payload_build_commit: str = "",
    usb_payload_sha256: str = "",
    version_drift_status: str = "unknown",
    deploy_drift_status: str = "unknown",
) -> dict[str, Any]:
    baseline = load_baseline_bvr(repo_root) or {}
    physical = load_physical_result(repo_root)
    i18n_status, supported, i18n_missing = evaluate_i18n_status(repo_root)

    if physical:
        run_id = str(physical.get("run_id") or "")
        overall = str(physical.get("overall_status") or "unknown")
        gui_visible = bool(physical.get("gui_visible"))
        fallback = bool(physical.get("watchdog_fallback"))
        gui_failure = physical.get("gui_failure_code")
        bvr_core = "passed" if overall in {"passed", "passed_with_gui_fallback"} else (
            "failed" if overall == "failed" else "unknown"
        )
        if gui_visible and not fallback:
            gui_status = "visible"
        elif fallback or overall == "passed_with_gui_fallback":
            gui_status = "fallback"
        elif gui_failure:
            gui_status = "failed"
        else:
            gui_status = "unknown"
        evidence_status = "complete" if physical.get("evidence_imported") else "partial"
        watchdog = "active" if fallback else "available"
    elif baseline:
        run_id = str(baseline.get("run_id") or BASELINE_RUN_ID)
        overall = str(baseline.get("overall_status") or "passed_with_gui_fallback")
        gui_status = "fallback"
        gui_failure = baseline.get("gui_failure_code") or "http_server_failed"
        bvr_core = "passed"
        evidence_status = "complete"
        watchdog = "active" if baseline.get("watchdog_fallback") else "available"
    else:
        run_id = ""
        overall = "unknown"
        gui_status = "unknown"
        gui_failure = None
        bvr_core = "unknown"
        evidence_status = "missing"
        watchdog = "unknown"

    if not physical and baseline:
        next_action = "Fix GUI HTTP runtime, rebuild payload, MSI retest required"
    elif physical and gui_status == "visible":
        next_action = "Maintain green gates; monitor drift"
    elif physical and gui_status == "fallback":
        next_action = "Investigate GUI fallback on latest physical run"
    else:
        next_action = "Collect physical MSI evidence"

    # Never paint green for unknown.
    traffic_gui = _traffic(gui_status if gui_status != "unknown" else "gray")
    traffic_bvr = _traffic(bvr_core if bvr_core != "unknown" else "gray")
    traffic_i18n = _traffic(i18n_status if i18n_status != "unknown" else "gray")
    traffic_version = _traffic(version_drift_status)
    traffic_deploy = _traffic(deploy_drift_status)
    if version_drift_status == "unknown":
        traffic_version = "gray"
    if deploy_drift_status == "unknown":
        traffic_deploy = "gray"

    overall_mapped = map_overall_status(
        bvr_core_status=bvr_core,
        gui_status=gui_status,
        evidence_status=evidence_status,
    )
    if overall and overall != "unknown":
        overall_mapped = overall

    return {
        "area": "rescue_stick",
        "task_id": TASK_ID,
        "workspace_path": str(repo_root),
        "workspace_branch": workspace_branch,
        "workspace_commit": workspace_commit,
        "origin_main_commit": origin_main_commit,
        "runtime_path": "/opt/setuphelfer",
        "runtime_commit": runtime_commit,
        "runtime_version": runtime_version,
        "payload_version": payload_version or str(baseline.get("payload_version") or ""),
        "payload_build_commit": payload_build_commit,
        "usb_payload_sha256": usb_payload_sha256,
        "last_physical_run_id": run_id,
        "last_physical_run_status": overall_mapped,
        "bvr_core_status": bvr_core,
        "gui_status": gui_status,
        "gui_failure_code": gui_failure,
        "watchdog_fallback_status": watchdog,
        "i18n_status": i18n_status,
        "i18n_missing": i18n_missing,
        "supported_locales": supported or list(SUPPORTED_LOCALES),
        "version_drift_status": version_drift_status,
        "deploy_drift_status": deploy_drift_status,
        "evidence_status": evidence_status,
        "traffic_lights": {
            "bvr_core": traffic_bvr,
            "gui": traffic_gui,
            "i18n": traffic_i18n,
            "version_drift": traffic_version,
            "deploy_drift": traffic_deploy,
            "evidence": _traffic(evidence_status if evidence_status != "missing" else "gray"),
        },
        "updated_at": _utc_now(),
        "next_action": next_action,
        "baseline_frozen": bool(baseline.get("bvr_core_frozen")),
    }
