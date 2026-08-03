"""
Read-only printer/scanner detection API.

PI-RS-HW-COMPAT-PROVISION-001 Phase 14 (peripherals half).

Read-only: only ``lpstat -v`` / ``lpinfo -v`` / ``scanimage -L`` /
``sane-find-scanner`` are invoked (all pure enumeration, no test print/scan, no
CUPS queue is created or modified — spec PHASE 8).
"""

from __future__ import annotations

import shutil
import subprocess
from typing import Any

from fastapi import APIRouter

from peripherals.printer_detection import build_printer_report, parse_lpinfo_v, parse_lpstat_v
from peripherals.printer_driver_resolver import resolve_printer_driver_plan
from peripherals.scanner_detection import build_scanner_report, parse_sane_find_scanner, parse_scanimage_l
from peripherals.scanner_driver_resolver import resolve_scanner_driver_plan

router = APIRouter(tags=["rescue-peripherals"])

_LAST_PRINTERS: dict[str, list[dict[str, Any]]] = {}
_LAST_SCANNERS: dict[str, list[dict[str, Any]]] = {}


def _run_readonly(argv: list[str]) -> str | None:
    if shutil.which(argv[0]) is None:
        return None
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=10, check=False)
        return result.stdout or ""
    except (OSError, subprocess.SubprocessError):
        return None


def _scan_printers() -> list[dict[str, Any]]:
    lpstat_text = _run_readonly(["lpstat", "-v"])
    lpinfo_text = _run_readonly(["lpinfo", "-v"])
    queues = parse_lpstat_v(lpstat_text or "")
    discovered = parse_lpinfo_v(lpinfo_text or "")

    reports: list[dict[str, Any]] = []
    for queue in queues:
        report = build_printer_report(device_id=f"cups:{queue['queue_name']}", has_printer_function=True)
        report["queue_name"] = queue["queue_name"]
        report["device_uri"] = queue["device_uri"]
        report["driver_plan_preview"] = resolve_printer_driver_plan(report)
        reports.append(report)
    for idx, entry in enumerate(discovered):
        report = build_printer_report(device_id=f"lpinfo:{idx}", has_printer_function=True)
        report["scheme"] = entry["scheme"]
        report["device_uri"] = entry["uri"]
        report["driver_plan_preview"] = resolve_printer_driver_plan(report)
        reports.append(report)

    _LAST_PRINTERS["latest"] = reports
    return reports


def _scan_scanners() -> list[dict[str, Any]]:
    scanimage_text = _run_readonly(["scanimage", "-L"])
    sane_find_text = _run_readonly(["sane-find-scanner"])
    scanimage_devices = parse_scanimage_l(scanimage_text or "")
    sane_find_devices = parse_sane_find_scanner(sane_find_text or "")

    reports: list[dict[str, Any]] = []
    for idx, dev in enumerate(scanimage_devices):
        report = build_scanner_report(device_id=f"sane:{idx}", has_sane_backend=True)
        report.update({k: v for k, v in dev.items()})
        report["driver_plan_preview"] = resolve_scanner_driver_plan(report)
        reports.append(report)
    for idx, dev in enumerate(sane_find_devices):
        report = build_scanner_report(device_id=f"usb_still_image:{idx}", is_usb_still_image=True)
        report.update({k: v for k, v in dev.items()})
        report["driver_plan_preview"] = resolve_scanner_driver_plan(report)
        reports.append(report)

    _LAST_SCANNERS["latest"] = reports
    return reports


@router.get("/api/rescue/peripherals/printers")
async def get_peripherals_printers() -> dict[str, Any]:
    reports = _LAST_PRINTERS.get("latest")
    if reports is None:
        reports = _scan_printers()
    return {"printers": reports}


@router.post("/api/rescue/peripherals/printers/scan")
async def post_peripherals_printers_scan() -> dict[str, Any]:
    return {"printers": _scan_printers()}


@router.get("/api/rescue/peripherals/scanners")
async def get_peripherals_scanners() -> dict[str, Any]:
    reports = _LAST_SCANNERS.get("latest")
    if reports is None:
        reports = _scan_scanners()
    return {"scanners": reports}


@router.post("/api/rescue/peripherals/scanners/scan")
async def post_peripherals_scanners_scan() -> dict[str, Any]:
    return {"scanners": _scan_scanners()}


__all__ = ["router"]
