from __future__ import annotations

from typing import Any


_ISSUE_TO_ACTION = {
    "missing_fstab": "REPAIR_REGENERATE_FSTAB",
    "missing_boot_dir": "REPAIR_REINSTALL_GRUB",
    "missing_kernel": "REPAIR_REBUILD_INITRAMFS",
    "missing_initramfs": "REPAIR_REBUILD_INITRAMFS",
    "missing_grub_config": "REPAIR_REINSTALL_GRUB",
    "missing_efi_structure": "REPAIR_RECREATE_EFI_ENTRIES",
    "uuid_mismatch_possible": "REPAIR_CHECK_UUID_MAPPING",
    "windows_boot_present": "REPAIR_MANUAL_WINDOWS_REQUIRED",
    "dualboot_detected": "REPAIR_MANUAL_DUALBOOT_REQUIRED",
}


def _action(code: str, applicable: bool, risk_level: str) -> dict[str, Any]:
    return {
        "code": code,
        "applicable": bool(applicable),
        "risk_level": risk_level,
        "requires_confirmation": True,
        "auto_allowed": False,
    }


def generate_boot_repair_plan(
    target_path: str,
    inspect_result: dict,
    post_verify: dict,
    boot_capability: dict,
) -> dict[str, Any]:
    issues: list[str] = []
    risks: list[str] = []
    proposed_actions: list[dict[str, Any]] = []

    if not isinstance(boot_capability, dict) or not target_path:
        return {
            "plan_status": "not_applicable",
            "issues": [],
            "proposed_actions": [_action("REPAIR_MANUAL_REVIEW_REQUIRED", True, "high")],
            "risks": ["BOOT_REPAIR_RISK_UNKNOWN_LAYOUT"],
            "requires_manual_review": True,
        }

    post_warnings = set(post_verify.get("warnings", []) if isinstance(post_verify, dict) else [])
    boot_warnings = set(boot_capability.get("warnings", []) if isinstance(boot_capability, dict) else [])
    boot_hints = set(boot_capability.get("boot_type_hints", []) if isinstance(boot_capability, dict) else [])

    if "POST_RESTORE_FSTAB_MISSING" in post_warnings or "BOOT_FSTAB_MISSING" in boot_warnings:
        issues.append("missing_fstab")
    if "POST_RESTORE_BOOT_DIR_MISSING" in post_warnings or "BOOT_DIR_MISSING" in boot_warnings:
        issues.append("missing_boot_dir")
    if "POST_RESTORE_KERNEL_MISSING" in post_warnings or "BOOT_KERNEL_MISSING" in boot_warnings:
        issues.append("missing_kernel")
    if "POST_RESTORE_INITRAMFS_MISSING" in post_warnings or "BOOT_INITRAMFS_MISSING" in boot_warnings:
        issues.append("missing_initramfs")
    if "BOOT_GRUB_HINT_FOUND" not in boot_hints:
        issues.append("missing_grub_config")
    if "BOOT_EFI_HINT_FOUND" not in boot_hints:
        issues.append("missing_efi_structure")
    if "BOOT_FSTAB_UUID_REFERENCES_MISSING" in boot_warnings:
        issues.append("uuid_mismatch_possible")
    if "BOOT_WINDOWS_BOOTMANAGER_FOUND" in boot_hints or "BOOT_WINDOWS_BOOTMANAGER_FOUND" in boot_warnings:
        issues.append("windows_boot_present")
    if "BOOT_DUALBOOT_RISK" in boot_warnings:
        issues.append("dualboot_detected")

    # inspect-based hard hints (defensive)
    cls = inspect_result.get("classification") if isinstance(inspect_result, dict) and isinstance(inspect_result.get("classification"), dict) else {}
    stype = str(cls.get("system_type") or "")
    if stype == "WINDOWS" and "windows_boot_present" not in issues:
        issues.append("windows_boot_present")
    if stype == "DUALBOOT" and "dualboot_detected" not in issues:
        issues.append("dualboot_detected")

    manual_review = False
    if "windows_boot_present" in issues:
        manual_review = True
        risks.extend(["BOOT_REPAIR_RISK_WINDOWS_OVERWRITE", "BOOT_REPAIR_RISK_WRONG_DISK"])
    if "dualboot_detected" in issues:
        manual_review = True
        risks.extend(["BOOT_REPAIR_RISK_DUALBOOT_BREAK", "BOOT_REPAIR_RISK_WRONG_DISK"])

    if any(x in issues for x in ["missing_boot_dir", "missing_efi_structure", "missing_grub_config"]):
        risks.append("BOOT_REPAIR_RISK_UNKNOWN_LAYOUT")
    if any(x in issues for x in ["missing_fstab", "missing_kernel", "missing_initramfs", "uuid_mismatch_possible"]):
        risks.append("BOOT_REPAIR_RISK_DATA_LOSS")

    # conflicting issues => manual review
    if len(set(issues)) >= 4:
        manual_review = True

    uniq_issues = list(dict.fromkeys(issues))
    uniq_risks = list(dict.fromkeys(risks))

    for issue in uniq_issues:
        action_code = _ISSUE_TO_ACTION.get(issue)
        if not action_code:
            continue
        risk_level = "low"
        if issue in {"missing_boot_dir", "missing_grub_config", "missing_efi_structure", "uuid_mismatch_possible"}:
            risk_level = "medium"
        if issue in {"windows_boot_present", "dualboot_detected"}:
            risk_level = "high"
        proposed_actions.append(_action(action_code, True, risk_level))

    if manual_review or not proposed_actions:
        proposed_actions.append(_action("REPAIR_MANUAL_REVIEW_REQUIRED", True, "high" if manual_review else "medium"))

    if not uniq_issues:
        plan_status = "ok"
    elif not target_path or (boot_capability.get("status") == "boot_unknown" and not isinstance(post_verify, dict)):
        plan_status = "not_applicable"
    else:
        plan_status = "review_required"

    if boot_capability.get("status") == "boot_unknown" and not uniq_issues:
        plan_status = "not_applicable"
        manual_review = True
        if "BOOT_REPAIR_RISK_UNKNOWN_LAYOUT" not in uniq_risks:
            uniq_risks.append("BOOT_REPAIR_RISK_UNKNOWN_LAYOUT")

    return {
        "plan_status": plan_status,
        "issues": uniq_issues,
        "proposed_actions": proposed_actions,
        "risks": uniq_risks,
        "requires_manual_review": bool(manual_review),
    }
