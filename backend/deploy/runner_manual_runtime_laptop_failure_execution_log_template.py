from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_RUNORDER_REL = "docs/evidence/runtime-results/handoff/laptop_failure_operator_runorder.json"
_EXEC_LOG_REL = "docs/evidence/runtime-results/handoff/laptop_failure_execution_log.json"
_MAX_OUTPUT_BYTES = 512 * 1024


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "EXEC_LOG_TEMPLATE_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "EXEC_LOG_TEMPLATE_PATH_INVALID"
    if ".." in p.parts:
        return None, "EXEC_LOG_TEMPLATE_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "EXEC_LOG_TEMPLATE_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "EXEC_LOG_TEMPLATE_OUTSIDE_HANDOFF"
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
        return None, "EXEC_LOG_TEMPLATE_JSON_INVALID"


def _emit(
    out_path: Path,
    template_status: str,
    ordered_runs: list[dict[str, Any]],
    deferred_runs: list[dict[str, Any]],
    blocked_reasons: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    body = {
        "execution_log_schema_version": 1,
        "strict_mode": "laptop_failure_execution_log_template",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "template_status": template_status,
        "ordered_runs": ordered_runs,
        "deferred_runs": deferred_runs,
        "warnings": list(dict.fromkeys(warnings)),
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return {
            "template_status": "blocked",
            "execution_log_file_path": _EXEC_LOG_REL,
            "warnings": [],
            "errors": ["EXEC_LOG_TEMPLATE_OUTPUT_TOO_LARGE"],
            "blocked_reasons": ["EXEC_LOG_TEMPLATE_OUTPUT_TOO_LARGE"],
        }
    try:
        _atomic_write(out_path, text)
    except OSError:
        return {
            "template_status": "blocked",
            "execution_log_file_path": _EXEC_LOG_REL,
            "warnings": [],
            "errors": ["EXEC_LOG_TEMPLATE_WRITE_FAILED"],
            "blocked_reasons": ["EXEC_LOG_TEMPLATE_WRITE_FAILED"],
        }
    out: dict[str, Any] = dict(body)
    out["execution_log_file_path"] = _EXEC_LOG_REL
    out["errors"] = list(dict.fromkeys(blocked_reasons)) if template_status == "blocked" else []
    return out


def _empty_log_entry(run: dict[str, Any]) -> dict[str, Any]:
    run_id = str(run.get("session_id") or run.get("run_id") or "").strip()
    return {
        "run_id": run_id,
        "failure_type": str(run.get("failure_type") or "").strip(),
        "operator_step_index": int(run.get("operator_step_index") or 0),
        "started_at": "",
        "completed_at": "",
        "operator": "",
        "host": "",
        "test_media": "",
        "pre_state": {
            "lsblk": "",
            "findmnt": "",
            "mount": "",
        },
        "observed_detection": "",
        "observed_status": "",
        "evidence_collected": [],
        "abort_triggered": False,
        "abort_reason": "",
        "rollback_performed": False,
        "post_state": {
            "lsblk": "",
            "findmnt": "",
            "mount": "",
        },
        "deviations": [],
        "notes": [],
        "destructive": False,
    }


def build_manual_laptop_failure_execution_log_template(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    blocked_reasons: list[str] = []
    deferred: list[dict[str, Any]] = []

    out_resolved, oerr = _resolve_handoff(_EXEC_LOG_REL)
    if oerr or out_resolved is None:
        return {
            "template_status": "blocked",
            "execution_log_file_path": _EXEC_LOG_REL,
            "warnings": [],
            "errors": [oerr or "EXEC_LOG_TEMPLATE_OUTPUT_PATH_INVALID"],
            "blocked_reasons": [oerr or "EXEC_LOG_TEMPLATE_OUTPUT_PATH_INVALID"],
        }
    if out_resolved.exists() and out_resolved.is_file() and not explicit_overwrite:
        return {
            "template_status": "blocked",
            "execution_log_file_path": _EXEC_LOG_REL,
            "warnings": [],
            "errors": ["EXEC_LOG_TEMPLATE_EXISTS_NO_OVERWRITE"],
            "blocked_reasons": ["EXEC_LOG_TEMPLATE_EXISTS_NO_OVERWRITE"],
        }

    in_resolved, ierr = _resolve_handoff(_RUNORDER_REL)
    if ierr or in_resolved is None or not in_resolved.is_file():
        blocked_reasons.append("EXEC_LOG_TEMPLATE_RUNORDER_INPUT_MISSING")
        return _emit(out_resolved, "blocked", [], deferred, blocked_reasons, warnings)

    doc, jerr = _load_json(in_resolved)
    if jerr or not isinstance(doc, dict):
        blocked_reasons.append(jerr or "EXEC_LOG_TEMPLATE_JSON_INVALID")
        return _emit(out_resolved, "blocked", [], deferred, blocked_reasons, warnings)

    runorder_status = str(doc.get("runorder_status") or "")
    if runorder_status not in ("ready", "review_required"):
        blocked_reasons.append("EXEC_LOG_TEMPLATE_RUNORDER_NOT_ALLOWED")
        return _emit(out_resolved, "blocked", [], deferred, blocked_reasons, warnings)

    if runorder_status == "review_required":
        warnings.append("upstream_runorder_review_required")

    ordered_runs = doc.get("ordered_runs")
    if not isinstance(ordered_runs, list) or len(ordered_runs) == 0:
        blocked_reasons.append("EXEC_LOG_TEMPLATE_ORDERED_RUNS_EMPTY")
        return _emit(out_resolved, "blocked", [], deferred, blocked_reasons, warnings)

    template_runs: list[dict[str, Any]] = []
    validation_failed = False
    for idx, run in enumerate(ordered_runs):
        if not isinstance(run, dict):
            blocked_reasons.append("EXEC_LOG_TEMPLATE_ORDERED_RUN_INVALID")
            return _emit(out_resolved, "blocked", [], deferred, blocked_reasons, warnings)
        sid = str(run.get("session_id") or run.get("run_id") or "").strip()
        ft = str(run.get("failure_type") or "").strip()
        ref = {"run_id": sid, "failure_type": ft, "source_index": idx}

        if str(run.get("execution_mode") or "") != "manual_only":
            deferred.append({**ref, "reason": "execution_mode_not_manual_only"})
            validation_failed = True
            continue
        if "destructive" in run and run.get("destructive") is not False:
            deferred.append({**ref, "reason": "destructive_not_false"})
            validation_failed = True
            continue
        if not isinstance(run.get("abort_conditions"), list) or len(run.get("abort_conditions") or []) == 0:
            deferred.append({**ref, "reason": "missing_abort_conditions"})
            validation_failed = True
            continue
        if not isinstance(run.get("evidence_to_capture"), list) or len(run.get("evidence_to_capture") or []) == 0:
            deferred.append({**ref, "reason": "missing_evidence_to_capture"})
            validation_failed = True
            continue

        template_runs.append(_empty_log_entry(run))

    if validation_failed:
        blocked_reasons.append("EXEC_LOG_TEMPLATE_VALIDATION_FAILED")
        return _emit(out_resolved, "blocked", [], deferred, blocked_reasons, warnings)

    template_status = "review_required" if runorder_status == "review_required" or warnings else "ok"
    return _emit(out_resolved, template_status, template_runs, deferred, blocked_reasons, warnings)
