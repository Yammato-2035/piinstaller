from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_SESSIONS_REL = "docs/evidence/runtime-results/handoff/failure_test_sessions.json"
_RESULTS_REL = "docs/evidence/runtime-results/handoff/failure_test_results.json"
_MAX_OUTPUT_BYTES = 512 * 1024


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "FAILURE_RESULT_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "FAILURE_RESULT_PATH_INVALID"
    if ".." in p.parts:
        return None, "FAILURE_RESULT_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "FAILURE_RESULT_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "FAILURE_RESULT_OUTSIDE_HANDOFF"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _result_row_for_session(s: dict[str, Any]) -> dict[str, Any]:
    return {
        "session_id": str(s.get("session_id") or ""),
        "failure_type": str(s.get("failure_type") or ""),
        "execution_mode": "manual_only",
        "operator": "",
        "executed_at": "",
        "observed_status": "review_required",
        "expected_status": "",
        "rollback_performed": False,
        "evidence_collected": [],
        "deviations": [],
        "notes": [],
        "destructive": False,
    }


def capture_manual_runtime_failure_test_results(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    blocked_reasons: list[str] = []

    def fail(codes: list[str]) -> dict[str, Any]:
        blocked_reasons.extend(c for c in codes if c not in blocked_reasons)
        return {
            "capture_status": "blocked",
            "results_file_path": _RESULTS_REL,
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors + blocked_reasons)),
            "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        }

    out_resolved, oerr = _resolve_handoff(_RESULTS_REL)
    if oerr or out_resolved is None:
        return fail([oerr or "FAILURE_RESULT_OUTPUT_PATH_INVALID"])
    if out_resolved.exists() and out_resolved.is_file() and not explicit_overwrite:
        return fail(["FAILURE_RESULT_EXISTS_NO_OVERWRITE"])

    sess_resolved, serr = _resolve_handoff(_SESSIONS_REL)
    if serr or sess_resolved is None:
        return fail([serr or "FAILURE_RESULT_SESSIONS_PATH_INVALID"])
    if not sess_resolved.is_file():
        return fail(["FAILURE_RESULT_SESSIONS_MISSING"])

    try:
        sess_doc = json.loads(sess_resolved.read_text(encoding="utf-8"))
    except Exception:
        return fail(["FAILURE_RESULT_SESSIONS_JSON_INVALID"])
    if not isinstance(sess_doc, dict):
        return fail(["FAILURE_RESULT_SESSIONS_JSON_INVALID"])

    raw_sessions = sess_doc.get("test_sessions")
    if not isinstance(raw_sessions, list) or len(raw_sessions) == 0:
        return fail(["FAILURE_RESULT_SESSIONS_EMPTY"])

    rows: list[dict[str, Any]] = []
    for item in raw_sessions:
        if not isinstance(item, dict):
            return fail(["FAILURE_RESULT_SESSION_ENTRY_INVALID"])
        sid = str(item.get("session_id") or "").strip()
        ft = str(item.get("failure_type") or "").strip()
        if not sid or not ft:
            return fail(["FAILURE_RESULT_SESSION_INCOMPLETE"])
        rows.append(_result_row_for_session(item))

    sess_warnings = sess_doc.get("warnings")
    rev = isinstance(sess_warnings, list) and len(sess_warnings) > 0

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = {
        "results_schema_version": 1,
        "strict_mode": "manual_failure_test_result_capture",
        "generated_at": generated_at,
        "session_results": rows,
        "warnings": list(sess_warnings) if isinstance(sess_warnings, list) else [],
        "blocked_reasons": [],
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return fail(["FAILURE_RESULT_OUTPUT_TOO_LARGE"])

    try:
        _atomic_write(out_resolved, text)
    except OSError:
        return fail(["FAILURE_RESULT_WRITE_FAILED"])

    capture_status = "review_required" if rev else "ok"
    return {
        "capture_status": capture_status,
        "results_file_path": _RESULTS_REL,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
        "blocked_reasons": [],
    }
