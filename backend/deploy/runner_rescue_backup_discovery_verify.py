from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from deploy.runner_rescue_io import (
    REPO_ROOT,
    guard_handoff_overwrite,
    load_json_handoff,
    resolve_handoff_path,
    resolve_under_build_rescue,
    write_json_handoff,
)

_PLAN_REL = "docs/evidence/runtime-results/handoff/rescue_backup_discovery_plan.json"
_RESULT_REL = "docs/evidence/runtime-results/handoff/rescue_backup_verify_result.json"
_MAX_BYTES = 1_500_000
_MAX_FILE_BYTES = 512 * 1024


def _emit_plan(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_backup_discovery_plan_status": status,
        "rescue_backup_discovery_plan_file_path": _PLAN_REL,
        "rescue_backup_discovery_plan": body,
        "rescue_backup_discovery_plan_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def _emit_verify(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_backup_verify_result_status": status,
        "rescue_backup_verify_result_file_path": _RESULT_REL,
        "rescue_backup_verify_result": body,
        "rescue_backup_verify_result_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_rescue_backup_discovery_plan(
    *,
    explicit_overwrite: bool = False,
    backup_scan_root: str | None = None,
) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_PLAN_REL, "RESCUE_BKDPLAN")
    if oerr or out_path is None:
        return _emit_plan("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_BKDPLAN_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_BKDPLAN")
    if gerr:
        return _emit_plan("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    root = (backup_scan_root or "build/rescue/backup-verify-lab").strip().replace("\\", "/")
    _, rerr = resolve_under_build_rescue(root.lstrip("/"), "RESCUE_BKDROOT")
    if rerr:
        return _emit_plan("blocked", {}, wrote=False, warnings=[], errors=[rerr])

    body: dict[str, Any] = {
        "rescue_backup_discovery_plan_schema_version": 1,
        "strict_mode": "rescue_backup_readonly_discovery",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "backup_scan_root": root,
        "manifest_names": ["backup_manifest.json", "setuphelfer_backup_manifest.json"],
        "writes_forbidden": True,
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_plan("blocked", body, wrote=False, warnings=[], errors=[werr])
    return _emit_plan("ok", body, wrote=True, warnings=[], errors=[])


def _scan_root_from_plan(plan: dict[str, Any] | None) -> tuple[Path | None, str | None]:
    if plan is None or not isinstance(plan, dict):
        return None, "RESCUE_BKDPLAN_MISSING"
    root = str(plan.get("backup_scan_root") or "build/rescue/backup-verify-lab").strip().replace("\\", "/")
    rp, err = resolve_under_build_rescue(root.lstrip("/"), "RESCUE_BKDROOT")
    return rp, err


def execute_rescue_backup_discovery(
    *,
    explicit_overwrite: bool = False,
    explicit_execute_backup_discovery: bool = False,
) -> dict[str, Any]:
    if not explicit_execute_backup_discovery:
        return _emit_verify(
            "blocked",
            {"reason": "EXECUTE_REQUIRES_EXPLICIT_BACKUP_DISCOVERY"},
            wrote=False,
            warnings=[],
            errors=["EXECUTE_REQUIRES_EXPLICIT_BACKUP_DISCOVERY"],
        )

    out_path, oerr = resolve_handoff_path(_RESULT_REL, "RESCUE_BKDVRES")
    if oerr or out_path is None:
        return _emit_verify("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_BKDVRES_INVALID"])
    g0 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_BKDVRES")
    if g0:
        return _emit_verify("blocked", {}, wrote=False, warnings=[], errors=[g0])

    plan, perr = load_json_handoff(_PLAN_REL, "RESCUE_BKDPLAN")
    if plan is not None and not isinstance(plan, dict):
        plan, perr = None, "RESCUE_BKDPLAN_JSON_INVALID"
    scan_root, rerr = _scan_root_from_plan(plan if isinstance(plan, dict) else None)
    warnings: list[str] = []
    errors: list[str] = []
    if perr:
        errors.append(str(perr))
    if rerr or scan_root is None:
        errors.append(str(rerr or "RESCUE_BKDROOT_INVALID"))

    manifest_path: Path | None = None
    manifest_obj: dict[str, Any] | None = None
    if scan_root and scan_root.is_dir():
        for name in ("backup_manifest.json", "setuphelfer_backup_manifest.json"):
            cand = scan_root / name
            if cand.is_file():
                manifest_path = cand
                try:
                    manifest_obj = json.loads(cand.read_text(encoding="utf-8"))
                except Exception:
                    manifest_obj = None
                    errors.append("RESCUE_BKD_MANIFEST_JSON_INVALID")
                break
        if manifest_path is None:
            warnings.append("RESCUE_BKD_NO_MANIFEST")
    else:
        if scan_root:
            warnings.append("RESCUE_BKD_SCAN_DIR_MISSING")

    merged: dict[str, Any] = {
        "rescue_backup_verify_result_schema_version": 1,
        "strict_mode": "rescue_backup_readonly_discovery_verify",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "discovery": {
            "backup_scan_root": str(scan_root.relative_to(REPO_ROOT)).replace("\\", "/") if scan_root else None,
            "manifest_path": str(manifest_path.relative_to(REPO_ROOT)).replace("\\", "/") if manifest_path else None,
            "manifest_present": manifest_path is not None and isinstance(manifest_obj, dict),
            "backup_version": (manifest_obj or {}).get("backup_version") if isinstance(manifest_obj, dict) else None,
            "legacy_backup_hint": str((manifest_obj or {}).get("backup_version") or "").startswith("0."),
        },
        "verify": {"pending": True},
    }
    werr = write_json_handoff(out_path, merged, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_verify("blocked", merged, wrote=False, warnings=warnings, errors=[werr])
    return build_rescue_backup_verify_result(explicit_overwrite=True, warnings=warnings, errors=errors)


def execute_rescue_backup_verify(
    *,
    explicit_overwrite: bool = False,
    explicit_execute_backup_verify: bool = False,
) -> dict[str, Any]:
    if not explicit_execute_backup_verify:
        return _emit_verify(
            "blocked",
            {"reason": "EXECUTE_REQUIRES_EXPLICIT_BACKUP_VERIFY"},
            wrote=False,
            warnings=[],
            errors=["EXECUTE_REQUIRES_EXPLICIT_BACKUP_VERIFY"],
        )

    out_path, oerr = resolve_handoff_path(_RESULT_REL, "RESCUE_BKDVRES")
    if oerr or out_path is None:
        return _emit_verify("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_BKDVRES_INVALID"])
    g0 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_BKDVRES")
    if g0:
        return _emit_verify("blocked", {}, wrote=False, warnings=[], errors=[g0])

    if not out_path.is_file():
        return _emit_verify("blocked", {}, wrote=False, warnings=[], errors=["RESCUE_BKDVRES_RUN_DISCOVERY_FIRST"])

    data = json.loads(out_path.read_text(encoding="utf-8"))
    disc = data.get("discovery") if isinstance(data.get("discovery"), dict) else {}
    manifest_rel = disc.get("manifest_path")
    scan_root_rel = disc.get("backup_scan_root")

    warnings: list[str] = []
    errors: list[str] = []
    sha_ok = True
    checked: list[dict[str, Any]] = []

    if not manifest_rel:
        errors.append("RESCUE_BKV_NO_MANIFEST")
        sha_ok = False
    else:
        mp = (REPO_ROOT / manifest_rel).resolve()
        try:
            mp.relative_to(REPO_ROOT.resolve(strict=False))
        except ValueError:
            errors.append("RESCUE_BKV_MANIFEST_OUTSIDE_REPO")
            sha_ok = False
        else:
            if mp.is_file():
                try:
                    man = json.loads(mp.read_text(encoding="utf-8"))
                except Exception:
                    man = {}
                    errors.append("RESCUE_BKV_MANIFEST_READ_FAIL")
                    sha_ok = False
                files = man.get("files") if isinstance(man.get("files"), list) else []
                root = (REPO_ROOT / str(scan_root_rel or "build/rescue/backup-verify-lab")).resolve()
                for ent in files[:200]:
                    if not isinstance(ent, dict):
                        continue
                    rel = str(ent.get("path") or "").strip().replace("\\", "/").lstrip("/")
                    expect = str(ent.get("sha256") or "").strip().lower()
                    if not rel or not expect:
                        warnings.append("RESCUE_BKV_ENTRY_INCOMPLETE")
                        continue
                    fp = (root / rel).resolve()
                    try:
                        fp.relative_to(root)
                    except ValueError:
                        errors.append(f"RESCUE_BKV_PATH_ESCAPE:{rel}")
                        sha_ok = False
                        continue
                    if not fp.is_file():
                        errors.append(f"RESCUE_BKV_MISSING_FILE:{rel}")
                        sha_ok = False
                        checked.append({"path": rel, "ok": False, "reason": "missing"})
                        continue
                    sz = fp.stat().st_size
                    if sz > _MAX_FILE_BYTES:
                        errors.append(f"RESCUE_BKV_FILE_TOO_LARGE:{rel}")
                        sha_ok = False
                        checked.append({"path": rel, "ok": False, "reason": "too_large"})
                        continue
                    h = hashlib.sha256()
                    h.update(fp.read_bytes())
                    got = h.hexdigest().lower()
                    ok = got == expect
                    if not ok:
                        errors.append(f"RESCUE_BKV_SHA256_MISMATCH:{rel}")
                        sha_ok = False
                    checked.append({"path": rel, "ok": ok, "sha256_expected_prefix": expect[:12]})

    merged = dict(data)
    merged["verify"] = {
        "pending": False,
        "sha256_chain_ok": sha_ok and not errors,
        "files_checked": checked,
        "damaged_backup_detected": not sha_ok or bool(errors),
    }
    merged["generated_at_verify"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    werr = write_json_handoff(out_path, merged, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_verify("blocked", merged, wrote=False, warnings=warnings, errors=[werr])
    return build_rescue_backup_verify_result(explicit_overwrite=True, warnings=warnings, errors=errors)


def build_rescue_backup_verify_result(
    *,
    explicit_overwrite: bool = False,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_RESULT_REL, "RESCUE_BKDVRES")
    if oerr or out_path is None:
        return _emit_verify("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_BKDVRES_INVALID"])
    if not out_path.is_file():
        return _emit_verify("blocked", {}, wrote=False, warnings=[], errors=["RESCUE_BKDVRES_MISSING"])
    g1 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_BKDVRES")
    if g1:
        return _emit_verify("blocked", {}, wrote=False, warnings=[], errors=[g1])

    data = json.loads(out_path.read_text(encoding="utf-8"))
    warn = list(warnings or [])
    errs = list(errors or [])
    disc = data.get("discovery") if isinstance(data.get("discovery"), dict) else {}
    ver = data.get("verify") if isinstance(data.get("verify"), dict) else {}

    pending = bool(ver.get("pending", False))
    if pending:
        st = "review_required"
        warn.append("RESCUE_BKV_VERIFY_PENDING")
    elif errs:
        st = "blocked"
    elif ver.get("damaged_backup_detected"):
        st = "blocked"
    elif not disc.get("manifest_present"):
        st = "review_required"
        warn.append("RESCUE_BKV_MANIFEST_MISSING")
    elif not ver.get("sha256_chain_ok", False):
        st = "blocked"
    else:
        st = "ok"

    restore_preview_possible = st == "ok" and bool(ver.get("sha256_chain_ok"))

    merged = dict(data)
    merged["evaluation"] = {
        "rescue_backup_verify_eval_status": st,
        "writes_performed": False,
        "restore_preview_possible": restore_preview_possible,
    }
    werr = write_json_handoff(out_path, merged, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_verify("blocked", merged, wrote=False, warnings=warn, errors=[werr])
    return _emit_verify(st, merged, wrote=True, warnings=warn, errors=errs if st == "blocked" else [])
