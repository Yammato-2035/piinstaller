from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_SELECTION_REL = "docs/evidence/runtime-results/handoff/laptop_failure_run_selection.json"
_RUNORDER_REL = "docs/evidence/runtime-results/handoff/laptop_failure_operator_runorder.json"
_MAX_OUTPUT_BYTES = 256 * 1024

_MEDIA_CHANGE_TYPES = frozenset(
    {
        "removed_usb_target",
        "unexpected_device_reenumeration",
    }
)
_MOUNT_CHANGE_TYPES = frozenset(
    {
        "mount_changed",
        "missing_mount",
        "readonly_target",
    }
)


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "RUNORDER_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "RUNORDER_PATH_INVALID"
    if ".." in p.parts:
        return None, "RUNORDER_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "RUNORDER_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "RUNORDER_OUTSIDE_HANDOFF"
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
        return None, "RUNORDER_JSON_INVALID"


def _runorder_sort_key(run: dict[str, Any]) -> tuple[int, int, int, int, tuple[Any, ...], str, str]:
    """Gruppierung: no_media_change, no_mount_change, rollback_not_required, medium_risk_last; Sortierung aus priority_key."""
    ft = str(run.get("failure_type") or "")
    risk = str(run.get("risk_level") or "medium")
    if risk not in ("low", "medium"):
        risk = "medium"
    rb = bool(run.get("rollback_required"))
    media_rank = 1 if ft in _MEDIA_CHANGE_TYPES else 0
    mount_rank = 1 if ft in _MOUNT_CHANGE_TYPES else 0
    rb_rank = 1 if rb else 0
    risk_rank = 1 if risk == "medium" else 0
    pk = run.get("priority_key")
    tie = tuple(pk) if isinstance(pk, list) else ()
    return (media_rank, mount_rank, rb_rank, risk_rank, tie, ft, str(run.get("session_id") or ""))


def _emit(
    out_path: Path,
    runorder_status: str,
    ordered_runs: list[dict[str, Any]],
    deferred_runs: list[dict[str, Any]],
    blocked_reasons: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    body = {
        "runorder_schema_version": 1,
        "strict_mode": "laptop_failure_operator_runorder",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "runorder_status": runorder_status,
        "ordered_runs": ordered_runs,
        "deferred_runs": deferred_runs,
        "warnings": list(dict.fromkeys(warnings)),
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return {
            "runorder_status": "blocked",
            "runorder_file_path": _RUNORDER_REL,
            "warnings": [],
            "errors": ["RUNORDER_OUTPUT_TOO_LARGE"],
            "blocked_reasons": ["RUNORDER_OUTPUT_TOO_LARGE"],
        }
    try:
        _atomic_write(out_path, text)
    except OSError:
        return {
            "runorder_status": "blocked",
            "runorder_file_path": _RUNORDER_REL,
            "warnings": [],
            "errors": ["RUNORDER_WRITE_FAILED"],
            "blocked_reasons": ["RUNORDER_WRITE_FAILED"],
        }
    out: dict[str, Any] = dict(body)
    out["runorder_file_path"] = _RUNORDER_REL
    out["errors"] = list(dict.fromkeys(blocked_reasons)) if runorder_status == "blocked" else []
    return out


def build_manual_laptop_failure_operator_runorder(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    blocked_reasons: list[str] = []
    deferred: list[dict[str, Any]] = []

    out_resolved, oerr = _resolve_handoff(_RUNORDER_REL)
    if oerr or out_resolved is None:
        return {
            "runorder_status": "blocked",
            "runorder_file_path": _RUNORDER_REL,
            "warnings": [],
            "errors": [oerr or "RUNORDER_OUTPUT_PATH_INVALID"],
            "blocked_reasons": [oerr or "RUNORDER_OUTPUT_PATH_INVALID"],
        }
    if out_resolved.exists() and out_resolved.is_file() and not explicit_overwrite:
        return {
            "runorder_status": "blocked",
            "runorder_file_path": _RUNORDER_REL,
            "warnings": [],
            "errors": ["RUNORDER_EXISTS_NO_OVERWRITE"],
            "blocked_reasons": ["RUNORDER_EXISTS_NO_OVERWRITE"],
        }

    in_resolved, ierr = _resolve_handoff(_SELECTION_REL)
    if ierr or in_resolved is None or not in_resolved.is_file():
        blocked_reasons.append("RUNORDER_SELECTION_INPUT_MISSING")
        return _emit(out_resolved, "blocked", [], deferred, blocked_reasons, warnings)

    doc, jerr = _load_json(in_resolved)
    if jerr or not isinstance(doc, dict):
        blocked_reasons.append(jerr or "RUNORDER_JSON_INVALID")
        return _emit(out_resolved, "blocked", [], deferred, blocked_reasons, warnings)

    sel_status = str(doc.get("selection_status") or "")
    if sel_status not in ("ready", "review_required"):
        blocked_reasons.append("RUNORDER_SELECTION_NOT_ALLOWED")
        return _emit(out_resolved, "blocked", [], deferred, blocked_reasons, warnings)

    if sel_status == "review_required":
        warnings.append("upstream_selection_review_required")

    selected = doc.get("selected_runs")
    if not isinstance(selected, list) or len(selected) == 0:
        blocked_reasons.append("RUNORDER_SELECTED_RUNS_EMPTY")
        return _emit(out_resolved, "blocked", [], deferred, blocked_reasons, warnings)

    validation_failed = False
    for idx, run in enumerate(selected):
        if not isinstance(run, dict):
            blocked_reasons.append("RUNORDER_SELECTED_RUN_INVALID")
            return _emit(out_resolved, "blocked", [], deferred, blocked_reasons, warnings)
        sid = str(run.get("session_id") or "").strip()
        ft = str(run.get("failure_type") or "").strip()
        ref = {"session_id": sid, "failure_type": ft, "source_index": idx}

        if str(run.get("execution_mode") or "") != "manual_only":
            deferred.append({**ref, "reason": "execution_mode_not_manual_only"})
            validation_failed = True
            continue

        if "destructive" in run and run.get("destructive") is not False:
            deferred.append({**ref, "reason": "destructive_not_false"})
            validation_failed = True
            continue

        ac = run.get("abort_conditions")
        if not isinstance(ac, list) or len(ac) == 0:
            deferred.append({**ref, "reason": "missing_abort_conditions"})
            validation_failed = True
            continue

        ev = run.get("evidence_to_capture")
        if not isinstance(ev, list) or len(ev) == 0:
            deferred.append({**ref, "reason": "missing_evidence_to_capture"})
            validation_failed = True
            continue

    if validation_failed:
        blocked_reasons.append("RUNORDER_VALIDATION_FAILED")

    if blocked_reasons:
        return _emit(out_resolved, "blocked", [], deferred, blocked_reasons, warnings)

    ordered_src = [dict(r) for r in selected if isinstance(r, dict)]
    ordered_src.sort(key=_runorder_sort_key)

    ordered: list[dict[str, Any]] = []
    for step, run in enumerate(ordered_src, start=1):
        ft = str(run.get("failure_type") or "")
        risk = str(run.get("risk_level") or "medium")
        rb = bool(run.get("rollback_required"))
        entry = dict(run)
        entry["operator_step_index"] = step
        entry["runorder_group"] = _runorder_group_label(ft=ft, risk=risk, rollback_required=rb)
        ordered.append(entry)

    ro_status = "review_required" if sel_status == "review_required" or warnings else "ready"
    return _emit(out_resolved, ro_status, ordered, deferred, blocked_reasons, warnings)


def _runorder_group_label(*, ft: str, risk: str, rollback_required: bool) -> str:
    parts: list[str] = []
    if ft not in _MEDIA_CHANGE_TYPES:
        parts.append("no_media_change")
    else:
        parts.append("media_change")
    if ft not in _MOUNT_CHANGE_TYPES:
        parts.append("no_mount_change")
    else:
        parts.append("mount_change")
    if not rollback_required:
        parts.append("rollback_not_required")
    else:
        parts.append("rollback_required")
    if risk == "medium":
        parts.append("medium_risk")
    else:
        parts.append("low_risk")
    return "|".join(parts)
