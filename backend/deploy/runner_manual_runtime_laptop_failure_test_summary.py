from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_VALIDATION_REL = "docs/evidence/runtime-results/handoff/laptop_failure_execution_log_validation.json"
_SUMMARY_REL = "docs/evidence/runtime-results/handoff/laptop_failure_test_summary.json"
_MAX_OUTPUT_BYTES = 256 * 1024


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "TEST_SUMMARY_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "TEST_SUMMARY_PATH_INVALID"
    if ".." in p.parts:
        return None, "TEST_SUMMARY_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "TEST_SUMMARY_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "TEST_SUMMARY_OUTSIDE_HANDOFF"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _load_json(path: Path) -> tuple[Any | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception:
        return None, "TEST_SUMMARY_JSON_INVALID"


def _emit(
    out_path: Path,
    summary_status: str,
    total_runs: int,
    ok_runs: int,
    review_required_runs: int,
    blocked_runs: int,
    abort_count: int,
    deviation_count: int,
    findings: list[str],
    blocked_reasons: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    body = {
        "summary_schema_version": 1,
        "strict_mode": "laptop_failure_test_summary",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary_status": summary_status,
        "total_runs": total_runs,
        "ok_runs": ok_runs,
        "review_required_runs": review_required_runs,
        "blocked_runs": blocked_runs,
        "abort_count": abort_count,
        "deviation_count": deviation_count,
        "findings": findings,
        "warnings": list(dict.fromkeys(warnings)),
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return {
            "summary_status": "blocked",
            "summary_file_path": _SUMMARY_REL,
            "warnings": [],
            "errors": ["TEST_SUMMARY_OUTPUT_TOO_LARGE"],
            "blocked_reasons": ["TEST_SUMMARY_OUTPUT_TOO_LARGE"],
        }
    try:
        _atomic_write(out_path, text)
    except OSError:
        return {
            "summary_status": "blocked",
            "summary_file_path": _SUMMARY_REL,
            "warnings": [],
            "errors": ["TEST_SUMMARY_WRITE_FAILED"],
            "blocked_reasons": ["TEST_SUMMARY_WRITE_FAILED"],
        }
    out: dict[str, Any] = dict(body)
    out["summary_file_path"] = _SUMMARY_REL
    out["errors"] = list(dict.fromkeys(blocked_reasons)) if summary_status == "blocked" else []
    return out


def build_manual_laptop_failure_test_summary(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    blocked_reasons: list[str] = []

    out_resolved, oerr = _resolve_handoff(_SUMMARY_REL)
    if oerr or out_resolved is None:
        return {
            "summary_status": "blocked",
            "summary_file_path": _SUMMARY_REL,
            "warnings": [],
            "errors": [oerr or "TEST_SUMMARY_OUTPUT_PATH_INVALID"],
            "blocked_reasons": [oerr or "TEST_SUMMARY_OUTPUT_PATH_INVALID"],
        }
    if out_resolved.exists() and out_resolved.is_file() and not explicit_overwrite:
        return {
            "summary_status": "blocked",
            "summary_file_path": _SUMMARY_REL,
            "warnings": [],
            "errors": ["TEST_SUMMARY_EXISTS_NO_OVERWRITE"],
            "blocked_reasons": ["TEST_SUMMARY_EXISTS_NO_OVERWRITE"],
        }

    in_resolved, ierr = _resolve_handoff(_VALIDATION_REL)
    if ierr or in_resolved is None or not in_resolved.is_file():
        blocked_reasons.append("TEST_SUMMARY_VALIDATION_INPUT_MISSING")
        return _emit(out_resolved, "blocked", 0, 0, 0, 0, 0, 0, [], blocked_reasons, warnings)

    doc, jerr = _load_json(in_resolved)
    if jerr or not isinstance(doc, dict):
        blocked_reasons.append(jerr or "TEST_SUMMARY_JSON_INVALID")
        return _emit(out_resolved, "blocked", 0, 0, 0, 0, 0, 0, [], blocked_reasons, warnings)

    validation_status = str(doc.get("validation_status") or "")
    runs = doc.get("run_validations")
    if validation_status not in ("ok", "review_required", "blocked") or not isinstance(runs, list):
        blocked_reasons.append("TEST_SUMMARY_VALIDATION_STRUCTURE_INVALID")
        return _emit(out_resolved, "blocked", 0, 0, 0, 0, 0, 0, [], blocked_reasons, warnings)

    total_runs = len(runs)
    ok_runs = 0
    review_required_runs = 0
    blocked_runs = 0
    abort_count = 0
    deviation_count = 0
    findings: list[str] = []

    for r in runs:
        if not isinstance(r, dict):
            blocked_reasons.append("TEST_SUMMARY_RUN_VALIDATION_INVALID")
            return _emit(out_resolved, "blocked", 0, 0, 0, 0, 0, 0, [], blocked_reasons, warnings)
        rv = str(r.get("run_validation_status") or "")
        if rv == "ok":
            ok_runs += 1
        elif rv == "review_required":
            review_required_runs += 1
        elif rv == "blocked":
            blocked_runs += 1

        issues = r.get("issues")
        if isinstance(issues, list):
            for it in issues:
                s = str(it)
                if "abort" in s:
                    abort_count += 1
                if "deviation" in s:
                    deviation_count += 1
                if s:
                    findings.append(s)

        obs = str(r.get("observed_status") or "")
        if obs == "review_required":
            review_required_runs = max(review_required_runs, review_required_runs)
        if obs == "blocked":
            blocked_runs = max(blocked_runs, blocked_runs)

    summary_status = "ok"
    if validation_status == "blocked" or blocked_runs > 0:
        summary_status = "blocked"
        blocked_reasons.append("TEST_SUMMARY_VALIDATION_BLOCKED")
    elif validation_status == "review_required" or deviation_count > 0 or abort_count > 0:
        summary_status = "review_required"
    elif validation_status != "ok":
        summary_status = "blocked"
        blocked_reasons.append("TEST_SUMMARY_VALIDATION_STATUS_INVALID")

    return _emit(
        out_resolved,
        summary_status,
        total_runs,
        ok_runs,
        review_required_runs,
        blocked_runs,
        abort_count,
        deviation_count,
        list(dict.fromkeys(findings)),
        blocked_reasons,
        warnings,
    )
