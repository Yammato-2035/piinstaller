from __future__ import annotations

import hashlib
import json
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_ACTIVATION_SESSION_STORE: dict[str, dict[str, Any]] = {}
_ACTIVATION_TTL_SECONDS = 900

_BLOCKING_CODES = {
    "ACTIVATION_BLOCKED_WINDOWS",
    "ACTIVATION_BLOCKED_DUALBOOT",
    "ACTIVATION_BLOCKED_UNKNOWN_LAYOUT",
    "ACTIVATION_BLOCKED_SAFETY",
    "ACTIVATION_BLOCKED_NO_LINUX_TARGET",
    "ACTIVATION_BLOCKED_BOOT_FAILED",
}
_ALLOWED_KEY_TYPES = {"ssh-ed25519", "ssh-rsa", "ecdsa-sha2-nistp256"}

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BACKEND_SOURCE_CANDIDATES = [
    _REPO_ROOT / "backend",
    _REPO_ROOT / "setuphelfer-backend.service",
    _REPO_ROOT / "debian" / "setuphelfer-backend.service",
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_plan(plan: dict[str, Any]) -> str:
    payload = json.dumps(plan or {}, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _safe_target_root(target_path: str) -> Path:
    p = Path(str(target_path or "")).expanduser().resolve(strict=False)
    if str(p) == "/":
        raise ValueError("root target forbidden")
    if not p.exists() or not p.is_dir():
        raise ValueError("target missing")
    return p


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


def _valid_step(step_code: str, plan: dict[str, Any]) -> bool:
    required = plan.get("required_steps") if isinstance(plan.get("required_steps"), list) else []
    for entry in required:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("code") or "") != step_code:
            continue
        return bool(entry.get("applicable")) and (not bool(entry.get("auto_allowed")))
    return False


def _plan_blocked(plan: dict[str, Any]) -> bool:
    st = str(plan.get("plan_status") or "")
    if st in {"blocked", "not_applicable", ""}:
        return True
    blocked_steps = plan.get("blocked_steps") if isinstance(plan.get("blocked_steps"), list) else []
    for b in blocked_steps:
        if isinstance(b, str) and b in _BLOCKING_CODES:
            return True
    return bool(blocked_steps)


def _validate_ssh_public_key(value: str) -> tuple[bool, str]:
    raw = str(value or "").strip()
    if not raw:
        return False, "RECOVERY_ACTIVATION_SSH_KEY_REQUIRED"
    if "\n" in raw or "\r" in raw:
        return False, "RECOVERY_ACTIVATION_SSH_KEY_INVALID"
    if len(raw) > 8192:
        return False, "RECOVERY_ACTIVATION_SSH_KEY_INVALID"
    if "BEGIN OPENSSH PRIVATE KEY" in raw or "PRIVATE KEY" in raw:
        return False, "RECOVERY_ACTIVATION_SSH_KEY_INVALID"
    if any(tok in raw for tok in [";", "&&", "||", "`", "$("]):
        return False, "RECOVERY_ACTIVATION_SSH_KEY_INVALID"

    parts = raw.split()
    if len(parts) < 2:
        return False, "RECOVERY_ACTIVATION_SSH_KEY_INVALID"
    if parts[0] not in _ALLOWED_KEY_TYPES:
        return False, "RECOVERY_ACTIVATION_SSH_KEY_INVALID"
    if not re.fullmatch(r"[A-Za-z0-9+/=]+", parts[1]):
        return False, "RECOVERY_ACTIVATION_SSH_KEY_INVALID"
    return True, ""


def _discover_backend_source() -> Path | None:
    for p in _BACKEND_SOURCE_CANDIDATES:
        if p.exists():
            return p
    return None


def _step_prepare_ssh_key_auth(target_root: Path, ssh_public_key: str) -> tuple[bool, str, dict[str, Any]]:
    ok, err_code = _validate_ssh_public_key(ssh_public_key)
    if not ok:
        return False, err_code, {}

    ak = _safe_under_target(target_root, "home/setuphelfer-recovery/.ssh/authorized_keys", create_parent=True)
    ak.write_text(ssh_public_key.strip() + "\n", encoding="utf-8")
    return True, "RECOVERY_ACTIVATION_STEP_COMPLETED", {"authorized_keys": str(ak)}


def _step_disable_password_login(target_root: Path) -> tuple[bool, str, dict[str, Any]]:
    cfg = _safe_under_target(target_root, "etc/ssh/sshd_config.setuphelfer_recovery", create_parent=True)
    cfg.write_text("PasswordAuthentication no\nPermitRootLogin no\n", encoding="utf-8")
    return True, "RECOVERY_ACTIVATION_PASSWORD_LOGIN_DISABLED", {"config_path": str(cfg), "root_login": "RECOVERY_ACTIVATION_ROOT_LOGIN_DISABLED"}


def _step_create_recovery_user_secure(target_root: Path) -> tuple[bool, str, dict[str, Any]]:
    marker = _safe_under_target(target_root, "var/log/setuphelfer/recovery-user.plan", create_parent=True)
    marker.write_text("user=setuphelfer-recovery\nmode=offline-plan-only\n", encoding="utf-8")
    return True, "RECOVERY_ACTIVATION_USER_PREPARED", {"marker": str(marker), "user": "setuphelfer-recovery"}


def _step_enable_ssh_service(target_root: Path) -> tuple[bool, str, dict[str, Any]]:
    marker = _safe_under_target(target_root, "etc/systemd/system/ssh.service.setuphelfer_prep", create_parent=True)
    marker.write_text("prepared=true\nexecute=deferred\n", encoding="utf-8")
    return True, "RECOVERY_ACTIVATION_SSH_SERVICE_PREPARED", {"marker": str(marker)}


def _step_enable_setuphelfer_backend(target_root: Path) -> tuple[bool, str, dict[str, Any]]:
    source = _discover_backend_source()
    if source is None:
        return False, "RECOVERY_ACTIVATION_STEP_FAILED", {"error": "RECOVERY_ACTIVATION_PLAN_INVALID"}

    marker = _safe_under_target(target_root, "opt/setuphelfer/backend.prepare", create_parent=True)
    marker.write_text(str(source) + "\n", encoding="utf-8")
    return True, "RECOVERY_ACTIVATION_BACKEND_PREPARED", {"source": str(source), "marker": str(marker)}


def _step_bind_backend_interface(target_root: Path, allow_lan_backend_bind: bool) -> tuple[bool, str, dict[str, Any], list[str]]:
    warnings: list[str] = []
    host = "127.0.0.1"
    if allow_lan_backend_bind:
        host = "0.0.0.0"
        warnings.append("RECOVERY_ACTIVATION_LAN_BIND_REQUIRES_CONFIRMATION")

    cfg = _safe_under_target(target_root, "opt/setuphelfer/backend-bind.json", create_parent=True)
    cfg.write_text(json.dumps({"host": host, "port": 8000}, sort_keys=True) + "\n", encoding="utf-8")
    return True, "RECOVERY_ACTIVATION_BACKEND_BIND_PREPARED", {"config": str(cfg), "host": host}, warnings


def _step_configure_basic_firewall(target_root: Path) -> tuple[bool, str, dict[str, Any]]:
    plan = _safe_under_target(target_root, "var/log/setuphelfer/firewall.plan", create_parent=True)
    plan.write_text("phase=plan-only\n", encoding="utf-8")
    return True, "RECOVERY_ACTIVATION_FIREWALL_PLAN_RECORDED", {"plan_file": str(plan)}


def _step_log_remote_access_details(target_root: Path, selected_steps: list[str], warnings: list[str]) -> tuple[bool, str, dict[str, Any]]:
    report = _safe_under_target(target_root, "var/log/setuphelfer/activation-access-report.json", create_parent=True)
    payload = {
        "generated_at": _now().isoformat(),
        "selected_steps": selected_steps,
        "warnings": warnings,
        "password_login_enabled": False,
        "root_login_enabled": False,
        "host_system_changed": False,
        "ports_opened_now": False,
    }
    report.write_text(json.dumps(payload, sort_keys=True, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return True, "RECOVERY_ACTIVATION_ACCESS_REPORT_WRITTEN", {"report": str(report)}


def create_recovery_activation_session(request: dict[str, Any]) -> dict[str, Any]:
    target_path = str(request.get("target_path") or "")
    selected_steps = request.get("selected_steps") if isinstance(request.get("selected_steps"), list) else []
    plan = request.get("plan") if isinstance(request.get("plan"), dict) else {}

    out = {
        "code": "RECOVERY_ACTIVATION_PLAN_INVALID",
        "activation_session_id": None,
        "confirmation_token": None,
        "expires_at": None,
        "warnings": [],
        "errors": [],
    }

    if not target_path or not selected_steps or _plan_blocked(plan):
        out["errors"].append("RECOVERY_ACTIVATION_PLAN_INVALID")
        return out

    if not isinstance(plan.get("required_steps"), list) or not plan.get("required_steps"):
        out["errors"].append("RECOVERY_ACTIVATION_PLAN_INVALID")
        return out

    for step in selected_steps:
        step_code = str(step or "")
        if not step_code or not _valid_step(step_code, plan):
            out["code"] = "RECOVERY_ACTIVATION_STEP_NOT_ALLOWED"
            out["errors"].append("RECOVERY_ACTIVATION_STEP_NOT_ALLOWED")
            return out

    activation_session_id = secrets.token_hex(8)
    token = secrets.token_urlsafe(24)
    created = _now()
    expires = created + timedelta(seconds=_ACTIVATION_TTL_SECONDS)

    _ACTIVATION_SESSION_STORE[activation_session_id] = {
        "activation_session_id": activation_session_id,
        "confirmation_token": token,
        "target_path": target_path,
        "selected_steps": [str(x) for x in selected_steps],
        "plan_snapshot_hash": _hash_plan(plan),
        "created_at": created.isoformat(),
        "expires_at": expires.isoformat(),
        "used": False,
    }

    out["code"] = "RECOVERY_ACTIVATION_SESSION_CREATED"
    out["activation_session_id"] = activation_session_id
    out["confirmation_token"] = token
    out["expires_at"] = expires.isoformat()
    return out


def execute_recovery_activation(request: dict[str, Any]) -> dict[str, Any]:
    activation_session_id = str(request.get("activation_session_id") or "")
    token = str(request.get("confirmation_token") or "")
    target_path = str(request.get("target_path") or "")
    plan = request.get("plan") if isinstance(request.get("plan"), dict) else {}
    ssh_public_key = str(request.get("ssh_public_key") or "")
    allow_lan_backend_bind = bool(request.get("allow_lan_backend_bind"))

    out: dict[str, Any] = {
        "code": "RECOVERY_ACTIVATION_EXECUTE_BLOCKED",
        "activation_session_id": activation_session_id or None,
        "steps": [],
        "warnings": [],
        "errors": [],
    }

    sess = _ACTIVATION_SESSION_STORE.get(activation_session_id)
    if not sess:
        out["code"] = "RECOVERY_ACTIVATION_SESSION_NOT_FOUND"
        out["errors"].append("RECOVERY_ACTIVATION_SESSION_NOT_FOUND")
        return out

    if bool(sess.get("used")):
        out["code"] = "RECOVERY_ACTIVATION_SESSION_ALREADY_USED"
        out["errors"].append("RECOVERY_ACTIVATION_SESSION_ALREADY_USED")
        return out

    if token != str(sess.get("confirmation_token") or ""):
        out["code"] = "RECOVERY_ACTIVATION_TOKEN_INVALID"
        out["errors"].append("RECOVERY_ACTIVATION_TOKEN_INVALID")
        return out

    try:
        expires = datetime.fromisoformat(str(sess.get("expires_at") or ""))
    except Exception:
        expires = _now() - timedelta(seconds=1)
    if _now() >= expires:
        out["code"] = "RECOVERY_ACTIVATION_SESSION_EXPIRED"
        out["errors"].append("RECOVERY_ACTIVATION_SESSION_EXPIRED")
        return out

    if target_path != str(sess.get("target_path") or ""):
        out["code"] = "RECOVERY_ACTIVATION_TARGET_INVALID"
        out["errors"].append("RECOVERY_ACTIVATION_TARGET_INVALID")
        return out

    if plan and _hash_plan(plan) != str(sess.get("plan_snapshot_hash") or ""):
        out["code"] = "RECOVERY_ACTIVATION_PLAN_MISMATCH"
        out["errors"].append("RECOVERY_ACTIVATION_PLAN_MISMATCH")
        return out

    try:
        target_root = _safe_target_root(target_path)
    except Exception:
        out["code"] = "RECOVERY_ACTIVATION_TARGET_INVALID"
        out["errors"].append("RECOVERY_ACTIVATION_TARGET_INVALID")
        return out

    # Controlled execute consumes session immediately at execution start.
    sess["used"] = True

    selected_steps = list(sess.get("selected_steps") or [])

    for step_code in selected_steps:
        step = {"code": step_code, "status": "blocked", "result_code": "RECOVERY_ACTIVATION_STEP_BLOCKED", "details": {}}

        try:
            if step_code == "ACTIVATION_STEP_PREPARE_SSH_KEY_AUTH":
                ok, result_code, details = _step_prepare_ssh_key_auth(target_root, ssh_public_key)
            elif step_code == "ACTIVATION_STEP_DISABLE_PASSWORD_LOGIN":
                ok, result_code, details = _step_disable_password_login(target_root)
            elif step_code == "ACTIVATION_STEP_CREATE_RECOVERY_USER_SECURE":
                ok, result_code, details = _step_create_recovery_user_secure(target_root)
            elif step_code == "ACTIVATION_STEP_ENABLE_SSH_SERVICE":
                ok, result_code, details = _step_enable_ssh_service(target_root)
            elif step_code == "ACTIVATION_STEP_ENABLE_SETUPHELPER_BACKEND":
                ok, result_code, details = _step_enable_setuphelfer_backend(target_root)
            elif step_code == "ACTIVATION_STEP_BIND_BACKEND_TO_SAFE_INTERFACE":
                ok, result_code, details, warns = _step_bind_backend_interface(target_root, allow_lan_backend_bind)
                for w in warns:
                    if w not in out["warnings"]:
                        out["warnings"].append(w)
            elif step_code == "ACTIVATION_STEP_CONFIGURE_BASIC_FIREWALL":
                ok, result_code, details = _step_configure_basic_firewall(target_root)
            elif step_code == "ACTIVATION_STEP_LOG_REMOTE_ACCESS_DETAILS":
                ok, result_code, details = _step_log_remote_access_details(target_root, selected_steps, out["warnings"])
            else:
                ok, result_code, details = False, "RECOVERY_ACTIVATION_STEP_BLOCKED", {}

            if ok:
                step["status"] = "completed"
                step["result_code"] = result_code
                step["details"] = details
                out["steps"].append(step)
                continue

            step["status"] = "failed"
            step["result_code"] = result_code or "RECOVERY_ACTIVATION_STEP_FAILED"
            step["details"] = details
            out["steps"].append(step)
            out["code"] = "RECOVERY_ACTIVATION_EXECUTE_FAILED"
            out["errors"].append(step["result_code"])
            return out
        except Exception:
            step["status"] = "failed"
            step["result_code"] = "RECOVERY_ACTIVATION_STEP_FAILED"
            out["steps"].append(step)
            out["code"] = "RECOVERY_ACTIVATION_EXECUTE_FAILED"
            out["errors"].append("RECOVERY_ACTIVATION_STEP_FAILED")
            return out

    out["code"] = "RECOVERY_ACTIVATION_EXECUTE_COMPLETED"
    return out
