"""
Phase 3C–3.N: Kontrollierter echter Restore — gestuft, mit Session-Bindung, Hard-Stops und Audit.

Voraussetzung: gültiger Dry-Run-Grant (Token). Keine Geheimnisse im Log.
"""

from __future__ import annotations

import binascii
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from core.rescue_hardstop import RestoreHardStopContext, evaluate_restore_hardstops
from core.rescue_allowlist import (
    RESCUE_LIVE_RESTORE_PREFIXES,
    assert_backup_readable_path,
    assert_restore_live_target_directory,
    path_under_prefixes,
)
from models.diagnosis import RescueRestoreRequest, RescueRestoreResponse, RestoreResultCode

from modules.backup_crypto import MAGIC, decrypt_file_to_path
from modules.backup_verify import verify_basic
from modules.inspect_boot import analyze_boot_status
from modules.rescue_boot_repair import run_boot_repair_pipeline
from modules.rescue_boot_restore_check import simulate_boot_preconditions
from modules.rescue_restore_gate import (
    consume_dry_run_grant,
    is_running_system_disk,
    validate_restore_preconditions,
    validate_target_confirmation_phrase,
)
from modules.restore_engine import restore_files

Runner = Callable[..., Any] | None

RESTORE_LOG_PATH = Path("/tmp/setuphelfer-rescue-restore.log")
RESTORE_REPORT_JSON = Path("/tmp/setuphelfer-rescue-restore-report.json")
RESTORE_REPORT_MD = Path("/tmp/setuphelfer-rescue-restore-report.md")

STAGE_PRECONDITION = "PRECONDITION_CHECK"
STAGE_TARGET_REVAL = "TARGET_REVALIDATION"
STAGE_BACKUP_REVAL = "BACKUP_REVALIDATION"
STAGE_HARDSTOP = "HARDSTOP_EVALUATION"
STAGE_TARGET_PREP = "TARGET_PREPARATION"
STAGE_DATA = "DATA_RESTORE"
STAGE_BOOT = "BOOT_PREPARATION_OR_REPAIR"
STAGE_POST = "POST_RESTORE_VALIDATION"
STAGE_FINAL = "FINAL_RESULT"


def _log(line: str, *, sensitive: bool = False) -> None:
    if sensitive:
        return
    try:
        ts = datetime.now(timezone.utc).isoformat()
        with RESTORE_LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(f"{ts} {line}\n")
    except OSError:
        pass


def _findmnt_source_for_path(path: Path, *, runner: Runner = None) -> str | None:
    import subprocess

    run = runner or subprocess.run
    r = run(
        ["findmnt", "-n", "-o", "SOURCE", "-T", str(path)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if r.returncode != 0:
        return None
    line = (r.stdout or "").strip().splitlines()
    return line[0].strip() if line else None


def _parent_disk(dev: str, *, runner: Runner = None) -> str | None:
    import subprocess

    run = runner or subprocess.run
    r = run(["lsblk", "-n", "-o", "PKNAME", "-p", dev], capture_output=True, text=True, timeout=30, check=False)
    pk = (r.stdout or "").strip()
    if r.returncode == 0 and pk.startswith("/dev/"):
        return pk
    return dev if dev.startswith("/dev/") else None


def validate_mount_matches_target_device(
    restore_dir: Path,
    target_device: str | None,
    *,
    runner: Runner = None,
) -> tuple[bool, str]:
    if not target_device or not str(target_device).strip():
        return True, "rescue.restore.mount_check_skipped"
    src = _findmnt_source_for_path(restore_dir, runner=runner)
    if not src or not src.startswith("/dev/"):
        return False, "rescue.restore.RESTORE_BLOCKED_INVALID_STATE"
    t_parent = _parent_disk(str(target_device).strip(), runner=runner)
    s_parent = _parent_disk(src, runner=runner)
    if t_parent and s_parent and Path(t_parent).resolve() == Path(s_parent).resolve():
        return True, "rescue.restore.mount_matches_target"
    return False, "rescue.restore.RESTORE_BLOCKED_INVALID_STATE"


def _target_dir_empty(restore_dir: Path) -> bool:
    try:
        entries = list(restore_dir.iterdir())
    except OSError:
        return False
    return len(entries) == 0


def post_restore_validate(restore_root: Path, *, runner: Runner = None) -> tuple[RestoreResultCode, list[str]]:
    """Erweiterte Post-Checks inkl. Boot-Artefakte."""
    warnings: list[str] = []
    critical = ["etc"]
    for d in critical:
        if not (restore_root / d).is_dir():
            return "RESTORE_PARTIAL", [f"rescue.validation.missing_{d}"]
    for d in ("usr", "home"):
        if not (restore_root / d).is_dir():
            warnings.append(f"rescue.validation.missing_{d}")
    boot_st = analyze_boot_status(restore_root, runner=runner)
    for c in boot_st.get("codes") or []:
        if c in ("rescue.boot.boot_dir_missing", "rescue.boot.fstab_missing", "rescue.boot.fstab_unreadable"):
            return "RESTORE_PARTIAL", warnings + [c]
        if c in ("rescue.boot.kernel_missing", "rescue.boot.initrd_missing", "rescue.boot.fstab_parse_error"):
            warnings.append(c)
    if warnings:
        return "RESTORE_SUCCESS_WITH_WARNINGS", warnings
    return "RESTORE_SUCCESS", []


def _prepare_archive_path(
    backup_path: Path,
    encryption_key_hex: str | None,
    work_parent: Path,
    *,
    runner: Runner = None,
) -> tuple[Path | None, str | None]:
    """Liefert Pfad zum lesbaren tar.gz oder None + Fehlercode."""
    if not encryption_key_hex or not str(encryption_key_hex).strip():
        return backup_path, None
    hx = str(encryption_key_hex).strip()
    try:
        key = binascii.unhexlify(hx)
    except binascii.Error:
        return None, "rescue.restore.RESTORE_KEY_INVALID"
    if len(key) != 32:
        return None, "rescue.restore.RESTORE_KEY_INVALID"
    try:
        head = backup_path.read_bytes()[: len(MAGIC)]
    except OSError:
        return None, "rescue.restore.RESTORE_BACKUP_CORRUPT"
    if head != MAGIC:
        return None, "rescue.restore.RESTORE_BACKUP_UNSUPPORTED"
    out = work_parent / f".decrypted-{backup_path.name}.tar.gz"
    ok, err = decrypt_file_to_path(backup_path, out, key)
    if not ok:
        return None, "rescue.restore.RESTORE_KEY_INVALID"
    return out, None


def _blocked_response(
    *,
    codes: list[str],
    result: RestoreResultCode = "RESTORE_BLOCKED",
    log_line: str,
) -> RescueRestoreResponse:
    _log(log_line)
    return RescueRestoreResponse(
        status="error",
        result=result,
        warnings=[],
        log_path=str(RESTORE_LOG_PATH),
        bootable=False,
        codes=codes,
    )


def _record_stage(stages: list[dict[str, Any]], name: str, ok: bool, codes: list[str]) -> None:
    stages.append(
        {
            "stage": name,
            "ok": ok,
            "codes": list(codes),
            "at": datetime.now(timezone.utc).isoformat(),
        }
    )


def _write_reports(
    *,
    result: RestoreResultCode,
    warnings: list[str],
    bootable: bool,
    codes: list[str],
    stages: list[dict[str, Any]],
    session_id: str,
    dry_run_token: str,
    grant_snapshot: dict[str, Any],
    acknowledgements: dict[str, bool],
    boot_repair: dict[str, Any] | None,
) -> None:
    payload = {
        "result": result,
        "warnings": warnings,
        "bootable": bootable,
        "codes": codes,
        "stages": stages,
        "session_id": session_id,
        "dry_run_token": dry_run_token,
        "grant_snapshot_redacted": {k: grant_snapshot.get(k) for k in ("backup_file", "target_device", "session_id", "restore_risk_level") if k in grant_snapshot},
        "acknowledgements": acknowledgements,
        "boot_repair": boot_repair or {},
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        RESTORE_REPORT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass
    try:
        lines = [
            "# Setuphelfer Rescue Restore Report",
            "",
            f"finished_at: {payload['finished_at']}",
            f"result: {result}",
            f"session_id: {session_id}",
            "",
            "## Stages",
        ]
        for s in stages:
            lines.append(f"- {s.get('stage')}: ok={s.get('ok')} codes={s.get('codes')}")
        lines.extend(["", "## Codes", ", ".join(codes) or "(none)"])
        RESTORE_REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError:
        pass


def run_rescue_restore(req: RescueRestoreRequest, *, runner: Runner = None) -> RescueRestoreResponse:
    codes: list[str] = []
    stages: list[dict[str, Any]] = []
    grant_snapshot: dict[str, Any] = {}
    _log("restore: start")

    ok_gate, gate_code, state = validate_restore_preconditions(
        dry_run_token=req.dry_run_token,
        backup_file=req.backup_id,
        target_device=req.target_device,
        confirmation=bool(req.confirmation),
        risk_acknowledged=bool(req.risk_acknowledged),
        session_id=req.session_id,
    )
    grant_snapshot = {k: v for k, v in (state or {}).items() if k not in ("token",)}
    _record_stage(stages, STAGE_PRECONDITION, ok_gate, [gate_code] if not ok_gate else [])
    if not ok_gate:
        codes.append(gate_code)
        if gate_code in (
            "rescue.restore.confirmation_missing",
            "rescue.restore.risk_ack_missing",
            "rescue.restore.session_missing",
            "rescue.restore.session_invalid",
            "rescue.restore.session_stale",
            "rescue.restore.dryrun_missing",
        ):
            pass
        elif gate_code in (
            "rescue.restore.RESTORE_BLOCKED_RED_RISK",
            "rescue.restore.RESTORE_BLOCKED_NO_DRYRUN",
            "rescue.restore.dryrun_missing",
        ):
            codes.append("rescue.hardstop.no_valid_dryrun")
        return _blocked_response(codes=codes, log_line=f"restore: gate_failed code={gate_code}")

    if not validate_target_confirmation_phrase(req.target_device, req.target_confirmation_text):
        codes.append("rescue.restore.RESTORE_BLOCKED_INVALID_STATE")
        _record_stage(stages, STAGE_PRECONDITION, False, codes)
        return _blocked_response(codes=codes, log_line="restore: confirmation_phrase_mismatch")

    if is_running_system_disk(req.target_device, runner=runner):
        codes.append("rescue.restore.RESTORE_BLOCKED_SYSTEM_DISK")
        codes.append("rescue.hardstop.current_system_target")
        _record_stage(stages, STAGE_TARGET_REVAL, False, codes)
        return _blocked_response(codes=codes, log_line="restore: blocked_running_system_disk")

    try:
        bp = assert_backup_readable_path(req.backup_id)
        tdir = assert_restore_live_target_directory(req.restore_target_directory)
    except ValueError:
        codes.append("rescue.restore.RESTORE_BLOCKED_INVALID_STATE")
        _record_stage(stages, STAGE_PRECONDITION, False, codes)
        return _blocked_response(codes=codes, log_line="restore: path_allowlist_failed")

    if not _target_dir_empty(tdir):
        codes.append("rescue.restore.RESTORE_BLOCKED_TARGET_NOT_EMPTY")
        _record_stage(stages, STAGE_TARGET_REVAL, False, codes)
        return _blocked_response(codes=codes, log_line="restore: target_not_empty")

    ok_m, mcode = validate_mount_matches_target_device(tdir, req.target_device, runner=runner)
    if not ok_m:
        codes.append(mcode)
        _record_stage(stages, STAGE_TARGET_REVAL, False, codes)
        return _blocked_response(codes=codes, log_line=f"restore: mount_mismatch code={mcode}")

    _record_stage(stages, STAGE_TARGET_REVAL, True, [])

    vb_ok, vb_key, _vb_det = verify_basic(bp, runner=runner)
    if not vb_ok:
        codes.append("rescue.restore.RESTORE_BACKUP_CORRUPT")
        codes.append("rescue.hardstop.backup_corrupt")
        if vb_key:
            codes.append("rescue.restore.verify_failed")
        _record_stage(stages, STAGE_BACKUP_REVAL, False, codes)
        return _blocked_response(
            codes=codes,
            result="RESTORE_BLOCKED",
            log_line="restore: verify_basic_failed",
        )
    _record_stage(stages, STAGE_BACKUP_REVAL, True, [])

    work_parent = tdir.parent
    if not path_under_prefixes(work_parent, RESCUE_LIVE_RESTORE_PREFIXES):
        codes.append("rescue.restore.RESTORE_BLOCKED_INVALID_STATE")
        _record_stage(stages, STAGE_TARGET_PREP, False, codes)
        return _blocked_response(codes=codes, log_line="restore: work_parent_not_allowlisted")

    hs_ctx = RestoreHardStopContext(
        state=state,
        backup_path=bp,
        target_device=req.target_device,
        restore_risk_level=str(state.get("restore_risk_level") or ""),
        encryption_key_hex=req.encryption_key_hex,
        runner=runner,
    )
    hs_list = evaluate_restore_hardstops(hs_ctx)
    _record_stage(stages, STAGE_HARDSTOP, len(hs_list) == 0, hs_list)
    if hs_list:
        codes.extend(hs_list)
        return _blocked_response(codes=sorted(set(codes)), log_line=f"restore: hardstop {hs_list[0]}")

    arch, dec_err = _prepare_archive_path(bp, req.encryption_key_hex, work_parent, runner=runner)
    if dec_err:
        codes.append(dec_err)
        codes.append("rescue.hardstop.invalid_key")
        _record_stage(stages, STAGE_TARGET_PREP, False, codes)
        return _blocked_response(codes=codes, log_line=f"restore: decrypt_failed code={dec_err}")

    if bool(req.perform_boot_repair) and not (req.target_device or "").strip():
        codes.append("rescue.restore.RESTORE_BLOCKED_INVALID_STATE")
        _record_stage(stages, STAGE_BOOT, False, codes)
        return _blocked_response(codes=codes, log_line="restore: boot_repair_without_blockdev")

    _record_stage(stages, STAGE_TARGET_PREP, True, [])

    ok_rf, rf_key, rf_err = restore_files(
        arch,
        tdir,
        allowed_target_prefixes=RESCUE_LIVE_RESTORE_PREFIXES,
        dry_run=False,
        runner=runner,
    )
    if not ok_rf:
        codes.append("rescue.restore.RESTORE_FAILED")
        codes.append(str(rf_key or "restore_files"))
        _record_stage(stages, STAGE_DATA, False, codes)
        _log(f"restore: extract_failed key={rf_key}")
        try:
            if arch != bp and arch.is_file():
                arch.unlink(missing_ok=True)
        except OSError:
            pass
        _write_reports(
            result="RESTORE_FAILED",
            warnings=[],
            bootable=False,
            codes=codes,
            stages=stages,
            session_id=req.session_id,
            dry_run_token=req.dry_run_token,
            grant_snapshot=grant_snapshot,
            acknowledgements={"confirmation": req.confirmation, "risk_acknowledged": req.risk_acknowledged},
            boot_repair=None,
        )
        return RescueRestoreResponse(
            status="error",
            result="RESTORE_FAILED",
            warnings=[],
            log_path=str(RESTORE_LOG_PATH),
            bootable=False,
            codes=codes,
        )

    _record_stage(stages, STAGE_DATA, True, [])
    consume_dry_run_grant(req.dry_run_token)
    _log("restore: token_consumed_after_successful_extract")

    try:
        if arch != bp and arch.is_file():
            arch.unlink(missing_ok=True)
    except OSError:
        pass

    result, warns = post_restore_validate(tdir, runner=runner)
    boot_wrap = simulate_boot_preconditions(tdir, runner=runner)
    est = (boot_wrap.get("estimate") or {}).get("bootability_class") or ""
    bootable = est == "BOOTABLE_LIKELY"
    if result == "RESTORE_SUCCESS" and not bootable:
        result = "RESTORE_SUCCESS_WITH_WARNINGS"
        warns.append("rescue.validation.boot_not_likely")

    boot_repair_out = run_boot_repair_pipeline(
        tdir,
        req.target_device,
        perform_boot_repair=bool(req.perform_boot_repair),
        dry_run=not bool(req.perform_boot_repair),
        runner=runner,
    )
    _record_stage(stages, STAGE_BOOT, True, boot_repair_out.get("codes") or [])
    br_codes = list(boot_repair_out.get("codes") or [])
    if bool(req.perform_boot_repair):
        if any(c in br_codes for c in ("rescue.boot.repair_failed", "rescue.boot.repair_not_supported")):
            if result == "RESTORE_SUCCESS":
                result = "RESTORE_PARTIAL"
            warns.extend(c for c in br_codes if c not in warns)
        elif "rescue.boot.validation_uncertain" in br_codes:
            if result == "RESTORE_SUCCESS":
                result = "RESTORE_SUCCESS_WITH_WARNINGS"
            warns.extend(c for c in br_codes if c not in warns)

    _record_stage(stages, STAGE_POST, result != "RESTORE_PARTIAL", [result])
    _record_stage(stages, STAGE_FINAL, True, [result])

    _log(f"restore: finished result={result}")

    _write_reports(
        result=result,
        warnings=warns,
        bootable=bootable,
        codes=codes,
        stages=stages,
        session_id=req.session_id,
        dry_run_token=req.dry_run_token,
        grant_snapshot=grant_snapshot,
        acknowledgements={"confirmation": req.confirmation, "risk_acknowledged": req.risk_acknowledged},
        boot_repair=boot_repair_out,
    )

    return RescueRestoreResponse(
        status="ok",
        result=result,
        warnings=warns,
        log_path=str(RESTORE_LOG_PATH),
        bootable=bootable,
        codes=codes,
    )


__all__ = [
    "RESTORE_LOG_PATH",
    "RESTORE_REPORT_JSON",
    "RESTORE_REPORT_MD",
    "post_restore_validate",
    "run_rescue_restore",
    "validate_mount_matches_target_device",
]
