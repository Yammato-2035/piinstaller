from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_CHECKLIST_REL = "docs/evidence/runtime-results/handoff/failure_operator_checklists.json"
_SESSIONS_REL = "docs/evidence/runtime-results/handoff/failure_test_sessions.json"
_MAX_OUTPUT_BYTES = 512 * 1024


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "FAILURE_SESSION_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "FAILURE_SESSION_PATH_INVALID"
    if ".." in p.parts:
        return None, "FAILURE_SESSION_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "FAILURE_SESSION_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "FAILURE_SESSION_OUTSIDE_HANDOFF"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _build_session(cl: dict[str, Any]) -> dict[str, Any]:
    failure_type = str(cl.get("failure_type") or "")
    risk = str(cl.get("risk_level") or "low")
    if risk not in ("low", "medium"):
        risk = "medium" if bool(cl.get("rollback_required")) else "low"
    rollback_required = bool(cl.get("rollback_required"))
    required_media = cl.get("required_media")
    if not isinstance(required_media, list):
        required_media = ["external_usb_test_drive", "test_nvme_or_vm_disk"]
    op_chk = cl.get("operator_checklist")
    operator_steps = list(op_chk) if isinstance(op_chk, list) else []
    if not operator_steps:
        operator_steps = ["Confirm dedicated test media only; abort if target is unknown."]
    req_ev = cl.get("required_evidence")
    evidence_to_capture = list(req_ev) if isinstance(req_ev, list) else ["operator_log"]
    abort = cl.get("abort_conditions")
    abort_conditions = list(abort) if isinstance(abort, list) else ["abort_on_unknown_target"]

    session_id = f"manual_failure_ts_v1_{failure_type}"

    return {
        "session_id": session_id,
        "failure_type": failure_type,
        "execution_mode": "manual_only",
        "risk_level": risk,
        "destructive": False,
        "rollback_required": rollback_required,
        "required_media": required_media,
        "operator_steps": operator_steps,
        "evidence_to_capture": evidence_to_capture,
        "abort_conditions": abort_conditions,
        "expected_final_state": [
            "detection_matches_expected_runtime_outcome",
            "no_write_to_productive_or_internal_os_media",
            "session_evidence_bundle_complete",
        ],
    }


def build_manual_runtime_failure_test_sessions(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    blocked_reasons: list[str] = []

    def fail(codes: list[str]) -> dict[str, Any]:
        blocked_reasons.extend(c for c in codes if c not in blocked_reasons)
        return {
            "sessions_status": "blocked",
            "sessions_file_path": _SESSIONS_REL,
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors + blocked_reasons)),
            "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        }

    out_resolved, oerr = _resolve_handoff(_SESSIONS_REL)
    if oerr or out_resolved is None:
        return fail([oerr or "FAILURE_SESSION_OUTPUT_PATH_INVALID"])
    if out_resolved.exists() and out_resolved.is_file() and not explicit_overwrite:
        return fail(["FAILURE_SESSION_EXISTS_NO_OVERWRITE"])

    chk_resolved, cerr = _resolve_handoff(_CHECKLIST_REL)
    if cerr or chk_resolved is None:
        return fail([cerr or "FAILURE_SESSION_CHECKLIST_PATH_INVALID"])
    if not chk_resolved.is_file():
        return fail(["FAILURE_SESSION_CHECKLIST_MISSING"])

    try:
        checklist_doc = json.loads(chk_resolved.read_text(encoding="utf-8"))
    except Exception:
        return fail(["FAILURE_SESSION_CHECKLIST_JSON_INVALID"])
    if not isinstance(checklist_doc, dict):
        return fail(["FAILURE_SESSION_CHECKLIST_JSON_INVALID"])

    raw_lists = checklist_doc.get("checklists")
    if not isinstance(raw_lists, list) or len(raw_lists) == 0:
        return fail(["FAILURE_SESSION_CHECKLISTS_MISSING"])

    sessions: list[dict[str, Any]] = []
    for item in raw_lists:
        if not isinstance(item, dict):
            return fail(["FAILURE_SESSION_CHECKLIST_ENTRY_INVALID"])
        sessions.append(_build_session(item))

    checklist_warnings = checklist_doc.get("warnings")
    rev = isinstance(checklist_warnings, list) and len(checklist_warnings) > 0

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = {
        "sessions_schema_version": 1,
        "strict_mode": "manual_failure_test_sessions",
        "generated_at": generated_at,
        "test_sessions": sessions,
        "warnings": list(checklist_warnings) if isinstance(checklist_warnings, list) else [],
        "blocked_reasons": [],
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return fail(["FAILURE_SESSION_OUTPUT_TOO_LARGE"])

    try:
        _atomic_write(out_resolved, text)
    except OSError:
        return fail(["FAILURE_SESSION_WRITE_FAILED"])

    sessions_status = "review_required" if rev else "ok"
    return {
        "sessions_status": sessions_status,
        "sessions_file_path": _SESSIONS_REL,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
        "blocked_reasons": [],
    }
