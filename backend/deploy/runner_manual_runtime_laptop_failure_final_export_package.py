from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_FINAL_REPORT_REL = "docs/evidence/runtime-results/handoff/laptop_failure_final_report.json"
_SUMMARY_REL = "docs/evidence/runtime-results/handoff/laptop_failure_test_summary.json"
_VALIDATION_REL = "docs/evidence/runtime-results/handoff/laptop_failure_execution_log_validation.json"
_EXEC_LOG_REL = "docs/evidence/runtime-results/handoff/laptop_failure_execution_log.json"
_EXPORT_REL = "docs/evidence/runtime-results/handoff/laptop_failure_final_export_package.json"
_MAX_OUTPUT_BYTES = 512 * 1024


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "FINAL_EXPORT_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "FINAL_EXPORT_PATH_INVALID"
    if ".." in p.parts:
        return None, "FINAL_EXPORT_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "FINAL_EXPORT_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "FINAL_EXPORT_OUTSIDE_HANDOFF"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _emit(
    out_path: Path,
    export_status: str,
    file_hashes: list[dict[str, str]],
    recommendation: str,
    blocked_reasons: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    body = {
        "export_schema_version": 1,
        "strict_mode": "laptop_failure_final_export_package",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "export_status": export_status,
        "recommendation": recommendation,
        "included_files": file_hashes,
        "warnings": list(dict.fromkeys(warnings)),
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return {
            "export_status": "blocked",
            "export_file_path": _EXPORT_REL,
            "warnings": [],
            "errors": ["FINAL_EXPORT_OUTPUT_TOO_LARGE"],
            "blocked_reasons": ["FINAL_EXPORT_OUTPUT_TOO_LARGE"],
        }
    try:
        _atomic_write(out_path, text)
    except OSError:
        return {
            "export_status": "blocked",
            "export_file_path": _EXPORT_REL,
            "warnings": [],
            "errors": ["FINAL_EXPORT_WRITE_FAILED"],
            "blocked_reasons": ["FINAL_EXPORT_WRITE_FAILED"],
        }
    out: dict[str, Any] = dict(body)
    out["export_file_path"] = _EXPORT_REL
    out["errors"] = list(dict.fromkeys(blocked_reasons)) if export_status == "blocked" else []
    return out


def build_manual_laptop_failure_final_export_package(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    blocked_reasons: list[str] = []
    file_hashes: list[dict[str, str]] = []

    out_resolved, oerr = _resolve_handoff(_EXPORT_REL)
    if oerr or out_resolved is None:
        return {
            "export_status": "blocked",
            "export_file_path": _EXPORT_REL,
            "warnings": [],
            "errors": [oerr or "FINAL_EXPORT_OUTPUT_PATH_INVALID"],
            "blocked_reasons": [oerr or "FINAL_EXPORT_OUTPUT_PATH_INVALID"],
        }
    if out_resolved.exists() and out_resolved.is_file() and not explicit_overwrite:
        return {
            "export_status": "blocked",
            "export_file_path": _EXPORT_REL,
            "warnings": [],
            "errors": ["FINAL_EXPORT_EXISTS_NO_OVERWRITE"],
            "blocked_reasons": ["FINAL_EXPORT_EXISTS_NO_OVERWRITE"],
        }

    inputs = [_FINAL_REPORT_REL, _SUMMARY_REL, _VALIDATION_REL, _EXEC_LOG_REL]
    raw_by_rel: dict[str, bytes] = {}
    for rel in inputs:
        p, err = _resolve_handoff(rel)
        if err or p is None or not p.is_file():
            blocked_reasons.append(f"FINAL_EXPORT_INPUT_MISSING:{Path(rel).name}")
            return _emit(out_resolved, "blocked", file_hashes, "blocked", blocked_reasons, warnings)
        try:
            raw = p.read_bytes()
        except OSError:
            blocked_reasons.append(f"FINAL_EXPORT_INPUT_READ_FAILED:{Path(rel).name}")
            return _emit(out_resolved, "blocked", file_hashes, "blocked", blocked_reasons, warnings)
        raw_by_rel[rel] = raw
        file_hashes.append(
            {
                "path": rel,
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )

    try:
        final_report = json.loads(raw_by_rel[_FINAL_REPORT_REL].decode("utf-8"))
    except Exception:
        blocked_reasons.append("FINAL_EXPORT_FINAL_REPORT_JSON_INVALID")
        return _emit(out_resolved, "blocked", file_hashes, "blocked", blocked_reasons, warnings)

    if not isinstance(final_report, dict):
        blocked_reasons.append("FINAL_EXPORT_FINAL_REPORT_STRUCTURE_INVALID")
        return _emit(out_resolved, "blocked", file_hashes, "blocked", blocked_reasons, warnings)

    report_status = str(final_report.get("report_status") or "")
    export_status = "blocked"
    recommendation = "blocked"
    if report_status == "ok":
        export_status = "ok"
        recommendation = "proceed"
    elif report_status == "review_required":
        export_status = "review_required"
        recommendation = "review_before_next_run"
    elif report_status == "blocked":
        export_status = "blocked"
        recommendation = "blocked"
    else:
        blocked_reasons.append("FINAL_EXPORT_REPORT_STATUS_INVALID")

    return _emit(out_resolved, export_status, file_hashes, recommendation, blocked_reasons, warnings)
