"""
Concrete driver/firmware failure naming for rescue hardware diagnostics.

PI-RS-ASUS-EMERGENCY-LINUX-TELEMETRY-003 Phase 6.

Builds on ``core.driver_resolver`` without duplicating its plan vocabulary.
Never emits a bare \"driver missing\" without naming the device and candidate.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from core.driver_resolver import resolve_driver_plan
from core.hardware_contracts import Bus, HardwareDevice, HardwareDriverState


def _parse_modinfo(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in (text or "").splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        out[key.strip().lower()] = value.strip()
    return out


def _firmware_from_modinfo(modinfo: Mapping[str, str]) -> list[str]:
    raw = modinfo.get("firmware") or ""
    if not raw:
        return []
    return [p.strip() for p in re.split(r"[\s,]+", raw) if p.strip()]


def resolve_driver_failure(
    *,
    device: str,
    vendor_id: str = "",
    product_id: str = "",
    modalias: str = "",
    bound_driver: str = "",
    candidate_modules: Sequence[str] | None = None,
    modules_alias_text: str = "",
    modprobe_resolve_output: str = "",
    modinfo_by_module: Mapping[str, str] | None = None,
    loaded_modules: Sequence[str] | None = None,
    module_files_present: Mapping[str, bool] | None = None,
    firmware_files_present: Mapping[str, bool] | None = None,
    blacklist_text: str = "",
    cmdline: str = "",
    secure_boot_enabled: bool | None = None,
    package_candidates: Sequence[str] | None = None,
    offline_cache_available: bool = False,
    network_install_candidate: bool = False,
    kernel_release: str = "",
) -> dict[str, Any]:
    """
    Produce a concrete driver/firmware failure report for one device.

    All probes are injectable via parameters — no mandatory shell execution.
    """
    candidates = list(candidate_modules or [])
    if modprobe_resolve_output:
        for token in re.split(r"\s+", modprobe_resolve_output.strip()):
            if token and token not in candidates:
                candidates.append(token)
    if modules_alias_text and modalias:
        for line in modules_alias_text.splitlines():
            if modalias in line or (vendor_id and product_id and vendor_id in line and product_id in line):
                parts = line.split()
                if parts:
                    mod = parts[-1]
                    if mod not in candidates:
                        candidates.append(mod)

    required = bound_driver or (candidates[0] if candidates else "")
    loaded = set(loaded_modules or [])
    files = dict(module_files_present or {})
    firmware_present_map = dict(firmware_files_present or {})

    modinfo_map = {k: _parse_modinfo(v) for k, v in (modinfo_by_module or {}).items()}
    missing_firmware: list[str] = []
    for mod in candidates or ([required] if required else []):
        for fw in _firmware_from_modinfo(modinfo_map.get(mod, {})):
            if firmware_present_map.get(fw) is False or (
                fw not in firmware_present_map and firmware_files_present is not None
            ):
                if fw not in missing_firmware:
                    missing_firmware.append(fw)

    blacklisted = False
    if required and blacklist_text and re.search(rf"\bblacklist\s+{re.escape(required)}\b", blacklist_text):
        blacklisted = True
    if required and cmdline and re.search(rf"modprobe\.blacklist=[^\s]*\b{re.escape(required)}\b", cmdline):
        blacklisted = True

    module_for_kernel = bool(required) and files.get(required, False)
    driver_loaded = bool(required) and required in loaded
    driver_present = bool(required) and (module_for_kernel or driver_loaded or bool(candidates))

    hw = HardwareDevice(
        device_id=device,
        device_class="pci",
        bus=Bus.PCI,
        vendor_id=vendor_id or None,
        product_id=product_id or None,
        kernel_modalias=modalias or None,
        driver=HardwareDriverState(
            kernel_driver_in_use=bound_driver or None,
            kernel_driver_candidates=tuple(candidates),
            kernel_modules_loaded=tuple(loaded_modules or ()),
        ),
    )
    plan = resolve_driver_plan(
        hw,
        firmware_missing=bool(missing_firmware),
        package_source="official_distribution_repository",
    )

    if not required:
        why = "no_driver_candidate_resolved_for_device"
        next_action = "capture_modalias_and_lspci_nnk_then_retry_resolution"
        confidence = 0.35
    elif blacklisted:
        why = f"module_{required}_blacklisted_by_cmdline_or_modprobe"
        next_action = f"review_blacklist_for_{required}_only_if_profile_allows"
        confidence = 0.8
    elif not driver_present:
        why = f"required_module_{required}_not_present_for_running_kernel"
        next_action = f"provide_module_or_package_for_{required}" + (f" kernel={kernel_release}" if kernel_release else "")
        confidence = 0.75
    elif not driver_loaded and missing_firmware:
        why = f"module_{required}_present_but_firmware_missing"
        next_action = "install_or_bundle_missing_firmware_files"
        confidence = 0.7
    elif not driver_loaded:
        why = f"module_{required}_present_but_not_loaded"
        next_action = f"modprobe_{required}_under_diagnostic_profile_only"
        confidence = 0.65
    else:
        why = f"driver_{required}_loaded"
        next_action = "continue_operational_probe"
        confidence = 0.85

    secure_boot_review = bool(secure_boot_enabled) and (
        (required or "").startswith("nvidia") or not module_for_kernel
    )

    # Forbidden bare claim: always name device + driver when possible.
    summary = (
        f"device={device} required_driver={required or 'unknown'} "
        f"present={driver_present} loaded={driver_loaded} reason={why}"
    )

    return {
        "device": device,
        "required_driver": required or None,
        "driver_present": driver_present,
        "driver_loaded": driver_loaded,
        "module_for_running_kernel_present": module_for_kernel,
        "missing_firmware": missing_firmware,
        "package_candidates": list(package_candidates or plan.get("package_candidates") or []),
        "offline_cache_available": bool(offline_cache_available),
        "network_install_candidate": bool(network_install_candidate),
        "secure_boot_review_required": secure_boot_review,
        "reboot_required": False,
        "recommended_next_action": next_action,
        "confidence": confidence,
        "technical_summary": summary,
        "candidate_modules": candidates,
        "blacklisted": blacklisted,
        "driver_plan": plan,
        "kernel_release": kernel_release or None,
    }


def probe_module_file(module: str, *, modules_dir: Path | None = None) -> bool:
    root = modules_dir or Path("/lib/modules")
    if not root.is_dir():
        return False
    for path in root.glob(f"*/kernel/**/{module}.ko*"):
        if path.is_file():
            return True
    return False
