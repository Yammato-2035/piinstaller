from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_SNAPSHOT_INPUT_REL = "docs/evidence/runtime-results/handoff/validator_evidence_final_snapshot.json"
_ACCEPTANCE_REL = "docs/evidence/runtime-results/handoff/validator_final_acceptance.json"
_MAX_SNAPSHOT_READ_BYTES = 256 * 1024
_MAX_ACCEPTANCE_BYTES = 128 * 1024


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "ACCEPTANCE_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "ACCEPTANCE_PATH_INVALID"
    if ".." in p.parts:
        return None, "ACCEPTANCE_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "ACCEPTANCE_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "ACCEPTANCE_OUTSIDE_HANDOFF"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def evaluate_manual_runtime_final_acceptance(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    blocked_reasons: list[str] = []

    def fail(codes: list[str]) -> dict[str, Any]:
        blocked_reasons.extend(c for c in codes if c not in blocked_reasons)
        return {
            "acceptance_status": "blocked",
            "acceptance_file_path": _ACCEPTANCE_REL,
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors + blocked_reasons)),
            "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        }

    out_resolved, oerr = _resolve_handoff(_ACCEPTANCE_REL)
    if oerr or out_resolved is None:
        return fail([oerr or "ACCEPTANCE_OUTPUT_PATH_INVALID"])

    if out_resolved.exists() and out_resolved.is_file() and not explicit_overwrite:
        return fail(["ACCEPTANCE_EXISTS_NO_OVERWRITE"])

    snap_resolved, serr = _resolve_handoff(_SNAPSHOT_INPUT_REL)
    if serr or snap_resolved is None:
        return fail([serr or "ACCEPTANCE_SNAPSHOT_PATH_INVALID"])

    if not snap_resolved.is_file():
        return fail(["ACCEPTANCE_SNAPSHOT_MISSING"])

    if snap_resolved.stat().st_size > _MAX_SNAPSHOT_READ_BYTES:
        return fail(["ACCEPTANCE_SNAPSHOT_TOO_LARGE"])

    try:
        raw_snap = snap_resolved.read_bytes()
        data = json.loads(raw_snap.decode("utf-8"))
    except Exception:
        return fail(["ACCEPTANCE_SNAPSHOT_JSON_INVALID"])

    if not isinstance(data, dict):
        return fail(["ACCEPTANCE_SNAPSHOT_JSON_INVALID"])

    tl_h = data.get("timeline_sha256")
    sn_h = data.get("snapshot_sha256")
    if not isinstance(tl_h, str) or not tl_h.strip():
        return fail(["ACCEPTANCE_TIMELINE_SHA256_MISSING"])
    if not isinstance(sn_h, str) or not sn_h.strip():
        return fail(["ACCEPTANCE_SNAPSHOT_SHA256_MISSING"])

    try:
        ec = int(data.get("event_count") or 0)
    except Exception:
        ec = 0
    if ec <= 0:
        return fail(["ACCEPTANCE_EVENT_COUNT_INVALID"])

    wo_hash = {k: v for k, v in data.items() if k != "snapshot_sha256"}
    exp_snap_hash = hashlib.sha256(
        json.dumps(wo_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if exp_snap_hash != sn_h.strip().lower():
        return fail(["ACCEPTANCE_SNAPSHOT_SHA256_MISMATCH"])

    tl_path_raw = data.get("timeline_path")
    if not isinstance(tl_path_raw, str) or not tl_path_raw.strip():
        return fail(["ACCEPTANCE_TIMELINE_PATH_MISSING"])

    tl_resolved, terr = _resolve_handoff(tl_path_raw.strip())
    if terr or tl_resolved is None:
        return fail([terr or "ACCEPTANCE_TIMELINE_PATH_INVALID"])

    if not tl_resolved.is_file():
        return fail(["ACCEPTANCE_TIMELINE_MISSING"])

    try:
        raw_tl = tl_resolved.read_bytes()
    except OSError:
        return fail(["ACCEPTANCE_TIMELINE_READ_FAILED"])

    if hashlib.sha256(raw_tl).hexdigest() != tl_h.strip().lower():
        return fail(["ACCEPTANCE_TIMELINE_SHA256_MISMATCH"])

    inner = str(data.get("status") or "")
    if inner == "ok":
        acc_st = "accepted"
    elif inner == "review_required":
        acc_st = "review_required"
    else:
        return fail(["ACCEPTANCE_SNAPSHOT_STATUS_INVALID"])

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = {
        "acceptance_schema_version": 1,
        "strict_mode": "final_evidence_acceptance_gate",
        "generated_at": generated_at,
        "snapshot_path": _SNAPSHOT_INPUT_REL,
        "snapshot_sha256": sn_h.strip(),
        "event_count": ec,
        "acceptance_status": acc_st,
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_ACCEPTANCE_BYTES:
        return fail(["ACCEPTANCE_OUTPUT_TOO_LARGE"])

    try:
        _atomic_write(out_resolved, text)
    except OSError:
        return fail(["ACCEPTANCE_WRITE_FAILED"])

    return {
        "acceptance_status": acc_st,
        "acceptance_file_path": _ACCEPTANCE_REL,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
        "blocked_reasons": [],
    }
