"""
Read-only early hardware baseline API.

PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 12.

Every route here is read-only or triggers only a bounded, safe "quick"
probe (a small in-process memory/CPU integrity check, never a system-level
stress test). No route writes to disk, changes a driver, installs a
package, or starts a SMART self-test. No route named ``/apply``,
``/install``, ``/flash``, ``/write``, ``/format``, ``/partition``,
``/firmware/update``, ``/driver/install``, ``/smart/self-test/start`` or
similar exists in this module (enforced by ``test_hardware_baseline_api_v1.py``).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from core.hardware_baseline_contracts import HardwareBaselineResult
from core.hardware_inventory import collect_pci_devices
from rescue.hardware_baseline_orchestrator import run_hardware_baseline
from rescue.hardware_baseline_storage_discovery import discover_storage_devices_for_baseline

router = APIRouter(tags=["rescue-hardware-baseline"])

_LAST_BASELINE: dict[str, HardwareBaselineResult] = {}


def _read_kernel_cmdline() -> str:
    try:
        return Path("/proc/cmdline").read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _current_platform_pci_devices() -> tuple[list[Any], str]:
    devices, _missing = collect_pci_devices()
    return devices, _read_kernel_cmdline()


def _run_baseline(mode: str) -> HardwareBaselineResult:
    pci_devices, cmdline_raw = _current_platform_pci_devices()
    storage_devices = discover_storage_devices_for_baseline()
    result = run_hardware_baseline(
        mode=mode,
        pci_devices=pci_devices,
        cmdline_raw=cmdline_raw,
        storage_devices=storage_devices,
    )
    _LAST_BASELINE["latest"] = result
    return result


def _require_latest() -> HardwareBaselineResult:
    result = _LAST_BASELINE.get("latest")
    if result is None:
        raise HTTPException(status_code=404, detail="hardware_baseline_not_run_yet")
    return result


def _find_subsystem(result: HardwareBaselineResult, subsystem: str):
    for s in result.subsystems:
        if s.subsystem == subsystem:
            return s
    return None


@router.get("/api/rescue/hardware/baseline/status")
async def get_hardware_baseline_status() -> dict[str, Any]:
    result = _LAST_BASELINE.get("latest")
    if result is None:
        return {"has_run": False}
    return {
        "has_run": True,
        "run_id": result.run_id,
        "collected_at": result.collected_at,
        "mode": result.mode,
        "gate": result.gate.to_dict(),
    }


@router.post("/api/rescue/hardware/baseline/quick")
async def post_hardware_baseline_quick() -> dict[str, Any]:
    return _run_baseline("quick").to_dict()


@router.post("/api/rescue/hardware/baseline/extended-preview")
async def post_hardware_baseline_extended_preview() -> dict[str, Any]:
    """Runs the same read-only baseline checks as ``/quick`` but surfaces
    extended-test *recommendations* more prominently. Never starts an
    actual extended test (e.g. Memtest86+/SMART extended self-test/GPU
    render stress) — those always require explicit, separate operator
    action outside this API."""
    return _run_baseline("extended_preview").to_dict()


@router.get("/api/rescue/hardware/baseline/latest")
async def get_hardware_baseline_latest() -> dict[str, Any]:
    return _require_latest().to_dict()


@router.get("/api/rescue/hardware/baseline/memory")
async def get_hardware_baseline_memory() -> dict[str, Any]:
    result = _require_latest()
    subsystem = _find_subsystem(result, "memory")
    if subsystem is None:
        raise HTTPException(status_code=404, detail="memory_baseline_not_found")
    return subsystem.to_dict()


@router.get("/api/rescue/hardware/baseline/cpu")
async def get_hardware_baseline_cpu() -> dict[str, Any]:
    result = _require_latest()
    subsystem = _find_subsystem(result, "cpu")
    if subsystem is None:
        raise HTTPException(status_code=404, detail="cpu_baseline_not_found")
    return subsystem.to_dict()


@router.get("/api/rescue/hardware/baseline/gpu")
async def get_hardware_baseline_gpu() -> dict[str, Any]:
    result = _require_latest()
    subsystem = _find_subsystem(result, "gpu")
    if subsystem is None:
        raise HTTPException(status_code=404, detail="gpu_baseline_not_found")
    return subsystem.to_dict()


@router.get("/api/rescue/hardware/baseline/storage")
async def get_hardware_baseline_storage() -> dict[str, Any]:
    result = _require_latest()
    storage_subsystems = {"hdd", "sata_ssd", "nvme"}
    devices = [s.to_dict() for s in result.subsystems if s.subsystem in storage_subsystems]
    return {"devices": devices}


@router.get("/api/rescue/hardware/baseline/storage/{device_id}")
async def get_hardware_baseline_storage_device(device_id: str) -> dict[str, Any]:
    result = _require_latest()
    storage_subsystems = {"hdd", "sata_ssd", "nvme"}
    for s in result.subsystems:
        if s.subsystem in storage_subsystems and s.device_id == device_id:
            return s.to_dict()
    raise HTTPException(status_code=404, detail="storage_baseline_device_not_found")


__all__ = ["router"]
