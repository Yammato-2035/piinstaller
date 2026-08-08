"""
Driver/firmware gap engine — concrete per-device gap reports.

PI-RS-ASUS-AUTONOMOUS-DIAG-INSTALL-007 Phase 5.

Never emits bare claims like \"nvidia broken\". Each device entry names the
hardware id, expected module, presence/load state, firmware request, packages,
risk and confidence.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from core.hardware_baseline_contracts import BaselineStatus
from core.kernel_event_classification import (
    detect_intentional_driver_blacklist,
    parse_modprobe_blacklist_modules,
)
from rescue.driver_failure_resolver import resolve_driver_failure

DRIVER_FIRMWARE_GAP_ENGINE_VERSION = 1

_GAP_STATUSES = frozenset(
    {
        "operational",
        "driver_missing",
        "firmware_missing",
        "driver_intentionally_disabled",
        "degraded",
        "unknown",
    }
)

_VENDOR_BY_PCI = {
    "10de": "nvidia",
    "1002": "amd",
    "1022": "amd",
    "8086": "intel",
}


def _norm_hex_id(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text.startswith("0x"):
        text = text[2:]
    return text


def _infer_vendor(device: Mapping[str, Any]) -> str:
    vid = _norm_hex_id(device.get("vendor_id"))
    if vid in _VENDOR_BY_PCI:
        return _VENDOR_BY_PCI[vid]
    modalias = str(device.get("modalias") or "").lower()
    if "v000010de" in modalias or "nvidia" in modalias:
        return "nvidia"
    if "v00001002" in modalias or "amdgpu" in modalias:
        return "amd"
    if "v00008086" in modalias or "i915" in modalias:
        return "intel"
    for name in device.get("candidate_modules") or ():
        low = str(name).lower()
        if low.startswith("nvidia") or low == "nouveau":
            return "nvidia"
        if low in ("amdgpu", "radeon"):
            return "amd"
        if low in ("i915", "xe"):
            return "intel"
    return ""


def _as_bool(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)


def _risk_for_status(status: str) -> str:
    if status in ("operational", "driver_intentionally_disabled"):
        return "low"
    if status == "degraded":
        return "medium"
    if status in ("driver_missing", "firmware_missing"):
        return "high"
    return "medium"


def _evaluate_one_device(
    device: Mapping[str, Any],
    *,
    cmdline: str,
    secure_boot_enabled: bool | None,
    kernel_release: str,
) -> dict[str, Any]:
    hardware_id = str(device.get("device_id") or device.get("pci_address") or "unknown")
    modalias = str(device.get("modalias") or "")
    candidates = [str(x) for x in (device.get("candidate_modules") or ()) if str(x).strip()]
    bound = str(device.get("bound_driver") or "")
    expected_hint = bound or (candidates[0] if candidates else "")

    module_present_in = _as_bool(device.get("module_present"))
    module_loaded_in = _as_bool(device.get("module_loaded"))
    firmware_present_in = _as_bool(device.get("firmware_present"))
    firmware_requested = str(device.get("firmware_requested") or "")

    module_files: dict[str, bool] = {}
    if expected_hint and module_present_in is not None:
        module_files[expected_hint] = module_present_in
    for name in candidates:
        if name not in module_files and module_present_in is not None:
            module_files[name] = module_present_in

    loaded_modules: list[str] = []
    if module_loaded_in and bound:
        loaded_modules = [bound]
    elif module_loaded_in and expected_hint:
        loaded_modules = [expected_hint]

    firmware_files: dict[str, bool] = {}
    if firmware_requested and firmware_present_in is not None:
        firmware_files[firmware_requested] = firmware_present_in

    failure = resolve_driver_failure(
        device=hardware_id,
        vendor_id=str(device.get("vendor_id") or ""),
        product_id=str(device.get("product_id") or ""),
        modalias=modalias,
        bound_driver=bound,
        candidate_modules=candidates,
        module_files_present=module_files or None,
        loaded_modules=loaded_modules,
        firmware_files_present=firmware_files or None,
        cmdline=cmdline,
        secure_boot_enabled=secure_boot_enabled,
        package_candidates=list(device.get("package_candidates") or ()),
        kernel_release=kernel_release,
    )

    expected_module = failure.get("required_driver")
    module_present = module_present_in if module_present_in is not None else bool(failure.get("driver_present"))
    module_loaded = module_loaded_in if module_loaded_in is not None else bool(failure.get("driver_loaded"))

    missing_firmware = list(failure.get("missing_firmware") or [])
    if firmware_requested:
        firmware_request = firmware_requested
    elif missing_firmware:
        firmware_request = missing_firmware[0]
    else:
        firmware_request = ""

    if firmware_present_in is not None:
        firmware_file_present = firmware_present_in
    elif missing_firmware:
        firmware_file_present = False
    elif firmware_request:
        firmware_file_present = False
    else:
        firmware_file_present = True

    vendor = _infer_vendor(device)
    intentional_tokens = detect_intentional_driver_blacklist(cmdline, vendor) if vendor else []
    blacklisted_modules = parse_modprobe_blacklist_modules(cmdline)
    expected_blacklisted = bool(expected_module and expected_module in blacklisted_modules)
    intentionally_disabled = bool(intentional_tokens or expected_blacklisted or failure.get("blacklisted"))

    kernel_error = device.get("kernel_error")
    operational_validation: str | None = None

    if intentionally_disabled and not module_loaded and not bound:
        status = "driver_intentionally_disabled"
        operational_validation = BaselineStatus.NOT_TESTED.value
        confidence = 0.9
    elif not expected_module:
        status = "unknown"
        confidence = float(failure.get("confidence") or 0.35)
    elif missing_firmware or (firmware_request and firmware_file_present is False and not module_loaded):
        status = "firmware_missing"
        confidence = float(failure.get("confidence") or 0.7)
    elif not module_present:
        status = "driver_missing"
        confidence = float(failure.get("confidence") or 0.75)
    elif module_loaded and firmware_file_present is not False:
        status = "operational"
        confidence = float(failure.get("confidence") or 0.85)
    elif module_present and not module_loaded:
        status = "degraded"
        confidence = float(failure.get("confidence") or 0.65)
    elif kernel_error:
        status = "degraded"
        confidence = float(failure.get("confidence") or 0.6)
    else:
        status = "unknown"
        confidence = float(failure.get("confidence") or 0.4)

    if status not in _GAP_STATUSES:
        status = "unknown"

    entry: dict[str, Any] = {
        "hardware_id": hardware_id,
        "modalias": modalias,
        "expected_module": expected_module,
        "module_present": bool(module_present),
        "module_loaded": bool(module_loaded),
        "firmware_request": firmware_request,
        "firmware_file_present": bool(firmware_file_present),
        "package_candidates": list(failure.get("package_candidates") or []),
        "risk": _risk_for_status(status),
        "confidence": confidence,
        "status": status,
        "device_class": device.get("device_class"),
        "vendor_id": device.get("vendor_id"),
        "product_id": device.get("product_id"),
        "pci_address": device.get("pci_address"),
        "kernel_error": kernel_error,
        "kernel_release": kernel_release or None,
        "secure_boot_review_required": bool(failure.get("secure_boot_review_required")),
        "intentional_blacklist_evidence": intentional_tokens,
        "technical_summary": failure.get("technical_summary"),
        "recommended_next_action": failure.get("recommended_next_action"),
    }
    if operational_validation is not None:
        entry["operational_validation"] = operational_validation
    return entry


def build_driver_gap_report(
    devices: list[dict] | Sequence[Mapping[str, Any]],
    *,
    cmdline: str = "",
    secure_boot_enabled: bool | None = None,
    kernel_release: str = "",
) -> dict[str, Any]:
    """
    Build a concrete driver/firmware gap report for the given device dicts.

    Injectable inputs only — no shell, no sysfs reads.
    """
    entries = [
        _evaluate_one_device(
            dict(device or {}),
            cmdline=cmdline or "",
            secure_boot_enabled=secure_boot_enabled,
            kernel_release=kernel_release or "",
        )
        for device in (devices or [])
    ]

    by_status: dict[str, int] = {}
    for entry in entries:
        by_status[entry["status"]] = by_status.get(entry["status"], 0) + 1

    gaps = [
        e
        for e in entries
        if e["status"] in ("driver_missing", "firmware_missing", "degraded", "unknown")
    ]

    return {
        "engine_version": DRIVER_FIRMWARE_GAP_ENGINE_VERSION,
        "schema_version": "driver-firmware-gap-report.v1",
        "kernel_release": kernel_release or None,
        "secure_boot_enabled": secure_boot_enabled,
        "cmdline": cmdline or "",
        "devices": entries,
        "gap_count": len(gaps),
        "status_counts": by_status,
        "writes_allowed": False,
        "read_only": True,
    }


__all__ = [
    "DRIVER_FIRMWARE_GAP_ENGINE_VERSION",
    "build_driver_gap_report",
]
