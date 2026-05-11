from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

_DEPLOY_WRITE_SESSION_STORE: dict[str, dict[str, Any]] = {}
_DEPLOY_WRITE_TTL_SECONDS = 900


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_payload(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload or {}, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _image_valid(image_inspect: dict[str, Any]) -> bool:
    code = str(image_inspect.get("code") or "")
    if code not in {"DEPLOY_IMAGE_INSPECT_OK", "DEPLOY_IMAGE_INSPECT_WARNING"}:
        return False
    errors = image_inspect.get("errors")
    if isinstance(errors, list) and errors:
        return False
    verification = image_inspect.get("verification")
    if isinstance(verification, dict) and bool(verification.get("checksum_expected")):
        return bool(verification.get("checksum_checked")) and bool(verification.get("checksum_ok"))
    return True


def _plan_valid_for_write_session(write_plan: dict[str, Any]) -> tuple[bool, str]:
    st = str(write_plan.get("plan_status") or "")
    if st not in {"ok", "review_required"}:
        return False, "DEPLOY_WRITE_PLAN_INVALID"
    if write_plan.get("blocked_reasons"):
        return False, "DEPLOY_WRITE_SESSION_BLOCKED"
    strategy = write_plan.get("write_strategy")
    if not isinstance(strategy, dict):
        return False, "DEPLOY_WRITE_PLAN_INVALID"
    if str(strategy.get("mode") or "") == "unsupported":
        return False, "DEPLOY_WRITE_SESSION_BLOCKED"
    image = write_plan.get("image")
    if isinstance(image, dict):
        inspect_code = str(image.get("inspect_code") or "")
        if inspect_code not in {"DEPLOY_IMAGE_INSPECT_OK", "DEPLOY_IMAGE_INSPECT_WARNING"}:
            return False, "DEPLOY_WRITE_IMAGE_INVALID"
    target = write_plan.get("target")
    if isinstance(target, dict) and not bool(target.get("write_allowed")):
        return False, "DEPLOY_WRITE_SESSION_BLOCKED"
    return True, ""


def create_deploy_write_session(request: dict[str, Any]) -> dict[str, Any]:
    target_device = str(request.get("target_device") or "")
    selected_profile = str(request.get("selected_profile") or "")
    image_inspect = request.get("image_inspect") if isinstance(request.get("image_inspect"), dict) else {}
    write_plan = request.get("write_plan") if isinstance(request.get("write_plan"), dict) else {}
    confirmations = request.get("confirmations") if isinstance(request.get("confirmations"), list) else []

    out = {
        "code": "DEPLOY_WRITE_PLAN_INVALID",
        "write_session_id": None,
        "confirmation_token": None,
        "expires_at": None,
        "warnings": [],
        "errors": [],
    }

    if not target_device or not selected_profile:
        out["code"] = "DEPLOY_WRITE_SESSION_BLOCKED"
        out["errors"].append("DEPLOY_WRITE_SESSION_BLOCKED")
        return out

    ok_plan, plan_err = _plan_valid_for_write_session(write_plan)
    if not ok_plan:
        out["code"] = plan_err
        out["errors"].append(plan_err)
        return out

    if not _image_valid(image_inspect):
        out["code"] = "DEPLOY_WRITE_IMAGE_INVALID"
        out["errors"].append("DEPLOY_WRITE_IMAGE_INVALID")
        return out

    image = write_plan.get("image") if isinstance(write_plan.get("image"), dict) else {}
    image_path = str(image.get("path") or "")
    if not image_path:
        out["code"] = "DEPLOY_WRITE_IMAGE_INVALID"
        out["errors"].append("DEPLOY_WRITE_IMAGE_INVALID")
        return out

    required = write_plan.get("required_confirmations") if isinstance(write_plan.get("required_confirmations"), list) else []
    req = [str(x) for x in required]
    got = [str(x) for x in confirmations]
    if len(set(got)) != len(got) or len(set(req)) != len(req):
        out["code"] = "DEPLOY_WRITE_CONFIRMATION_INVALID"
        out["errors"].append("DEPLOY_WRITE_CONFIRMATION_INVALID")
        return out
    if any(x not in req for x in got):
        out["code"] = "DEPLOY_WRITE_CONFIRMATION_INVALID"
        out["errors"].append("DEPLOY_WRITE_CONFIRMATION_INVALID")
        return out
    if any(x not in got for x in req):
        out["code"] = "DEPLOY_WRITE_CONFIRMATION_MISSING"
        out["errors"].append("DEPLOY_WRITE_CONFIRMATION_MISSING")
        return out

    sid = secrets.token_hex(8)
    token = secrets.token_urlsafe(24)
    created = _now()
    expires = created + timedelta(seconds=_DEPLOY_WRITE_TTL_SECONDS)
    _DEPLOY_WRITE_SESSION_STORE[sid] = {
        "write_session_id": sid,
        "confirmation_token": token,
        "target_device": target_device,
        "selected_profile": selected_profile,
        "image_path": image_path,
        "write_plan_hash": _hash_payload(write_plan),
        "required_confirmations": req,
        "created_at": created.isoformat(),
        "expires_at": expires.isoformat(),
        "used": False,
    }
    out["code"] = "DEPLOY_WRITE_SESSION_CREATED"
    out["write_session_id"] = sid
    out["confirmation_token"] = token
    out["expires_at"] = expires.isoformat()
    return out


def _simulated_execution_steps() -> list[dict[str, Any]]:
    seq = [
        ("DEPLOY_EXEC_RECHECK_TARGET", False),
        ("DEPLOY_EXEC_RECHECK_IMAGE", False),
        ("DEPLOY_EXEC_UNMOUNT_TARGET", False),
        ("DEPLOY_EXEC_WRITE_IMAGE", True),
        ("DEPLOY_EXEC_SYNC", False),
        ("DEPLOY_EXEC_VERIFY_IMAGE", False),
        ("DEPLOY_EXEC_EXPAND_FILESYSTEM", True),
        ("DEPLOY_EXEC_INSTALL_SETUPHELPER", True),
        ("DEPLOY_EXEC_FINALIZE", False),
    ]
    return [
        {
            "code": code,
            "status": "simulated",
            "would_write": would_write,
            "requires_confirmation": True,
            "auto_allowed": False,
        }
        for code, would_write in seq
    ]


def execute_deploy_write_dryrun(request: dict[str, Any]) -> dict[str, Any]:
    sid = str(request.get("write_session_id") or "")
    token = str(request.get("confirmation_token") or "")
    target_device = str(request.get("target_device") or "")
    selected_profile = str(request.get("selected_profile") or "")
    image_path = str(request.get("image_path") or "")
    write_plan = request.get("write_plan") if isinstance(request.get("write_plan"), dict) else {}

    out = {
        "code": "DEPLOY_WRITE_EXECUTE_BLOCKED",
        "write_session_id": sid or None,
        "target_device": target_device or None,
        "selected_profile": selected_profile or None,
        "image_path": image_path or None,
        "simulated_execution": [],
        "warnings": [],
        "errors": [],
    }

    sess = _DEPLOY_WRITE_SESSION_STORE.get(sid)
    if not sess:
        out["code"] = "DEPLOY_WRITE_SESSION_NOT_FOUND"
        out["errors"].append("DEPLOY_WRITE_SESSION_NOT_FOUND")
        return out
    if token != str(sess.get("confirmation_token") or ""):
        out["code"] = "DEPLOY_WRITE_TOKEN_INVALID"
        out["errors"].append("DEPLOY_WRITE_TOKEN_INVALID")
        return out
    try:
        expires = datetime.fromisoformat(str(sess.get("expires_at") or ""))
    except Exception:
        expires = _now() - timedelta(seconds=1)
    if _now() >= expires:
        out["code"] = "DEPLOY_WRITE_SESSION_EXPIRED"
        out["errors"].append("DEPLOY_WRITE_SESSION_EXPIRED")
        return out
    if target_device != str(sess.get("target_device") or ""):
        out["code"] = "DEPLOY_WRITE_TARGET_MISMATCH"
        out["errors"].append("DEPLOY_WRITE_TARGET_MISMATCH")
        return out
    if selected_profile != str(sess.get("selected_profile") or ""):
        out["code"] = "DEPLOY_WRITE_PROFILE_MISMATCH"
        out["errors"].append("DEPLOY_WRITE_PROFILE_MISMATCH")
        return out
    if image_path != str(sess.get("image_path") or ""):
        out["code"] = "DEPLOY_WRITE_IMAGE_MISMATCH"
        out["errors"].append("DEPLOY_WRITE_IMAGE_MISMATCH")
        return out
    if write_plan and _hash_payload(write_plan) != str(sess.get("write_plan_hash") or ""):
        out["code"] = "DEPLOY_WRITE_PLAN_MISMATCH"
        out["errors"].append("DEPLOY_WRITE_PLAN_MISMATCH")
        return out

    ok_plan, _ = _plan_valid_for_write_session(write_plan if write_plan else {})
    # Fail-closed: write_plan is required for execute dry-run.
    if not write_plan or not ok_plan:
        out["code"] = "DEPLOY_WRITE_EXECUTE_BLOCKED"
        out["errors"].append("DEPLOY_WRITE_EXECUTE_BLOCKED")
        return out

    out["code"] = "DEPLOY_WRITE_EXECUTE_READY"
    out["target_device"] = str(sess.get("target_device") or "")
    out["selected_profile"] = str(sess.get("selected_profile") or "")
    out["image_path"] = str(sess.get("image_path") or "")
    out["simulated_execution"] = _simulated_execution_steps()
    return out
