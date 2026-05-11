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


def generate_recovery_activation_plan(
    target_path: str,
    inspect_result: dict | None = None,
    post_restore: dict | None = None,
    boot_capability: dict | None = None,
    recovery_minimal_plan: dict | None = None,
    safety_summary: dict | None = None,
) -> dict[str, Any]:
    inspect_result = inspect_result or {}
    post_restore = post_restore or {}
    boot_capability = boot_capability or {}
    recovery_minimal_plan = recovery_minimal_plan or {}
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

    safety_blocked = False
    targets = safety_summary.get("targets") if isinstance(safety_summary.get("targets"), list) else []
    if targets:
        safety_blocked = any(isinstance(t, dict) and not bool(t.get("write_allowed", True)) for t in targets)

    blocked = False
    if not target_exists or not target_readable:
        blocked = True
        blocked_steps.append("ACTIVATION_BLOCKED_NO_LINUX_TARGET")
    if safety_blocked:
        blocked = True
        blocked_steps.append("ACTIVATION_BLOCKED_SAFETY")
    if system_type == "WINDOWS":
        blocked = True
        blocked_steps.append("ACTIVATION_BLOCKED_WINDOWS")
    if system_type == "DUALBOOT":
        blocked = True
        blocked_steps.append("ACTIVATION_BLOCKED_DUALBOOT")
    if system_type in {"UNKNOWN", "PARTIAL_SYSTEM"}:
        blocked_steps.append("ACTIVATION_BLOCKED_UNKNOWN_LAYOUT")
        requires_manual_review = True
        blocked = True
    if boot_status == "boot_failed":
        blocked = True
        blocked_steps.append("ACTIVATION_BLOCKED_BOOT_FAILED")

    if blocked:
        errors.extend(blocked_steps)

    # required activation steps (advisory only)
    required_steps.extend(
        [
            _step("ACTIVATION_STEP_PREPARE_SSH_KEY_AUTH", True, "medium"),
            _step("ACTIVATION_STEP_DISABLE_PASSWORD_LOGIN", True, "medium"),
            _step("ACTIVATION_STEP_CREATE_RECOVERY_USER_SECURE", True, "high"),
            _step("ACTIVATION_STEP_ENABLE_SSH_SERVICE", True, "high"),
            _step("ACTIVATION_STEP_ENABLE_SETUPHELPER_BACKEND", True, "medium"),
            _step("ACTIVATION_STEP_BIND_BACKEND_TO_SAFE_INTERFACE", True, "medium"),
            _step("ACTIVATION_STEP_CONFIGURE_BASIC_FIREWALL", True, "medium"),
            _step("ACTIVATION_STEP_LOG_REMOTE_ACCESS_DETAILS", True, "low"),
        ]
    )

    exposed_services = [
        {"service": "ssh", "port": 22, "exposure": "lan", "risk_level": "high"},
        {"service": "setuphelfer-backend", "port": 8000, "exposure": "lan", "risk_level": "medium"},
        {"service": "setuphelfer-ui", "port": 5173, "exposure": "localhost", "risk_level": "low"},
    ]

    interfaces = []
    net = inspect_result.get("network") if isinstance(inspect_result.get("network"), dict) else {}
    if isinstance(net.get("interfaces"), list):
        interfaces = [str(i) for i in net.get("interfaces", []) if isinstance(i, str)]

    network_impact = {
        "requires_dhcp": True,
        "interfaces_detected": interfaces,
        "connectivity": "ok" if interfaces else "unknown",
        "warnings": [] if interfaces else ["ACTIVATION_RISK_UNKNOWN_NETWORK"],
    }

    # risk aggregation
    risks.extend(
        [
            "ACTIVATION_RISK_REMOTE_ACCESS",
            "ACTIVATION_RISK_OPEN_PORTS",
            "ACTIVATION_RISK_WEAK_AUTH",
            "ACTIVATION_RISK_NETWORK_EXPOSURE",
            "ACTIVATION_RISK_SERVICE_CONFLICT",
        ]
    )
    if not interfaces:
        risks.append("ACTIVATION_RISK_UNKNOWN_NETWORK")
        warnings.append("ACTIVATION_RISK_UNKNOWN_NETWORK")
        requires_manual_review = True

    if "POST_RESTORE_SETUPHELPER_PATH_MISSING" in (post_restore.get("warnings") or []):
        warnings.append("POST_RESTORE_SETUPHELPER_PATH_MISSING")
        requires_manual_review = True

    if boot_status == "boot_warning":
        warnings.append("BOOT_CAPABILITY_WARNING")
        requires_manual_review = True

    minimal_status = str(recovery_minimal_plan.get("plan_status") or "")
    if minimal_status in {"blocked", "not_applicable"}:
        blocked = True
        blocked_steps.append("ACTIVATION_BLOCKED_NO_LINUX_TARGET")

    if blocked:
        plan_status = "blocked"
    else:
        linux_plausible = system_type in {"LINUX", "BROKEN_BOOT"}
        if linux_plausible and target_readable and boot_status in {"boot_likely", "boot_warning"} and not safety_blocked:
            plan_status = "ok" if boot_status == "boot_likely" and not warnings else "review_required"
        elif target_exists and target_readable:
            plan_status = "review_required"
            requires_manual_review = True
        else:
            plan_status = "not_applicable"

    if plan_status == "not_applicable":
        requires_manual_review = True

    return {
        "plan_status": plan_status,
        "target": {"path": str(target), "exists": bool(target_exists), "readable": bool(target_readable)},
        "activation_scope": {
            "ssh_considered": True,
            "setuphelfer_backend_considered": True,
            "ports_reviewed": [22, 8000, 5173],
        },
        "required_steps": required_steps,
        "blocked_steps": list(dict.fromkeys(blocked_steps)),
        "exposed_services": exposed_services,
        "network_impact": network_impact,
        "risks": list(dict.fromkeys(risks)),
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
        "requires_manual_review": bool(requires_manual_review),
    }
