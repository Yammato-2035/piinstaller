from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_ACCEPTANCE_REL = "docs/evidence/runtime-results/handoff/laptop_failure_final_acceptance.json"
_SNAPSHOT_REL = "docs/evidence/runtime-results/handoff/laptop_failure_final_snapshot.json"
_TIMELINE_REL = "docs/evidence/runtime-results/handoff/laptop_failure_evidence_timeline.json"
_EXPORT_REL = "docs/evidence/runtime-results/handoff/laptop_failure_final_export_package.json"
_FINAL_REPORT_REL = "docs/evidence/runtime-results/handoff/laptop_failure_final_report.json"
_SUMMARY_REL = "docs/evidence/runtime-results/handoff/laptop_failure_test_summary.json"
_VALIDATION_REL = "docs/evidence/runtime-results/handoff/laptop_failure_execution_log_validation.json"
_EXEC_LOG_REL = "docs/evidence/runtime-results/handoff/laptop_failure_execution_log.json"
_FINALIZED_REL = "docs/evidence/runtime-results/handoff/laptop_failure_finalized_export_package.json"
_MAX_OUTPUT_BYTES = 512 * 1024


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "FINALIZED_EXPORT_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "FINALIZED_EXPORT_PATH_INVALID"
    if ".." in p.parts:
        return None, "FINALIZED_EXPORT_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "FINALIZED_EXPORT_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "FINALIZED_EXPORT_OUTSIDE_HANDOFF"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def build_manual_laptop_failure_finalized_export_package(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    blocked_reasons: list[str] = []
    rels = [
        _ACCEPTANCE_REL,
        _SNAPSHOT_REL,
        _TIMELINE_REL,
        _EXPORT_REL,
        _FINAL_REPORT_REL,
        _SUMMARY_REL,
        _VALIDATION_REL,
        _EXEC_LOG_REL,
    ]

    out_path, oerr = _resolve_handoff(_FINALIZED_REL)
    if oerr or out_path is None:
        return {
            "export_status": "blocked",
            "finalized_export_file_path": _FINALIZED_REL,
            "warnings": [],
            "errors": [oerr or "FINALIZED_EXPORT_OUTPUT_PATH_INVALID"],
            "blocked_reasons": [oerr or "FINALIZED_EXPORT_OUTPUT_PATH_INVALID"],
        }
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return {
            "export_status": "blocked",
            "finalized_export_file_path": _FINALIZED_REL,
            "warnings": [],
            "errors": ["FINALIZED_EXPORT_EXISTS_NO_OVERWRITE"],
            "blocked_reasons": ["FINALIZED_EXPORT_EXISTS_NO_OVERWRITE"],
        }

    included_files: list[str] = []
    sha_map: dict[str, str] = {}
    raw_docs: dict[str, dict[str, Any]] = {}
    for rel in rels:
        p, err = _resolve_handoff(rel)
        if err or p is None or not p.is_file():
            blocked_reasons.append(f"FINALIZED_EXPORT_INPUT_MISSING:{Path(rel).name}")
            return _emit(out_path, "blocked", "blocked", included_files, sha_map, blocked_reasons, warnings)
        try:
            raw = p.read_bytes()
        except OSError:
            blocked_reasons.append(f"FINALIZED_EXPORT_INPUT_READ_FAILED:{Path(rel).name}")
            return _emit(out_path, "blocked", "blocked", included_files, sha_map, blocked_reasons, warnings)
        sha_map[rel] = hashlib.sha256(raw).hexdigest()
        included_files.append(rel)
        try:
            doc = json.loads(raw.decode("utf-8"))
        except Exception:
            blocked_reasons.append(f"FINALIZED_EXPORT_JSON_INVALID:{Path(rel).name}")
            return _emit(out_path, "blocked", "blocked", included_files, sha_map, blocked_reasons, warnings)
        if not isinstance(doc, dict):
            blocked_reasons.append(f"FINALIZED_EXPORT_STRUCTURE_INVALID:{Path(rel).name}")
            return _emit(out_path, "blocked", "blocked", included_files, sha_map, blocked_reasons, warnings)
        raw_docs[rel] = doc

    acceptance_status = str(raw_docs[_ACCEPTANCE_REL].get("acceptance_status") or "")
    export_status = "blocked"
    if acceptance_status == "accepted":
        export_status = "ok"
    elif acceptance_status == "review_required":
        export_status = "review_required"
    elif acceptance_status == "blocked":
        export_status = "blocked"
    else:
        blocked_reasons.append("FINALIZED_EXPORT_ACCEPTANCE_STATUS_INVALID")
        export_status = "blocked"

    return _emit(out_path, acceptance_status, export_status, included_files, sha_map, blocked_reasons, warnings)


def _emit(
    out_path: Path,
    acceptance_status: str,
    export_status: str,
    included_files: list[str],
    sha_map: dict[str, str],
    blocked_reasons: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    body = {
        "export_schema_version": 1,
        "strict_mode": "laptop_failure_finalized_export_package",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "acceptance_status": acceptance_status,
        "export_status": export_status,
        "included_files": included_files,
        "file_count": len(included_files),
        "sha256": sha_map,
        "warnings": list(dict.fromkeys(warnings)),
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return {
            "export_status": "blocked",
            "finalized_export_file_path": _FINALIZED_REL,
            "warnings": [],
            "errors": ["FINALIZED_EXPORT_OUTPUT_TOO_LARGE"],
            "blocked_reasons": ["FINALIZED_EXPORT_OUTPUT_TOO_LARGE"],
        }
    try:
        _atomic_write(out_path, text)
    except OSError:
        return {
            "export_status": "blocked",
            "finalized_export_file_path": _FINALIZED_REL,
            "warnings": [],
            "errors": ["FINALIZED_EXPORT_WRITE_FAILED"],
            "blocked_reasons": ["FINALIZED_EXPORT_WRITE_FAILED"],
        }
    out = dict(body)
    out["finalized_export_file_path"] = _FINALIZED_REL
    out["errors"] = list(dict.fromkeys(blocked_reasons)) if export_status == "blocked" else []
    return out
