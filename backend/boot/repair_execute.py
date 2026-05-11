from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from boot.capability import check_boot_capability

_REPAIR_SESSION_STORE: dict[str, dict[str, Any]] = {}
_REPAIR_SESSION_TTL_SECONDS = 900

_ALLOWED_LOW = {"REPAIR_REGENERATE_FSTAB", "REPAIR_CHECK_UUID_MAPPING"}
_ALLOWED_MEDIUM = {"REPAIR_REBUILD_INITRAMFS", "REPAIR_RPI_BOOT_FILES"}
_ALLOWED_OPTIONAL = {"REPAIR_REINSTALL_GRUB"}
_BLOCKED_ALWAYS = {
    "REPAIR_MANUAL_WINDOWS_REQUIRED",
    "REPAIR_MANUAL_DUALBOOT_REQUIRED",
    "REPAIR_MANUAL_REVIEW_REQUIRED",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_plan_snapshot(plan: dict[str, Any]) -> str:
    blob = json.dumps(plan, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _bool_windows_or_dualboot(boot_capability: dict[str, Any]) -> bool:
    hints = boot_capability.get("boot_type_hints") if isinstance(boot_capability.get("boot_type_hints"), list) else []
    warns = boot_capability.get("warnings") if isinstance(boot_capability.get("warnings"), list) else []
    return ("BOOT_WINDOWS_BOOTMANAGER_FOUND" in hints) or ("BOOT_DUALBOOT_RISK" in warns)


def _is_action_allowed(action_code: str, plan: dict[str, Any], boot_capability: dict[str, Any]) -> bool:
    if action_code in _BLOCKED_ALWAYS:
        return False
    if _bool_windows_or_dualboot(boot_capability):
        return False

    actions = plan.get("proposed_actions") if isinstance(plan.get("proposed_actions"), list) else []
    selected = None
    for a in actions:
        if isinstance(a, dict) and str(a.get("code") or "") == action_code:
            selected = a
            break
    if not selected:
        return False

    if str(selected.get("risk_level") or "") == "high":
        return False

    if action_code in _ALLOWED_LOW or action_code in _ALLOWED_MEDIUM:
        return True

    if action_code in _ALLOWED_OPTIONAL:
        # Optional grub reinstall only in clear Linux-only context
        return not _bool_windows_or_dualboot(boot_capability)

    return False


def create_boot_repair_session(
    *,
    target_path: str,
    selected_action_code: str,
    inspect_result: dict[str, Any],
    post_verify: dict[str, Any],
    boot_capability: dict[str, Any],
    boot_repair_plan: dict[str, Any],
) -> dict[str, Any]:
    out = {
        "code": "BOOT_REPAIR_EXECUTE_FAILED",
        "repair_session_id": None,
        "confirmation_token": None,
        "warnings": [],
        "errors": [],
    }

    action_code = str(selected_action_code or "")
    target = str(target_path or "")

    if not action_code or not target:
        out["code"] = "BOOT_REPAIR_PRECHECK_FAILED"
        out["errors"].append("BOOT_REPAIR_PRECHECK_FAILED")
        return out

    if not _is_action_allowed(action_code, boot_repair_plan, boot_capability):
        out["code"] = "BOOT_REPAIR_ACTION_NOT_ALLOWED"
        out["errors"].append("BOOT_REPAIR_ACTION_NOT_ALLOWED")
        return out

    session_id = secrets.token_hex(8)
    token = secrets.token_urlsafe(24)
    created = _now()
    expires = created + timedelta(seconds=_REPAIR_SESSION_TTL_SECONDS)
    snapshot_hash = _hash_plan_snapshot(boot_repair_plan)

    _REPAIR_SESSION_STORE[session_id] = {
        "repair_session_id": session_id,
        "confirmation_token": token,
        "target_path": target,
        "selected_action_code": action_code,
        "originating_plan_hash": snapshot_hash,
        "originating_plan_snapshot": dict(boot_repair_plan),
        "inspect_result": dict(inspect_result or {}),
        "post_verify": dict(post_verify or {}),
        "created_at": created.isoformat(),
        "expires_at": expires.isoformat(),
        "used": False,
    }

    out["code"] = "BOOT_REPAIR_EXECUTE_STARTED"
    out["repair_session_id"] = session_id
    out["confirmation_token"] = token
    return out


def _action_regenerate_fstab(target_path: Path) -> tuple[bool, dict[str, Any]]:
    etc = target_path / "etc"
    if not etc.is_dir():
        return False, {"reason": "etc_missing"}
    fstab = etc / "fstab"
    lines = [
        "# setuphelfer minimal fstab",
        "UUID=UNKNOWN-ROOT / ext4 defaults 0 1",
    ]
    if (target_path / "boot").is_dir():
        lines.append("UUID=UNKNOWN-BOOT /boot ext4 defaults 0 2")
    fstab.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True, {"path": str(fstab), "entries": len(lines) - 1}


def _action_check_uuid_mapping(target_path: Path) -> tuple[bool, dict[str, Any]]:
    fstab = target_path / "etc" / "fstab"
    if not fstab.is_file():
        return False, {"reason": "fstab_missing"}
    content = fstab.read_text(encoding="utf-8", errors="ignore")
    refs = [line.strip() for line in content.splitlines() if line.strip().startswith(("UUID=", "PARTUUID="))]
    return True, {"uuid_reference_count": len(refs), "has_uuid_references": bool(refs)}


def _action_rebuild_initramfs(target_path: Path) -> tuple[bool, dict[str, Any]]:
    boot = target_path / "boot"
    has_kernel = any(boot.glob("vmlinuz*")) or any(boot.glob("Image*"))
    if not has_kernel:
        return False, {"reason": "kernel_missing"}

    if os.getenv("SETUPHELFER_ENABLE_REPAIR_CMDS") != "1":
        return False, {"reason": "repair_commands_disabled"}

    if shutil.which("chroot") and shutil.which("update-initramfs"):
        cmd = ["chroot", str(target_path), "update-initramfs", "-u"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc.returncode == 0, {"returncode": proc.returncode}

    return False, {"reason": "tool_missing"}


def _action_rpi_boot_files(target_path: Path) -> tuple[bool, dict[str, Any]]:
    boot = target_path / "boot"
    firmware = boot / "firmware"
    candidates = [(boot / "config.txt", boot / "cmdline.txt"), (firmware / "config.txt", firmware / "cmdline.txt")]
    for cfg, cmd in candidates:
        if cfg.is_file() and cmd.is_file():
            return True, {"layout": str(cfg.parent)}
    return False, {"reason": "rpi_layout_not_found"}


def _action_reinstall_grub(target_path: Path, boot_capability: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    if _bool_windows_or_dualboot(boot_capability):
        return False, {"reason": "windows_or_dualboot_detected"}
    if not (target_path / "boot").is_dir():
        return False, {"reason": "boot_dir_missing"}

    if os.getenv("SETUPHELFER_ENABLE_REPAIR_CMDS") != "1":
        return False, {"reason": "repair_commands_disabled"}

    if shutil.which("chroot") and shutil.which("grub-install"):
        cmd = ["chroot", str(target_path), "grub-install"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc.returncode == 0, {"returncode": proc.returncode}

    return False, {"reason": "tool_missing"}


def execute_boot_repair(request: dict[str, Any]) -> dict[str, Any]:
    session_id = str(request.get("repair_session_id") or "")
    token = str(request.get("confirmation_token") or "")
    action_code = str(request.get("action_code") or "")
    target_path = str(request.get("target_path") or "")

    out: dict[str, Any] = {
        "code": "BOOT_REPAIR_EXECUTE_FAILED",
        "repair_session_id": session_id or None,
        "action": {"code": action_code, "target_path": target_path},
        "result": {},
        "post_check": {},
        "warnings": [],
        "errors": [],
    }

    sess = _REPAIR_SESSION_STORE.get(session_id)
    if not sess:
        out["code"] = "BOOT_REPAIR_SESSION_NOT_FOUND"
        out["errors"].append("BOOT_REPAIR_SESSION_NOT_FOUND")
        return out

    if bool(sess.get("used")):
        out["code"] = "BOOT_REPAIR_SESSION_NOT_FOUND"
        out["errors"].append("BOOT_REPAIR_SESSION_NOT_FOUND")
        return out

    if token != str(sess.get("confirmation_token") or ""):
        out["code"] = "BOOT_REPAIR_TOKEN_INVALID"
        out["errors"].append("BOOT_REPAIR_TOKEN_INVALID")
        return out

    try:
        expires_at = datetime.fromisoformat(str(sess.get("expires_at") or ""))
    except Exception:
        expires_at = _now() - timedelta(seconds=1)
    if _now() >= expires_at:
        out["code"] = "BOOT_REPAIR_SESSION_EXPIRED"
        out["errors"].append("BOOT_REPAIR_SESSION_EXPIRED")
        return out

    if action_code != str(sess.get("selected_action_code") or ""):
        out["code"] = "BOOT_REPAIR_ACTION_MISMATCH"
        out["errors"].append("BOOT_REPAIR_ACTION_MISMATCH")
        return out

    if target_path != str(sess.get("target_path") or ""):
        out["code"] = "BOOT_REPAIR_ACTION_MISMATCH"
        out["errors"].append("BOOT_REPAIR_ACTION_MISMATCH")
        return out

    plan_snapshot = sess.get("originating_plan_snapshot") if isinstance(sess.get("originating_plan_snapshot"), dict) else {}
    if _hash_plan_snapshot(plan_snapshot) != str(sess.get("originating_plan_hash") or ""):
        out["code"] = "BOOT_REPAIR_PLAN_MISMATCH"
        out["errors"].append("BOOT_REPAIR_PLAN_MISMATCH")
        return out

    current_cap = check_boot_capability(target_path, inspect_result=sess.get("inspect_result") or {})
    out["post_check"]["pre_action"] = current_cap

    if _bool_windows_or_dualboot(current_cap):
        out["code"] = "BOOT_REPAIR_ACTION_NOT_ALLOWED"
        out["errors"].append("BOOT_REPAIR_ACTION_NOT_ALLOWED")
        return out

    if not _is_action_allowed(action_code, plan_snapshot, current_cap):
        out["code"] = "BOOT_REPAIR_ACTION_NOT_ALLOWED"
        out["errors"].append("BOOT_REPAIR_ACTION_NOT_ALLOWED")
        return out

    target = Path(target_path).expanduser()
    if not target.exists() or not os.access(target, os.R_OK | os.X_OK):
        out["code"] = "BOOT_REPAIR_PRECHECK_FAILED"
        out["errors"].append("BOOT_REPAIR_PRECHECK_FAILED")
        return out

    ok = False
    detail: dict[str, Any] = {}
    if action_code == "REPAIR_REGENERATE_FSTAB":
        ok, detail = _action_regenerate_fstab(target)
    elif action_code == "REPAIR_CHECK_UUID_MAPPING":
        ok, detail = _action_check_uuid_mapping(target)
    elif action_code == "REPAIR_REBUILD_INITRAMFS":
        ok, detail = _action_rebuild_initramfs(target)
    elif action_code == "REPAIR_RPI_BOOT_FILES":
        ok, detail = _action_rpi_boot_files(target)
    elif action_code == "REPAIR_REINSTALL_GRUB":
        ok, detail = _action_reinstall_grub(target, current_cap)
    else:
        out["code"] = "BOOT_REPAIR_ACTION_NOT_ALLOWED"
        out["errors"].append("BOOT_REPAIR_ACTION_NOT_ALLOWED")
        return out

    out["result"] = {"ok": bool(ok), "detail": detail}
    if not ok:
        out["code"] = "BOOT_REPAIR_EXECUTE_FAILED"
        out["errors"].append("BOOT_REPAIR_PRECHECK_FAILED")
        return out

    # Token is single-use
    sess["used"] = True

    post_check = check_boot_capability(target_path, inspect_result=sess.get("inspect_result") or {})
    out["post_check"]["after_action"] = post_check
    out["code"] = "BOOT_REPAIR_EXECUTE_COMPLETED"
    return out
