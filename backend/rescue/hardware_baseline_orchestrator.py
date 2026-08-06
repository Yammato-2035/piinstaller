"""
Hardware baseline startup orchestrator — sequences all subsystem checks.

PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 10.

Runs the memory/CPU/GPU/storage baseline builders in sequence, dispatches
each storage device to the correct per-class builder (HDD/SATA-SSD/NVMe)
based on ``core.storage_health_normalizer.classify_device_class``, and
aggregates everything into one ``HardwareBaselineResult`` including the
additive safety gate from ``hardware_baseline_gate``. Every fixture
(``meminfo_text``, ``dmesg_text``, per-device SMART/NVMe raw text, etc.) is
injectable so this never has to touch the real system in tests.

Two modes:

- ``"quick"``: bounded quick probes run (memory/CPU), no long-running tests.
- ``"extended_preview"``: same checks, but callers may additionally request
  the extended-test *recommendations* to be surfaced more prominently in
  the UI layer — this module itself never starts an actual extended test
  in either mode (spec: baseline never auto-starts an extended test).
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, Callable

from core.cpu_baseline_diagnostics import build_cpu_baseline_result
from core.gpu_baseline_diagnostics import build_gpu_baseline_result
from core.hardware_baseline_contracts import HardwareBaselineResult, _utc_now
from core.hardware_contracts import HardwareDevice
from core.hdd_baseline_diagnostics import build_hdd_baseline_result
from core.memory_baseline_diagnostics import build_memory_baseline_result
from core.nvme_baseline_diagnostics import build_nvme_baseline_result
from core.sata_ssd_baseline_diagnostics import build_sata_ssd_baseline_result
from rescue.hardware_baseline_gate import build_hardware_baseline_gate

HARDWARE_BASELINE_ORCHESTRATOR_VERSION = 1

Runner = Callable[..., Any] | None

_VALID_MODES = ("quick", "extended_preview")


def _dispatch_storage_device(device: dict[str, Any], *, sysfs_root: Path | None, dmesg_text: str | None, runner: Runner):
    device_id = device["device_id"]
    device_class = device.get("device_class", "unknown")

    if device_class == "virtual":
        return None
    if device_class == "nvme":
        return build_nvme_baseline_result(
            device_id=device_id,
            smart_log_raw=device.get("smart_log_raw"),
            id_ctrl_raw=device.get("id_ctrl_raw"),
            nvme_cli_available=device.get("nvme_cli_available", True),
            dmesg_text=dmesg_text,
            runner=runner,
        )
    if device_class == "non_rotational":
        return build_sata_ssd_baseline_result(
            device_id=device_id,
            smart_health_raw=device.get("smart_health_raw"),
            smart_attributes_raw=device.get("smart_attributes_raw"),
            smartctl_available=device.get("smartctl_available", True),
            dmesg_text=dmesg_text,
            sysfs_root=sysfs_root,
            runner=runner,
        )
    # rotational, usb_bridge, and unknown all fall back to the HDD builder,
    # which degrades gracefully to TEST_UNAVAILABLE when smartctl/attributes
    # are absent (the conservative choice for a class we can't fully trust).
    return build_hdd_baseline_result(
        device_id=device_id,
        smart_health_raw=device.get("smart_health_raw"),
        smart_attributes_raw=device.get("smart_attributes_raw"),
        smartctl_available=device.get("smartctl_available", True),
        dmesg_text=dmesg_text,
        runner=runner,
    )


def run_hardware_baseline(
    *,
    mode: str = "quick",
    run_id: str | None = None,
    pci_devices: list[HardwareDevice] | None = None,
    cmdline_raw: str = "",
    storage_devices: list[dict[str, Any]] | None = None,
    meminfo_text: str | None = None,
    dmidecode_text: str | None = None,
    dmesg_text: str | None = None,
    sysfs_root: Path | None = None,
    dev_root: Path | None = None,
    runner: Runner = None,
    skip_quick_probes: bool = False,
) -> HardwareBaselineResult:
    if mode not in _VALID_MODES:
        raise ValueError(f"Unknown hardware baseline mode: {mode!r} (expected one of {_VALID_MODES}).")

    memory_result = build_memory_baseline_result(
        meminfo_text=meminfo_text,
        dmidecode_text=dmidecode_text,
        dmesg_text=dmesg_text,
        runner=runner,
        skip_quick_probe=skip_quick_probes,
    )
    cpu_result = build_cpu_baseline_result(
        dmesg_text=dmesg_text,
        sysfs_root=sysfs_root,
        runner=runner,
        skip_quick_probe=skip_quick_probes,
    )
    gpu_result = build_gpu_baseline_result(
        pci_devices=pci_devices or [],
        cmdline_raw=cmdline_raw,
        sysfs_root=sysfs_root,
        dev_root=dev_root,
        dmesg_text=dmesg_text,
        runner=runner,
        run_optional_probes=True,
    )

    storage_results = []
    for device in storage_devices or []:
        result = _dispatch_storage_device(device, sysfs_root=sysfs_root, dmesg_text=dmesg_text, runner=runner)
        if result is not None:
            storage_results.append(result)

    gate = build_hardware_baseline_gate(memory=memory_result, cpu=cpu_result, gpu=gpu_result, storage=storage_results)

    subsystems = (memory_result, cpu_result, gpu_result, *storage_results)
    total_duration_ms = sum(s.duration_ms for s in subsystems)

    return HardwareBaselineResult(
        run_id=run_id or uuid.uuid4().hex,
        collected_at=_utc_now(),
        mode=mode,
        subsystems=subsystems,
        gate=gate,
        total_duration_ms=total_duration_ms,
    )


def build_hardware_baseline_orchestrator_diagnostics() -> dict[str, Any]:
    return {
        "module_version": HARDWARE_BASELINE_ORCHESTRATOR_VERSION,
        "module": "rescue.hardware_baseline_orchestrator",
        "read_only": True,
        "valid_modes": list(_VALID_MODES),
        "starts_extended_test_automatically": False,
    }


__all__ = [
    "HARDWARE_BASELINE_ORCHESTRATOR_VERSION",
    "run_hardware_baseline",
    "build_hardware_baseline_orchestrator_diagnostics",
]
