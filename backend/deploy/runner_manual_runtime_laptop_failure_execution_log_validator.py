from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_EXEC_LOG_REL = "docs/evidence/runtime-results/handoff/laptop_failure_execution_log.json"
_VALIDATION_REL = "docs/evidence/runtime-results/handoff/laptop_failure_execution_log_validation.json"
_MAX_OUTPUT_BYTES = 512 * 1024
_VALID_STATUSES = {"ok", "review_required", "blocked"}


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "EXEC_LOG_VALIDATION_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "EXEC_LOG_VALIDATION_PATH_INVALID"
    if ".." in p.parts:
        return None, "EXEC_LOG_VALIDATION_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "EXEC_LOG_VALIDATION_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "EXEC_LOG_VALIDATION_OUTSIDE_HANDOFF"
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
        return None, "EXEC_LOG_VALIDATION_JSON_INVALID"


def _non_empty_str(v: Any) -> bool:
    return isinstance(v, str) and v.strip() != ""


def _emit(
    out_path: Path,
    validation_status: str,
    run_validations: list[dict[str, Any]],
    blocked_reasons: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    body = {
        "validation_schema_version": 1,
        "strict_mode": "laptop_failure_execution_log_validator",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "validation_status": validation_status,
        "run_validations": run_validations,
        "warnings": list(dict.fromkeys(warnings)),
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return {
            "validation_status": "blocked",
            "validation_file_path": _VALIDATION_REL,
            "warnings": [],
            "errors": ["EXEC_LOG_VALIDATION_OUTPUT_TOO_LARGE"],
            "blocked_reasons": ["EXEC_LOG_VALIDATION_OUTPUT_TOO_LARGE"],
        }
    try:
        _atomic_write(out_path, text)
    except OSError:
        return {
            "validation_status": "blocked",
            "validation_file_path": _VALIDATION_REL,
            "warnings": [],
            "errors": ["EXEC_LOG_VALIDATION_WRITE_FAILED"],
            "blocked_reasons": ["EXEC_LOG_VALIDATION_WRITE_FAILED"],
        }
    out: dict[str, Any] = dict(body)
    out["validation_file_path"] = _VALIDATION_REL
    out["errors"] = list(dict.fromkeys(blocked_reasons)) if validation_status == "blocked" else []
    return out


def validate_manual_laptop_failure_execution_log(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    blocked_reasons: list[str] = []

    out_resolved, oerr = _resolve_handoff(_VALIDATION_REL)
    if oerr or out_resolved is None:
        return {
            "validation_status": "blocked",
            "validation_file_path": _VALIDATION_REL,
            "warnings": [],
            "errors": [oerr or "EXEC_LOG_VALIDATION_OUTPUT_PATH_INVALID"],
            "blocked_reasons": [oerr or "EXEC_LOG_VALIDATION_OUTPUT_PATH_INVALID"],
        }
    if out_resolved.exists() and out_resolved.is_file() and not explicit_overwrite:
        return {
            "validation_status": "blocked",
            "validation_file_path": _VALIDATION_REL,
            "warnings": [],
            "errors": ["EXEC_LOG_VALIDATION_EXISTS_NO_OVERWRITE"],
            "blocked_reasons": ["EXEC_LOG_VALIDATION_EXISTS_NO_OVERWRITE"],
        }

    in_resolved, ierr = _resolve_handoff(_EXEC_LOG_REL)
    if ierr or in_resolved is None or not in_resolved.is_file():
        blocked_reasons.append("EXEC_LOG_VALIDATION_INPUT_MISSING")
        return _emit(out_resolved, "blocked", [], blocked_reasons, warnings)

    doc, jerr = _load_json(in_resolved)
    if jerr or not isinstance(doc, dict):
        blocked_reasons.append(jerr or "EXEC_LOG_VALIDATION_JSON_INVALID")
        return _emit(out_resolved, "blocked", [], blocked_reasons, warnings)

    runs = doc.get("ordered_runs")
    if not isinstance(runs, list) or len(runs) == 0:
        blocked_reasons.append("EXEC_LOG_VALIDATION_ORDERED_RUNS_EMPTY")
        return _emit(out_resolved, "blocked", [], blocked_reasons, warnings)

    any_review = False
    any_blocked = False
    run_validations: list[dict[str, Any]] = []
    for idx, run in enumerate(runs):
        if not isinstance(run, dict):
            blocked_reasons.append("EXEC_LOG_VALIDATION_RUN_STRUCTURE_INVALID")
            return _emit(out_resolved, "blocked", [], blocked_reasons, warnings)

        rid = str(run.get("run_id") or "").strip()
        ft = str(run.get("failure_type") or "").strip()
        issues: list[str] = []

        if not rid:
            issues.append("missing_run_id")
        if not ft:
            issues.append("missing_failure_type")

        for f in ("started_at", "completed_at", "operator", "host", "test_media", "observed_detection"):
            if not _non_empty_str(run.get(f)):
                issues.append(f"missing_{f}")

        obs = str(run.get("observed_status") or "")
        if obs not in _VALID_STATUSES:
            issues.append("invalid_observed_status")

        pre = run.get("pre_state")
        post = run.get("post_state")
        if not isinstance(pre, dict):
            issues.append("missing_pre_state")
        else:
            for f in ("lsblk", "findmnt", "mount"):
                if not _non_empty_str(pre.get(f)):
                    issues.append(f"missing_pre_state_{f}")
        if not isinstance(post, dict):
            issues.append("missing_post_state")
        else:
            for f in ("lsblk", "findmnt", "mount"):
                if not _non_empty_str(post.get(f)):
                    issues.append(f"missing_post_state_{f}")

        evidence = run.get("evidence_collected")
        if not isinstance(evidence, list) or len(evidence) == 0:
            issues.append("missing_evidence_collected")

        if not isinstance(run.get("abort_triggered"), bool):
            issues.append("invalid_abort_triggered")
        if not isinstance(run.get("rollback_performed"), bool):
            issues.append("invalid_rollback_performed")
        if run.get("destructive") is not False:
            issues.append("destructive_not_false")
        if not isinstance(run.get("deviations"), list):
            issues.append("invalid_deviations")
        if not isinstance(run.get("notes"), list):
            issues.append("invalid_notes")

        run_status = "ok"
        if issues or obs == "blocked":
            run_status = "blocked"
            any_blocked = True
        else:
            deviations = run.get("deviations") or []
            abort_triggered = bool(run.get("abort_triggered"))
            if obs == "review_required" or abort_triggered or len(deviations) > 0:
                run_status = "review_required"
                any_review = True

        run_validations.append(
            {
                "run_id": rid or f"index_{idx}",
                "failure_type": ft,
                "observed_status": obs,
                "run_validation_status": run_status,
                "issues": issues,
            }
        )

    final_status = "ok"
    if any_blocked:
        final_status = "blocked"
        blocked_reasons.append("EXEC_LOG_VALIDATION_RUN_BLOCKED")
    elif any_review:
        final_status = "review_required"

    return _emit(out_resolved, final_status, run_validations, blocked_reasons, warnings)
