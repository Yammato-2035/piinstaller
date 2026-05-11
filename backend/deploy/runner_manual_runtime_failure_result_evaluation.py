from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_RESULTS_REL = "docs/evidence/runtime-results/handoff/failure_test_results.json"
_SESSIONS_REL = "docs/evidence/runtime-results/handoff/failure_test_sessions.json"
_PREVIEW_REL = "docs/evidence/runtime-results/handoff/failure_execution_preview.json"
_EVAL_REL = "docs/evidence/runtime-results/handoff/failure_result_evaluation.json"
_MAX_OUTPUT_BYTES = 512 * 1024

_VALID_STATUS = frozenset({"ok", "review_required", "blocked"})


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "FAILURE_EVAL_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "FAILURE_EVAL_PATH_INVALID"
    if ".." in p.parts:
        return None, "FAILURE_EVAL_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "FAILURE_EVAL_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "FAILURE_EVAL_OUTSIDE_HANDOFF"
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
        return None, "FAILURE_EVAL_JSON_INVALID"


def evaluate_manual_runtime_failure_results(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    blocked_reasons: list[str] = []

    def fail(codes: list[str]) -> dict[str, Any]:
        blocked_reasons.extend(c for c in codes if c not in blocked_reasons)
        return {
            "evaluation_status": "blocked",
            "evaluation_file_path": _EVAL_REL,
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors + blocked_reasons)),
            "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        }

    out_resolved, oerr = _resolve_handoff(_EVAL_REL)
    if oerr or out_resolved is None:
        return fail([oerr or "FAILURE_EVAL_OUTPUT_PATH_INVALID"])
    if out_resolved.exists() and out_resolved.is_file() and not explicit_overwrite:
        return fail(["FAILURE_EVAL_EXISTS_NO_OVERWRITE"])

    for rel in (_RESULTS_REL, _SESSIONS_REL, _PREVIEW_REL):
        rsv, rerr = _resolve_handoff(rel)
        if rerr or rsv is None:
            return fail([rerr or "FAILURE_EVAL_INPUT_PATH_INVALID"])
        if not rsv.is_file():
            return fail([f"FAILURE_EVAL_INPUT_MISSING:{Path(rel).name}"])

    res_path = _resolve_handoff(_RESULTS_REL)[0]
    ses_path = _resolve_handoff(_SESSIONS_REL)[0]
    prv_path = _resolve_handoff(_PREVIEW_REL)[0]
    assert res_path and ses_path and prv_path

    res_doc, e1 = _load_json(res_path)
    ses_doc, e2 = _load_json(ses_path)
    prv_doc, e3 = _load_json(prv_path)
    if e1 or e2 or e3 or not isinstance(res_doc, dict) or not isinstance(ses_doc, dict) or not isinstance(prv_doc, dict):
        return fail(["FAILURE_EVAL_JSON_INVALID"])

    sessions = ses_doc.get("test_sessions")
    results = res_doc.get("session_results")
    preview_cases = prv_doc.get("preview_cases")
    if not isinstance(sessions, list) or not isinstance(results, list) or not isinstance(preview_cases, list):
        return fail(["FAILURE_EVAL_STRUCTURE_INVALID"])
    if len(sessions) == 0:
        return fail(["FAILURE_EVAL_SESSIONS_EMPTY"])
    if len(sessions) != len(results):
        return fail(["FAILURE_EVAL_SESSION_RESULT_COUNT_MISMATCH"])

    preview_by_ft: dict[str, str] = {}
    for pc in preview_cases:
        if not isinstance(pc, dict):
            return fail(["FAILURE_EVAL_PREVIEW_CASE_INVALID"])
        ft = str(pc.get("failure_type") or "").strip()
        if not ft:
            return fail(["FAILURE_EVAL_PREVIEW_CASE_INVALID"])
        ers = str(pc.get("expected_runtime_status") or "").strip()
        preview_by_ft[ft] = ers if ers in _VALID_STATUS else "review_required"

    results_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for r in results:
        if not isinstance(r, dict):
            return fail(["FAILURE_EVAL_RESULT_ENTRY_INVALID"])
        sid = str(r.get("session_id") or "").strip()
        ft = str(r.get("failure_type") or "").strip()
        if not sid or not ft:
            return fail(["FAILURE_EVAL_RESULT_INCOMPLETE"])
        results_by_key[(sid, ft)] = r

    findings: list[dict[str, Any]] = []
    any_blocked = False

    for s in sessions:
        if not isinstance(s, dict):
            return fail(["FAILURE_EVAL_SESSION_ENTRY_INVALID"])
        sid = str(s.get("session_id") or "").strip()
        ft = str(s.get("failure_type") or "").strip()
        if not sid or not ft:
            return fail(["FAILURE_EVAL_SESSION_INCOMPLETE"])

        r = results_by_key.get((sid, ft))
        if r is None:
            return fail(["FAILURE_EVAL_RESULT_ROW_MISSING"])

        if ft not in preview_by_ft:
            findings.append(
                {"session_id": sid, "failure_type": ft, "finding": "failure_type_not_in_preview", "severity": "blocked"}
            )
            any_blocked = True
            continue

        if r.get("destructive") is not False:
            findings.append(
                {"session_id": sid, "failure_type": ft, "finding": "destructive_must_be_false", "severity": "blocked"}
            )
            any_blocked = True
            continue

        obs = str(r.get("observed_status") or "").strip()
        exp = str(r.get("expected_status") or "").strip()
        if not obs or not exp or obs not in _VALID_STATUS or exp not in _VALID_STATUS:
            findings.append(
                {"session_id": sid, "failure_type": ft, "finding": "missing_or_invalid_status_fields", "severity": "blocked"}
            )
            any_blocked = True
            continue

        ev = r.get("evidence_collected")
        if not isinstance(ev, list) or len(ev) == 0:
            findings.append(
                {
                    "session_id": sid,
                    "failure_type": ft,
                    "finding": "evidence_collected_missing_or_empty",
                    "severity": "blocked",
                }
            )
            any_blocked = True
            continue

        dev = r.get("deviations")
        if not isinstance(dev, list):
            findings.append(
                {"session_id": sid, "failure_type": ft, "finding": "deviations_not_a_list", "severity": "blocked"}
            )
            any_blocked = True
            continue

        if not isinstance(r.get("rollback_performed"), bool):
            findings.append(
                {
                    "session_id": sid,
                    "failure_type": ft,
                    "finding": "rollback_performed_not_boolean",
                    "severity": "blocked",
                }
            )
            any_blocked = True
            continue

    if any_blocked:
        return fail(["FAILURE_EVAL_SESSION_VALIDATION_BLOCKED"])

    matching = 0
    mismatching = 0
    review_required_sessions = 0
    findings = []

    for s in sessions:
        sid = str(s.get("session_id") or "").strip()
        ft = str(s.get("failure_type") or "").strip()
        r = results_by_key[(sid, ft)]
        preview_exp = preview_by_ft[ft]
        obs = str(r.get("observed_status") or "").strip()
        exp = str(r.get("expected_status") or "").strip()
        dev: list[Any] = r.get("deviations")  # type: ignore[assignment]
        rb_sess = bool(s.get("rollback_required"))
        rb_res = bool(r.get("rollback_performed"))

        if obs == "review_required":
            review_required_sessions += 1

        if exp != preview_exp:
            findings.append(
                {
                    "session_id": sid,
                    "failure_type": ft,
                    "finding": "expected_status_differs_from_preview_rule",
                    "severity": "review_required",
                }
            )

        if rb_sess and not rb_res:
            findings.append(
                {
                    "session_id": sid,
                    "failure_type": ft,
                    "finding": "rollback_required_but_not_performed",
                    "severity": "review_required",
                }
            )

        if len(dev) > 0:
            findings.append(
                {"session_id": sid, "failure_type": ft, "finding": "deviations_present", "severity": "review_required"}
            )

        if obs != exp:
            mismatching += 1
            findings.append(
                {"session_id": sid, "failure_type": ft, "finding": "observed_status_mismatch", "severity": "review_required"}
            )
        else:
            matching += 1

    has_review = any(f.get("severity") == "review_required" for f in findings)
    if mismatching > 0 or review_required_sessions > 0 or has_review:
        eval_st = "review_required"
    else:
        eval_st = "ok"

    total = len(sessions)
    body = {
        "evaluation_schema_version": 1,
        "strict_mode": "failure_result_evaluation",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_sessions": total,
        "matching_sessions": matching,
        "mismatching_sessions": mismatching,
        "review_required_sessions": review_required_sessions,
        "findings": findings,
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return fail(["FAILURE_EVAL_OUTPUT_TOO_LARGE"])

    try:
        _atomic_write(out_resolved, text)
    except OSError:
        return fail(["FAILURE_EVAL_WRITE_FAILED"])

    return {
        "evaluation_status": eval_st,
        "evaluation_file_path": _EVAL_REL,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
        "blocked_reasons": [],
    }
