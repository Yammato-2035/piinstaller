from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_DRYRUN_REL = "docs/evidence/runtime-results/handoff/validator_dryrun_report.json"
_INDEX_REL = "docs/evidence/runtime-results/handoff/validator_seal_index.json"
_AUDIT_REL = "docs/evidence/runtime-results/handoff/validator_seal_consistency_audit.json"
_TIMELINE_REL = "docs/evidence/runtime-results/handoff/validator_evidence_timeline.json"
_MAX_DRYRUN = 512 * 1024
_MAX_SEAL = 128 * 1024
_MAX_INDEX = 256 * 1024
_MAX_AUDIT = 256 * 1024
_MAX_TIMELINE_OUT = 512 * 1024


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "TIMELINE_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "TIMELINE_PATH_INVALID"
    if ".." in p.parts:
        return None, "TIMELINE_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "TIMELINE_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "TIMELINE_OUTSIDE_HANDOFF"
    return resolved, None


def _path_chain_clean(path: Path) -> bool:
    cur = path
    while True:
        if cur.exists() and cur.is_symlink():
            return False
        if cur.parent == cur:
            break
        cur = cur.parent
    return True


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _parse_sort_key(ts: str, mtime: float) -> float:
    t = str(ts or "").strip()
    if t:
        try:
            if t.endswith("Z"):
                t = t[:-1] + "+00:00"
            return datetime.fromisoformat(t).timestamp()
        except Exception:
            pass
    return float(mtime)


def _event_status_dryrun(data: dict[str, Any]) -> str:
    return "ok" if str(data.get("dryrun_status") or "") == "ok" else "review_required"


def _event_status_seal(data: dict[str, Any]) -> str:
    return "ok" if str(data.get("validator_status") or "") == "ok" else "review_required"


def _event_status_index(data: dict[str, Any]) -> str:
    st = str(data.get("index_status") or "ok")
    return "ok" if st == "ok" else "review_required"


def _event_status_audit(data: dict[str, Any]) -> str:
    try:
        inv = int(data.get("invalid_entries") or 0)
    except Exception:
        inv = 0
    return "ok" if inv == 0 else "review_required"


def build_manual_runtime_evidence_timeline(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    blocked_reasons: list[str] = []
    events: list[dict[str, Any]] = []
    audit_invalid_entries = 0

    def fail(codes: list[str]) -> dict[str, Any]:
        blocked_reasons.extend(c for c in codes if c not in blocked_reasons)
        return {
            "timeline_status": "blocked",
            "timeline_file_path": _TIMELINE_REL,
            "event_count": 0,
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors + blocked_reasons)),
            "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        }

    out_resolved, oerr = _resolve_handoff(_TIMELINE_REL)
    if oerr or out_resolved is None:
        return fail([oerr or "TIMELINE_OUTPUT_PATH_INVALID"])

    if out_resolved.exists() and out_resolved.is_file() and not explicit_overwrite:
        return fail(["TIMELINE_EXISTS_NO_OVERWRITE"])

    _HANDOFF_ROOT.mkdir(parents=True, exist_ok=True)
    if not _path_chain_clean(_HANDOFF_ROOT):
        return fail(["TIMELINE_HANDOFF_SYMLINK_BLOCKED"])

    def add_event(
        *,
        event_type: str,
        rel_path: str,
        max_bytes: int,
    ) -> None:
        nonlocal audit_invalid_entries
        resolved, err = _resolve_handoff(rel_path)
        if err or resolved is None:
            warnings.append(f"timeline_skip:{rel_path}:{err}")
            return
        if not resolved.is_file():
            return
        if not _path_chain_clean(resolved):
            warnings.append(f"timeline_skip_symlink:{Path(rel_path).name}")
            return
        if resolved.stat().st_size > max_bytes:
            warnings.append(f"timeline_skip_too_large:{Path(rel_path).name}")
            return
        try:
            raw = resolved.read_bytes()
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            warnings.append(f"timeline_skip_invalid_json:{Path(rel_path).name}")
            return
        if not isinstance(data, dict):
            warnings.append(f"timeline_skip_invalid_json:{Path(rel_path).name}")
            return

        if event_type == "consistency_audit":
            try:
                audit_invalid_entries = int(data.get("invalid_entries") or 0)
            except Exception:
                audit_invalid_entries = 0

        ts = ""
        if event_type == "dryrun_report":
            ts = str(data.get("created_at") or "")
            st = _event_status_dryrun(data)
        elif event_type == "seal":
            ts = str(data.get("sealed_at") or "")
            st = _event_status_seal(data)
        elif event_type == "seal_index":
            ts = str(data.get("generated_at") or "")
            st = _event_status_index(data)
        else:
            ts = str(data.get("generated_at") or "")
            st = _event_status_audit(data)

        mtime = resolved.stat().st_mtime
        if not ts.strip():
            ts = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        events.append(
            {
                "event_type": event_type,
                "path": rel_path,
                "timestamp": ts,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "status": st,
                "_sort": _parse_sort_key(ts, mtime),
            }
        )

    add_event(event_type="dryrun_report", rel_path=_DRYRUN_REL, max_bytes=_MAX_DRYRUN)
    add_event(event_type="seal_index", rel_path=_INDEX_REL, max_bytes=_MAX_INDEX)
    add_event(event_type="consistency_audit", rel_path=_AUDIT_REL, max_bytes=_MAX_AUDIT)

    for entry in sorted(_HANDOFF_ROOT.iterdir(), key=lambda p: p.name):
        if not entry.is_file() or not entry.name.endswith(".seal.json"):
            continue
        if not _path_chain_clean(entry):
            warnings.append(f"timeline_skip_symlink:{entry.name}")
            continue
        rel = str(entry.resolve(strict=False).relative_to(_REPO_ROOT))
        add_event(event_type="seal", rel_path=rel, max_bytes=_MAX_SEAL)

    events.sort(key=lambda e: (e.get("_sort", 0.0), e.get("path") or ""))
    for e in events:
        e.pop("_sort", None)

    if not events:
        blocked_reasons.append("TIMELINE_NO_VALID_EVENTS")
        return {
            "timeline_status": "blocked",
            "timeline_file_path": _TIMELINE_REL,
            "event_count": 0,
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors + blocked_reasons)),
            "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        }

    any_event_review = any(str(e.get("status")) != "ok" for e in events)
    timeline_status = "ok"
    if audit_invalid_entries > 0:
        timeline_status = "review_required"
    elif any_event_review:
        timeline_status = "review_required"

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body: dict[str, Any] = {
        "timeline_schema_version": 1,
        "strict_mode": "immutable_evidence_timeline",
        "generated_at": generated_at,
        "event_count": len(events),
        "events": events,
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_TIMELINE_OUT:
        return fail(["TIMELINE_OUTPUT_TOO_LARGE"])

    try:
        _atomic_write(out_resolved, text)
    except OSError:
        return fail(["TIMELINE_WRITE_FAILED"])

    return {
        "timeline_status": timeline_status,
        "timeline_file_path": _TIMELINE_REL,
        "event_count": len(events),
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
        "blocked_reasons": [],
    }
