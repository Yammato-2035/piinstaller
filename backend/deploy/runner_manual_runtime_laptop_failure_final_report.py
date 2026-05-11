from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_SUMMARY_REL = "docs/evidence/runtime-results/handoff/laptop_failure_test_summary.json"
_REPORT_REL = "docs/evidence/runtime-results/handoff/laptop_failure_final_report.json"
_MAX_OUTPUT_BYTES = 256 * 1024


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "FINAL_REPORT_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "FINAL_REPORT_PATH_INVALID"
    if ".." in p.parts:
        return None, "FINAL_REPORT_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "FINAL_REPORT_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "FINAL_REPORT_OUTSIDE_HANDOFF"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _emit(
    out_path: Path,
    report_status: str,
    recommendation: str,
    summary_sha256: str,
    summary_snapshot: dict[str, Any],
    blocked_reasons: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    body = {
        "report_schema_version": 1,
        "strict_mode": "laptop_failure_final_report",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "report_status": report_status,
        "recommendation": recommendation,
        "summary_sha256": summary_sha256,
        "summary_snapshot": summary_snapshot,
        "warnings": list(dict.fromkeys(warnings)),
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return {
            "report_status": "blocked",
            "report_file_path": _REPORT_REL,
            "warnings": [],
            "errors": ["FINAL_REPORT_OUTPUT_TOO_LARGE"],
            "blocked_reasons": ["FINAL_REPORT_OUTPUT_TOO_LARGE"],
        }
    try:
        _atomic_write(out_path, text)
    except OSError:
        return {
            "report_status": "blocked",
            "report_file_path": _REPORT_REL,
            "warnings": [],
            "errors": ["FINAL_REPORT_WRITE_FAILED"],
            "blocked_reasons": ["FINAL_REPORT_WRITE_FAILED"],
        }
    out: dict[str, Any] = dict(body)
    out["report_file_path"] = _REPORT_REL
    out["errors"] = list(dict.fromkeys(blocked_reasons)) if report_status == "blocked" else []
    return out


def build_manual_laptop_failure_final_report(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    blocked_reasons: list[str] = []

    out_resolved, oerr = _resolve_handoff(_REPORT_REL)
    if oerr or out_resolved is None:
        return {
            "report_status": "blocked",
            "report_file_path": _REPORT_REL,
            "warnings": [],
            "errors": [oerr or "FINAL_REPORT_OUTPUT_PATH_INVALID"],
            "blocked_reasons": [oerr or "FINAL_REPORT_OUTPUT_PATH_INVALID"],
        }
    if out_resolved.exists() and out_resolved.is_file() and not explicit_overwrite:
        return {
            "report_status": "blocked",
            "report_file_path": _REPORT_REL,
            "warnings": [],
            "errors": ["FINAL_REPORT_EXISTS_NO_OVERWRITE"],
            "blocked_reasons": ["FINAL_REPORT_EXISTS_NO_OVERWRITE"],
        }

    summary_resolved, serr = _resolve_handoff(_SUMMARY_REL)
    if serr or summary_resolved is None or not summary_resolved.is_file():
        blocked_reasons.append("FINAL_REPORT_SUMMARY_INPUT_MISSING")
        return _emit(out_resolved, "blocked", "blocked", "", {}, blocked_reasons, warnings)

    try:
        summary_raw = summary_resolved.read_bytes()
    except OSError:
        blocked_reasons.append("FINAL_REPORT_SUMMARY_READ_FAILED")
        return _emit(out_resolved, "blocked", "blocked", "", {}, blocked_reasons, warnings)

    try:
        summary_doc = json.loads(summary_raw.decode("utf-8"))
    except Exception:
        blocked_reasons.append("FINAL_REPORT_SUMMARY_JSON_INVALID")
        return _emit(out_resolved, "blocked", "blocked", "", {}, blocked_reasons, warnings)

    if not isinstance(summary_doc, dict):
        blocked_reasons.append("FINAL_REPORT_SUMMARY_STRUCTURE_INVALID")
        return _emit(out_resolved, "blocked", "blocked", "", {}, blocked_reasons, warnings)

    summary_status = str(summary_doc.get("summary_status") or "")
    report_status = "blocked"
    recommendation = "blocked"
    if summary_status == "ok":
        report_status = "ok"
        recommendation = "proceed"
    elif summary_status == "review_required":
        report_status = "review_required"
        recommendation = "review_before_next_run"
    elif summary_status == "blocked":
        report_status = "blocked"
        recommendation = "blocked"
    else:
        blocked_reasons.append("FINAL_REPORT_SUMMARY_STATUS_INVALID")

    summary_sha256 = hashlib.sha256(summary_raw).hexdigest()
    return _emit(
        out_resolved,
        report_status,
        recommendation,
        summary_sha256,
        summary_doc,
        blocked_reasons,
        warnings,
    )
