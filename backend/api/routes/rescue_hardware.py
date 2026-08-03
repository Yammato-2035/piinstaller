"""
Read-only rescue hardware inventory/detection API.

PI-RS-HW-COMPAT-PROVISION-001 Phase 14.

Every route here is read-only or preview-only. No route named ``/apply``,
``/install``, ``/flash``, ``/write``, ``/format``, ``/partition``,
``/firmware/update``, ``/driver/install``, ``/driver/activate``,
``/eeprom/update`` or ``/bios/update`` exists in this module (enforced by
``test_hardware_api_readonly_v1.py``).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from core.cpu_platform_detection import build_cpu_platform_details
from core.driver_activation_plan import build_driver_activation_preview
from core.driver_resolver import resolve_driver_plan
from core.gpu_detection import build_gpu_report
from core.gpu_driver_resolver import resolve_gpu_driver_plan
from core.hardware_compat_catalog import match_catalog_entry
from core.hardware_inventory import (
    collect_hardware_inventory,
    build_hardware_inventory_summary,
    write_hardware_inventory_evidence,
)
from core.hardware_contracts import HardwareDevice, HardwareInventory, PlatformIdentity
from core.input_device_detection import build_input_device_report
from core.mainboard_chipset_detection import build_mainboard_chipset_report, read_dmi_fields
from core.usb_device_detection import classify_usb_device, collect_usb_class_info, is_composite_device

router = APIRouter(tags=["rescue-hardware"])

_LAST_INVENTORY: dict[str, HardwareInventory] = {}


def _current_inventory() -> HardwareInventory:
    dmi_fields = read_dmi_fields()
    platform = PlatformIdentity(
        platform_class="unknown",
        system_vendor=dmi_fields.get("sys_vendor"),
        system_product=dmi_fields.get("product_name"),
    )
    inventory = collect_hardware_inventory(platform=platform)
    _LAST_INVENTORY["latest"] = inventory
    return inventory


@router.get("/api/rescue/hardware/inventory")
async def get_hardware_inventory() -> dict[str, Any]:
    inventory = _LAST_INVENTORY.get("latest") or _current_inventory()
    return inventory.to_dict()


@router.post("/api/rescue/hardware/scan")
async def post_hardware_scan() -> dict[str, Any]:
    inventory = _current_inventory()
    paths = write_hardware_inventory_evidence(inventory)
    return {
        "run_id": inventory.run_id,
        "summary": build_hardware_inventory_summary(inventory),
        "evidence_paths": {k: str(v) for k, v in paths.items()},
    }


@router.get("/api/rescue/hardware/devices")
async def get_hardware_devices() -> dict[str, Any]:
    inventory = _LAST_INVENTORY.get("latest") or _current_inventory()
    return {"devices": [d.to_dict() for d in inventory.devices]}


def _find_device(device_id: str) -> HardwareDevice:
    inventory = _LAST_INVENTORY.get("latest") or _current_inventory()
    for device in inventory.devices:
        if device.device_id == device_id:
            return device
    raise HTTPException(status_code=404, detail="device_not_found")


@router.get("/api/rescue/hardware/devices/{device_id}")
async def get_hardware_device(device_id: str) -> dict[str, Any]:
    return _find_device(device_id).to_dict()


@router.get("/api/rescue/hardware/devices/{device_id}/driver-plan")
async def get_hardware_device_driver_plan(device_id: str) -> dict[str, Any]:
    device = _find_device(device_id)
    quirk_entry = None
    catalog_match = match_catalog_entry(vendor_id=device.vendor_id, product_id=device.product_id)
    if catalog_match:
        quirk_entry = dict(catalog_match.get("driver_recommendation") or {})
        quirk_entry["known_issues"] = catalog_match.get("known_issues") or []
    plan = resolve_driver_plan(device, quirk_entry=quirk_entry)
    return build_driver_activation_preview(plan)


@router.get("/api/rescue/hardware/cpu")
async def get_hardware_cpu() -> dict[str, Any]:
    return build_cpu_platform_details()


@router.get("/api/rescue/hardware/gpus")
async def get_hardware_gpus() -> dict[str, Any]:
    inventory = _LAST_INVENTORY.get("latest") or _current_inventory()
    pci_devices = [d for d in inventory.devices if d.device_class == "pci"]
    reports = build_gpu_report(pci_devices=pci_devices)
    for entry in reports:
        entry["driver_plan_preview"] = resolve_gpu_driver_plan(entry)
    return {"gpus": reports}


@router.get("/api/rescue/hardware/mainboard")
async def get_hardware_mainboard() -> dict[str, Any]:
    inventory = _LAST_INVENTORY.get("latest") or _current_inventory()
    pci_devices = [d for d in inventory.devices if d.device_class == "pci"]
    return build_mainboard_chipset_report(pci_devices=pci_devices, is_raspberry_pi=inventory.platform.is_raspberry_pi)


@router.get("/api/rescue/hardware/usb")
async def get_hardware_usb() -> dict[str, Any]:
    """Two independent, honestly-separate views (spec: bus/device numbering from
    ``lsusb`` and sysfs topology IDs are different identifier spaces — this route
    never fabricates a cross-reference between them):

    - ``lsusb_devices``: vendor/product identity from the generic inventory (Phase 3)
    - ``usb_functions``: per-sysfs-entry function classification (Phase 6)
    """
    inventory = _LAST_INVENTORY.get("latest") or _current_inventory()
    usb_devices = [d for d in inventory.devices if d.device_class == "usb"]
    class_info_by_sysfs_id = collect_usb_class_info()
    usb_functions = [
        {
            "sysfs_id": sysfs_id,
            "functions": [c.to_dict() for c in classify_usb_device(device_id=f"usb:{sysfs_id}", class_info=info)],
            "is_composite": is_composite_device(info),
        }
        for sysfs_id, info in class_info_by_sysfs_id.items()
    ]
    return {
        "lsusb_devices": [d.to_dict() for d in usb_devices],
        "usb_functions": usb_functions,
    }


@router.get("/api/rescue/hardware/input")
async def get_hardware_input() -> dict[str, Any]:
    inventory = _LAST_INVENTORY.get("latest") or _current_inventory()
    input_devices = [d for d in inventory.devices if d.device_class == "input"]
    return {"input_devices": build_input_device_report(input_devices)}


__all__ = ["router"]
