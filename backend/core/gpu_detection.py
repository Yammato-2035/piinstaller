"""
GPU / display readiness detection — read-only.

PI-RS-HW-COMPAT-PROVISION-001 Phase 5.

Keeps every stage of "GPU per PCI erkannt" -> "Treiber in use" -> "Modul geladen"
-> "DRM-Gerät erzeugt" -> "Displayconnector vorhanden" -> "aktive Kernelparameter"
separate (spec requirement). Never collapses "driver candidate known" into
"device ready".

Consumes ``HardwareDevice`` rows from ``hardware_inventory.collect_pci_devices`` —
this module does not run ``lspci`` itself (single PCI parser, see audit doc).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from core.hardware_contracts import HardwareDevice

GPU_DETECTION_VERSION = 1

_VGA_3D_DISPLAY_MARKERS = ("vga", "3d controller", "display controller")

_VENDOR_BY_PCI_ID = {
    "8086": "intel",
    "1002": "amd",
    "1022": "amd",  # some AMD APU host-side IDs
    "10de": "nvidia",
}

_INTEL_MODESET_PARAM = "i915.modeset=0"
_AMD_MODESET_PARAM = "amdgpu.modeset=0"
_NOUVEAU_MODESET_PARAM = "nouveau.modeset=0"


def is_gpu_pci_device(device: HardwareDevice) -> bool:
    name = (device.product_name or "").lower()
    return any(marker in name for marker in _VGA_3D_DISPLAY_MARKERS)


def classify_gpu_vendor(device: HardwareDevice) -> str:
    if device.vendor_id and device.vendor_id.lower() in _VENDOR_BY_PCI_ID:
        return _VENDOR_BY_PCI_ID[device.vendor_id.lower()]
    name = (device.product_name or "").lower()
    if "intel" in name:
        return "intel"
    if "nvidia" in name:
        return "nvidia"
    # "ati"/"amd" require word boundaries — generic PCI strings like "VGA compatible
    # controller" contain "ati" as a substring of "compatible" and would otherwise
    # be misclassified as AMD.
    if "radeon" in name or re.search(r"\bamd\b", name) or re.search(r"\bati\b", name):
        return "amd"
    return "unknown"


def classify_gpu_type(device: HardwareDevice, vendor: str) -> str:
    """integrated|discrete|unknown — Intel is always integrated in this generation of
    hardware assumptions; AMD/NVIDIA require a name heuristic; unclear cases stay
    unknown rather than guessed."""
    name = (device.product_name or "").lower()
    if vendor == "intel":
        return "integrated"
    if vendor == "amd":
        if any(k in name for k in ("radeon graphics", "vega", "raphael", "phoenix", "renoir", "cezanne")):
            return "integrated"
        if "rx " in name or "radeon rx" in name:
            return "discrete"
        return "unknown"
    if vendor == "nvidia":
        return "discrete"
    return "unknown"


def parse_kernel_cmdline(text: str) -> set[str]:
    return set((text or "").split())


def detect_disabling_cmdline_params(cmdline_params: set[str], vendor: str, *, cmdline_raw: str = "") -> list[str]:
    from core.kernel_event_classification import detect_intentional_driver_blacklist

    found: list[str] = []
    if "nomodeset" in cmdline_params:
        found.append("nomodeset")
    vendor_param = {"intel": _INTEL_MODESET_PARAM, "amd": _AMD_MODESET_PARAM, "nvidia": _NOUVEAU_MODESET_PARAM}.get(
        vendor
    )
    if vendor_param and vendor_param in cmdline_params:
        found.append(vendor_param)
    # Prefer original cmdline string for modprobe.blacklist=a,b,c parsing.
    raw = cmdline_raw or " ".join(sorted(cmdline_params))
    found.extend(detect_intentional_driver_blacklist(raw, vendor))
    # stable unique order
    seen: set[str] = set()
    ordered: list[str] = []
    for item in found:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def resolve_drm_card_for_pci(device_id: str, *, sysfs_root: Path | None = None) -> str | None:
    """Map a PCI GPU device_id (``pci:BB:DD.F`` / ``pci:0000:BB:DD.F``) to DRM cardN."""
    root = sysfs_root or Path("/")
    raw = (device_id or "").removeprefix("pci:")
    candidates = [raw]
    if re.match(r"^[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9a-fA-F]$", raw):
        candidates.append(f"0000:{raw}")
    for addr in candidates:
        drm_dir = root / "sys" / "bus" / "pci" / "devices" / addr / "drm"
        if not drm_dir.exists():
            continue
        try:
            for entry in sorted(drm_dir.iterdir()):
                if re.fullmatch(r"card\d+", entry.name):
                    return entry.name
        except OSError:
            continue
    return None


def collect_drm_cards(*, sysfs_root: Path | None = None) -> dict[str, list[dict[str, str]]]:
    """Map DRM card name -> list of {connector, status} (no EDID content read here)."""
    root = sysfs_root or Path("/")
    base = root / "sys" / "class" / "drm"
    out: dict[str, list[dict[str, str]]] = {}
    if not base.exists():
        return out
    try:
        for entry in sorted(base.iterdir()):
            if "-" not in entry.name:
                continue  # only connector entries look like cardN-HDMI-A-1
            card_name, _, connector = entry.name.partition("-")
            status_path = entry / "status"
            status = "unknown"
            if status_path.exists():
                try:
                    status = status_path.read_text(encoding="utf-8", errors="ignore").strip() or "unknown"
                except OSError:
                    pass
            out.setdefault(card_name, []).append({"connector": connector, "status": status})
    except OSError:
        pass
    return out


_GPU_DRIVER_CANDIDATES = {
    "intel": ("i915", "xe"),
    "amd": ("amdgpu",),
    "nvidia": ("nouveau", "nvidia"),
}


def build_gpu_report(
    *,
    pci_devices: list[HardwareDevice],
    cmdline_raw: str = "",
    sysfs_root: Path | None = None,
) -> list[dict[str, Any]]:
    """One report entry per detected GPU PCI device."""
    cmdline_params = parse_kernel_cmdline(cmdline_raw)
    drm_cards = collect_drm_cards(sysfs_root=sysfs_root)
    reports: list[dict[str, Any]] = []

    gpu_devices = [d for d in pci_devices if is_gpu_pci_device(d)]
    for idx, device in enumerate(gpu_devices):
        vendor = classify_gpu_vendor(device)
        gpu_type = classify_gpu_type(device, vendor)
        driver_in_use = device.driver.kernel_driver_in_use
        candidates = _GPU_DRIVER_CANDIDATES.get(vendor, ())
        disabling_params = detect_disabling_cmdline_params(cmdline_params, vendor, cmdline_raw=cmdline_raw)
        intentional_blacklist = any(p.startswith("modprobe.blacklist=") for p in disabling_params)
        # Prefer PCI→DRM sysfs mapping; fall back to discovery-order card{idx}.
        card_key = resolve_drm_card_for_pci(device.device_id, sysfs_root=sysfs_root) or f"card{idx}"
        connectors = drm_cards.get(card_key, [])
        drm_card_present = card_key in drm_cards
        active_connectors = [c for c in connectors if c["status"] == "connected"]

        operational_validation = "not_tested"
        if intentional_blacklist and not driver_in_use:
            gpu_status = "driver_intentionally_disabled"
            operational_validation = "not_tested"
        elif disabling_params and not intentional_blacklist:
            gpu_status = "disabled_by_cmdline"
        elif not driver_in_use:
            gpu_status = "driver_missing" if candidates else "unknown"
        elif not drm_card_present:
            gpu_status = "limited"
        elif not active_connectors:
            gpu_status = "limited"
        else:
            gpu_status = "ready"
            operational_validation = "baseline_connectors_ok"

        gui_boot_recommendation = "gui_possible" if gpu_status == "ready" else "safe_tui_only"
        safe_boot_profile = "remove_nomodeset_recommended" if "nomodeset" in disabling_params else "default"

        reports.append(
            {
                "device_id": device.device_id,
                "vendor": vendor,
                "gpu_type": gpu_type,
                "product_name": device.product_name,
                "driver_in_use": driver_in_use,
                "driver_candidates": list(candidates),
                "drm_card": card_key,
                "drm_card_present": drm_card_present,
                "connectors": connectors,
                "active_connector_count": len(active_connectors),
                "disabling_cmdline_params": disabling_params,
                "gpu_status": gpu_status,
                "operational_validation": operational_validation,
                "gui_boot_recommendation": gui_boot_recommendation,
                "safe_boot_profile": safe_boot_profile,
                "physical_test_required": True,
            }
        )
    return reports


def build_gpu_detection_diagnostics() -> dict[str, Any]:
    return {
        "detection_version": GPU_DETECTION_VERSION,
        "module": "core.gpu_detection",
        "read_only": True,
        "writes_allowed": False,
        "blacklist_modified": False,
    }


__all__ = [
    "GPU_DETECTION_VERSION",
    "is_gpu_pci_device",
    "classify_gpu_vendor",
    "classify_gpu_type",
    "parse_kernel_cmdline",
    "detect_disabling_cmdline_params",
    "resolve_drm_card_for_pci",
    "collect_drm_cards",
    "build_gpu_report",
    "build_gpu_detection_diagnostics",
]
