from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def _step(code: str, applicable: bool, risk_level: str) -> dict[str, Any]:
    return {
        "code": code,
        "applicable": bool(applicable),
        "risk_level": risk_level,
        "requires_confirmation": True,
        "auto_allowed": False,
    }


def generate_recovery_minimal_plan(
    target_path: str,
    inspect_result: dict | None = None,
    boot_capability: dict | None = None,
    post_restore: dict | None = None,
    safety_summary: dict | None = None,
) -> dict[str, Any]:
    inspect_result = inspect_result or {}
    boot_capability = boot_capability or {}
    post_restore = post_restore or {}
    safety_summary = safety_summary or {}

    warnings: list[str] = []
    errors: list[str] = []
    blocked_steps: list[str] = []
    risks: list[str] = []
    required_steps: list[dict[str, Any]] = []
    requires_manual_review = False

    target = Path(str(target_path or "")).expanduser()
    target_exists = target.exists()
    target_readable = bool(target_exists and os.access(target, os.R_OK | os.X_OK))

    cls = inspect_result.get("classification") if isinstance(inspect_result.get("classification"), dict) else {}
    system_type = str(cls.get("system_type") or "UNKNOWN")

    boot_status = str(boot_capability.get("status") or "boot_unknown")
    boot_warnings = boot_capability.get("warnings") if isinstance(boot_capability.get("warnings"), list) else []
    post_warnings = post_restore.get("warnings") if isinstance(post_restore.get("warnings"), list) else []

    safety_blocked = False
    targets = safety_summary.get("targets") if isinstance(safety_summary.get("targets"), list) else []
    if targets:
        for t in targets:
            if isinstance(t, dict) and not bool(t.get("write_allowed", True)):
                safety_blocked = True
                break

    blocked = False
    if not target_exists or not target_readable:
        blocked = True
        blocked_steps.append("RECOVERY_BLOCKED_TARGET_NOT_READABLE")
    if safety_blocked:
        blocked = True
        blocked_steps.append("RECOVERY_BLOCKED_SAFETY")
    if system_type == "WINDOWS":
        blocked = True
        blocked_steps.append("RECOVERY_BLOCKED_WINDOWS")
    if system_type == "DUALBOOT":
        blocked = True
        blocked_steps.append("RECOVERY_BLOCKED_DUALBOOT")
    if system_type in {"UNKNOWN", "PARTIAL_SYSTEM"}:
        blocked_steps.append("RECOVERY_BLOCKED_UNKNOWN_LAYOUT")
        requires_manual_review = True
        if system_type == "UNKNOWN":
            blocked = True
    if system_type not in {"LINUX", "BROKEN_BOOT", "PARTIAL_SYSTEM", "UNKNOWN", "WINDOWS", "DUALBOOT"}:
        blocked = True
        blocked_steps.append("RECOVERY_BLOCKED_NO_LINUX_TARGET")

    if blocked:
        errors.extend(blocked_steps)

    # Risk baseline
    risks.extend([
        "RECOVERY_RISK_REMOTE_ACCESS",
        "RECOVERY_RISK_NETWORK_EXPOSURE",
        "RECOVERY_RISK_SERVICE_CONFLICT",
    ])
    if not target_readable:
        risks.append("RECOVERY_RISK_WRONG_TARGET")
    if boot_status in {"boot_warning", "boot_failed", "boot_unknown"}:
        risks.append("RECOVERY_RISK_INCOMPLETE_SYSTEM")
    if system_type in {"WINDOWS", "DUALBOOT", "UNKNOWN", "PARTIAL_SYSTEM"}:
        risks.append("RECOVERY_RISK_WRONG_TARGET")

    # Required steps (advisory only)
    required_steps.append(_step("RECOVERY_STEP_INSTALL_SETUPHELPER_AGENT", True, "medium"))
    required_steps.append(_step("RECOVERY_STEP_ENABLE_SETUPHELPER_BACKEND", True, "medium"))
    required_steps.append(_step("RECOVERY_STEP_ENABLE_SSH", True, "high"))
    required_steps.append(_step("RECOVERY_STEP_CREATE_RECOVERY_USER", True, "high"))
    required_steps.append(_step("RECOVERY_STEP_CONFIGURE_NETWORK_DHCP", True, "medium"))
    required_steps.append(_step("RECOVERY_STEP_WRITE_RECOVERY_NOTES", True, "low"))
    required_steps.append(_step("RECOVERY_STEP_ENABLE_FIREWALL_BASELINE", True, "low"))
    required_steps.append(_step("RECOVERY_STEP_CREATE_POST_RECOVERY_BACKUP", True, "low"))

    if "POST_RESTORE_SETUPHELPER_PATH_MISSING" in post_warnings or "POST_RESTORE_SETUPHELPER_UNIT_MISSING" in post_warnings:
        warnings.append("POST_RESTORE_SETUPHELPER_PATH_MISSING")
        requires_manual_review = True

    if boot_status in {"boot_warning", "boot_unknown"}:
        warnings.append("BOOT_CAPABILITY_WARNING")
        requires_manual_review = True

    if blocked:
        plan_status = "blocked"
    else:
        linux_plausible = system_type in {"LINUX", "BROKEN_BOOT"}
        if linux_plausible and target_readable and boot_status == "boot_likely" and not safety_blocked:
            plan_status = "ok"
        elif target_exists and target_readable:
            plan_status = "review_required"
            requires_manual_review = True
        else:
            plan_status = "not_applicable"

    if plan_status == "not_applicable":
        requires_manual_review = True

    return {
        "plan_status": plan_status,
        "target": {
            "path": str(target),
            "exists": bool(target_exists),
            "readable": bool(target_readable),
        },
        "system_assessment": {
            "system_type": system_type,
            "boot_status": boot_status,
            "safety_blocked": bool(safety_blocked),
        },
        "required_steps": required_steps,
        "blocked_steps": list(dict.fromkeys(blocked_steps)),
        "risks": list(dict.fromkeys(risks)),
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
        "requires_manual_review": bool(requires_manual_review),
    }
