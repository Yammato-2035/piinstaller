from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

_DEPLOY_SESSION_STORE: dict[str, dict[str, Any]] = {}
_DEPLOY_TTL_SECONDS = 900

_BLOCKING_STEP_CODES = {
    "DEPLOY_BLOCKED_WINDOWS",
    "DEPLOY_BLOCKED_DUALBOOT",
    "DEPLOY_BLOCKED_SYSTEM_DISK",
    "DEPLOY_BLOCKED_LIVE_SYSTEM",
    "DEPLOY_BLOCKED_UNKNOWN_LAYOUT",
    "DEPLOY_BLOCKED_NOT_EMPTY",
    "DEPLOY_BLOCKED_SAFETY",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_plan(plan: dict[str, Any]) -> str:
    payload = json.dumps(plan or {}, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _find_selected_profile(plan: dict[str, Any], selected_profile: str) -> dict[str, Any] | None:
    profiles = plan.get("deploy_profiles")
    if not isinstance(profiles, list):
        return None
    for prof in profiles:
        if not isinstance(prof, dict):
            continue
        if str(prof.get("code") or "") == selected_profile:
            return prof
    return None


def _validate_plan_for_session(plan: dict[str, Any], selected_profile: str, target_device: str) -> tuple[bool, str]:
    if not isinstance(plan, dict) or not plan:
        return False, "DEPLOY_PLAN_INVALID"
    if str(plan.get("plan_status") or "") != "ok":
        return False, "DEPLOY_PLAN_INVALID"

    blocked_steps = plan.get("blocked_steps")
    if not isinstance(blocked_steps, list):
        blocked_steps = []
    if blocked_steps:
        return False, "DEPLOY_PLAN_INVALID"

    # Defensive hard-stop recheck by codes if exposed in plan.
    risks = plan.get("risks")
    if isinstance(risks, list) and any(str(x) in _BLOCKING_STEP_CODES for x in blocked_steps):
        return False, "DEPLOY_PLAN_INVALID"

    required_steps = plan.get("required_steps")
    if not isinstance(required_steps, list) or not required_steps:
        return False, "DEPLOY_PLAN_INVALID"
    for step in required_steps:
        if not isinstance(step, dict):
            return False, "DEPLOY_PLAN_INVALID"
        if bool(step.get("auto_allowed")):
            return False, "DEPLOY_PLAN_INVALID"

    if not selected_profile:
        return False, "DEPLOY_PROFILE_NOT_ALLOWED"
    profile = _find_selected_profile(plan, selected_profile)
    if profile is None:
        return False, "DEPLOY_PROFILE_NOT_ALLOWED"
    if not bool(profile.get("suitable")):
        return False, "DEPLOY_PROFILE_NOT_ALLOWED"
    if bool(profile.get("auto_allowed")):
        return False, "DEPLOY_PROFILE_NOT_ALLOWED"

    target = plan.get("target")
    if isinstance(target, dict):
        planned_dev = str(target.get("target_device") or "")
        if planned_dev and planned_dev != target_device:
            return False, "DEPLOY_TARGET_MISMATCH"

    return True, ""


def create_deploy_session(request: dict[str, Any]) -> dict[str, Any]:
    target_device = str(request.get("target_device") or "")
    selected_profile = str(request.get("selected_profile") or "")
    plan = request.get("plan") if isinstance(request.get("plan"), dict) else {}

    out: dict[str, Any] = {
        "code": "DEPLOY_PLAN_INVALID",
        "deploy_session_id": None,
        "confirmation_token": None,
        "expires_at": None,
        "warnings": [],
        "errors": [],
    }

    if not target_device:
        out["errors"].append("DEPLOY_TARGET_MISMATCH")
        return out

    ok, err = _validate_plan_for_session(plan, selected_profile, target_device)
    if not ok:
        out["code"] = err
        out["errors"].append(err)
        return out

    deploy_session_id = secrets.token_hex(8)
    token = secrets.token_urlsafe(24)
    created = _now()
    expires = created + timedelta(seconds=_DEPLOY_TTL_SECONDS)

    _DEPLOY_SESSION_STORE[deploy_session_id] = {
        "deploy_session_id": deploy_session_id,
        "confirmation_token": token,
        "target_device": target_device,
        "selected_profile": selected_profile,
        "plan_snapshot_hash": _hash_plan(plan),
        "created_at": created.isoformat(),
        "expires_at": expires.isoformat(),
        "used": False,
    }

    out["code"] = "DEPLOY_SESSION_CREATED"
    out["deploy_session_id"] = deploy_session_id
    out["confirmation_token"] = token
    out["expires_at"] = expires.isoformat()
    return out


def execute_deploy(request: dict[str, Any]) -> dict[str, Any]:
    deploy_session_id = str(request.get("deploy_session_id") or "")
    token = str(request.get("confirmation_token") or "")
    target_device = str(request.get("target_device") or "")
    selected_profile = str(request.get("selected_profile") or "")
    plan = request.get("plan") if isinstance(request.get("plan"), dict) else {}

    out: dict[str, Any] = {
        "code": "DEPLOY_EXECUTE_BLOCKED",
        "deploy_session_id": deploy_session_id or None,
        "target_device": target_device or None,
        "selected_profile": selected_profile or None,
        "next_phase": "deploy_preview",
        "warnings": [],
        "errors": [],
    }

    sess = _DEPLOY_SESSION_STORE.get(deploy_session_id)
    if not sess:
        out["code"] = "DEPLOY_SESSION_NOT_FOUND"
        out["errors"].append("DEPLOY_SESSION_NOT_FOUND")
        return out

    if bool(sess.get("used")):
        out["code"] = "DEPLOY_SESSION_ALREADY_USED"
        out["errors"].append("DEPLOY_SESSION_ALREADY_USED")
        return out

    if token != str(sess.get("confirmation_token") or ""):
        out["code"] = "DEPLOY_TOKEN_INVALID"
        out["errors"].append("DEPLOY_TOKEN_INVALID")
        return out

    try:
        expires = datetime.fromisoformat(str(sess.get("expires_at") or ""))
    except Exception:
        expires = _now() - timedelta(seconds=1)
    if _now() >= expires:
        out["code"] = "DEPLOY_SESSION_EXPIRED"
        out["errors"].append("DEPLOY_SESSION_EXPIRED")
        return out

    if target_device != str(sess.get("target_device") or ""):
        out["code"] = "DEPLOY_TARGET_MISMATCH"
        out["errors"].append("DEPLOY_TARGET_MISMATCH")
        return out

    if selected_profile != str(sess.get("selected_profile") or ""):
        out["code"] = "DEPLOY_PROFILE_MISMATCH"
        out["errors"].append("DEPLOY_PROFILE_MISMATCH")
        return out

    if plan and _hash_plan(plan) != str(sess.get("plan_snapshot_hash") or ""):
        out["code"] = "DEPLOY_PLAN_MISMATCH"
        out["errors"].append("DEPLOY_PLAN_MISMATCH")
        return out

    # NO-OP prep phase: no install, no writes, no session consumption.
    out["code"] = "DEPLOY_EXECUTE_READY"
    out["target_device"] = str(sess.get("target_device") or "")
    out["selected_profile"] = str(sess.get("selected_profile") or "")
    return out
