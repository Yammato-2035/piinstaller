from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_RUNTIME_RESULTS_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results").resolve(strict=False)
_INDEX_REL = "docs/evidence/runtime-results/handoff/validator_seal_index.json"
_AUDIT_REL = "docs/evidence/runtime-results/handoff/validator_seal_consistency_audit.json"
_MAX_INDEX_BYTES = 256 * 1024
_MAX_AUDIT_BYTES = 256 * 1024
_MAX_SEAL_BYTES = 128 * 1024
_MAX_SOURCE_BYTES = 2 * 1024 * 1024


def _resolve_under_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "AUDIT_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "AUDIT_PATH_INVALID"
    if ".." in p.parts:
        return None, "AUDIT_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "AUDIT_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "AUDIT_OUTSIDE_HANDOFF"
    return resolved, None


def _resolve_under_runtime_results(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "AUDIT_SOURCE_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "AUDIT_SOURCE_PATH_INVALID"
    if ".." in p.parts:
        return None, "AUDIT_SOURCE_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "AUDIT_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_RUNTIME_RESULTS_ROOT) + os.sep) or str(resolved) == str(_RUNTIME_RESULTS_ROOT)):
        return None, "AUDIT_SOURCE_OUTSIDE_RUNTIME_RESULTS"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def run_validator_seal_consistency_audit(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    blocked_reasons: list[str] = []
    findings: list[dict[str, Any]] = []
    checked_entries = 0
    valid_entries = 0
    invalid_entries = 0

    def fail(codes: list[str]) -> dict[str, Any]:
        blocked_reasons.extend(c for c in codes if c not in blocked_reasons)
        return {
            "audit_status": "blocked",
            "checked_entries": checked_entries,
            "valid_entries": valid_entries,
            "invalid_entries": invalid_entries,
            "audit_report_path": _AUDIT_REL,
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors + blocked_reasons)),
            "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        }

    audit_resolved, aerr = _resolve_under_handoff(_AUDIT_REL)
    if aerr or audit_resolved is None:
        return fail([aerr or "AUDIT_OUTPUT_PATH_INVALID"])

    if audit_resolved.exists() and audit_resolved.is_file() and not explicit_overwrite:
        return fail(["AUDIT_OUTPUT_EXISTS_NO_OVERWRITE"])

    index_resolved, ierr = _resolve_under_handoff(_INDEX_REL)
    if ierr or index_resolved is None:
        return fail([ierr or "AUDIT_INDEX_PATH_INVALID"])

    if not index_resolved.is_file():
        return fail(["AUDIT_INDEX_MISSING"])

    if index_resolved.stat().st_size > _MAX_INDEX_BYTES:
        return fail(["AUDIT_INDEX_TOO_LARGE"])

    try:
        index_data = json.loads(index_resolved.read_text(encoding="utf-8"))
    except Exception:
        return fail(["AUDIT_INDEX_JSON_INVALID"])

    if not isinstance(index_data, dict):
        return fail(["AUDIT_INDEX_JSON_INVALID"])

    seals = index_data.get("seals")
    if not isinstance(seals, list):
        return fail(["AUDIT_INDEX_SEALS_MISSING"])

    checked_entries = len(seals)

    for i, entry in enumerate(seals):
        if not isinstance(entry, dict):
            invalid_entries += 1
            findings.append({"entry_index": i, "issue": "invalid_index_entry"})
            warnings.append(f"invalid_index_entry:{i}")
            continue

        sf = str(entry.get("seal_file") or "").strip()
        sr = str(entry.get("source_report") or "").strip()
        expect_sha = str(entry.get("source_report_sha256") or "").strip()
        sealed_at_idx = str(entry.get("sealed_at") or "").strip()

        if not sf or not sr or not expect_sha or not sealed_at_idx:
            invalid_entries += 1
            findings.append({"entry_index": i, "seal_file": sf, "issue": "missing_index_fields"})
            warnings.append(f"missing_index_fields:{i}")
            continue

        seal_path, e1 = _resolve_under_handoff(sf)
        if e1 or seal_path is None or not seal_path.is_file():
            invalid_entries += 1
            findings.append({"entry_index": i, "seal_file": sf, "issue": "seal_file_missing"})
            warnings.append(f"seal_file_missing:{Path(sf).name}")
            continue

        if seal_path.stat().st_size > _MAX_SEAL_BYTES:
            invalid_entries += 1
            findings.append({"entry_index": i, "seal_file": sf, "issue": "seal_file_too_large"})
            warnings.append(f"seal_file_too_large:{Path(sf).name}")
            continue

        try:
            seal_raw = seal_path.read_bytes()
            seal_json = json.loads(seal_raw.decode("utf-8"))
        except Exception:
            invalid_entries += 1
            findings.append({"entry_index": i, "seal_file": sf, "issue": "invalid_seal_json"})
            warnings.append(f"invalid_seal_json:{Path(sf).name}")
            continue

        if not isinstance(seal_json, dict):
            invalid_entries += 1
            findings.append({"entry_index": i, "seal_file": sf, "issue": "invalid_seal_json"})
            warnings.append(f"invalid_seal_json:{Path(sf).name}")
            continue

        if not str(seal_json.get("sealed_at") or "").strip():
            invalid_entries += 1
            findings.append({"entry_index": i, "seal_file": sf, "issue": "sealed_at_missing_in_seal"})
            warnings.append(f"sealed_at_missing_in_seal:{Path(sf).name}")
            continue

        if str(seal_json.get("validator_status") or "") != "ok":
            invalid_entries += 1
            findings.append({"entry_index": i, "seal_file": sf, "issue": "validator_status_not_ok_in_seal"})
            warnings.append(f"validator_status_not_ok_in_seal:{Path(sf).name}")
            continue

        src_path, e2 = _resolve_under_runtime_results(sr)
        if e2 or src_path is None or not src_path.is_file():
            invalid_entries += 1
            findings.append({"entry_index": i, "source_report": sr, "issue": "missing_source_report"})
            warnings.append(f"missing_source_report:{Path(sr).name}")
            continue

        if src_path.stat().st_size > _MAX_SOURCE_BYTES:
            invalid_entries += 1
            findings.append({"entry_index": i, "source_report": sr, "issue": "source_report_too_large"})
            warnings.append(f"source_report_too_large:{Path(sr).name}")
            continue

        try:
            src_raw = src_path.read_bytes()
        except OSError:
            invalid_entries += 1
            findings.append({"entry_index": i, "source_report": sr, "issue": "source_read_failed"})
            warnings.append(f"source_read_failed:{Path(sr).name}")
            continue

        actual_sha = hashlib.sha256(src_raw).hexdigest()
        if actual_sha != expect_sha:
            invalid_entries += 1
            findings.append({"entry_index": i, "seal_file": sf, "issue": "sha256_mismatch"})
            warnings.append(f"sha256_mismatch:{Path(sf).name}")
            continue

        valid_entries += 1

    if valid_entries == 0:
        blocked_reasons.append("AUDIT_NO_VALID_ENTRIES")
        return {
            "audit_status": "blocked",
            "checked_entries": checked_entries,
            "valid_entries": valid_entries,
            "invalid_entries": invalid_entries,
            "audit_report_path": _AUDIT_REL,
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors + blocked_reasons)),
            "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        }

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report_body: dict[str, Any] = {
        "audit_schema_version": 1,
        "strict_mode": "validator_seal_consistency_audit",
        "generated_at": generated_at,
        "checked_entries": checked_entries,
        "valid_entries": valid_entries,
        "invalid_entries": invalid_entries,
        "findings": findings,
    }
    text = json.dumps(report_body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_AUDIT_BYTES:
        return fail(["AUDIT_OUTPUT_TOO_LARGE"])

    try:
        _atomic_write(audit_resolved, text)
    except OSError:
        return fail(["AUDIT_WRITE_FAILED"])

    if invalid_entries > 0:
        audit_status = "review_required"
    else:
        audit_status = "ok"

    return {
        "audit_status": audit_status,
        "checked_entries": checked_entries,
        "valid_entries": valid_entries,
        "invalid_entries": invalid_entries,
        "audit_report_path": _AUDIT_REL,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
        "blocked_reasons": [],
    }
