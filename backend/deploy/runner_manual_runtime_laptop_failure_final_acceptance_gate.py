from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_SNAPSHOT_REL = "docs/evidence/runtime-results/handoff/laptop_failure_final_snapshot.json"
_ACCEPTANCE_REL = "docs/evidence/runtime-results/handoff/laptop_failure_final_acceptance.json"
_MAX_OUTPUT_BYTES = 128 * 1024


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "FINAL_ACCEPTANCE_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "FINAL_ACCEPTANCE_PATH_INVALID"
    if ".." in p.parts:
        return None, "FINAL_ACCEPTANCE_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "FINAL_ACCEPTANCE_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "FINAL_ACCEPTANCE_OUTSIDE_HANDOFF"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _canonical_without_snapshot_sha256(doc: dict[str, Any]) -> bytes:
    cpy = dict(doc)
    cpy.pop("snapshot_sha256", None)
    return json.dumps(cpy, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def evaluate_manual_laptop_failure_final_acceptance(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    blocked_reasons: list[str] = []

    out_path, oerr = _resolve_handoff(_ACCEPTANCE_REL)
    if oerr or out_path is None:
        return {
            "acceptance_status": "blocked",
            "acceptance_file_path": _ACCEPTANCE_REL,
            "warnings": [],
            "errors": [oerr or "FINAL_ACCEPTANCE_OUTPUT_PATH_INVALID"],
            "blocked_reasons": [oerr or "FINAL_ACCEPTANCE_OUTPUT_PATH_INVALID"],
        }
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return {
            "acceptance_status": "blocked",
            "acceptance_file_path": _ACCEPTANCE_REL,
            "warnings": [],
            "errors": ["FINAL_ACCEPTANCE_EXISTS_NO_OVERWRITE"],
            "blocked_reasons": ["FINAL_ACCEPTANCE_EXISTS_NO_OVERWRITE"],
        }

    snapshot_path, serr = _resolve_handoff(_SNAPSHOT_REL)
    if serr or snapshot_path is None or not snapshot_path.is_file():
        blocked_reasons.append("FINAL_ACCEPTANCE_SNAPSHOT_INPUT_MISSING")
        return _emit(out_path, "blocked", "", "", 0, blocked_reasons, warnings)

    try:
        raw = snapshot_path.read_bytes()
    except OSError:
        blocked_reasons.append("FINAL_ACCEPTANCE_SNAPSHOT_READ_FAILED")
        return _emit(out_path, "blocked", "", "", 0, blocked_reasons, warnings)

    try:
        snap = json.loads(raw.decode("utf-8"))
    except Exception:
        blocked_reasons.append("FINAL_ACCEPTANCE_SNAPSHOT_JSON_INVALID")
        return _emit(out_path, "blocked", "", "", 0, blocked_reasons, warnings)
    if not isinstance(snap, dict):
        blocked_reasons.append("FINAL_ACCEPTANCE_SNAPSHOT_STRUCTURE_INVALID")
        return _emit(out_path, "blocked", "", "", 0, blocked_reasons, warnings)

    snap_hash = str(snap.get("snapshot_sha256") or "")
    if not snap_hash:
        blocked_reasons.append("FINAL_ACCEPTANCE_SNAPSHOT_SHA_MISSING")
    expected_hash = hashlib.sha256(_canonical_without_snapshot_sha256(snap)).hexdigest()
    if snap_hash != expected_hash:
        blocked_reasons.append("FINAL_ACCEPTANCE_SNAPSHOT_SHA_MISMATCH")

    timeline_sha = str(snap.get("timeline_sha256") or "")
    if not timeline_sha:
        blocked_reasons.append("FINAL_ACCEPTANCE_TIMELINE_SHA_MISSING")
    event_count = int(snap.get("event_count") or 0)
    if event_count <= 0:
        blocked_reasons.append("FINAL_ACCEPTANCE_EVENT_COUNT_INVALID")

    snap_status = str(snap.get("snapshot_status") or "")
    acceptance_status = "blocked"
    if not blocked_reasons:
        if snap_status == "ok":
            acceptance_status = "accepted"
        elif snap_status == "review_required":
            acceptance_status = "review_required"
        elif snap_status == "blocked":
            acceptance_status = "blocked"
        else:
            blocked_reasons.append("FINAL_ACCEPTANCE_SNAPSHOT_STATUS_INVALID")
            acceptance_status = "blocked"

    return _emit(
        out_path,
        acceptance_status,
        _SNAPSHOT_REL,
        snap_hash or expected_hash,
        event_count,
        blocked_reasons,
        warnings,
    )


def _emit(
    out_path: Path,
    acceptance_status: str,
    snapshot_path: str,
    snapshot_sha256: str,
    event_count: int,
    blocked_reasons: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    body = {
        "acceptance_schema_version": 1,
        "strict_mode": "laptop_failure_final_acceptance_gate",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "snapshot_path": snapshot_path,
        "snapshot_sha256": snapshot_sha256,
        "event_count": event_count,
        "acceptance_status": acceptance_status,
        "warnings": list(dict.fromkeys(warnings)),
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return {
            "acceptance_status": "blocked",
            "acceptance_file_path": _ACCEPTANCE_REL,
            "warnings": [],
            "errors": ["FINAL_ACCEPTANCE_OUTPUT_TOO_LARGE"],
            "blocked_reasons": ["FINAL_ACCEPTANCE_OUTPUT_TOO_LARGE"],
        }
    try:
        _atomic_write(out_path, text)
    except OSError:
        return {
            "acceptance_status": "blocked",
            "acceptance_file_path": _ACCEPTANCE_REL,
            "warnings": [],
            "errors": ["FINAL_ACCEPTANCE_WRITE_FAILED"],
            "blocked_reasons": ["FINAL_ACCEPTANCE_WRITE_FAILED"],
        }
    out = dict(body)
    out["acceptance_file_path"] = _ACCEPTANCE_REL
    out["errors"] = list(dict.fromkeys(blocked_reasons)) if acceptance_status == "blocked" else []
    return out
