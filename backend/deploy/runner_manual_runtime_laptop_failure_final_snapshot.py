from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_TIMELINE_REL = "docs/evidence/runtime-results/handoff/laptop_failure_evidence_timeline.json"
_SNAPSHOT_REL = "docs/evidence/runtime-results/handoff/laptop_failure_final_snapshot.json"
_MAX_OUTPUT_BYTES = 256 * 1024


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "FINAL_SNAPSHOT_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "FINAL_SNAPSHOT_PATH_INVALID"
    if ".." in p.parts:
        return None, "FINAL_SNAPSHOT_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "FINAL_SNAPSHOT_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "FINAL_SNAPSHOT_OUTSIDE_HANDOFF"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _canonical_without_snapshot_sha256(body: dict[str, Any]) -> bytes:
    cpy = dict(body)
    cpy.pop("snapshot_sha256", None)
    return json.dumps(cpy, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def build_manual_laptop_failure_final_snapshot(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    blocked_reasons: list[str] = []

    out_path, oerr = _resolve_handoff(_SNAPSHOT_REL)
    if oerr or out_path is None:
        return {
            "snapshot_status": "blocked",
            "snapshot_file_path": _SNAPSHOT_REL,
            "warnings": [],
            "errors": [oerr or "FINAL_SNAPSHOT_OUTPUT_PATH_INVALID"],
            "blocked_reasons": [oerr or "FINAL_SNAPSHOT_OUTPUT_PATH_INVALID"],
        }
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return {
            "snapshot_status": "blocked",
            "snapshot_file_path": _SNAPSHOT_REL,
            "warnings": [],
            "errors": ["FINAL_SNAPSHOT_EXISTS_NO_OVERWRITE"],
            "blocked_reasons": ["FINAL_SNAPSHOT_EXISTS_NO_OVERWRITE"],
        }

    timeline_path, terr = _resolve_handoff(_TIMELINE_REL)
    if terr or timeline_path is None or not timeline_path.is_file():
        blocked_reasons.append("FINAL_SNAPSHOT_TIMELINE_INPUT_MISSING")
        return _emit(out_path, "blocked", "", "", 0, blocked_reasons, warnings)

    try:
        raw = timeline_path.read_bytes()
    except OSError:
        blocked_reasons.append("FINAL_SNAPSHOT_TIMELINE_READ_FAILED")
        return _emit(out_path, "blocked", "", "", 0, blocked_reasons, warnings)

    try:
        timeline = json.loads(raw.decode("utf-8"))
    except Exception:
        blocked_reasons.append("FINAL_SNAPSHOT_TIMELINE_JSON_INVALID")
        return _emit(out_path, "blocked", "", "", 0, blocked_reasons, warnings)
    if not isinstance(timeline, dict):
        blocked_reasons.append("FINAL_SNAPSHOT_TIMELINE_STRUCTURE_INVALID")
        return _emit(out_path, "blocked", "", "", 0, blocked_reasons, warnings)

    events = timeline.get("events")
    if not isinstance(events, list) or len(events) == 0:
        blocked_reasons.append("FINAL_SNAPSHOT_EVENTS_EMPTY")
        return _emit(out_path, "blocked", "", "", 0, blocked_reasons, warnings)
    status = str(timeline.get("timeline_status") or "")
    if status not in ("ok", "review_required", "blocked"):
        blocked_reasons.append("FINAL_SNAPSHOT_TIMELINE_STATUS_INVALID")
        status = "blocked"

    timeline_sha256 = hashlib.sha256(raw).hexdigest()
    return _emit(
        out_path,
        status,
        _TIMELINE_REL,
        timeline_sha256,
        len(events),
        blocked_reasons,
        warnings,
    )


def _emit(
    out_path: Path,
    snapshot_status: str,
    timeline_path: str,
    timeline_sha256: str,
    event_count: int,
    blocked_reasons: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "snapshot_schema_version": 1,
        "strict_mode": "laptop_failure_final_snapshot",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "timeline_path": timeline_path,
        "timeline_sha256": timeline_sha256,
        "event_count": event_count,
        "snapshot_status": snapshot_status,
        "warnings": list(dict.fromkeys(warnings)),
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
    }
    payload["snapshot_sha256"] = hashlib.sha256(_canonical_without_snapshot_sha256(payload)).hexdigest()
    text = json.dumps(payload, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return {
            "snapshot_status": "blocked",
            "snapshot_file_path": _SNAPSHOT_REL,
            "warnings": [],
            "errors": ["FINAL_SNAPSHOT_OUTPUT_TOO_LARGE"],
            "blocked_reasons": ["FINAL_SNAPSHOT_OUTPUT_TOO_LARGE"],
        }
    try:
        _atomic_write(out_path, text)
    except OSError:
        return {
            "snapshot_status": "blocked",
            "snapshot_file_path": _SNAPSHOT_REL,
            "warnings": [],
            "errors": ["FINAL_SNAPSHOT_WRITE_FAILED"],
            "blocked_reasons": ["FINAL_SNAPSHOT_WRITE_FAILED"],
        }
    out = dict(payload)
    out["snapshot_file_path"] = _SNAPSHOT_REL
    out["errors"] = list(dict.fromkeys(blocked_reasons)) if snapshot_status == "blocked" else []
    return out
