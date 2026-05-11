from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_TIMELINE_REL = "docs/evidence/runtime-results/handoff/validator_evidence_timeline.json"
_SNAPSHOT_REL = "docs/evidence/runtime-results/handoff/validator_evidence_final_snapshot.json"
_MAX_TIMELINE_BYTES = 512 * 1024
_MAX_SNAPSHOT_BYTES = 256 * 1024


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "SNAPSHOT_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "SNAPSHOT_PATH_INVALID"
    if ".." in p.parts:
        return None, "SNAPSHOT_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "SNAPSHOT_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "SNAPSHOT_OUTSIDE_HANDOFF"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def build_manual_runtime_evidence_final_snapshot(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    blocked_reasons: list[str] = []

    def fail(codes: list[str]) -> dict[str, Any]:
        blocked_reasons.extend(c for c in codes if c not in blocked_reasons)
        return {
            "snapshot_status": "blocked",
            "snapshot_file_path": _SNAPSHOT_REL,
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors + blocked_reasons)),
            "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        }

    snap_resolved, serr = _resolve_handoff(_SNAPSHOT_REL)
    if serr or snap_resolved is None:
        return fail([serr or "SNAPSHOT_OUTPUT_PATH_INVALID"])

    if snap_resolved.exists() and snap_resolved.is_file() and not explicit_overwrite:
        return fail(["SNAPSHOT_EXISTS_NO_OVERWRITE"])

    tl_resolved, terr = _resolve_handoff(_TIMELINE_REL)
    if terr or tl_resolved is None:
        return fail([terr or "SNAPSHOT_TIMELINE_PATH_INVALID"])

    if not tl_resolved.is_file():
        return fail(["SNAPSHOT_TIMELINE_MISSING"])

    if tl_resolved.stat().st_size > _MAX_TIMELINE_BYTES:
        return fail(["SNAPSHOT_TIMELINE_TOO_LARGE"])

    try:
        raw = tl_resolved.read_bytes()
        data = json.loads(raw.decode("utf-8"))
    except Exception:
        return fail(["SNAPSHOT_TIMELINE_JSON_INVALID"])

    if not isinstance(data, dict):
        return fail(["SNAPSHOT_TIMELINE_JSON_INVALID"])

    try:
        ec = int(data.get("event_count") or 0)
    except Exception:
        ec = 0
    events = data.get("events")
    if ec <= 0 or not isinstance(events, list) or len(events) == 0:
        return fail(["SNAPSHOT_TIMELINE_NO_EVENTS"])

    inner_status = "ok"
    for ev in events:
        if not isinstance(ev, dict):
            inner_status = "review_required"
            break
        if str(ev.get("status") or "") != "ok":
            inner_status = "review_required"

    timeline_sha256 = hashlib.sha256(raw).hexdigest()
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    body_wo_hash: dict[str, Any] = {
        "snapshot_schema_version": 1,
        "strict_mode": "evidence_final_snapshot",
        "generated_at": generated_at,
        "timeline_path": _TIMELINE_REL,
        "timeline_sha256": timeline_sha256,
        "event_count": ec,
        "status": inner_status,
    }
    snapshot_sha256 = hashlib.sha256(
        json.dumps(body_wo_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    body_full = {**body_wo_hash, "snapshot_sha256": snapshot_sha256}
    text = json.dumps(body_full, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_SNAPSHOT_BYTES:
        return fail(["SNAPSHOT_OUTPUT_TOO_LARGE"])

    try:
        _atomic_write(snap_resolved, text)
    except OSError:
        return fail(["SNAPSHOT_WRITE_FAILED"])

    snap_st = "review_required" if inner_status == "review_required" else "ok"
    return {
        "snapshot_status": snap_st,
        "snapshot_file_path": _SNAPSHOT_REL,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
        "blocked_reasons": [],
    }
