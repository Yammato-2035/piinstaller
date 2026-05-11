from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_EXPORT_REL = "docs/evidence/runtime-results/handoff/laptop_failure_final_export_package.json"
_FINAL_REPORT_REL = "docs/evidence/runtime-results/handoff/laptop_failure_final_report.json"
_SUMMARY_REL = "docs/evidence/runtime-results/handoff/laptop_failure_test_summary.json"
_VALIDATION_REL = "docs/evidence/runtime-results/handoff/laptop_failure_execution_log_validation.json"
_EXEC_LOG_REL = "docs/evidence/runtime-results/handoff/laptop_failure_execution_log.json"
_TIMELINE_REL = "docs/evidence/runtime-results/handoff/laptop_failure_evidence_timeline.json"
_MAX_OUTPUT_BYTES = 512 * 1024


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "EVIDENCE_TIMELINE_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "EVIDENCE_TIMELINE_PATH_INVALID"
    if ".." in p.parts:
        return None, "EVIDENCE_TIMELINE_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "EVIDENCE_TIMELINE_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "EVIDENCE_TIMELINE_OUTSIDE_HANDOFF"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _parse_timestamp(doc: dict[str, Any]) -> str:
    ts = doc.get("generated_at")
    return str(ts) if isinstance(ts, str) else ""


def _emit(
    out_path: Path,
    timeline_status: str,
    events: list[dict[str, Any]],
    blocked_reasons: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    body = {
        "timeline_schema_version": 1,
        "strict_mode": "laptop_failure_evidence_timeline",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "timeline_status": timeline_status,
        "events": events,
        "warnings": list(dict.fromkeys(warnings)),
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return {
            "timeline_status": "blocked",
            "timeline_file_path": _TIMELINE_REL,
            "warnings": [],
            "errors": ["EVIDENCE_TIMELINE_OUTPUT_TOO_LARGE"],
            "blocked_reasons": ["EVIDENCE_TIMELINE_OUTPUT_TOO_LARGE"],
        }
    try:
        _atomic_write(out_path, text)
    except OSError:
        return {
            "timeline_status": "blocked",
            "timeline_file_path": _TIMELINE_REL,
            "warnings": [],
            "errors": ["EVIDENCE_TIMELINE_WRITE_FAILED"],
            "blocked_reasons": ["EVIDENCE_TIMELINE_WRITE_FAILED"],
        }
    out: dict[str, Any] = dict(body)
    out["timeline_file_path"] = _TIMELINE_REL
    out["errors"] = list(dict.fromkeys(blocked_reasons)) if timeline_status == "blocked" else []
    return out


def build_manual_laptop_failure_evidence_timeline(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    blocked_reasons: list[str] = []

    out_resolved, oerr = _resolve_handoff(_TIMELINE_REL)
    if oerr or out_resolved is None:
        return {
            "timeline_status": "blocked",
            "timeline_file_path": _TIMELINE_REL,
            "warnings": [],
            "errors": [oerr or "EVIDENCE_TIMELINE_OUTPUT_PATH_INVALID"],
            "blocked_reasons": [oerr or "EVIDENCE_TIMELINE_OUTPUT_PATH_INVALID"],
        }
    if out_resolved.exists() and out_resolved.is_file() and not explicit_overwrite:
        return {
            "timeline_status": "blocked",
            "timeline_file_path": _TIMELINE_REL,
            "warnings": [],
            "errors": ["EVIDENCE_TIMELINE_EXISTS_NO_OVERWRITE"],
            "blocked_reasons": ["EVIDENCE_TIMELINE_EXISTS_NO_OVERWRITE"],
        }

    rels = [_EXPORT_REL, _FINAL_REPORT_REL, _SUMMARY_REL, _VALIDATION_REL, _EXEC_LOG_REL]
    docs: dict[str, dict[str, Any]] = {}
    raws: dict[str, bytes] = {}
    for rel in rels:
        p, err = _resolve_handoff(rel)
        if err or p is None or not p.is_file():
            blocked_reasons.append(f"EVIDENCE_TIMELINE_INPUT_MISSING:{Path(rel).name}")
            return _emit(out_resolved, "blocked", [], blocked_reasons, warnings)
        try:
            raw = p.read_bytes()
        except OSError:
            blocked_reasons.append(f"EVIDENCE_TIMELINE_INPUT_READ_FAILED:{Path(rel).name}")
            return _emit(out_resolved, "blocked", [], blocked_reasons, warnings)
        try:
            doc = json.loads(raw.decode("utf-8"))
        except Exception:
            blocked_reasons.append(f"EVIDENCE_TIMELINE_JSON_INVALID:{Path(rel).name}")
            return _emit(out_resolved, "blocked", [], blocked_reasons, warnings)
        if not isinstance(doc, dict):
            blocked_reasons.append(f"EVIDENCE_TIMELINE_STRUCTURE_INVALID:{Path(rel).name}")
            return _emit(out_resolved, "blocked", [], blocked_reasons, warnings)
        raws[rel] = raw
        docs[rel] = doc

    export_status = str(docs[_EXPORT_REL].get("export_status") or "")
    timeline_status = "blocked"
    if export_status == "ok":
        timeline_status = "ok"
    elif export_status == "review_required":
        timeline_status = "review_required"
    elif export_status == "blocked":
        timeline_status = "blocked"
    else:
        blocked_reasons.append("EVIDENCE_TIMELINE_EXPORT_STATUS_INVALID")

    events: list[dict[str, Any]] = []
    for rel in rels:
        events.append(
            {
                "path": rel,
                "sha256": hashlib.sha256(raws[rel]).hexdigest(),
                "timestamp": _parse_timestamp(docs[rel]),
            }
        )

    events.sort(key=lambda e: (e["timestamp"] == "", e["timestamp"], e["path"]))
    return _emit(out_resolved, timeline_status, events, blocked_reasons, warnings)
