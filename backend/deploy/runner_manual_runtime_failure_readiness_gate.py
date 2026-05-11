from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_MATRIX_REL = "docs/evidence/runtime-results/handoff/failure_injection_matrix.json"
_PREVIEW_REL = "docs/evidence/runtime-results/handoff/failure_execution_preview.json"
_CHECKLISTS_REL = "docs/evidence/runtime-results/handoff/failure_operator_checklists.json"
_SESSIONS_REL = "docs/evidence/runtime-results/handoff/failure_test_sessions.json"
_RESULTS_REL = "docs/evidence/runtime-results/handoff/failure_test_results.json"
_EVAL_REL = "docs/evidence/runtime-results/handoff/failure_result_evaluation.json"
_READINESS_REL = "docs/evidence/runtime-results/handoff/failure_test_readiness.json"
_MAX_OUTPUT_BYTES = 256 * 1024

_INPUT_RELS: tuple[str, ...] = (
    _MATRIX_REL,
    _PREVIEW_REL,
    _CHECKLISTS_REL,
    _SESSIONS_REL,
    _RESULTS_REL,
    _EVAL_REL,
)

_FORBIDDEN_PRODUCTIVE_MARKERS = (
    "/dev/nvme0n1",
    "/dev/sda",
    "productive_system_partition",
    "productive_internal_partition",
)


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "READINESS_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "READINESS_PATH_INVALID"
    if ".." in p.parts:
        return None, "READINESS_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "READINESS_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "READINESS_OUTSIDE_HANDOFF"
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
        return None, "READINESS_JSON_INVALID"


def _failure_types_from_cases(items: Any, key: str = "failure_type") -> set[str] | None:
    if not isinstance(items, list):
        return None
    out: set[str] = set()
    for it in items:
        if not isinstance(it, dict):
            return None
        ft = str(it.get(key) or "").strip()
        if not ft:
            return None
        out.add(ft)
    return out


def _collect_destructive_true(obj: Any, path: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            if k == "destructive" and v is True:
                hits.append(p)
            hits.extend(_collect_destructive_true(v, p))
    elif isinstance(obj, list):
        for i, x in enumerate(obj):
            hits.extend(_collect_destructive_true(x, f"{path}[{i}]"))
    return hits


def _eval_implied_status(ev: dict[str, Any]) -> str:
    try:
        m = int(ev.get("mismatching_sessions") or 0)
        r = int(ev.get("review_required_sessions") or 0)
    except Exception:
        return "blocked"
    findings = ev.get("findings")
    if not isinstance(findings, list):
        return "blocked"
    if m > 0 or r > 0 or len(findings) > 0:
        return "review_required"
    return "ok"


def _gather_warnings(*docs: dict[str, Any]) -> list[str]:
    w: list[str] = []
    for d in docs:
        raw = d.get("warnings")
        if isinstance(raw, list):
            for x in raw:
                if isinstance(x, str) and x.strip():
                    w.append(x.strip())
    return list(dict.fromkeys(w))


def _write_readiness_file(
    out_path: Path,
    readiness_status: str,
    findings: list[str],
    warnings: list[str],
    blocked_reasons: list[str],
    checked_failure_types: int,
    checked_sessions: int,
) -> str | None:
    body = {
        "readiness_schema_version": 1,
        "strict_mode": "hardware_failure_test_readiness_gate",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "readiness_status": readiness_status,
        "checked_failure_types": checked_failure_types,
        "checked_sessions": checked_sessions,
        "findings": list(dict.fromkeys(findings)),
        "warnings": list(dict.fromkeys(warnings)),
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return "READINESS_OUTPUT_TOO_LARGE"
    try:
        _atomic_write(out_path, text)
    except OSError:
        return "READINESS_WRITE_FAILED"
    return None


def evaluate_manual_runtime_failure_readiness(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    findings: list[str] = []
    blocked_reasons: list[str] = []
    warnings: list[str] = []
    checked_ft = 0
    checked_sess = 0

    out_resolved, oerr = _resolve_handoff(_READINESS_REL)
    if oerr or out_resolved is None:
        return {
            "readiness_status": "blocked",
            "readiness_file_path": _READINESS_REL,
            "warnings": [],
            "errors": [oerr or "READINESS_OUTPUT_PATH_INVALID"],
            "blocked_reasons": [oerr or "READINESS_OUTPUT_PATH_INVALID"],
        }
    if out_resolved.exists() and out_resolved.is_file() and not explicit_overwrite:
        return {
            "readiness_status": "blocked",
            "readiness_file_path": _READINESS_REL,
            "warnings": [],
            "errors": ["READINESS_EXISTS_NO_OVERWRITE"],
            "blocked_reasons": ["READINESS_EXISTS_NO_OVERWRITE"],
        }

    def finish(
        status: str,
        br: list[str],
        fd: list[str],
        wn: list[str],
        nft: int,
        ns: int,
    ) -> dict[str, Any]:
        werr = _write_readiness_file(out_resolved, status, fd, wn, br, nft, ns)
        if werr:
            return {
                "readiness_status": "blocked",
                "readiness_file_path": _READINESS_REL,
                "warnings": [],
                "errors": [werr],
                "blocked_reasons": [werr],
            }
        return {
            "readiness_status": status,
            "readiness_file_path": _READINESS_REL,
            "warnings": list(dict.fromkeys(wn)),
            "errors": list(dict.fromkeys(br)) if status == "blocked" else [],
            "blocked_reasons": list(dict.fromkeys(br)),
        }

    paths: dict[str, Path] = {}
    for rel in _INPUT_RELS:
        rsv, rerr = _resolve_handoff(rel)
        if rerr or rsv is None:
            blocked_reasons.append(rerr or "READINESS_INPUT_PATH_INVALID")
            return finish("blocked", blocked_reasons, findings, warnings, 0, 0)
        if not rsv.is_file():
            blocked_reasons.append(f"READINESS_ARTIFACT_MISSING:{Path(rel).name}")
            return finish("blocked", blocked_reasons, findings, warnings, 0, 0)
        paths[rel] = rsv

    loaded: dict[str, Any] = {}
    for rel in _INPUT_RELS:
        data, err = _load_json(paths[rel])
        if err or not isinstance(data, dict):
            blocked_reasons.append(f"READINESS_ARTIFACT_JSON_INVALID:{Path(rel).name}")
            return finish("blocked", blocked_reasons, findings, warnings, 0, 0)
        loaded[rel] = data

    matrix = loaded[_MATRIX_REL]
    preview = loaded[_PREVIEW_REL]
    checklists_doc = loaded[_CHECKLISTS_REL]
    sessions_doc = loaded[_SESSIONS_REL]
    results_doc = loaded[_RESULTS_REL]
    eval_doc = loaded[_EVAL_REL]

    blob = json.dumps(loaded, sort_keys=True).lower()
    for marker in _FORBIDDEN_PRODUCTIVE_MARKERS:
        if marker.lower() in blob:
            blocked_reasons.append(f"READINESS_PRODUCTIVE_MARKER:{marker}")
            return finish("blocked", blocked_reasons, findings, warnings, 0, 0)

    for rel, doc in loaded.items():
        if _collect_destructive_true(doc):
            blocked_reasons.append(f"READINESS_DESTRUCTIVE_TRUE:{Path(rel).name}")
            return finish("blocked", blocked_reasons, findings, warnings, 0, 0)

    m_cases = matrix.get("failure_cases")
    p_cases = preview.get("preview_cases")
    c_lists = checklists_doc.get("checklists")
    sessions = sessions_doc.get("test_sessions")
    results = results_doc.get("session_results")

    types_m = _failure_types_from_cases(m_cases)
    types_p = _failure_types_from_cases(p_cases)
    types_c = _failure_types_from_cases(c_lists)
    if types_m is None or types_p is None or types_c is None:
        blocked_reasons.append("READINESS_FAILURE_TYPE_STRUCTURE_INVALID")
        return finish("blocked", blocked_reasons, findings, warnings, 0, 0)

    if not isinstance(sessions, list) or not isinstance(results, list):
        blocked_reasons.append("READINESS_SESSIONS_RESULTS_INVALID")
        return finish("blocked", blocked_reasons, findings, warnings, 0, 0)

    types_s: set[str] = set()
    session_ids: list[str] = []
    for s in sessions:
        if not isinstance(s, dict):
            blocked_reasons.append("READINESS_SESSION_ENTRY_INVALID")
            return finish("blocked", blocked_reasons, findings, warnings, 0, 0)
        sid = str(s.get("session_id") or "").strip()
        ft = str(s.get("failure_type") or "").strip()
        if not sid or not ft:
            blocked_reasons.append("READINESS_SESSION_INCOMPLETE")
            return finish("blocked", blocked_reasons, findings, warnings, 0, 0)
        types_s.add(ft)
        session_ids.append(sid)
        ev_cap = s.get("evidence_to_capture")
        if not isinstance(ev_cap, list) or len(ev_cap) == 0:
            blocked_reasons.append("READINESS_SESSION_EVIDENCE_TO_CAPTURE_MISSING")
            return finish("blocked", blocked_reasons, findings, warnings, 0, 0)
        abort_s = s.get("abort_conditions")
        if not isinstance(abort_s, list) or len(abort_s) == 0:
            blocked_reasons.append("READINESS_SESSION_ABORT_CONDITIONS_MISSING")
            return finish("blocked", blocked_reasons, findings, warnings, 0, 0)

    if len(session_ids) != len(set(session_ids)):
        blocked_reasons.append("READINESS_DUPLICATE_SESSION_ID")
        return finish("blocked", blocked_reasons, findings, warnings, 0, 0)

    types_r: set[str] = set()
    for r in results:
        if not isinstance(r, dict):
            blocked_reasons.append("READINESS_RESULT_ENTRY_INVALID")
            return finish("blocked", blocked_reasons, findings, warnings, 0, 0)
        ft = str(r.get("failure_type") or "").strip()
        if not ft:
            blocked_reasons.append("READINESS_RESULT_INCOMPLETE")
            return finish("blocked", blocked_reasons, findings, warnings, 0, 0)
        types_r.add(ft)
        ev = r.get("evidence_collected")
        if not isinstance(ev, list) or len(ev) == 0:
            blocked_reasons.append("READINESS_RESULT_EVIDENCE_MISSING")
            return finish("blocked", blocked_reasons, findings, warnings, 0, 0)

    if types_m != types_p or types_m != types_c or types_m != types_s or types_m != types_r:
        blocked_reasons.append("READINESS_FAILURE_TYPE_MISMATCH")
        return finish("blocked", blocked_reasons, findings, warnings, 0, 0)

    if isinstance(c_lists, list):
        for cl in c_lists:
            if not isinstance(cl, dict):
                blocked_reasons.append("READINESS_CHECKLIST_ENTRY_INVALID")
                return finish("blocked", blocked_reasons, findings, warnings, 0, 0)
            ac = cl.get("abort_conditions")
            if not isinstance(ac, list) or len(ac) == 0:
                blocked_reasons.append("READINESS_CHECKLIST_ABORT_CONDITIONS_MISSING")
                return finish("blocked", blocked_reasons, findings, warnings, 0, 0)
            re = cl.get("required_evidence")
            if not isinstance(re, list) or len(re) == 0:
                blocked_reasons.append("READINESS_CHECKLIST_REQUIRED_EVIDENCE_MISSING")
                return finish("blocked", blocked_reasons, findings, warnings, 0, 0)

    eval_status = _eval_implied_status(eval_doc)
    if eval_status == "blocked":
        blocked_reasons.append("READINESS_EVALUATION_INVALID_OR_BLOCKED")
        return finish("blocked", blocked_reasons, findings, warnings, 0, 0)

    checked_ft = len(types_m)
    checked_sess = len(sessions)

    warnings.extend(_gather_warnings(matrix, preview, checklists_doc, sessions_doc, results_doc))

    if eval_status == "review_required":
        findings.append("evaluation_review_required")
    if warnings:
        findings.append("upstream_warnings_present")

    if eval_status == "review_required" or warnings:
        readiness_status = "review_required"
    else:
        readiness_status = "ready"

    return finish(readiness_status, blocked_reasons, findings, warnings, checked_ft, checked_sess)
