from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from core.rescue_allowlist import assert_restore_live_target_directory, path_under_prefixes, RESCUE_LIVE_RESTORE_PREFIXES

_RECOVERY_MINIMAL_SESSION_STORE: dict[str, dict[str, Any]] = {}
_RECOVERY_MINIMAL_TTL_SECONDS = 900

_REPO_ROOT = Path(__file__).resolve().parents[2]
_AGENT_SOURCE_CANDIDATES = [
    _REPO_ROOT / "backend",
    _REPO_ROOT / "setuphelfer.service",
]
_BACKEND_UNIT_CANDIDATES = [
    _REPO_ROOT / "setuphelfer-backend.service",
    _REPO_ROOT / "debian" / "setuphelfer-backend.service",
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_plan(plan: dict[str, Any]) -> str:
    payload = json.dumps(plan or {}, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _plan_invalid(plan: dict[str, Any]) -> bool:
    status = str(plan.get("plan_status") or "")
    if status in {"blocked", "not_applicable", ""}:
        return True
    blocked_steps = plan.get("blocked_steps") if isinstance(plan.get("blocked_steps"), list) else []
    return bool(blocked_steps)


def _step_allowed(step_code: str, plan: dict[str, Any]) -> bool:
    required_steps = plan.get("required_steps") if isinstance(plan.get("required_steps"), list) else []
    for step in required_steps:
        if not isinstance(step, dict):
            continue
        if str(step.get("code") or "") != step_code:
            continue
        return bool(step.get("applicable")) and (not bool(step.get("auto_allowed")))
    return False


def _blocked_by_assessment(plan: dict[str, Any]) -> bool:
    assessment = plan.get("system_assessment") if isinstance(plan.get("system_assessment"), dict) else {}
    system_type = str(assessment.get("system_type") or "")
    return system_type in {"WINDOWS", "DUALBOOT", "UNKNOWN", "PARTIAL_SYSTEM"} or bool(assessment.get("safety_blocked"))


def _safe_under_target(target_root: Path, rel_path: str, *, create_parent: bool = False) -> Path:
    candidate = (target_root / rel_path).resolve(strict=False)
    try:
        candidate.relative_to(target_root)
    except ValueError as exc:
        raise ValueError("path outside target") from exc
    if create_parent:
        parent = candidate.parent
        parent.mkdir(parents=True, exist_ok=True)
        resolved_parent = parent.resolve(strict=True)
        try:
            resolved_parent.relative_to(target_root)
        except ValueError as exc:
            raise ValueError("parent outside target") from exc
    return candidate


def _validated_target(target_path: str) -> Path:
    if not target_path:
        raise ValueError("empty target path")
    target = Path(target_path).resolve(strict=False)
    if str(target) == "/":
        raise ValueError("root target forbidden")
    # existing allowlist present -> enforce
    _ = assert_restore_live_target_directory(str(target))
    if not target.exists() or not target.is_dir():
        raise ValueError("target missing")
    if not path_under_prefixes(target, RESCUE_LIVE_RESTORE_PREFIXES):
        raise ValueError("target outside allowed recovery roots")
    return target


def create_recovery_minimal_session(request: dict[str, Any]) -> dict[str, Any]:
    target_path = str(request.get("target_path") or "")
    selected_steps = request.get("selected_steps") if isinstance(request.get("selected_steps"), list) else []
    plan = request.get("plan") if isinstance(request.get("plan"), dict) else {}

    out = {
        "code": "RECOVERY_MINIMAL_PLAN_INVALID",
        "session_id": None,
        "confirmation_token": None,
        "expires_at": None,
        "warnings": [],
        "errors": [],
    }

    if not target_path or not selected_steps or _plan_invalid(plan) or _blocked_by_assessment(plan):
        out["errors"].append("RECOVERY_MINIMAL_PLAN_INVALID")
        return out

    try:
        _validated_target(target_path)
    except Exception:
        out["code"] = "RECOVERY_MINIMAL_EXECUTE_BLOCKED"
        out["errors"].append("RECOVERY_MINIMAL_TARGET_INVALID")
        return out

    for step in selected_steps:
        step_code = str(step or "")
        if not step_code or not _step_allowed(step_code, plan):
            out["code"] = "RECOVERY_MINIMAL_STEP_NOT_ALLOWED"
            out["errors"].append("RECOVERY_MINIMAL_STEP_NOT_ALLOWED")
            return out

    session_id = secrets.token_hex(8)
    token = secrets.token_urlsafe(24)
    created_at = _now()
    expires_at = created_at + timedelta(seconds=_RECOVERY_MINIMAL_TTL_SECONDS)

    _RECOVERY_MINIMAL_SESSION_STORE[session_id] = {
        "session_id": session_id,
        "confirmation_token": token,
        "target_path": target_path,
        "selected_steps": [str(x) for x in selected_steps],
        "plan_snapshot_hash": _hash_plan(plan),
        "system_assessment": dict(plan.get("system_assessment") or {}),
        "created_at": created_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "used": False,
    }

    out["code"] = "RECOVERY_MINIMAL_SESSION_CREATED"
    out["session_id"] = session_id
    out["confirmation_token"] = token
    out["expires_at"] = expires_at.isoformat()
    return out


def _discover_existing(candidates: list[Path]) -> Path | None:
    for p in candidates:
        if p.exists():
            return p
    return None


def _write_recovery_notes(target_root: Path, selected_steps: list[str], performed: list[dict[str, Any]], blocked: list[str], warnings: list[str]) -> tuple[bool, str, dict[str, Any]]:
    notes_file = _safe_under_target(target_root, "var/log/setuphelfer/recovery-notes.json", create_parent=True)
    payload = {
        "generated_at": _now().isoformat(),
        "selected_steps": selected_steps,
        "performed_steps": [s.get("code") for s in performed if s.get("status") == "completed"],
        "blocked_steps": blocked,
        "recommendations": ["NEXT_MANUAL_REVIEW_REQUIRED"],
        "warnings": warnings,
        "no_auto_ssh_enabled": True,
        "no_user_created": True,
        "no_network_changed": True,
    }
    notes_file.write_text(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return True, "RECOVERY_MINIMAL_WRITE_NOTES_COMPLETED", {"notes_path": str(notes_file)}


def _prepare_setuphelfer_agent(target_root: Path) -> tuple[bool, str, dict[str, Any]]:
    src = _discover_existing(_AGENT_SOURCE_CANDIDATES)
    if src is None:
        return False, "RECOVERY_MINIMAL_LOCAL_SOURCE_MISSING", {}
    marker = _safe_under_target(target_root, "opt/setuphelfer/prepared-agent-source.txt", create_parent=True)
    marker.write_text(str(src) + "\n", encoding="utf-8")
    return True, "RECOVERY_MINIMAL_SETUPHELPER_PREPARED", {"source": str(src), "marker": str(marker)}


def _prepare_backend_unit(target_root: Path) -> tuple[bool, str, dict[str, Any]]:
    src = _discover_existing(_BACKEND_UNIT_CANDIDATES)
    if src is None:
        return False, "RECOVERY_MINIMAL_LOCAL_SOURCE_MISSING", {}
    dst = _safe_under_target(target_root, "etc/systemd/system/setuphelfer-backend.service", create_parent=True)
    dst.write_text(src.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
    return True, "RECOVERY_MINIMAL_BACKEND_UNIT_PREPARED", {"source": str(src), "target": str(dst)}


def _record_plan_step(target_root: Path, step_code: str, result_code: str) -> tuple[bool, str, dict[str, Any]]:
    plan_file = _safe_under_target(target_root, f"var/log/setuphelfer/{step_code.lower()}.plan", create_parent=True)
    plan_file.write_text(result_code + "\n", encoding="utf-8")
    return True, result_code, {"plan_file": str(plan_file)}


def execute_recovery_minimal(request: dict[str, Any]) -> dict[str, Any]:
    session_id = str(request.get("session_id") or "")
    token = str(request.get("confirmation_token") or "")
    target_path = str(request.get("target_path") or "")
    plan = request.get("plan") if isinstance(request.get("plan"), dict) else {}

    out: dict[str, Any] = {
        "code": "RECOVERY_MINIMAL_EXECUTE_BLOCKED",
        "session_id": session_id or None,
        "steps": [],
        "warnings": [],
        "errors": [],
    }

    sess = _RECOVERY_MINIMAL_SESSION_STORE.get(session_id)
    if not sess:
        out["code"] = "RECOVERY_MINIMAL_SESSION_NOT_FOUND"
        out["errors"].append("RECOVERY_MINIMAL_SESSION_NOT_FOUND")
        return out

    if bool(sess.get("used")):
        out["code"] = "RECOVERY_MINIMAL_SESSION_ALREADY_USED"
        out["errors"].append("RECOVERY_MINIMAL_SESSION_ALREADY_USED")
        return out

    if token != str(sess.get("confirmation_token") or ""):
        out["code"] = "RECOVERY_MINIMAL_TOKEN_INVALID"
        out["errors"].append("RECOVERY_MINIMAL_TOKEN_INVALID")
        return out

    try:
        expires_at = datetime.fromisoformat(str(sess.get("expires_at") or ""))
    except Exception:
        expires_at = _now() - timedelta(seconds=1)
    if _now() >= expires_at:
        out["code"] = "RECOVERY_MINIMAL_SESSION_EXPIRED"
        out["errors"].append("RECOVERY_MINIMAL_SESSION_EXPIRED")
        return out

    if target_path != str(sess.get("target_path") or ""):
        out["code"] = "RECOVERY_MINIMAL_TARGET_INVALID"
        out["errors"].append("RECOVERY_MINIMAL_TARGET_INVALID")
        return out

    if plan and _hash_plan(plan) != str(sess.get("plan_snapshot_hash") or ""):
        out["code"] = "RECOVERY_MINIMAL_PLAN_INVALID"
        out["errors"].append("RECOVERY_MINIMAL_PLAN_INVALID")
        return out

    assessment = sess.get("system_assessment") if isinstance(sess.get("system_assessment"), dict) else {}
    system_type = str(assessment.get("system_type") or "")
    if system_type in {"WINDOWS", "DUALBOOT", "UNKNOWN", "PARTIAL_SYSTEM"} or bool(assessment.get("safety_blocked")):
        out["code"] = "RECOVERY_MINIMAL_EXECUTE_BLOCKED"
        out["errors"].append("RECOVERY_MINIMAL_EXECUTE_BLOCKED")
        return out

    # start of actual phase-2b execution path => single-use consumed
    sess["used"] = True

    try:
        target_root = _validated_target(target_path)
    except Exception:
        out["code"] = "RECOVERY_MINIMAL_TARGET_INVALID"
        out["errors"].append("RECOVERY_MINIMAL_TARGET_INVALID")
        return out

    selected_steps = list(sess.get("selected_steps") or [])
    blocked_steps: list[str] = []

    for step_code in selected_steps:
        step_result = {
            "code": step_code,
            "status": "blocked",
            "result_code": "RECOVERY_MINIMAL_STEP_BLOCKED",
            "details": {},
        }

        try:
            if step_code == "RECOVERY_STEP_WRITE_RECOVERY_NOTES":
                ok, result_code, details = _write_recovery_notes(target_root, selected_steps, out["steps"], blocked_steps, out["warnings"])
            elif step_code == "RECOVERY_STEP_INSTALL_SETUPHELPER_AGENT":
                ok, result_code, details = _prepare_setuphelfer_agent(target_root)
            elif step_code == "RECOVERY_STEP_ENABLE_SETUPHELPER_BACKEND":
                ok, result_code, details = _prepare_backend_unit(target_root)
            elif step_code == "RECOVERY_STEP_ENABLE_SSH":
                ok, result_code, details = _record_plan_step(target_root, step_code, "RECOVERY_MINIMAL_SSH_PLAN_RECORDED")
            elif step_code == "RECOVERY_STEP_CREATE_RECOVERY_USER":
                ok, result_code, details = _record_plan_step(target_root, step_code, "RECOVERY_MINIMAL_USER_PLAN_RECORDED")
            elif step_code == "RECOVERY_STEP_CONFIGURE_NETWORK_DHCP":
                ok, result_code, details = _record_plan_step(target_root, step_code, "RECOVERY_MINIMAL_NETWORK_PLAN_RECORDED")
            elif step_code == "RECOVERY_STEP_ENABLE_FIREWALL_BASELINE":
                ok, result_code, details = _record_plan_step(target_root, step_code, "RECOVERY_MINIMAL_FIREWALL_PLAN_RECORDED")
            elif step_code == "RECOVERY_STEP_CREATE_POST_RECOVERY_BACKUP":
                ok, result_code, details = _record_plan_step(target_root, step_code, "RECOVERY_MINIMAL_POST_BACKUP_PLAN_RECORDED")
            else:
                ok, result_code, details = False, "RECOVERY_MINIMAL_STEP_BLOCKED", {}

            if ok:
                step_result["status"] = "completed"
                step_result["result_code"] = result_code
                step_result["details"] = details
            else:
                step_result["status"] = "failed"
                step_result["result_code"] = result_code if result_code else "RECOVERY_MINIMAL_STEP_FAILED"
                step_result["details"] = details
                out["steps"].append(step_result)
                out["code"] = "RECOVERY_MINIMAL_EXECUTE_FAILED"
                out["errors"].append(step_result["result_code"])
                return out

            out["steps"].append(step_result)
        except Exception:
            step_result["status"] = "failed"
            step_result["result_code"] = "RECOVERY_MINIMAL_STEP_FAILED"
            out["steps"].append(step_result)
            out["code"] = "RECOVERY_MINIMAL_EXECUTE_FAILED"
            out["errors"].append("RECOVERY_MINIMAL_STEP_FAILED")
            return out

    out["code"] = "RECOVERY_MINIMAL_EXECUTE_COMPLETED"
    return out
