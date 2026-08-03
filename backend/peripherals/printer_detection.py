"""
Printer detection — read-only, rescue-stick specific.

PI-RS-HW-COMPAT-PROVISION-001 Phase 8 (printer half).

Strict rule (spec): printer technology (matrix/inkjet/laser/thermal/label) and color
capability (monochrome/color) must never be guessed from a free-text model name.
They stay ``"unknown"`` / ``classification_status = "review_required"`` unless backed
by explicit IPP capability attributes, PPD metadata, or a curated catalog entry
(``data/hardware/hardware_compat_catalog.json``, Phase 10).

No test print. No CUPS queue is created or modified by this module.
"""

from __future__ import annotations

import re
from typing import Any

PRINTER_DETECTION_VERSION = 1

_ALLOWED_TECHNOLOGIES = {"matrix", "inkjet", "laser", "thermal", "label", "unknown"}
_ALLOWED_COLOR_CAPABILITIES = {"monochrome", "color", "unknown"}
_ALLOWED_DEVICE_KINDS = {"printer", "multifunction", "scanner", "fax_multifunction", "unknown"}


def parse_lpstat_v(text: str) -> list[dict[str, str]]:
    """Parse ``lpstat -v`` ("device for <queue>: <uri>") into queue/uri pairs."""
    out: list[dict[str, str]] = []
    pattern = re.compile(r"^device for (?P<queue>\S+):\s*(?P<uri>\S+)")
    for line in (text or "").splitlines():
        m = pattern.match(line.strip())
        if m:
            out.append({"queue_name": m.group("queue"), "device_uri": m.group("uri")})
    return out


def parse_lpinfo_v(text: str) -> list[dict[str, str]]:
    """Parse ``lpinfo -v`` ("<scheme> <uri>") discovered-but-unconfigured devices."""
    out: list[dict[str, str]] = []
    for line in (text or "").splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) == 2:
            out.append({"scheme": parts[0], "uri": parts[1]})
    return out


def classify_printer_technology(
    *, ipp_output_supported: str | None = None, ppd_text: str | None = None
) -> tuple[str, str]:
    """Return (technology, classification_status). Defaults to unknown/review_required."""
    if ipp_output_supported:
        val = ipp_output_supported.lower()
        for tech in ("laser", "inkjet", "thermal", "label", "matrix"):
            if tech in val:
                return tech, "confirmed"
    if ppd_text:
        low = ppd_text.lower()
        if "*technology" in low or "*modelname" in low:
            for tech in ("laser", "inkjet", "thermal", "label", "matrix", "dot matrix", "impact"):
                if tech in low:
                    normalized = "matrix" if tech in ("dot matrix", "impact") else tech
                    return normalized, "confirmed"
    return "unknown", "review_required"


def classify_color_capability(
    *, ipp_color_supported: bool | None = None, ppd_text: str | None = None
) -> tuple[str, str]:
    if ipp_color_supported is True:
        return "color", "confirmed"
    if ipp_color_supported is False:
        return "monochrome", "confirmed"
    if ppd_text:
        low = ppd_text.lower()
        if "*colordevice: true" in low:
            return "color", "confirmed"
        if "*colordevice: false" in low:
            return "monochrome", "confirmed"
    return "unknown", "review_required"


def classify_device_kind(*, has_printer_function: bool, has_scanner_function: bool, has_fax_function: bool = False) -> str:
    if has_printer_function and has_scanner_function:
        return "fax_multifunction" if has_fax_function else "multifunction"
    if has_printer_function:
        return "printer"
    if has_scanner_function:
        return "scanner"
    return "unknown"


def build_printer_report(
    *,
    device_id: str,
    has_printer_function: bool,
    has_scanner_function: bool = False,
    has_fax_function: bool = False,
    ipp_output_supported: str | None = None,
    ipp_color_supported: bool | None = None,
    ppd_text: str | None = None,
    driverless_ipp_supported: bool = False,
) -> dict[str, Any]:
    """Build one printer report entry. Driverless IPP is preferred over any distro
    driver package (see driver order rule PHASE 8) when the environment supports it."""
    technology, tech_status = classify_printer_technology(ipp_output_supported=ipp_output_supported, ppd_text=ppd_text)
    color, color_status = classify_color_capability(ipp_color_supported=ipp_color_supported, ppd_text=ppd_text)
    device_kind = classify_device_kind(
        has_printer_function=has_printer_function,
        has_scanner_function=has_scanner_function,
        has_fax_function=has_fax_function,
    )
    classification_status = "review_required" if "review_required" in (tech_status, color_status) else "confirmed"

    driver_order = []
    if driverless_ipp_supported:
        driver_order.append("driverless_ipp")
    driver_order.extend(["distribution_driver", "generic_free_driver", "curated_vendor_package", "proprietary_optional"])

    return {
        "device_id": device_id,
        "device_kind": device_kind,
        "technology": technology,
        "color_capability": color,
        "classification_status": classification_status,
        "driver_order": driver_order,
        "requires_physical_print_test": True,
        "operator_action_required_for_test": True,
    }


def build_printer_detection_diagnostics() -> dict[str, Any]:
    return {
        "detection_version": PRINTER_DETECTION_VERSION,
        "module": "peripherals.printer_detection",
        "read_only": True,
        "writes_allowed": False,
        "test_print_triggered": False,
        "cups_queue_modified": False,
        "allowed_technologies": sorted(_ALLOWED_TECHNOLOGIES),
        "allowed_color_capabilities": sorted(_ALLOWED_COLOR_CAPABILITIES),
        "allowed_device_kinds": sorted(_ALLOWED_DEVICE_KINDS),
    }


__all__ = [
    "PRINTER_DETECTION_VERSION",
    "parse_lpstat_v",
    "parse_lpinfo_v",
    "classify_printer_technology",
    "classify_color_capability",
    "classify_device_kind",
    "build_printer_report",
    "build_printer_detection_diagnostics",
]
