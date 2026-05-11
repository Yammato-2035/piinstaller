from __future__ import annotations

import platform
import socket
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_models_path = Path(__file__).resolve().parent / "models.py"
_models_spec = importlib.util.spec_from_file_location("setuphelfer_inspect_models", _models_path)
if not (_models_spec and _models_spec.loader):
    raise ImportError(f"cannot load inspect models from {_models_path}")
_models_mod = importlib.util.module_from_spec(_models_spec)
sys.modules["setuphelfer_inspect_models"] = _models_mod
_models_spec.loader.exec_module(_models_mod)
InspectResult = _models_mod.InspectResult

_classifier_path = Path(__file__).resolve().parent / "classifier.py"
_classifier_spec = importlib.util.spec_from_file_location("setuphelfer_inspect_classifier", _classifier_path)
if not (_classifier_spec and _classifier_spec.loader):
    raise ImportError("cannot load inspect classifier")
_classifier_mod = importlib.util.module_from_spec(_classifier_spec)
_classifier_spec.loader.exec_module(_classifier_mod)
classify_system = _classifier_mod.classify_system

_advisor_path = Path(__file__).resolve().parent / "advisor.py"
_advisor_spec = importlib.util.spec_from_file_location("setuphelfer_inspect_advisor", _advisor_path)
if not (_advisor_spec and _advisor_spec.loader):
    raise ImportError("cannot load inspect advisor")
_advisor_mod = importlib.util.module_from_spec(_advisor_spec)
_advisor_spec.loader.exec_module(_advisor_mod)
generate_advice = _advisor_mod.generate_advice

_write_guard_path = Path(__file__).resolve().parent.parent / "safety" / "write_guard.py"
_write_guard_spec = importlib.util.spec_from_file_location("setuphelfer_write_guard", _write_guard_path)
if not (_write_guard_spec and _write_guard_spec.loader):
    raise ImportError("cannot load write_guard")
_write_guard_mod = importlib.util.module_from_spec(_write_guard_spec)
_write_guard_spec.loader.exec_module(_write_guard_mod)
build_write_safety_summary = _write_guard_mod.build_write_safety_summary

from modules.inspect_boot import analyze_boot_status
from modules.inspect_storage import check_mountability, detect_uuid_conflicts
from modules.rescue_readonly_analyze import _analyze_network
from modules.storage_detection import classify_devices, detect_block_devices, detect_filesystems


def _collect_os_hints(
    *,
    devices_raw: list[dict[str, Any]],
    filesystems_map: dict[str, dict[str, str]],
    boot_status: dict[str, Any],
) -> dict[str, bool]:
    fstypes: set[str] = set()
    for meta in filesystems_map.values():
        ft = meta.get("type")
        if isinstance(ft, str) and ft.strip():
            fstypes.add(ft.strip().lower())

    linux_fstypes = {"ext2", "ext3", "ext4", "xfs", "btrfs"}
    windows_fstypes = {"ntfs", "exfat", "vfat", "fat32"}

    has_linux_fs = bool(fstypes & linux_fstypes)
    has_windows_fs = bool(fstypes & windows_fstypes)

    kernel_files = boot_status.get("kernel_files")
    has_kernel_files = isinstance(kernel_files, list) and len(kernel_files) > 0

    possible_linux = has_linux_fs or has_kernel_files
    possible_windows = has_windows_fs
    possible_dualboot = possible_linux and possible_windows

    partition_count = 0
    for node in devices_raw:
        parts = node.get("partitions")
        if isinstance(parts, list):
            partition_count += len(parts)
    possible_empty_disk = bool(devices_raw) and partition_count == 0 and not filesystems_map

    boot_codes = boot_status.get("codes") if isinstance(boot_status, dict) else []
    bad_boot_codes = {
        "rescue.boot.kernel_missing",
        "rescue.boot.boot_dir_missing",
        "rescue.boot.fstab_missing",
        "rescue.boot.fstab_unreadable",
        "rescue.boot.fstab_parse_error",
        "rescue.boot.initrd_missing",
    }
    possible_broken_boot = isinstance(boot_codes, list) and any(code in bad_boot_codes for code in boot_codes)

    unknown_layout = not devices_raw or (not filesystems_map and not has_kernel_files)

    return {
        "possible_linux": bool(possible_linux),
        "possible_windows": bool(possible_windows),
        "possible_dualboot": bool(possible_dualboot),
        "possible_empty_disk": bool(possible_empty_disk),
        "possible_broken_boot": bool(possible_broken_boot),
        "unknown_layout": bool(unknown_layout),
    }


def collect_inspect_result() -> InspectResult:
    warnings: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    source_modules: list[str] = []

    devices_raw: list[dict[str, Any]] = []
    devices_classified: list[dict[str, Any]] = []
    mountability: list[dict[str, Any]] = []
    uuid_conflicts: dict[str, Any] = {}
    filesystems_map: dict[str, dict[str, str]] = {}
    boot_status: dict[str, Any] = {}
    network_status: dict[str, Any] = {}

    try:
        devices_raw = detect_block_devices()
        source_modules.append("modules.storage_detection.detect_block_devices")
    except Exception as exc:
        errors.append({"code": "inspect.storage.detect_block_devices_failed", "detail": type(exc).__name__})

    try:
        devices_classified = classify_devices(devices_raw)
        source_modules.append("modules.storage_detection.classify_devices")
    except Exception as exc:
        errors.append({"code": "inspect.storage.classify_devices_failed", "detail": type(exc).__name__})

    try:
        filesystems_map = detect_filesystems()
        source_modules.append("modules.storage_detection.detect_filesystems")
    except Exception as exc:
        errors.append({"code": "inspect.storage.detect_filesystems_failed", "detail": type(exc).__name__})

    try:
        mountability = check_mountability(read_only=True)
        source_modules.append("modules.inspect_storage.check_mountability")
    except Exception as exc:
        errors.append({"code": "inspect.storage.check_mountability_failed", "detail": type(exc).__name__})

    try:
        uuid_conflicts = detect_uuid_conflicts()
        source_modules.append("modules.inspect_storage.detect_uuid_conflicts")
    except Exception as exc:
        errors.append({"code": "inspect.storage.detect_uuid_conflicts_failed", "detail": type(exc).__name__})

    try:
        boot_status = analyze_boot_status("/")
        source_modules.append("modules.inspect_boot.analyze_boot_status")
    except Exception as exc:
        errors.append({"code": "inspect.boot.analyze_boot_status_failed", "detail": type(exc).__name__})

    try:
        network_status = _analyze_network()
        source_modules.append("modules.rescue_readonly_analyze._analyze_network")
    except Exception as exc:
        errors.append({"code": "inspect.network.analyze_network_failed", "detail": type(exc).__name__})

    if uuid_conflicts.get("has_conflicts") is True:
        warnings.append({"code": "inspect.storage.uuid_conflicts_present"})
    if isinstance(network_status, dict) and network_status.get("code") == "rescue.network.psutil_missing":
        warnings.append({"code": "inspect.network.psutil_missing"})

    os_hints = _collect_os_hints(
        devices_raw=devices_raw,
        filesystems_map=filesystems_map,
        boot_status=boot_status,
    )

    base_payload: dict[str, Any] = {
        "system": {
            "hostname": socket.gethostname(),
            "platform_system": platform.system(),
            "platform_release": platform.release(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "storage": {
            "devices_raw": devices_raw,
            "devices_classified": devices_classified,
            "mountability": mountability,
        },
        "filesystems": {
            "detected": filesystems_map,
            "uuid_conflicts": uuid_conflicts,
        },
        "boot": boot_status,
        "network": network_status,
        "capabilities": {
            "read_only_collection": True,
            "writes_performed": False,
            "hints_only": True,
            "os_hints": os_hints,
        },
        "warnings": warnings,
        "errors": errors,
        "source_modules": source_modules,
    }

    try:
        classification = classify_system(base_payload)
    except Exception as exc:
        classification = {
            "system_type": "UNKNOWN",
            "confidence": 0.0,
            "indicators": ["classifier.indicator.classification_failed"],
            "risk_level": "medium",
            "detail": type(exc).__name__,
        }

    try:
        advice = generate_advice(classification, base_payload)
    except Exception as exc:
        advice = {
            "recommended_paths": [
                {
                    "code": "advice.further_assessment_required",
                    "priority": "high",
                    "requires_confirmation": True,
                }
            ],
            "detail": type(exc).__name__,
        }

    full_payload: dict[str, Any] = {
        **base_payload,
        "classification": classification,
        "advice": advice,
    }
    try:
        write_safety_summary = build_write_safety_summary(full_payload)
    except Exception as exc:
        write_safety_summary = {"policy_code": "safety.summary.failed", "targets": [], "detail": type(exc).__name__}

    return InspectResult(
        **base_payload,
        classification=classification,
        advice=advice,
        write_safety_summary=write_safety_summary,
    )
