"""
Scanner detection — read-only, rescue-stick specific.

PI-RS-HW-COMPAT-PROVISION-001 Phase 8 (scanner half).

A scanner function detected on a multifunction device is always reported
independently from that device's printer function (never "scanner works because
printer works"). No scan is ever triggered by this module.
"""

from __future__ import annotations

from typing import Any

SCANNER_DETECTION_VERSION = 1


def parse_scanimage_l(text: str) -> list[dict[str, str]]:
    """Parse ``scanimage -L`` ("device `<backend:device>' is a <Vendor> <Model> ...")."""
    out: list[dict[str, str]] = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line.startswith("device `"):
            continue
        try:
            backend_device = line.split("`", 1)[1].split("'", 1)[0]
            rest = line.split("'", 1)[1]
            description = rest.split(" is a ", 1)[1].strip() if " is a " in rest else rest.strip()
        except IndexError:
            continue
        out.append({"backend_device": backend_device, "description": description})
    return out


def parse_sane_find_scanner(text: str) -> list[dict[str, str]]:
    """Parse ``sane-find-scanner`` USB lines ("found USB scanner (vendor=0x... [Name])")."""
    out: list[dict[str, str]] = []
    for line in (text or "").splitlines():
        low = line.lower()
        if "found usb scanner" in low or "found usb processor" in low:
            out.append({"raw_line": line.strip()})
    return out


def classify_scanner_source(*, has_sane_backend: bool, has_escl: bool, is_usb_still_image: bool) -> str:
    """usb_still_image|sane_backend|escl_airscan|network_mfp|unknown."""
    if has_sane_backend:
        return "sane_backend"
    if has_escl:
        return "escl_airscan"
    if is_usb_still_image:
        return "usb_still_image"
    return "unknown"


def build_scanner_report(
    *,
    device_id: str,
    is_usb_still_image: bool = False,
    has_sane_backend: bool = False,
    has_escl: bool = False,
    is_network_device: bool = False,
) -> dict[str, Any]:
    source = classify_scanner_source(
        has_sane_backend=has_sane_backend, has_escl=has_escl, is_usb_still_image=is_usb_still_image
    )
    operational_status = "ready" if source in ("sane_backend", "escl_airscan") else "review_required"
    if source == "unknown":
        operational_status = "unknown"

    return {
        "device_id": device_id,
        "source": source,
        "is_network_device": is_network_device,
        "operational_status": operational_status,
        "requires_physical_scan_test": True,
        "operator_action_required_for_test": True,
    }


def build_scanner_detection_diagnostics() -> dict[str, Any]:
    return {
        "detection_version": SCANNER_DETECTION_VERSION,
        "module": "peripherals.scanner_detection",
        "read_only": True,
        "writes_allowed": False,
        "scan_triggered": False,
    }


__all__ = [
    "SCANNER_DETECTION_VERSION",
    "parse_scanimage_l",
    "parse_sane_find_scanner",
    "classify_scanner_source",
    "build_scanner_report",
    "build_scanner_detection_diagnostics",
]
