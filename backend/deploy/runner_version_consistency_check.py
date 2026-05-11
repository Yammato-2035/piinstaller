from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_VERSION_STATE_REL = "docs/evidence/runtime-results/handoff/version_state.json"
_TRACKING_REL = "docs/evidence/runtime-results/handoff/phase_release_tracking.json"
_OUT_REL = "docs/evidence/runtime-results/handoff/version_consistency_check.json"
_MAX_OUTPUT_BYTES = 256 * 1024


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "VERSION_CONSISTENCY_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute() or ".." in p.parts:
        return None, "VERSION_CONSISTENCY_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "VERSION_CONSISTENCY_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "VERSION_CONSISTENCY_OUTSIDE_HANDOFF"
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
        return None, "VERSION_CONSISTENCY_JSON_INVALID"


def _parse(v: str) -> tuple[int, int, int] | None:
    parts = str(v).split(".")
    if len(parts) != 3:
        return None
    try:
        return int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return None


def check_version_consistency(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    blocked_reasons: list[str] = []
    out_path, oerr = _resolve_handoff(_OUT_REL)
    if oerr or out_path is None:
        return _ret("blocked", {}, [oerr or "VERSION_CONSISTENCY_OUTPUT_PATH_INVALID"], [])
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _ret("blocked", {}, ["VERSION_CONSISTENCY_EXISTS_NO_OVERWRITE"], [])

    vpath, verr = _resolve_handoff(_VERSION_STATE_REL)
    tpath, terr = _resolve_handoff(_TRACKING_REL)
    if verr or vpath is None or not vpath.is_file():
        blocked_reasons.append("VERSION_CONSISTENCY_VERSION_STATE_MISSING")
    if terr or tpath is None or not tpath.is_file():
        blocked_reasons.append("VERSION_CONSISTENCY_TRACKING_MISSING")
    if blocked_reasons:
        return _emit(out_path, "blocked", {}, blocked_reasons, warnings)

    vs, e1 = _load_json(vpath)
    tr, e2 = _load_json(tpath)
    if e1 or e2 or not isinstance(vs, dict) or not isinstance(tr, dict):
        blocked_reasons.append("VERSION_CONSISTENCY_JSON_INVALID")
        return _emit(out_path, "blocked", {}, blocked_reasons, warnings)

    cur = str(vs.get("current_version") or "")
    prev = str(vs.get("previous_version") or "")
    curp = _parse(cur)
    prevp = _parse(prev)
    if curp is None or prevp is None:
        blocked_reasons.append("VERSION_CONSISTENCY_VERSION_INVALID")
    elif curp <= prevp:
        blocked_reasons.append("VERSION_CONSISTENCY_VERSION_NOT_INCREASED")

    phase = str(vs.get("strict_mode_phase") or "")
    phase_status = str(vs.get("phase_status") or "")
    test_status = str(vs.get("test_status") or "")
    release_readiness = str(vs.get("release_readiness") or "")
    if test_status not in ("green", "yellow", "red"):
        blocked_reasons.append("VERSION_CONSISTENCY_TEST_STATUS_INVALID")
    if release_readiness not in ("internal_testing", "staging", "production_ready"):
        blocked_reasons.append("VERSION_CONSISTENCY_RELEASE_READINESS_INVALID")

    tracked = tr.get("tracked_phases")
    if not isinstance(tracked, list):
        blocked_reasons.append("VERSION_CONSISTENCY_TRACKING_INVALID")
        tracked = []
    match = None
    for it in tracked:
        if isinstance(it, dict) and str(it.get("phase_name") or "") == phase:
            match = it
            break
    if phase_status == "completed":
        if match is None:
            blocked_reasons.append("VERSION_CONSISTENCY_PHASE_NOT_TRACKED")
        else:
            if str(match.get("version") or "") != cur:
                blocked_reasons.append("VERSION_CONSISTENCY_TRACKING_VERSION_MISMATCH")
            if str(match.get("test_status") or "") != test_status:
                blocked_reasons.append("VERSION_CONSISTENCY_TRACKING_TEST_STATUS_MISMATCH")

    check_status = "ok" if not blocked_reasons else "blocked"
    body = {
        "check_schema_version": 1,
        "strict_mode": "version_consistency_check",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "check_status": check_status,
        "current_version": cur,
        "previous_version": prev,
        "phase": phase,
        "test_status": test_status,
        "release_readiness": release_readiness,
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
    }
    return _emit(out_path, check_status, body, blocked_reasons, warnings)


def _emit(out_path: Path, check_status: str, body: dict[str, Any], blocked_reasons: list[str], warnings: list[str]) -> dict[str, Any]:
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _ret("blocked", {}, ["VERSION_CONSISTENCY_OUTPUT_TOO_LARGE"], [])
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _ret("blocked", {}, ["VERSION_CONSISTENCY_WRITE_FAILED"], [])
    return _ret(check_status, body, blocked_reasons if check_status == "blocked" else [], warnings)


def _ret(check_status: str, body: dict[str, Any], blocked_reasons: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "check_status": check_status,
        "check_file_path": _OUT_REL,
        "check": body,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(blocked_reasons)) if check_status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
    }
