from __future__ import annotations

from typing import Any


def _sec(code: str, status: str, items: list[str]) -> dict[str, Any]:
    return {"code": code, "status": status, "items": items}


def _add_unique(dst: list[str], values: list[str]) -> None:
    for v in values:
        if isinstance(v, str) and v and v not in dst:
            dst.append(v)


def _status_from_code(code: str | None, ok_values: set[str], failed_values: set[str]) -> str:
    c = str(code or "")
    if c in failed_values:
        return "failed"
    if c in ok_values:
        return "ok"
    if c:
        return "warning"
    return "not_run"


def build_rescue_report(
    inspect_result: dict | None = None,
    safety_summary: dict | None = None,
    preflight_result: dict | None = None,
    preview_result: dict | None = None,
    execute_result: dict | None = None,
    post_restore: dict | None = None,
    boot_capability: dict | None = None,
    boot_repair_plan: dict | None = None,
) -> dict[str, Any]:
    inspect_result = inspect_result or {}
    safety_summary = safety_summary or {}
    preflight_result = preflight_result or {}
    preview_result = preview_result or {}
    execute_result = execute_result or {}
    post_restore = post_restore or {}
    boot_capability = boot_capability or {}
    boot_repair_plan = boot_repair_plan or {}

    sections: list[dict[str, Any]] = []
    risks: list[str] = []
    recommendations: list[str] = []
    blocked_actions: list[str] = []
    next_steps: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []

    cls = inspect_result.get("classification") if isinstance(inspect_result.get("classification"), dict) else {}
    system_type = str(cls.get("system_type") or "UNKNOWN")

    sections.append(_sec("REPORT_SECTION_INSPECT", "ok" if inspect_result else "not_run", []))
    sections.append(_sec("REPORT_SECTION_CLASSIFICATION", "ok" if cls else "unknown", [system_type] if cls else []))

    safety_targets = safety_summary.get("targets") if isinstance(safety_summary.get("targets"), list) else []
    safety_status = "not_run"
    if safety_targets:
        safety_status = "ok"
        for t in safety_targets:
            if isinstance(t, dict) and not bool(t.get("write_allowed", True)):
                safety_status = "warning"
                blocked_actions.append("ACTION_BLOCKED_WRITE_TO_SYSTEM_DISK")
    sections.append(_sec("REPORT_SECTION_SAFETY", safety_status, []))

    preflight_code = str(preflight_result.get("code") or "")
    preflight_status = _status_from_code(preflight_code, {"PREFLIGHT_BACKUP_EXECUTED", "PREFLIGHT_PREVIEW_CREATED"}, {"PREFLIGHT_BACKUP_FAILED"})
    sections.append(_sec("REPORT_SECTION_PREFLIGHT", preflight_status, [preflight_code] if preflight_code else []))

    preview_code = str(preview_result.get("code") or "")
    preview_status = _status_from_code(preview_code, {"RESCUE_PREVIEW_CREATED"}, {"RESCUE_PREVIEW_FAILED"})
    sections.append(_sec("REPORT_SECTION_RESTORE_PREVIEW", preview_status, [preview_code] if preview_code else []))

    execute_code = str(execute_result.get("code") or "")
    execute_status = _status_from_code(execute_code, {"RESCUE_EXECUTE_COMPLETED"}, {"RESCUE_EXECUTE_FAILED", "RESCUE_RESTORE_ENGINE_FAILED"})
    sections.append(_sec("REPORT_SECTION_RESTORE_EXECUTE", execute_status, [execute_code] if execute_code else []))

    post_status = str(post_restore.get("status") or "")
    sections.append(_sec("REPORT_SECTION_POST_RESTORE", ("ok" if post_status == "valid" else "warning" if post_status == "warning" else "failed" if post_status == "failed" else "not_run"), post_restore.get("warnings", []) if isinstance(post_restore.get("warnings"), list) else []))

    bc_status = str(boot_capability.get("status") or "")
    bc_section_status = "not_run"
    if bc_status == "boot_likely":
        bc_section_status = "ok"
    elif bc_status == "boot_warning":
        bc_section_status = "warning"
    elif bc_status == "boot_failed":
        bc_section_status = "failed"
    elif bc_status == "boot_unknown":
        bc_section_status = "unknown"
    sections.append(_sec("REPORT_SECTION_BOOT_CAPABILITY", bc_section_status, boot_capability.get("warnings", []) if isinstance(boot_capability.get("warnings"), list) else []))

    plan_status = str(boot_repair_plan.get("plan_status") or "")
    plan_section_status = "not_run"
    if plan_status == "ok":
        plan_section_status = "ok"
    elif plan_status == "review_required":
        plan_section_status = "warning"
    elif plan_status == "not_applicable":
        plan_section_status = "unknown"
    sections.append(_sec("REPORT_SECTION_BOOT_REPAIR_PLAN", plan_section_status, boot_repair_plan.get("issues", []) if isinstance(boot_repair_plan.get("issues"), list) else []))

    # Aggregation existing codes only
    _add_unique(risks, [str(execute_code)] if execute_code else [])
    _add_unique(risks, post_restore.get("warnings", []) if isinstance(post_restore.get("warnings"), list) else [])
    _add_unique(risks, post_restore.get("errors", []) if isinstance(post_restore.get("errors"), list) else [])
    _add_unique(risks, boot_capability.get("warnings", []) if isinstance(boot_capability.get("warnings"), list) else [])
    _add_unique(risks, boot_capability.get("errors", []) if isinstance(boot_capability.get("errors"), list) else [])
    _add_unique(risks, boot_repair_plan.get("risks", []) if isinstance(boot_repair_plan.get("risks"), list) else [])

    _add_unique(warnings, preview_result.get("warnings", []) if isinstance(preview_result.get("warnings"), list) else [])
    _add_unique(warnings, execute_result.get("warnings", []) if isinstance(execute_result.get("warnings"), list) else [])
    _add_unique(errors, preview_result.get("errors", []) if isinstance(preview_result.get("errors"), list) else [])
    _add_unique(errors, execute_result.get("errors", []) if isinstance(execute_result.get("errors"), list) else [])
    _add_unique(errors, post_restore.get("errors", []) if isinstance(post_restore.get("errors"), list) else [])

    # Policy / blocked actions
    if system_type == "WINDOWS":
        blocked_actions.append("ACTION_BLOCKED_WINDOWS_REPAIR_AUTOMATIC")
    if system_type == "DUALBOOT" or "BOOT_DUALBOOT_RISK" in risks:
        blocked_actions.append("ACTION_BLOCKED_DUALBOOT_REPAIR_AUTOMATIC")
    if not boot_repair_plan:
        blocked_actions.append("ACTION_BLOCKED_BOOT_REPAIR_WITHOUT_PLAN")
    blocked_actions.append("ACTION_BLOCKED_DEPLOY_WITHOUT_EXPLICIT_SELECTION")
    if preview_code != "RESCUE_PREVIEW_CREATED":
        blocked_actions.append("ACTION_BLOCKED_RESTORE_WITHOUT_VALID_PREVIEW")
    if execute_code in {"RESCUE_PREVIEW_TOKEN_INVALID", "RESCUE_PREVIEW_SESSION_NOT_FOUND", ""}:
        blocked_actions.append("ACTION_BLOCKED_RESTORE_WITHOUT_TOKEN")

    # Recommendations / next steps (advisory only)
    if preflight_status in {"not_run", "warning"}:
        next_steps.append("NEXT_RUN_PREFLIGHT_BACKUP")
    if preview_status in {"not_run", "warning", "failed"}:
        next_steps.append("NEXT_RUN_RESTORE_PREVIEW")
    if preview_code == "RESCUE_PREVIEW_CREATED" and execute_code != "RESCUE_EXECUTE_COMPLETED":
        next_steps.append("NEXT_EXECUTE_RESTORE_WITH_TOKEN")
    if not post_restore:
        next_steps.append("NEXT_RUN_POST_RESTORE_VALIDATION")
    if not boot_capability:
        next_steps.append("NEXT_RUN_BOOT_CAPABILITY_CHECK")
    if boot_repair_plan:
        next_steps.append("NEXT_REVIEW_BOOT_REPAIR_PLAN")
    if bool(boot_repair_plan.get("requires_manual_review")):
        next_steps.append("NEXT_MANUAL_REVIEW_REQUIRED")

    setuphelfer_missing = False
    if isinstance(post_restore.get("warnings"), list):
        setuphelfer_missing = (
            "POST_RESTORE_SETUPHELPER_UNIT_MISSING" in post_restore.get("warnings", [])
            or "POST_RESTORE_SETUPHELPER_PATH_MISSING" in post_restore.get("warnings", [])
        )
    if setuphelfer_missing:
        next_steps.append("NEXT_INSTALL_OR_UPDATE_SETUPHELPER")

    next_steps.extend(["NEXT_CHECK_UPDATES_AND_SECURITY", "NEXT_CREATE_NEW_BACKUP", "NEXT_EXPORT_REPORT"])
    _add_unique(recommendations, next_steps)

    # overall status
    report_status = "unknown"
    if errors or post_status == "failed" or execute_status == "failed":
        report_status = "failed"
    elif any(s.get("status") == "warning" for s in sections) or warnings:
        report_status = "warning"
    elif any(s.get("status") == "ok" for s in sections):
        report_status = "ok"

    sections.append(_sec("REPORT_SECTION_NEXT_STEPS", "ok" if next_steps else "unknown", next_steps))

    return {
        "report_status": report_status,
        "summary": {
            "system_type": system_type,
            "restore_code": execute_code or None,
            "preview_code": preview_code or None,
            "post_restore_status": post_status or None,
            "boot_status": bc_status or None,
            "boot_plan_status": plan_status or None,
        },
        "sections": sections,
        "risks": risks,
        "recommendations": recommendations,
        "blocked_actions": list(dict.fromkeys(blocked_actions)),
        "next_steps": list(dict.fromkeys(next_steps)),
        "warnings": warnings,
        "errors": errors,
    }
