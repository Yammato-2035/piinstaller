from __future__ import annotations

import importlib.util
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from core.rescue_allowlist import assert_backup_readable_path, assert_restore_live_target_directory
from models.diagnosis import RestoreDryRunRequest
from modules.backup_verify import verify_basic
from modules.rescue_restore_dryrun import run_restore_dryrun_pipeline
from modules.restore_engine import restore_files
from rescue.post_restore_validation import validate_restored_target
from boot.capability import check_boot_capability
from boot.repair_plan import generate_boot_repair_plan
from rescue.report import build_rescue_report

_base = Path(__file__).resolve().parent

_collector_spec = importlib.util.spec_from_file_location(
    "setuphelfer_inspect_collector_rescue_orchestrator",
    _base.parent / "inspect" / "collector.py",
)
if not (_collector_spec and _collector_spec.loader):
    raise ImportError("cannot load inspect collector")
_collector_mod = importlib.util.module_from_spec(_collector_spec)
_collector_spec.loader.exec_module(_collector_mod)
collect_inspect_result = _collector_mod.collect_inspect_result

_wg_spec = importlib.util.spec_from_file_location("setuphelfer_write_guard_rescue_orchestrator", _base.parent / "safety" / "write_guard.py")
if not (_wg_spec and _wg_spec.loader):
    raise ImportError("cannot load write_guard")
_wg_mod = importlib.util.module_from_spec(_wg_spec)
_wg_spec.loader.exec_module(_wg_mod)
evaluate_write_target = _wg_mod.evaluate_write_target

_pf_spec = importlib.util.spec_from_file_location("setuphelfer_preflight_backup_rescue_orchestrator", _base.parent / "preflight" / "backup.py")
if not (_pf_spec and _pf_spec.loader):
    raise ImportError("cannot load preflight backup module")
_pf_mod = importlib.util.module_from_spec(_pf_spec)
_pf_spec.loader.exec_module(_pf_mod)
_PREFLIGHT_PLAN_STORE = _pf_mod._PLAN_STORE

_BLOCKED_SAFETY = {
    "SAFETY_SYSTEM_DISK",
    "SAFETY_LIVE_SYSTEM",
    "SAFETY_WINDOWS_DETECTED",
    "SAFETY_DUALBOOT",
    "SAFETY_UNKNOWN_DEVICE",
}

_WARNING_TARGET_REASONS = {"SAFETY_EMPTY_DISK"}
_PREVIEW_TTL_SECONDS = 900

# Preview-Session Store (Phase 2: in-memory)
_PREVIEW_SESSION_STORE: dict[str, dict[str, Any]] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _initial_preview_response(preview_id: str) -> dict[str, Any]:
    return {
        "code": "RESCUE_UNKNOWN_ERROR",
        "preview_id": preview_id,
        "confirmation_token": None,
        "target": {},
        "backup": {},
        "safety": {},
        "verify": {},
        "preview": {},
        "preflight": {},
        "warnings": [],
        "errors": [],
    }


def _initial_execute_response(preview_id: str | None) -> dict[str, Any]:
    return {
        "code": "RESCUE_EXECUTE_FAILED",
        "preview_id": preview_id,
        "target": {},
        "backup": {},
        "safety": {},
        "verify": {},
        "restore": {},
        "post_verify": {},
        "boot_capability": {},
        "boot_repair_plan": {},
        "rescue_report": {},
        "warnings": [],
        "errors": [],
    }


def _safety_fingerprint(target_device: str | None, safety_result: dict[str, Any]) -> str:
    return "|".join(
        [
            str(target_device or ""),
            str(safety_result.get("allowed")),
            str(safety_result.get("reason_code") or ""),
            str(safety_result.get("risk_level") or ""),
        ]
    )


def _preview_requires_preflight(safety_reason: str) -> bool:
    return safety_reason in _WARNING_TARGET_REASONS


def preview_rescue_restore(request: dict[str, Any]) -> dict[str, Any]:
    preview_id = secrets.token_hex(8)
    confirmation_token = secrets.token_urlsafe(24)
    out = _initial_preview_response(preview_id)

    try:
        inspect_result = collect_inspect_result().model_dump()

        backup_path_raw = request.get("backup_path")
        backup_path = Path(str(backup_path_raw or "")).expanduser()
        target_device = str(request.get("target_device") or "").strip() or None
        target_path = str(request.get("target_path") or "").strip() or None
        preflight_plan_id = str(request.get("preflight_plan_id") or "").strip() or None
        encryption_key_hex = str(request.get("encryption_key_hex") or "").strip()

        out["target"] = {
            "target_device": target_device,
            "target_path": target_path,
        }

        safety_result: dict[str, Any] = {
            "reason_code": "SAFETY_UNKNOWN_DEVICE",
            "allowed": False,
            "risk_level": "high",
        }
        if target_device:
            safety_result = evaluate_write_target(target_device, inspect_result)
        out["safety"] = {
            "allowed": bool(safety_result.get("allowed")),
            "reason_code": safety_result.get("reason_code"),
            "risk_level": safety_result.get("risk_level"),
        }
        safety_reason = str(safety_result.get("reason_code") or "")

        if safety_reason in _BLOCKED_SAFETY:
            out["code"] = "RESCUE_TARGET_BLOCKED"
            out["errors"].append("RESCUE_TARGET_BLOCKED")
            return out

        preflight_known = bool(preflight_plan_id and preflight_plan_id in _PREFLIGHT_PLAN_STORE)
        out["preflight"] = {
            "preflight_plan_id": preflight_plan_id,
            "known": preflight_known,
        }
        if not preflight_known:
            out["warnings"].append("RESCUE_PREFLIGHT_RECOMMENDED")

        try:
            backup_checked = assert_backup_readable_path(str(backup_path))
            backup_exists = True
        except Exception:
            backup_checked = backup_path
            backup_exists = backup_path.is_file()

        if not backup_exists:
            out["backup"] = {
                "path": str(backup_path),
                "exists": False,
            }
            out["code"] = "RESCUE_BACKUP_NOT_FOUND"
            out["errors"].append("RESCUE_BACKUP_NOT_FOUND")
            return out

        if backup_checked.suffix.lower() in {".enc", ".gpg"} and not encryption_key_hex:
            out["backup"] = {
                "path": str(backup_checked),
                "exists": True,
                "encryption": "key_required",
            }
            out["code"] = "RESCUE_BACKUP_KEY_REQUIRED"
            out["errors"].append("RESCUE_BACKUP_KEY_REQUIRED")
            return out

        out["backup"] = {
            "path": str(backup_checked),
            "exists": True,
            "encryption": "provided" if encryption_key_hex else "not_required",
        }

        ok_verify, key_verify, _detail_verify = verify_basic(backup_checked)
        out["verify"] = {
            "ok": bool(ok_verify),
            "key": key_verify,
        }
        if not ok_verify:
            out["code"] = "RESCUE_BACKUP_VERIFY_FAILED"
            out["errors"].append("RESCUE_BACKUP_VERIFY_FAILED")
            return out

        dryrun_req = RestoreDryRunRequest(
            backup_file=str(backup_checked),
            target_device=target_device,
            mode="dryrun",
            encryption_key_available=bool(encryption_key_hex),
        )
        dryrun_resp = run_restore_dryrun_pipeline(dryrun_req, auth_session_id=None)
        dryrun_data = dryrun_resp.model_dump()
        preview_result = {
            "status": dryrun_data.get("status"),
            "restore_risk_level": dryrun_data.get("restore_risk_level"),
            "restore_decision": dryrun_data.get("restore_decision"),
            "allow_restore": dryrun_data.get("allow_restore"),
            "recommended_actions": dryrun_data.get("recommended_actions", []),
            "codes": [
                f.get("code")
                for f in dryrun_data.get("findings", [])
                if isinstance(f, dict) and isinstance(f.get("code"), str) and f.get("code")
            ],
        }
        out["preview"] = preview_result

        created_at = datetime.now(timezone.utc)
        expires_at = created_at + timedelta(seconds=_PREVIEW_TTL_SECONDS)
        _PREVIEW_SESSION_STORE[preview_id] = {
            "preview_id": preview_id,
            "confirmation_token": confirmation_token,
            "backup_path": str(backup_checked),
            "target_device": target_device,
            "target_path": target_path,
            "preflight_plan_id": preflight_plan_id,
            "safety_fingerprint": _safety_fingerprint(target_device, safety_result),
            "safety_reason": safety_reason,
            "verify_result": {"ok": bool(ok_verify), "key": key_verify},
            "preview_result": preview_result,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat(),
        }

        out["code"] = "RESCUE_PREVIEW_CREATED"
        out["confirmation_token"] = confirmation_token
        return out
    except Exception:
        out["code"] = "RESCUE_PREVIEW_FAILED"
        out["errors"].append("RESCUE_UNKNOWN_ERROR")
        return out


def execute_rescue_restore(request: dict[str, Any]) -> dict[str, Any]:
    preview_id = str(request.get("preview_id") or "").strip() or None
    out = _initial_execute_response(preview_id)

    if not preview_id or preview_id not in _PREVIEW_SESSION_STORE:
        out["code"] = "RESCUE_PREVIEW_SESSION_NOT_FOUND"
        out["errors"].append("RESCUE_PREVIEW_SESSION_NOT_FOUND")
        return out

    sess = _PREVIEW_SESSION_STORE.get(preview_id) or {}

    token = str(request.get("confirmation_token") or "")
    if token != str(sess.get("confirmation_token") or ""):
        out["code"] = "RESCUE_PREVIEW_TOKEN_INVALID"
        out["errors"].append("RESCUE_PREVIEW_TOKEN_INVALID")
        return out

    expires_raw = str(sess.get("expires_at") or "")
    try:
        expires_at = datetime.fromisoformat(expires_raw)
    except Exception:
        expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    if datetime.now(timezone.utc) >= expires_at:
        out["code"] = "RESCUE_PREVIEW_SESSION_EXPIRED"
        out["errors"].append("RESCUE_PREVIEW_SESSION_EXPIRED")
        return out

    req_backup = str(request.get("backup_path") or "")
    req_target_device = str(request.get("target_device") or "") or None
    req_target_path = str(request.get("target_path") or "") or None
    if (
        req_backup != str(sess.get("backup_path") or "")
        or req_target_device != str(sess.get("target_device") or "")
        or req_target_path != str(sess.get("target_path") or "")
    ):
        out["code"] = "RESCUE_PREVIEW_MISMATCH"
        out["errors"].append("RESCUE_PREVIEW_MISMATCH")
        return out

    out["target"] = {
        "target_device": req_target_device,
        "target_path": req_target_path,
    }
    out["backup"] = {"path": req_backup}

    try:
        inspect_result = collect_inspect_result().model_dump()
        safety_result = evaluate_write_target(req_target_device, inspect_result) if req_target_device else {
            "allowed": False,
            "reason_code": "SAFETY_UNKNOWN_DEVICE",
            "risk_level": "high",
        }
        safety_reason = str(safety_result.get("reason_code") or "")
        out["safety"] = {
            "allowed": bool(safety_result.get("allowed")),
            "reason_code": safety_reason,
            "risk_level": safety_result.get("risk_level"),
        }

        if safety_reason in _BLOCKED_SAFETY:
            out["code"] = "RESCUE_TARGET_BLOCKED"
            out["errors"].append("RESCUE_TARGET_BLOCKED")
            return out

        if _safety_fingerprint(req_target_device, safety_result) != str(sess.get("safety_fingerprint") or ""):
            out["code"] = "RESCUE_SAFETY_CHANGED"
            out["errors"].append("RESCUE_SAFETY_CHANGED")
            return out

        preflight_plan_id = str(sess.get("preflight_plan_id") or "")
        preflight_known = bool(preflight_plan_id and preflight_plan_id in _PREFLIGHT_PLAN_STORE)
        if not preflight_known:
            if _preview_requires_preflight(safety_reason):
                out["code"] = "RESCUE_PREFLIGHT_REQUIRED"
                out["errors"].append("RESCUE_PREFLIGHT_REQUIRED")
                return out
            out["warnings"].append("RESCUE_PREFLIGHT_RECOMMENDED")

        try:
            backup_checked = assert_backup_readable_path(req_backup)
        except Exception:
            out["code"] = "RESCUE_BACKUP_NOT_FOUND"
            out["errors"].append("RESCUE_BACKUP_NOT_FOUND")
            return out

        ok_verify, key_verify, _detail = verify_basic(backup_checked)
        out["verify"] = {"ok": bool(ok_verify), "key": key_verify}
        if not ok_verify:
            out["code"] = "RESCUE_BACKUP_VERIFY_FAILED"
            out["errors"].append("RESCUE_BACKUP_VERIFY_FAILED")
            return out

        # Start execute (nur via gültiger Preview-Session)
        out["restore"] = {"state": "RESCUE_EXECUTE_STARTED", "engine": "modules.restore_engine.restore_files"}

        if not req_target_path:
            out["code"] = "RESCUE_PREVIEW_MISMATCH"
            out["errors"].append("RESCUE_PREVIEW_MISMATCH")
            return out

        try:
            restore_target = assert_restore_live_target_directory(req_target_path)
        except Exception:
            out["code"] = "RESCUE_TARGET_BLOCKED"
            out["errors"].append("RESCUE_TARGET_BLOCKED")
            return out

        ok_restore, key_restore, detail_restore = restore_files(
            backup_checked,
            restore_target,
            allowed_target_prefixes=(restore_target.resolve(),),
            dry_run=False,
        )
        out["restore"] = {
            "state": "RESCUE_EXECUTE_STARTED",
            "engine": "modules.restore_engine.restore_files",
            "ok": bool(ok_restore),
            "key": key_restore,
        }
        if not ok_restore:
            out["code"] = "RESCUE_RESTORE_ENGINE_FAILED"
            out["errors"].append("RESCUE_RESTORE_ENGINE_FAILED")
            if detail_restore:
                out["restore"]["detail_type"] = type(detail_restore).__name__
            return out

        # Post-Restore-Validation (rein lesend)
        post_validation = validate_restored_target(str(restore_target))
        out["post_verify"] = post_validation
        if post_validation.get("status") == "failed":
            out["code"] = "RESCUE_POST_VERIFY_FAILED"
            out["errors"].append("RESCUE_POST_VERIFY_FAILED")
            return out
        if post_validation.get("status") == "warning":
            for w in post_validation.get("warnings") or []:
                if isinstance(w, str) and w not in out["warnings"]:
                    out["warnings"].append(w)

        # Optionaler Boot Capability Check (rein lesend, keine Reparatur)
        if req_target_path:
            try:
                boot_capability = check_boot_capability(req_target_path, inspect_result=inspect_result)
            except Exception:
                boot_capability = {
                    "status": "boot_unknown",
                    "checks": [],
                    "boot_type_hints": [],
                    "risks": [],
                    "recommendations": ["BOOT_MANUAL_REVIEW_RECOMMENDED"],
                    "warnings": [],
                    "errors": [],
                }
            out["boot_capability"] = boot_capability

            # Optionaler Boot-Repair-Plan (nur theoretisch, keine Ausführung)
            try:
                out["boot_repair_plan"] = generate_boot_repair_plan(
                    target_path=req_target_path,
                    inspect_result=inspect_result,
                    post_verify=post_validation,
                    boot_capability=boot_capability,
                )
            except Exception:
                out["boot_repair_plan"] = {
                    "plan_status": "not_applicable",
                    "issues": [],
                    "proposed_actions": [
                        {
                            "code": "REPAIR_MANUAL_REVIEW_REQUIRED",
                            "applicable": True,
                            "risk_level": "high",
                            "requires_confirmation": True,
                            "auto_allowed": False,
                        }
                    ],
                    "risks": ["BOOT_REPAIR_RISK_UNKNOWN_LAYOUT"],
                    "requires_manual_review": True,
                }

            # Optionaler Rescue-Report (rein aggregierend)
            try:
                out["rescue_report"] = build_rescue_report(
                    inspect_result=inspect_result,
                    safety_summary={"targets": [{"write_allowed": bool(out.get("safety", {}).get("allowed"))}]},
                    preflight_result={"code": "PREFLIGHT_BACKUP_EXECUTED" if preflight_known else "PREFLIGHT_BACKUP_RECOMMENDED"},
                    preview_result={"code": "RESCUE_PREVIEW_CREATED", "warnings": out.get("warnings", []), "errors": []},
                    execute_result={"code": "RESCUE_EXECUTE_COMPLETED", "warnings": out.get("warnings", []), "errors": []},
                    post_restore=post_validation,
                    boot_capability=out.get("boot_capability", {}),
                    boot_repair_plan=out.get("boot_repair_plan", {}),
                )
            except Exception:
                out["rescue_report"] = {}

        out["code"] = "RESCUE_EXECUTE_COMPLETED"
        return out
    except Exception:
        out["code"] = "RESCUE_EXECUTE_FAILED"
        out["errors"].append("RESCUE_UNKNOWN_ERROR")
        return out
