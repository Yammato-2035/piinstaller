from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from deploy.runner_rescue_io import (
    BUILD_RESCUE_ROOT,
    REPO_ROOT,
    ensure_rescue_workspace_dirs,
    guard_handoff_overwrite,
    resolve_handoff_path,
    write_json_handoff,
)

_PRECHECK_REL = "docs/evidence/runtime-results/handoff/rescue_iso_build_precheck.json"
_RESULT_REL = "docs/evidence/runtime-results/handoff/rescue_iso_build_result.json"
_CONTROLLED_SCRIPT = REPO_ROOT / "scripts" / "rescue" / "build-rescue-iso-controlled.sh"
_MAX_BYTES = 768 * 1024
_MIN_FREE_DEFAULT = 12_000_000_000
_FORBIDDEN_LOG_PATTERNS = (
    r"\bdd\s+if=",
    r"\bdd\s+of=",
    r"\bmkfs\b",
    r"\bwipefs\b",
    r"\bmount\s+/dev/sd",
    r"\bsystemctl\s+",
    r"\bapt(?:-get)?\s+install\b",
)


def _emit_pre(
    status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]
) -> dict[str, Any]:
    return {
        "rescue_iso_build_precheck_status": status,
        "rescue_iso_build_precheck_file_path": _PRECHECK_REL,
        "rescue_iso_build_precheck": body,
        "rescue_iso_build_precheck_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def _emit_result(
    status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]
) -> dict[str, Any]:
    return {
        "rescue_iso_build_result_status": status,
        "rescue_iso_build_result_file_path": _RESULT_REL,
        "rescue_iso_build_result": body,
        "rescue_iso_build_result_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def _forbidden_in_logs(text: str) -> list[str]:
    low = text.lower()
    hits: list[str] = []
    for pat in _FORBIDDEN_LOG_PATTERNS:
        if re.search(pat, low, re.IGNORECASE):
            hits.append(pat)
    return hits


def build_rescue_iso_build_precheck(
    *,
    explicit_overwrite: bool = False,
    min_free_disk_bytes: int | None = None,
) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_PRECHECK_REL, "RESCUE_PRE")
    if oerr or out_path is None:
        return _emit_pre("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_PRE_OUTPUT_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_PRE")
    if gerr:
        return _emit_pre("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    ensure_rescue_workspace_dirs()
    warnings: list[str] = []
    errors: list[str] = []

    ws = BUILD_RESCUE_ROOT
    if not ws.is_dir():
        errors.append("RESCUE_PRE_WORKSPACE_MISSING")

    min_free = int(min_free_disk_bytes or _MIN_FREE_DEFAULT)
    try:
        usage = shutil.disk_usage(ws)
        free_ok = usage.free >= min_free
        free_b = int(usage.free)
    except OSError:
        free_ok = False
        free_b = -1
        errors.append("RESCUE_PRE_DISK_USAGE_FAILED")
    if not free_ok and not errors:
        errors.append("RESCUE_PRE_INSUFFICIENT_DISK")

    lb_ok = shutil.which("lb") is not None
    if not lb_ok:
        warnings.append("RESCUE_PRE_LB_NOT_IN_PATH")

    forbidden_paths = False
    for bad in ("/dev/sd", "/dev/nvme", "/mnt/", "/media/"):
        if bad in str(ws):
            forbidden_paths = True
    if forbidden_paths:
        errors.append("RESCUE_PRE_PATH_SUSPICIOUS")

    status = "ok" if not errors else "blocked"
    body: dict[str, Any] = {
        "rescue_iso_build_precheck_schema_version": 1,
        "strict_mode": "setuphelfer_rescue_iso_phase1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "workspace_root": str(ws.relative_to(REPO_ROOT)).replace("\\", "/"),
        "workspace_exists": ws.is_dir(),
        "free_disk_bytes": free_b,
        "min_free_disk_bytes": min_free,
        "live_build_lb_available": lb_ok,
        "forbidden_paths_detected": forbidden_paths,
    }

    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_pre("blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit_pre(status, body, wrote=True, warnings=warnings, errors=errors)


def execute_rescue_iso_build(
    *,
    explicit_overwrite: bool = False,
    explicit_execute_iso_build: bool = False,
    explicit_rescue_build_approved: bool = False,
    build_timeout_seconds: int = 7200,
) -> dict[str, Any]:
    """Runs the controlled ISO build script (subprocess). Requires explicit flags + approval."""
    if not explicit_execute_iso_build:
        return _emit_result(
            "blocked",
            {"reason": "EXECUTE_REQUIRES_EXPLICIT_EXECUTE_ISO_BUILD"},
            wrote=False,
            warnings=[],
            errors=["RESCUE_BUILD_EXECUTE_NOT_AUTHORIZED"],
        )
    if not explicit_rescue_build_approved:
        return _emit_result(
            "blocked",
            {"reason": "EXECUTE_REQUIRES_EXPLICIT_RESCUE_BUILD_APPROVED"},
            wrote=False,
            warnings=[],
            errors=["RESCUE_BUILD_APPROVAL_MISSING"],
        )

    ensure_rescue_workspace_dirs()
    log_dir = BUILD_RESCUE_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = log_dir / f"iso_build_{ts}.log"

    if not _CONTROLLED_SCRIPT.is_file():
        return _emit_result(
            "blocked",
            {},
            wrote=False,
            warnings=[],
            errors=["RESCUE_BUILD_SCRIPT_MISSING"],
        )

    env = dict(**os.environ)
    env["SETUPHELFER_RESCUE_BUILD_APPROVED"] = "1"

    proc = subprocess.run(
        ["bash", str(_CONTROLLED_SCRIPT)],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=int(build_timeout_seconds),
        check=False,
    )
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    try:
        log_path.write_text(combined, encoding="utf-8", errors="replace")
    except OSError:
        pass

    forbidden_hits = _forbidden_in_logs(combined)
    return build_rescue_iso_build_result(
        explicit_overwrite=explicit_overwrite,
        subprocess_exit_code=int(proc.returncode),
        subprocess_log_path=str(log_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        forbidden_hits=forbidden_hits,
    )


def build_rescue_iso_build_result(
    *,
    explicit_overwrite: bool = False,
    subprocess_exit_code: int | None = None,
    subprocess_log_path: str | None = None,
    forbidden_hits: list[str] | None = None,
) -> dict[str, Any]:
    """Writes ``rescue_iso_build_result.json`` from workspace scan (and optional execute metadata)."""
    out_path, oerr = resolve_handoff_path(_RESULT_REL, "RESCUE_BRES")
    if oerr or out_path is None:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_BRES_OUTPUT_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_BRES")
    if gerr:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    out_dir = BUILD_RESCUE_ROOT / "output"
    iso_files = sorted(out_dir.glob("*.iso")) if out_dir.is_dir() else []
    primary: Path | None = iso_files[-1] if iso_files else None

    iso_sha256 = ""
    iso_bytes = 0
    if primary and primary.is_file():
        iso_bytes = int(primary.stat().st_size)
        h = hashlib.sha256()
        with primary.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        iso_sha256 = h.hexdigest()

    fh = list(forbidden_hits or [])
    log_scan_hits: list[str] = []
    if subprocess_log_path:
        lp = REPO_ROOT / subprocess_log_path.replace("\\", "/")
        try:
            if lp.is_file():
                log_scan_hits = _forbidden_in_logs(lp.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            pass
    fh.extend(log_scan_hits)
    fh = list(dict.fromkeys(fh))

    warnings: list[str] = []
    errors: list[str] = []
    if subprocess_exit_code is not None and subprocess_exit_code != 0:
        errors.append(f"RESCUE_BUILD_SUBPROCESS_EXIT_{subprocess_exit_code}")
    if fh:
        errors.append("RESCUE_BUILD_FORBIDDEN_PATTERN_IN_LOGS")

    if not primary:
        errors.append("RESCUE_BUILD_ISO_MISSING")

    max_iso = 4_000_000_000
    if primary and primary.is_file() and iso_bytes > max_iso:
        errors.append("RESCUE_BUILD_ISO_TOO_LARGE")

    build_success = bool(primary and primary.is_file() and not errors)
    status = "ok" if build_success else "blocked"

    body: dict[str, Any] = {
        "rescue_iso_build_result_schema_version": 1,
        "strict_mode": "setuphelfer_rescue_iso_phase1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "build_success": build_success,
        "iso_found": bool(primary),
        "iso_path": str(primary.relative_to(REPO_ROOT)).replace("\\", "/") if primary else "",
        "iso_bytes": iso_bytes,
        "iso_sha256": iso_sha256,
        "subprocess_exit_code": subprocess_exit_code,
        "subprocess_log_rel": subprocess_log_path or "",
        "forbidden_commands_detected": fh,
        "max_iso_bytes": max_iso,
    }

    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_result("blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit_result(status, body, wrote=True, warnings=warnings, errors=errors)
