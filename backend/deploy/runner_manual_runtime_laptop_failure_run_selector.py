from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_READINESS_REL = "docs/evidence/runtime-results/handoff/failure_test_readiness.json"
_SESSIONS_REL = "docs/evidence/runtime-results/handoff/failure_test_sessions.json"
_CHECKLISTS_REL = "docs/evidence/runtime-results/handoff/failure_operator_checklists.json"
_SELECTION_REL = "docs/evidence/runtime-results/handoff/laptop_failure_run_selection.json"
_MAX_OUTPUT_BYTES = 256 * 1024

_FORBIDDEN_MARKERS = (
    "/dev/nvme0n1",
    "/dev/sda",
    "productive_system_partition",
    "productive_internal_partition",
    "internal_os_volume",
    "internal_os_partition",
)

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
        return None, "RUN_SELECT_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "RUN_SELECT_PATH_INVALID"
    if ".." in p.parts:
        return None, "RUN_SELECT_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "RUN_SELECT_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "RUN_SELECT_OUTSIDE_HANDOFF"
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
        return None, "RUN_SELECT_JSON_INVALID"


def _sort_key(ft: str, risk: str, rb: bool) -> tuple[int, int, int, int, str]:
    risk_rank = 0 if risk == "low" else 1
    media = 1 if ft in _MEDIA_CHANGE_TYPES else 0
    mount = 1 if ft in _MOUNT_CHANGE_TYPES else 0
    rb_rank = 1 if rb else 0
    return (risk_rank, media, mount, rb_rank, ft)


def select_manual_laptop_failure_test_runs(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    blocked_reasons: list[str] = []

    out_resolved, oerr = _resolve_handoff(_SELECTION_REL)
    if oerr or out_resolved is None:
        return {
            "selection_status": "blocked",
            "selection_file_path": _SELECTION_REL,
            "warnings": [],
            "errors": [oerr or "RUN_SELECT_OUTPUT_PATH_INVALID"],
            "blocked_reasons": [oerr or "RUN_SELECT_OUTPUT_PATH_INVALID"],
        }
    if out_resolved.exists() and out_resolved.is_file() and not explicit_overwrite:
        return {
            "selection_status": "blocked",
            "selection_file_path": _SELECTION_REL,
            "warnings": [],
            "errors": ["RUN_SELECT_EXISTS_NO_OVERWRITE"],
            "blocked_reasons": ["RUN_SELECT_EXISTS_NO_OVERWRITE"],
        }

    for rel in (_READINESS_REL, _SESSIONS_REL, _CHECKLISTS_REL):
        rsv, rerr = _resolve_handoff(rel)
        if rerr or rsv is None or not rsv.is_file():
            blocked_reasons.append(f"RUN_SELECT_INPUT_MISSING:{Path(rel).name}")
            return _emit(
                out_resolved,
                "blocked",
                [],
                [],
                blocked_reasons,
                warnings,
                explicit_overwrite,
            )

    rd_path = _resolve_handoff(_READINESS_REL)[0]
    ses_path = _resolve_handoff(_SESSIONS_REL)[0]
    chk_path = _resolve_handoff(_CHECKLISTS_REL)[0]
    assert rd_path and ses_path and chk_path

    rd, e1 = _load_json(rd_path)
    ses_doc, e2 = _load_json(ses_path)
    chk_doc, e3 = _load_json(chk_path)
    if e1 or e2 or e3 or not isinstance(rd, dict) or not isinstance(ses_doc, dict) or not isinstance(chk_doc, dict):
        blocked_reasons.append("RUN_SELECT_JSON_INVALID")
        return _emit(out_resolved, "blocked", [], [], blocked_reasons, warnings, explicit_overwrite)

    readiness_status = str(rd.get("readiness_status") or "")
    if readiness_status not in ("ready", "review_required"):
        blocked_reasons.append("RUN_SELECT_READINESS_NOT_ALLOWED")
        return _emit(out_resolved, "blocked", [], [], blocked_reasons, warnings, explicit_overwrite)

    if readiness_status == "review_required":
        warnings.append("upstream_readiness_review_required")

    sessions = ses_doc.get("test_sessions")
    c_lists = chk_doc.get("checklists")
    if not isinstance(sessions, list) or not isinstance(c_lists, list):
        blocked_reasons.append("RUN_SELECT_STRUCTURE_INVALID")
        return _emit(out_resolved, "blocked", [], [], blocked_reasons, warnings, explicit_overwrite)

    chk_by_ft: dict[str, dict[str, Any]] = {}
    for cl in c_lists:
        if isinstance(cl, dict):
            ft = str(cl.get("failure_type") or "").strip()
            if ft:
                chk_by_ft[ft] = cl

    selected: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []

    for s in sessions:
        if not isinstance(s, dict):
            blocked_reasons.append("RUN_SELECT_SESSION_INVALID")
            return _emit(out_resolved, "blocked", [], [], blocked_reasons, warnings, explicit_overwrite)

        ft = str(s.get("failure_type") or "").strip()
        sid = str(s.get("session_id") or "").strip()
        if not ft or not sid:
            deferred.append({"session_id": sid, "failure_type": ft, "reason": "incomplete_session"})
            continue

        blob = json.dumps(s, sort_keys=True).lower()
        for m in _FORBIDDEN_MARKERS:
            if m.lower() in blob:
                deferred.append({"session_id": sid, "failure_type": ft, "reason": f"productive_or_internal_marker:{m}"})
                break
        else:
            chk = chk_by_ft.get(ft)
            if chk is None:
                deferred.append({"session_id": sid, "failure_type": ft, "reason": "no_checklist_for_failure_type"})
                continue

            chk_blob = json.dumps(chk, sort_keys=True).lower()
            bad_marker = False
            for m in _FORBIDDEN_MARKERS:
                if m.lower() in chk_blob:
                    deferred.append(
                        {"session_id": sid, "failure_type": ft, "reason": f"checklist_productive_marker:{m}"}
                    )
                    bad_marker = True
                    break
            if bad_marker:
                continue

            if str(s.get("execution_mode") or "") != "manual_only":
                deferred.append({"session_id": sid, "failure_type": ft, "reason": "execution_mode_not_manual_only"})
                continue

            if s.get("destructive") is not False:
                deferred.append({"session_id": sid, "failure_type": ft, "reason": "destructive_not_false"})
                continue

            if chk.get("destructive") is not False:
                deferred.append({"session_id": sid, "failure_type": ft, "reason": "checklist_destructive_not_false"})
                continue

            ac = s.get("abort_conditions")
            if not isinstance(ac, list) or len(ac) == 0:
                deferred.append({"session_id": sid, "failure_type": ft, "reason": "missing_abort_conditions"})
                continue

            ev = s.get("evidence_to_capture")
            if not isinstance(ev, list) or len(ev) == 0:
                deferred.append({"session_id": sid, "failure_type": ft, "reason": "missing_evidence_to_capture"})
                continue

            risk = str(chk.get("risk_level") or "medium")
            if risk not in ("low", "medium"):
                risk = "medium"

            rb = bool(s.get("rollback_required"))
            entry = {
                "session_id": sid,
                "failure_type": ft,
                "execution_mode": "manual_only",
                "risk_level": risk,
                "rollback_required": rb,
                "abort_conditions": list(ac),
                "evidence_to_capture": list(ev),
                "priority_key": list(_sort_key(ft, risk, rb)),
            }
            selected.append(entry)

    selected.sort(key=lambda e: _sort_key(str(e["failure_type"]), str(e["risk_level"]), bool(e["rollback_required"])))

    if len(sessions) > 0 and len(selected) == 0:
        blocked_reasons.append("RUN_SELECT_NO_ELIGIBLE_RUNS")
        return _emit(out_resolved, "blocked", selected, deferred, blocked_reasons, warnings, explicit_overwrite)

    sel_status = "review_required" if readiness_status == "review_required" or warnings else "ready"

    return _emit(
        out_resolved,
        sel_status,
        selected,
        deferred,
        blocked_reasons,
        warnings,
        explicit_overwrite,
    )


def _emit(
    out_path: Path,
    selection_status: str,
    selected_runs: list[dict[str, Any]],
    deferred_runs: list[dict[str, Any]],
    blocked_reasons: list[str],
    warnings: list[str],
    explicit_overwrite: bool,
) -> dict[str, Any]:
    body = {
        "selection_schema_version": 1,
        "strict_mode": "laptop_failure_run_selector",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "selection_status": selection_status,
        "selected_runs": selected_runs,
        "deferred_runs": deferred_runs,
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        "warnings": list(dict.fromkeys(warnings)),
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return {
            "selection_status": "blocked",
            "selection_file_path": _SELECTION_REL,
            "warnings": [],
            "errors": ["RUN_SELECT_OUTPUT_TOO_LARGE"],
            "blocked_reasons": ["RUN_SELECT_OUTPUT_TOO_LARGE"],
        }
    try:
        _atomic_write(out_path, text)
    except OSError:
        return {
            "selection_status": "blocked",
            "selection_file_path": _SELECTION_REL,
            "warnings": [],
            "errors": ["RUN_SELECT_WRITE_FAILED"],
            "blocked_reasons": ["RUN_SELECT_WRITE_FAILED"],
        }

    out: dict[str, Any] = dict(body)
    out["selection_file_path"] = _SELECTION_REL
    out["errors"] = list(dict.fromkeys(blocked_reasons)) if selection_status == "blocked" else []
    return out
