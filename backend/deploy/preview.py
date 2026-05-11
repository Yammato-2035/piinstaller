from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from deploy.execute import _DEPLOY_SESSION_STORE, _hash_plan

_PREVIEW_TTL_SECONDS = 900


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _validate_os_source(os_source: dict[str, Any]) -> tuple[bool, str, list[str]]:
    warnings: list[str] = []
    if not isinstance(os_source, dict):
        return False, "DEPLOY_PREVIEW_OS_SOURCE_INVALID", warnings
    src_type = str(os_source.get("type") or "")
    name = str(os_source.get("name") or "")
    if src_type not in {"local_image", "remote_image", "official_installer"}:
        return False, "DEPLOY_PREVIEW_OS_SOURCE_INVALID", warnings
    if not name:
        return False, "DEPLOY_PREVIEW_OS_SOURCE_INVALID", warnings
    if src_type == "remote_image":
        url = str(os_source.get("url") or "")
        checksum = str(os_source.get("checksum") or "")
        if not (url.startswith("http://") or url.startswith("https://")) or not checksum:
            return False, "DEPLOY_PREVIEW_OS_SOURCE_INVALID", warnings
        warnings.append("DEPLOY_PREVIEW_REMOTE_DOWNLOAD_BLOCKED")
    return True, "", warnings


def _simulated_steps() -> list[dict[str, Any]]:
    items = [
        ("DEPLOY_SIM_VALIDATE_TARGET", False),
        ("DEPLOY_SIM_PARTITION_DISK", True),
        ("DEPLOY_SIM_FORMAT_FILESYSTEM", True),
        ("DEPLOY_SIM_INSTALL_BASE_SYSTEM", True),
        ("DEPLOY_SIM_INSTALL_SETUPHELPER", True),
        ("DEPLOY_SIM_APPLY_PROFILE", True),
        ("DEPLOY_SIM_INITIAL_HARDENING", True),
        ("DEPLOY_SIM_ENABLE_RECOVERY_ACCESS", True),
    ]
    return [
        {
            "code": code,
            "would_write": would_write,
            "requires_confirmation": True,
            "auto_allowed": False,
        }
        for code, would_write in items
    ]


def preview_deploy(request: dict[str, Any]) -> dict[str, Any]:
    deploy_session_id = str(request.get("deploy_session_id") or "")
    token = str(request.get("confirmation_token") or "")
    target_device = str(request.get("target_device") or "")
    selected_profile = str(request.get("selected_profile") or "")
    plan = request.get("plan") if isinstance(request.get("plan"), dict) else {}
    os_source = request.get("os_source") if isinstance(request.get("os_source"), dict) else {}

    out: dict[str, Any] = {
        "code": "DEPLOY_PREVIEW_FAILED",
        "preview_id": None,
        "target": {"target_device": target_device or None},
        "profile": {"code": selected_profile or None},
        "os_source": os_source if isinstance(os_source, dict) else {},
        "simulated_steps": [],
        "safety": {"allowed": False},
        "warnings": [],
        "errors": [],
    }

    sess = _DEPLOY_SESSION_STORE.get(deploy_session_id)
    if not sess:
        out["code"] = "DEPLOY_PREVIEW_SESSION_NOT_FOUND"
        out["errors"].append("DEPLOY_PREVIEW_SESSION_NOT_FOUND")
        return out

    if token != str(sess.get("confirmation_token") or ""):
        out["code"] = "DEPLOY_PREVIEW_TOKEN_INVALID"
        out["errors"].append("DEPLOY_PREVIEW_TOKEN_INVALID")
        return out

    try:
        expires = datetime.fromisoformat(str(sess.get("expires_at") or ""))
    except Exception:
        expires = _now() - timedelta(seconds=1)
    if _now() >= expires:
        out["code"] = "DEPLOY_PREVIEW_SESSION_EXPIRED"
        out["errors"].append("DEPLOY_PREVIEW_SESSION_EXPIRED")
        return out

    if target_device != str(sess.get("target_device") or ""):
        out["code"] = "DEPLOY_PREVIEW_TARGET_MISMATCH"
        out["errors"].append("DEPLOY_PREVIEW_TARGET_MISMATCH")
        return out

    if selected_profile != str(sess.get("selected_profile") or ""):
        out["code"] = "DEPLOY_PREVIEW_PROFILE_MISMATCH"
        out["errors"].append("DEPLOY_PREVIEW_PROFILE_MISMATCH")
        return out

    if plan and _hash_plan(plan) != str(sess.get("plan_snapshot_hash") or ""):
        out["code"] = "DEPLOY_PREVIEW_PLAN_MISMATCH"
        out["errors"].append("DEPLOY_PREVIEW_PLAN_MISMATCH")
        return out

    blocked_steps = plan.get("blocked_steps") if isinstance(plan.get("blocked_steps"), list) else []
    if blocked_steps:
        out["code"] = "DEPLOY_PREVIEW_SAFETY_BLOCKED"
        out["errors"].append("DEPLOY_PREVIEW_SAFETY_BLOCKED")
        out["safety"] = {"allowed": False, "blocked_steps": blocked_steps}
        return out

    ok_src, src_err, src_warns = _validate_os_source(os_source)
    if not ok_src:
        out["code"] = src_err
        out["errors"].append(src_err)
        return out
    out["warnings"].extend(src_warns)

    out["code"] = "DEPLOY_PREVIEW_CREATED"
    out["preview_id"] = secrets.token_hex(8)
    out["safety"] = {"allowed": True, "code": "DEPLOY_PREVIEW_SAFETY_OK"}
    out["target"] = {"target_device": str(sess.get("target_device") or "")}
    out["profile"] = {"code": str(sess.get("selected_profile") or ""), "requires_confirmation": True, "auto_allowed": False}
    out["simulated_steps"] = _simulated_steps()
    return out
