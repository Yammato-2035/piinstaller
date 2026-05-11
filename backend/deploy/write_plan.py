from __future__ import annotations

from typing import Any

_BLOCK_BY_SAFETY_REASON = {
    "SAFETY_SYSTEM_DISK": "DEPLOY_WRITE_BLOCKED_SYSTEM_DISK",
    "SAFETY_LIVE_SYSTEM": "DEPLOY_WRITE_BLOCKED_LIVE_SYSTEM",
    "SAFETY_WINDOWS_DETECTED": "DEPLOY_WRITE_BLOCKED_WINDOWS",
    "SAFETY_DUALBOOT": "DEPLOY_WRITE_BLOCKED_DUALBOOT",
    "SAFETY_UNKNOWN_DEVICE": "DEPLOY_WRITE_BLOCKED_UNKNOWN",
    "SAFETY_BACKUP_TARGET_OK": "DEPLOY_WRITE_BLOCKED_NOT_EMPTY",
}

_CONFIRMATIONS = [
    "CONFIRM_TARGET_DEVICE",
    "CONFIRM_DATA_LOSS",
    "CONFIRM_IMAGE_SOURCE",
    "CONFIRM_NO_WINDOWS_DUALBOOT",
    "CONFIRM_FINAL_DEPLOY_WRITE",
]


def _safety_target(safety_summary: dict[str, Any], device: str) -> dict[str, Any] | None:
    targets = safety_summary.get("targets")
    if not isinstance(targets, list):
        return None
    for t in targets:
        if isinstance(t, dict) and str(t.get("device") or "") == device:
            return t
    return None


def _is_empty_target(t: dict[str, Any]) -> bool:
    return str(t.get("reason_code") or "") == "SAFETY_EMPTY_DISK"


def _image_is_acceptable(image_inspect: dict[str, Any]) -> bool:
    code = str(image_inspect.get("code") or "")
    if code not in {"DEPLOY_IMAGE_INSPECT_OK", "DEPLOY_IMAGE_INSPECT_WARNING"}:
        return False
    errs = image_inspect.get("errors")
    if isinstance(errs, list) and errs:
        return False
    verification = image_inspect.get("verification")
    if not isinstance(verification, dict):
        return True
    if bool(verification.get("checksum_expected")):
        return bool(verification.get("checksum_checked")) and bool(verification.get("checksum_ok"))
    return True


def _write_mode(deploy_preview: dict[str, Any]) -> str:
    os_source = deploy_preview.get("os_source")
    if not isinstance(os_source, dict):
        return "unsupported"
    src_type = str(os_source.get("type") or "")
    if src_type in {"local_image", "remote_image"}:
        return "image_to_disk"
    if src_type == "official_installer":
        return "installer_to_disk"
    return "unsupported"


def _simulated_operations() -> list[dict[str, Any]]:
    ops = [
        ("DEPLOY_WRITE_OP_RECHECK_TARGET", False, False),
        ("DEPLOY_WRITE_OP_UNMOUNT_TARGET", False, False),
        ("DEPLOY_WRITE_OP_WRITE_IMAGE", True, True),
        ("DEPLOY_WRITE_OP_SYNC", False, False),
        ("DEPLOY_WRITE_OP_VERIFY_WRITTEN_IMAGE", False, False),
        ("DEPLOY_WRITE_OP_EXPAND_FILESYSTEM", True, True),
        ("DEPLOY_WRITE_OP_INSTALL_SETUPHELPER", True, False),
        ("DEPLOY_WRITE_OP_INITIAL_HARDENING", True, False),
    ]
    return [
        {
            "code": code,
            "would_write": would_write,
            "destructive": destructive,
            "requires_confirmation": True,
            "auto_allowed": False,
        }
        for code, would_write, destructive in ops
    ]


def generate_deploy_write_plan(
    deploy_session: dict,
    deploy_preview: dict,
    image_inspect: dict,
    inspect_result: dict,
    safety_summary: dict,
) -> dict[str, Any]:
    target_device = str(deploy_session.get("target_device") or "")
    preview_target = str((deploy_preview.get("target") or {}).get("target_device") or "")
    image_view = image_inspect.get("image") if isinstance(image_inspect.get("image"), dict) else {}
    blocked_reasons: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []
    risks: list[str] = []

    if not target_device:
        blocked_reasons.append("DEPLOY_WRITE_BLOCKED_TARGET_MISSING")
    if preview_target and target_device and preview_target != target_device:
        blocked_reasons.append("DEPLOY_WRITE_BLOCKED_TARGET_MISMATCH")

    if str(safety_summary.get("policy_code") or "") != "safety.summary.v1":
        blocked_reasons.append("DEPLOY_WRITE_BLOCKED_SAFETY")

    target_eval = _safety_target(safety_summary if isinstance(safety_summary, dict) else {}, target_device)
    if target_device and target_eval is None:
        blocked_reasons.append("DEPLOY_WRITE_BLOCKED_UNKNOWN")
    if isinstance(target_eval, dict):
        if not bool(target_eval.get("write_allowed")):
            blocked_reasons.append("DEPLOY_WRITE_BLOCKED_SAFETY")
        mapped = _BLOCK_BY_SAFETY_REASON.get(str(target_eval.get("reason_code") or ""))
        if mapped:
            blocked_reasons.append(mapped)
        if not _is_empty_target(target_eval):
            blocked_reasons.append("DEPLOY_WRITE_BLOCKED_NOT_EMPTY")

    cls = inspect_result.get("classification") if isinstance(inspect_result, dict) else {}
    if isinstance(cls, dict):
        st = str(cls.get("system_type") or "")
        if st == "WINDOWS":
            blocked_reasons.append("DEPLOY_WRITE_BLOCKED_WINDOWS")
        if st == "DUALBOOT":
            blocked_reasons.append("DEPLOY_WRITE_BLOCKED_DUALBOOT")
        if st == "UNKNOWN":
            blocked_reasons.append("DEPLOY_WRITE_BLOCKED_UNKNOWN")

    if not _image_is_acceptable(image_inspect if isinstance(image_inspect, dict) else {}):
        blocked_reasons.append("DEPLOY_WRITE_BLOCKED_IMAGE_INVALID")

    blocked_reasons = list(dict.fromkeys(blocked_reasons))
    mode = _write_mode(deploy_preview if isinstance(deploy_preview, dict) else {})

    if mode == "unsupported":
        warnings.append("DEPLOY_WRITE_MODE_UNSUPPORTED")

    simulated_operations = _simulated_operations()
    write_strategy = {
        "mode": mode,
        "requires_destructive_write": True,
        "requires_exclusive_device": True,
        "requires_reboot_after": mode == "installer_to_disk",
        "estimated_operations": [o["code"] for o in simulated_operations],
    }

    plan_status = "blocked" if blocked_reasons else ("review_required" if mode == "unsupported" else "ok")
    if blocked_reasons:
        errors.extend(blocked_reasons)
        risks.extend(
            [
                "DEPLOY_WRITE_RISK_DATA_LOSS",
                "DEPLOY_WRITE_RISK_WRONG_TARGET",
            ]
        )
    else:
        risks.append("DEPLOY_WRITE_RISK_DESTRUCTIVE")

    return {
        "plan_status": plan_status,
        "target": {
            "target_device": target_device or None,
            "preview_target_device": preview_target or None,
            "safety_reason_code": str((target_eval or {}).get("reason_code") or ""),
            "write_allowed": bool((target_eval or {}).get("write_allowed")),
        },
        "image": {
            "path": image_view.get("path"),
            "extension": image_view.get("extension"),
            "size_bytes": image_view.get("size_bytes"),
            "inspect_code": str(image_inspect.get("code") or ""),
        },
        "write_strategy": write_strategy,
        "simulated_operations": simulated_operations,
        "required_confirmations": list(_CONFIRMATIONS),
        "blocked_reasons": blocked_reasons,
        "risks": list(dict.fromkeys(risks)),
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
        "requires_manual_review": bool(plan_status != "ok"),
    }
