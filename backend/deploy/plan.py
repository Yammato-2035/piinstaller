"""
Advisory deploy plan from existing Inspect + Safety data only.
No installation, downloads, partitioning, or disk writes.
"""

from __future__ import annotations

import re
from typing import Any

_LINUX_FS = frozenset({"ext2", "ext3", "ext4", "xfs", "btrfs"})
_EFI_LIKE = frozenset({"vfat", "fat32"})

_DEPLOY_PROFILES_BASE: list[dict[str, Any]] = [
    {
        "code": "DEPLOY_PROFILE_MINIMAL_LINUX",
        "description": "deploy.profile.DEPLOY_PROFILE_MINIMAL_LINUX",
        "requirements": ["deploy.req.minimal_storage", "deploy.req.network_optional"],
        "suitable": False,
        "risk_level": "low",
        "requires_confirmation": True,
        "auto_allowed": False,
    },
    {
        "code": "DEPLOY_PROFILE_WEB_SERVER",
        "description": "deploy.profile.DEPLOY_PROFILE_WEB_SERVER",
        "requirements": ["deploy.req.moderate_cpu_ram", "deploy.req.network_recommended"],
        "suitable": False,
        "risk_level": "medium",
        "requires_confirmation": True,
        "auto_allowed": False,
    },
    {
        "code": "DEPLOY_PROFILE_BACKUP_NODE",
        "description": "deploy.profile.DEPLOY_PROFILE_BACKUP_NODE",
        "requirements": ["deploy.req.large_storage", "deploy.req.network_recommended"],
        "suitable": False,
        "risk_level": "medium",
        "requires_confirmation": True,
        "auto_allowed": False,
    },
    {
        "code": "DEPLOY_PROFILE_NAS",
        "description": "deploy.profile.DEPLOY_PROFILE_NAS",
        "requirements": ["deploy.req.large_storage", "deploy.req.network_recommended"],
        "suitable": False,
        "risk_level": "high",
        "requires_confirmation": True,
        "auto_allowed": False,
    },
    {
        "code": "DEPLOY_PROFILE_EXPERIMENTAL",
        "description": "deploy.profile.DEPLOY_PROFILE_EXPERIMENTAL",
        "requirements": ["deploy.req.manual_review"],
        "suitable": False,
        "risk_level": "high",
        "requires_confirmation": True,
        "auto_allowed": False,
    },
]

_REQUIRED_STEP_CODES = [
    "DEPLOY_STEP_PARTITION_DISK",
    "DEPLOY_STEP_FORMAT_FILESYSTEM",
    "DEPLOY_STEP_INSTALL_BASE_SYSTEM",
    "DEPLOY_STEP_INSTALL_PROFILE_COMPONENTS",
    "DEPLOY_STEP_INSTALL_SETUPHELPER",
    "DEPLOY_STEP_ENABLE_SSH",
    "DEPLOY_STEP_INITIAL_HARDENING",
]


def _os_hints(inspect_result: dict[str, Any]) -> dict[str, Any]:
    cap = inspect_result.get("capabilities")
    if not isinstance(cap, dict):
        return {}
    h = cap.get("os_hints")
    return h if isinstance(h, dict) else {}


def _merge_classification(inspect_result: dict[str, Any], classification: dict[str, Any] | None) -> dict[str, Any]:
    if classification and isinstance(classification, dict) and classification:
        return dict(classification)
    c = inspect_result.get("classification")
    return dict(c) if isinstance(c, dict) else {}


def _filesystem_types(detected: Any) -> set[str]:
    out: set[str] = set()
    if not isinstance(detected, dict):
        return out
    for meta in detected.values():
        if isinstance(meta, dict):
            t = meta.get("type")
            if isinstance(t, str) and t.strip():
                out.add(t.strip().lower())
    return out


def _parse_size_bytes(size_val: Any) -> int | None:
    if size_val is None:
        return None
    if isinstance(size_val, (int, float)):
        return int(size_val)
    s = str(size_val).strip().upper()
    m = re.match(r"^([\d.]+)\s*([KMGTPE]?)(?:I?B)?$", s)
    if not m:
        return None
    num = float(m.group(1))
    suf = m.group(2) or ""
    mult = {"": 1, "K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4, "P": 1024**5, "E": 1024**6}.get(suf, None)
    if mult is None:
        return None
    return int(num * mult)


def _hardware_summary(inspect_result: dict[str, Any]) -> dict[str, Any]:
    sys_d = inspect_result.get("system")
    sys_d = sys_d if isinstance(sys_d, dict) else {}

    cpu_cores = sys_d.get("cpu_count") or sys_d.get("cpu_cores")
    try:
        cpu_n = int(cpu_cores) if cpu_cores is not None else None
    except (TypeError, ValueError):
        cpu_n = None
    if cpu_n is None:
        cpu_class = "unknown"
    elif cpu_n <= 2:
        cpu_class = "low"
    elif cpu_n <= 8:
        cpu_class = "medium"
    else:
        cpu_class = "high"

    ram_gb = sys_d.get("total_memory_gb") or sys_d.get("memory_gb")
    try:
        ram = float(ram_gb) if ram_gb is not None else None
    except (TypeError, ValueError):
        ram = None
    if ram is None:
        ram_class = "unknown"
    elif ram < 2:
        ram_class = "low"
    elif ram < 8:
        ram_class = "medium"
    else:
        ram_class = "high"

    storage = inspect_result.get("storage")
    storage = storage if isinstance(storage, dict) else {}
    classified = storage.get("devices_classified")
    classified_list = classified if isinstance(classified, list) else []
    disk_nodes = [n for n in classified_list if isinstance(n, dict) and n.get("type") == "disk"]
    disk_count = len(disk_nodes)
    total_b = 0
    any_size = False
    for n in disk_nodes:
        b = _parse_size_bytes(n.get("size"))
        if b is not None:
            total_b += b
            any_size = True
    if not any_size:
        storage_class = "unknown"
    elif total_b < 32 * 1024**3:
        storage_class = "small"
    elif total_b < 500 * 1024**3:
        storage_class = "medium"
    else:
        storage_class = "large"

    net = inspect_result.get("network")
    net = net if isinstance(net, dict) else {}
    if net.get("code") == "rescue.network.psutil_missing":
        network_available: bool | str = "unknown"
    else:
        ipv4 = net.get("ipv4")
        if isinstance(ipv4, list) and len(ipv4) > 0:
            network_available = True
        elif isinstance(net.get("interfaces"), list) and len(net.get("interfaces") or []) > 1:
            network_available = True
        elif isinstance(net.get("interfaces"), list) and net.get("interfaces"):
            network_available = False
        else:
            network_available = "unknown"

    return {
        "cpu_class": cpu_class,
        "ram_class": ram_class,
        "storage_class": storage_class,
        "network_available": network_available,
        "disk_count": disk_count,
    }


def _collect_safety_signals(safety_summary: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(safety_summary, dict):
        return {"targets": [], "policy_failed": True}
    targets = safety_summary.get("targets")
    tlist = targets if isinstance(targets, list) else []
    pc = str(safety_summary.get("policy_code") or "")
    policy_failed = pc.endswith("failed") or bool(safety_summary.get("detail"))
    return {"targets": tlist, "policy_failed": policy_failed}


def _has_linux_filesystem(types_set: set[str]) -> bool:
    return bool(types_set & _LINUX_FS)


def _data_on_filesystems(types_set: set[str]) -> bool:
    if _has_linux_filesystem(types_set):
        return True
    if "ntfs" in types_set and (types_set - {"ntfs"} - _EFI_LIKE):
        return True
    if types_set - {"ntfs"} - _EFI_LIKE:
        return True
    return False


def _analyze_deploy_eligibility(
    *,
    inspect_result: dict[str, Any],
    safety_summary: dict[str, Any],
    classification: dict[str, Any],
) -> tuple[str, list[str], list[str], list[str], dict[str, Any]]:
    blocked_steps: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []
    hints = _os_hints(inspect_result)
    types_set = _filesystem_types((inspect_result.get("filesystems") or {}).get("detected"))

    sig = _collect_safety_signals(safety_summary)
    targets: list[dict[str, Any]] = sig["targets"]

    empty_disk_reasons = sum(1 for t in targets if isinstance(t, dict) and t.get("reason_code") == "SAFETY_EMPTY_DISK")
    reason_codes = [str(t.get("reason_code") or "") for t in targets if isinstance(t, dict)]
    system_type = str(classification.get("system_type") or "UNKNOWN")

    target_info: dict[str, Any] = {
        "disk_targets": len(targets),
        "empty_disk_targets": empty_disk_reasons,
        "possible_empty_disk_hint": bool(hints.get("possible_empty_disk")),
        "classification_system_type": system_type,
        "filesystem_types_present": sorted(types_set),
    }

    if not targets:
        return "not_applicable", [], [], [], target_info

    if sig["policy_failed"]:
        blocked_steps.append("DEPLOY_BLOCKED_SAFETY")

    if any(r == "SAFETY_WINDOWS_DETECTED" for r in reason_codes):
        blocked_steps.append("DEPLOY_BLOCKED_WINDOWS")
    if any(r == "SAFETY_DUALBOOT" for r in reason_codes):
        blocked_steps.append("DEPLOY_BLOCKED_DUALBOOT")
    if any(r == "SAFETY_SYSTEM_DISK" for r in reason_codes):
        blocked_steps.append("DEPLOY_BLOCKED_SYSTEM_DISK")
    if any(r == "SAFETY_LIVE_SYSTEM" for r in reason_codes):
        blocked_steps.append("DEPLOY_BLOCKED_LIVE_SYSTEM")

    if system_type == "WINDOWS":
        blocked_steps.append("DEPLOY_BLOCKED_WINDOWS")
    if system_type == "DUALBOOT":
        blocked_steps.append("DEPLOY_BLOCKED_DUALBOOT")

    if any(r == "SAFETY_BACKUP_TARGET_OK" for r in reason_codes):
        blocked_steps.append("DEPLOY_BLOCKED_NOT_EMPTY")

    has_data_fs = _data_on_filesystems(types_set)
    if has_data_fs and system_type != "EMPTY":
        blocked_steps.append("DEPLOY_BLOCKED_NOT_EMPTY")

    all_targets_empty_disk = len(targets) > 0 and empty_disk_reasons == len(targets)
    classified_empty = system_type == "EMPTY"
    hint_empty = bool(hints.get("possible_empty_disk"))
    no_fs = len(types_set) == 0

    empty_eligible = all_targets_empty_disk or (classified_empty and no_fs) or (hint_empty and no_fs and len(targets) > 0)

    if hint_empty and types_set:
        empty_eligible = False
        blocked_steps.append("DEPLOY_BLOCKED_NOT_EMPTY")

    unknown_layout_hint = bool(hints.get("unknown_layout"))

    if any(r == "SAFETY_UNKNOWN_DEVICE" for r in reason_codes) and not all_targets_empty_disk:
        blocked_steps.append("DEPLOY_BLOCKED_UNKNOWN_LAYOUT")

    blocked_steps = list(dict.fromkeys(blocked_steps))

    if blocked_steps:
        return "blocked", list(dict.fromkeys(blocked_steps)), warnings, errors, target_info

    # No hard blocks: decide ok vs review
    if not empty_eligible:
        if unknown_layout_hint or system_type in ("UNKNOWN", "PARTIAL_SYSTEM"):
            return "review_required", [], warnings, errors, target_info
        blocked_steps.append("DEPLOY_BLOCKED_NOT_EMPTY")
        return "blocked", list(dict.fromkeys(blocked_steps)), warnings, errors, target_info

    mixed_signals = unknown_layout_hint or system_type in ("UNKNOWN", "PARTIAL_SYSTEM", "BROKEN_BOOT")
    if mixed_signals:
        warnings.append("deploy.warning.mixed_signals")
        return "review_required", [], warnings, errors, target_info

    return "ok", [], warnings, errors, target_info


def _risks_for_plan(
    plan_status: str,
    hardware_summary: dict[str, Any],
    blocked_steps: list[str],
    classification: dict[str, Any],
) -> list[str]:
    risks: list[str] = []
    if plan_status == "blocked":
        risks.append("DEPLOY_RISK_WRONG_DISK")
    if "DEPLOY_BLOCKED_NOT_EMPTY" in blocked_steps or "DEPLOY_BLOCKED_SYSTEM_DISK" in blocked_steps:
        risks.append("DEPLOY_RISK_DATA_LOSS")
    if hardware_summary.get("cpu_class") == "unknown" or hardware_summary.get("ram_class") == "unknown":
        risks.append("DEPLOY_RISK_HARDWARE_LIMITATION")
    if hardware_summary.get("storage_class") == "small":
        risks.append("DEPLOY_RISK_HARDWARE_LIMITATION")
    if hardware_summary.get("network_available") is False:
        risks.append("DEPLOY_RISK_NETWORK_MISSING")
    if str(classification.get("system_type") or "") in ("BROKEN_BOOT", "PARTIAL_SYSTEM", "UNKNOWN"):
        risks.append("DEPLOY_RISK_UNSUPPORTED_CONFIG")
    return list(dict.fromkeys(risks))


def _score_profiles(hardware_summary: dict[str, Any]) -> list[dict[str, Any]]:
    cpu = hardware_summary.get("cpu_class")
    ram = hardware_summary.get("ram_class")
    stor = hardware_summary.get("storage_class")
    net = hardware_summary.get("network_available")

    profiles: list[dict[str, Any]] = []
    for p in _DEPLOY_PROFILES_BASE:
        entry = {**p, "suitable": False, "risk_level": p["risk_level"]}
        code = p["code"]
        if code == "DEPLOY_PROFILE_MINIMAL_LINUX":
            ok = stor != "unknown" and cpu != "unknown" and ram != "unknown"
            entry["suitable"] = ok
            if stor == "small":
                entry["risk_level"] = "medium"
        elif code == "DEPLOY_PROFILE_WEB_SERVER":
            ok = cpu in ("medium", "high") and ram in ("medium", "high") and stor in ("medium", "large")
            entry["suitable"] = ok and net is not False
            if net == "unknown":
                entry["risk_level"] = "medium"
        elif code == "DEPLOY_PROFILE_BACKUP_NODE":
            ok = stor in ("medium", "large") and ram != "low"
            entry["suitable"] = ok
        elif code == "DEPLOY_PROFILE_NAS":
            ok = stor == "large" and ram in ("medium", "high")
            entry["suitable"] = ok and net is True
        elif code == "DEPLOY_PROFILE_EXPERIMENTAL":
            entry["suitable"] = False
        profiles.append(entry)
    return profiles


def _pick_recommended(
    plan_status: str,
    profiles: list[dict[str, Any]],
    hardware_summary: dict[str, Any],
    risks: list[str],
) -> dict[str, Any]:
    if plan_status != "ok":
        return {}
    if hardware_summary.get("cpu_class") == "unknown" or hardware_summary.get("ram_class") == "unknown":
        return {}
    if hardware_summary.get("storage_class") == "unknown":
        return {}
    if any(r == "DEPLOY_RISK_HARDWARE_LIMITATION" for r in risks):
        return {}
    suitable = [p for p in profiles if p.get("suitable") and p.get("risk_level") != "high"]
    if not suitable:
        return {}
    order = [
        "DEPLOY_PROFILE_MINIMAL_LINUX",
        "DEPLOY_PROFILE_WEB_SERVER",
        "DEPLOY_PROFILE_BACKUP_NODE",
    ]
    for code in order:
        for p in suitable:
            if p.get("code") == code:
                return {
                    "code": p["code"],
                    "risk_level": p["risk_level"],
                    "requires_confirmation": True,
                    "auto_allowed": False,
                }
    return {}


def _system_assessment(classification: dict[str, Any], blocked_steps: list[str]) -> dict[str, Any]:
    return {
        "system_type": str(classification.get("system_type") or "UNKNOWN"),
        "confidence": classification.get("confidence"),
        "risk_level": classification.get("risk_level"),
        "safety_blocked": bool(blocked_steps),
    }


def generate_deploy_plan(
    inspect_result: dict[str, Any],
    safety_summary: dict[str, Any],
    classification: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cls = _merge_classification(inspect_result, classification)
    hardware_summary = _hardware_summary(inspect_result)

    plan_status, blocked_steps, warnings, errors, target_info = _analyze_deploy_eligibility(
        inspect_result=inspect_result,
        safety_summary=safety_summary,
        classification=cls,
    )

    risks = _risks_for_plan(plan_status, hardware_summary, blocked_steps, cls)
    deploy_profiles = _score_profiles(hardware_summary)
    recommended = _pick_recommended(plan_status, deploy_profiles, hardware_summary, risks)

    requires_manual_review = True
    if plan_status == "not_applicable":
        requires_manual_review = True

    required_steps: list[dict[str, Any]] = [
        {
            "code": c,
            "applicable": plan_status == "ok",
            "auto_allowed": False,
            "requires_confirmation": True,
        }
        for c in _REQUIRED_STEP_CODES
    ]
    if plan_status != "ok":
        for s in required_steps:
            s["applicable"] = False

    return {
        "plan_status": plan_status,
        "target": target_info,
        "system_assessment": _system_assessment(cls, blocked_steps),
        "deploy_profiles": deploy_profiles,
        "recommended_profile": recommended,
        "required_steps": required_steps,
        "blocked_steps": blocked_steps,
        "hardware_summary": hardware_summary,
        "risks": risks,
        "warnings": warnings,
        "errors": errors,
        "requires_manual_review": requires_manual_review,
    }
