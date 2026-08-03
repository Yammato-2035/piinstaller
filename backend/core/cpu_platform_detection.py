"""
CPU / SoC platform detection — read-only, normalized HardwareDevice for the CPU.

PI-RS-HW-COMPAT-PROVISION-001 Phase 4 (CPU/SoC half).

Relationship to existing code (see docs/evidence/rescue/hardware-compat-001/
HARDWARE_DISCOVERY_IST_AUDIT.md): ``core.hardware_discovery`` already exposes
display-oriented CPU helpers (``get_cpu_name``, ``get_cpu_summary``) for the
product app's System-Info tab. This module does not reuse or replace those —
it builds a separate, structured ``HardwareDevice`` aimed at driver/firmware
status rather than a pretty display string, and every source is injectable so
tests never depend on a real ``/proc``/``lscpu``.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any, Callable

from core.hardware_contracts import Bus, HardwareDevice, HardwareDriverState

CPU_PLATFORM_DETECTION_VERSION = 1

Runner = Callable[..., "subprocess.CompletedProcess[str]"] | None

_KNOWN_ARCHITECTURES = {"x86_64", "i686", "armv7l", "aarch64"}

# Virtualization capability flags per architecture family.
_VIRT_FLAGS_X86 = {"vmx", "svm"}

_RASPBERRY_PI_COMPATIBLE_MARKERS = ("raspberrypi", "brcm,bcm2")


def _run_tool(argv: list[str], *, runner: Runner = None, timeout: int = 10) -> tuple[str, bool]:
    try:
        if runner is not None:
            result = runner(argv, capture_output=True, text=True, timeout=timeout)
        else:
            result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)  # noqa: S603
        return (result.stdout or ""), True
    except FileNotFoundError:
        return "", False
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
        return "", False


def normalize_architecture(uname_machine: str | None) -> str:
    """Map ``uname -m`` output to the spec's stable architecture vocabulary."""
    m = (uname_machine or "").strip().lower()
    if m == "x86_64":
        return "x86_64"
    if m in ("i686", "i586", "i486", "i386"):
        return "i686"
    if m in ("armv7l", "armv7"):
        return "armv7"
    if m in ("aarch64", "arm64"):
        return "aarch64"
    return "unknown"


def parse_lscpu(text: str) -> dict[str, str]:
    """Parse ``lscpu`` colon-delimited output into a flat field map."""
    fields: dict[str, str] = {}
    for line in (text or "").splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def parse_cpuinfo_first_block(text: str) -> dict[str, str]:
    """Parse the first processor block of ``/proc/cpuinfo`` into a flat field map."""
    block = (text or "").split("\n\n")[0]
    fields: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def detect_virtualization_available(flags_text: str, architecture: str) -> bool:
    flags = set((flags_text or "").split())
    if architecture in ("x86_64", "i686"):
        return bool(flags & _VIRT_FLAGS_X86)
    # ARM virtualization extension detection is not reliably exposed via /proc/cpuinfo
    # flags; stay conservative rather than guessing.
    return False


def detect_microcode_status(cpuinfo_fields: dict[str, str]) -> str:
    """Return 'present' | 'unknown' — never guess a version we cannot verify."""
    if cpuinfo_fields.get("microcode"):
        return "present"
    return "unknown"


def is_raspberry_pi_soc(compatible_text: str | None) -> bool:
    text = (compatible_text or "").lower()
    return any(marker in text for marker in _RASPBERRY_PI_COMPATIBLE_MARKERS)


def collect_thermal_sources(*, sysfs_root: Path | None = None) -> list[str]:
    """List thermal zone *names* only (no numeric read here — see gpu/cpu telemetry)."""
    root = sysfs_root or Path("/")
    base = root / "sys" / "class" / "thermal"
    if not base.exists():
        return []
    names: list[str] = []
    try:
        for zone in sorted(base.glob("thermal_zone*")):
            type_path = zone / "type"
            if type_path.exists():
                try:
                    names.append(type_path.read_text(encoding="utf-8", errors="ignore").strip())
                except OSError:
                    continue
    except OSError:
        pass
    return names


def detect_cpu_platform(
    *,
    lscpu_raw: str | None = None,
    cpuinfo_raw: str | None = None,
    uname_machine_raw: str | None = None,
    device_tree_compatible: str | None = None,
    runner: Runner = None,
    sysfs_root: Path | None = None,
) -> tuple[HardwareDevice, list[str]]:
    """Build the normalized CPU/SoC HardwareDevice. Returns (device, missing_tools)."""
    missing: list[str] = []

    lscpu_text = lscpu_raw
    if lscpu_text is None:
        lscpu_text, available = _run_tool(["lscpu"], runner=runner)
        if not available:
            missing.append("lscpu")
            lscpu_text = ""

    cpuinfo_text = cpuinfo_raw
    if cpuinfo_text is None:
        root = sysfs_root or Path("/")
        cpuinfo_path = root / "proc" / "cpuinfo"
        if cpuinfo_path.exists():
            try:
                cpuinfo_text = cpuinfo_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                cpuinfo_text = ""
                missing.append("proc:cpuinfo")
        else:
            cpuinfo_text = ""
            missing.append("proc:cpuinfo")

    uname_text = uname_machine_raw
    if uname_text is None:
        uname_text, available = _run_tool(["uname", "-m"], runner=runner)
        if not available:
            missing.append("uname")
            uname_text = ""

    lscpu_fields = parse_lscpu(lscpu_text)
    cpuinfo_fields = parse_cpuinfo_first_block(cpuinfo_text)

    architecture = normalize_architecture(uname_text or lscpu_fields.get("Architecture"))
    vendor = lscpu_fields.get("Vendor ID") or cpuinfo_fields.get("vendor_id")
    family = lscpu_fields.get("CPU family") or cpuinfo_fields.get("cpu family")
    model = lscpu_fields.get("Model") or cpuinfo_fields.get("model")
    stepping = lscpu_fields.get("Stepping") or cpuinfo_fields.get("stepping")
    model_name = lscpu_fields.get("Model name") or cpuinfo_fields.get("model name")

    cores_per_socket = lscpu_fields.get("Core(s) per socket")
    sockets = lscpu_fields.get("Socket(s)")
    threads_per_core = lscpu_fields.get("Thread(s) per core")
    flags_text = lscpu_fields.get("Flags") or cpuinfo_fields.get("flags") or cpuinfo_fields.get("Features") or ""

    is_pi_soc = is_raspberry_pi_soc(device_tree_compatible)

    virt_available = detect_virtualization_available(flags_text, architecture)
    microcode_status = detect_microcode_status(cpuinfo_fields)

    details: dict[str, Any] = {
        "cores_per_socket": cores_per_socket,
        "sockets": sockets,
        "threads_per_core": threads_per_core,
        "virtualization_available": virt_available,
        "microcode_status": microcode_status,
        "is_raspberry_pi_soc": is_pi_soc,
        "relevant_flags": sorted(set(flags_text.split()) & (_VIRT_FLAGS_X86 | {"aes", "sha_ni", "avx2", "avx512f", "neon"})),
    }

    device = HardwareDevice(
        device_id="cpu:0",
        device_class="cpu",
        subclass="soc" if is_pi_soc else "processor",
        bus=Bus.PLATFORM if is_pi_soc else Bus.UNKNOWN,
        vendor_name=vendor,
        product_name=model_name,
        model_name=model_name,
        driver=HardwareDriverState(),
        operational_status="ready" if model_name else "unknown",
        detection_confidence=0.95 if model_name else 0.3,
    )
    # Attach the structured extras via to_dict()-time consumers; the dataclass itself
    # stays to the contract shape, so extras travel through the caller-level dict merge.
    return device, missing


def build_cpu_platform_details(
    *,
    lscpu_raw: str | None = None,
    cpuinfo_raw: str | None = None,
    uname_machine_raw: str | None = None,
    device_tree_compatible: str | None = None,
    runner: Runner = None,
    sysfs_root: Path | None = None,
) -> dict[str, Any]:
    """Full CPU/SoC report: HardwareDevice dict + architecture/virt/microcode extras."""
    device, missing = detect_cpu_platform(
        lscpu_raw=lscpu_raw,
        cpuinfo_raw=cpuinfo_raw,
        uname_machine_raw=uname_machine_raw,
        device_tree_compatible=device_tree_compatible,
        runner=runner,
        sysfs_root=sysfs_root,
    )
    lscpu_fields = parse_lscpu(lscpu_raw or "")
    cpuinfo_fields = parse_cpuinfo_first_block(cpuinfo_raw or "")
    flags_text = lscpu_fields.get("Flags") or cpuinfo_fields.get("flags") or cpuinfo_fields.get("Features") or ""
    architecture = normalize_architecture(uname_machine_raw or lscpu_fields.get("Architecture"))
    return {
        "device": device.to_dict(),
        "architecture": architecture,
        "cores_per_socket": lscpu_fields.get("Core(s) per socket"),
        "sockets": lscpu_fields.get("Socket(s)"),
        "threads_per_core": lscpu_fields.get("Thread(s) per core"),
        "virtualization_available": detect_virtualization_available(flags_text, architecture),
        "microcode_status": detect_microcode_status(cpuinfo_fields),
        "is_raspberry_pi_soc": is_raspberry_pi_soc(device_tree_compatible),
        "thermal_sources": collect_thermal_sources(sysfs_root=sysfs_root),
        "missing_tools": missing,
    }


def build_cpu_platform_detection_diagnostics() -> dict[str, Any]:
    return {
        "detection_version": CPU_PLATFORM_DETECTION_VERSION,
        "module": "core.cpu_platform_detection",
        "read_only": True,
        "writes_allowed": False,
        "known_architectures": sorted(_KNOWN_ARCHITECTURES),
    }


__all__ = [
    "CPU_PLATFORM_DETECTION_VERSION",
    "normalize_architecture",
    "parse_lscpu",
    "parse_cpuinfo_first_block",
    "detect_virtualization_available",
    "detect_microcode_status",
    "is_raspberry_pi_soc",
    "collect_thermal_sources",
    "detect_cpu_platform",
    "build_cpu_platform_details",
    "build_cpu_platform_detection_diagnostics",
]
