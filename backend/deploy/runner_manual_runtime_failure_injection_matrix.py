from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_ACCEPTANCE_REL = "docs/evidence/runtime-results/handoff/validator_final_acceptance.json"
_MATRIX_REL = "docs/evidence/runtime-results/handoff/failure_injection_matrix.json"
_MAX_OUTPUT_BYTES = 512 * 1024

_FAILURE_CASES: tuple[dict[str, Any], ...] = (
    {"failure_type": "missing_backup_archive", "expected_detection_layer": "backup_archive_validation", "expected_status": "blocked"},
    {"failure_type": "corrupted_manifest", "expected_detection_layer": "manifest_schema_validation", "expected_status": "blocked"},
    {"failure_type": "sha256_mismatch", "expected_detection_layer": "integrity_hash_validation", "expected_status": "blocked"},
    {"failure_type": "interrupted_verify", "expected_detection_layer": "verify_runtime_guard", "expected_status": "review_required"},
    {"failure_type": "interrupted_restore_preview", "expected_detection_layer": "restore_preview_guard", "expected_status": "review_required"},
    {"failure_type": "readonly_target", "expected_detection_layer": "mount_rw_validation", "expected_status": "blocked"},
    {"failure_type": "missing_mount", "expected_detection_layer": "mount_presence_guard", "expected_status": "blocked"},
    {"failure_type": "mount_changed", "expected_detection_layer": "mount_identity_recheck", "expected_status": "blocked"},
    {"failure_type": "rollback_incomplete", "expected_detection_layer": "rollback_consistency_guard", "expected_status": "review_required"},
    {"failure_type": "stale_snapshot", "expected_detection_layer": "snapshot_freshness_guard", "expected_status": "review_required"},
    {"failure_type": "missing_job_hash", "expected_detection_layer": "runner_job_hash_validation", "expected_status": "blocked"},
    {"failure_type": "invalid_fingerprint", "expected_detection_layer": "fingerprint_validation", "expected_status": "blocked"},
    {
        "failure_type": "unexpected_device_reenumeration",
        "expected_detection_layer": "device_identity_guard",
        "expected_status": "blocked",
    },
    {"failure_type": "removed_usb_target", "expected_detection_layer": "hotplug_target_presence_guard", "expected_status": "blocked"},
    {"failure_type": "permission_denied", "expected_detection_layer": "permission_boundary_guard", "expected_status": "blocked"},
    {"failure_type": "partial_restore_metadata", "expected_detection_layer": "restore_metadata_validation", "expected_status": "review_required"},
)

_ROLLBACK_REQUIRED_TYPES = frozenset(
    {
        "interrupted_verify",
        "interrupted_restore_preview",
        "mount_changed",
        "rollback_incomplete",
        "stale_snapshot",
        "unexpected_device_reenumeration",
        "removed_usb_target",
        "partial_restore_metadata",
    }
)


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "FAILURE_MATRIX_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "FAILURE_MATRIX_PATH_INVALID"
    if ".." in p.parts:
        return None, "FAILURE_MATRIX_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "FAILURE_MATRIX_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "FAILURE_MATRIX_OUTSIDE_HANDOFF"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def build_manual_runtime_failure_injection_matrix(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    blocked_reasons: list[str] = []

    def fail(codes: list[str]) -> dict[str, Any]:
        blocked_reasons.extend(c for c in codes if c not in blocked_reasons)
        return {
            "matrix_status": "blocked",
            "matrix_file_path": _MATRIX_REL,
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors + blocked_reasons)),
            "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        }

    out_resolved, oerr = _resolve_handoff(_MATRIX_REL)
    if oerr or out_resolved is None:
        return fail([oerr or "FAILURE_MATRIX_OUTPUT_PATH_INVALID"])
    if out_resolved.exists() and out_resolved.is_file() and not explicit_overwrite:
        return fail(["FAILURE_MATRIX_EXISTS_NO_OVERWRITE"])

    acc_resolved, aerr = _resolve_handoff(_ACCEPTANCE_REL)
    if aerr or acc_resolved is None:
        return fail([aerr or "FAILURE_MATRIX_ACCEPTANCE_PATH_INVALID"])
    if not acc_resolved.is_file():
        return fail(["FAILURE_MATRIX_ACCEPTANCE_MISSING"])

    try:
        acceptance = json.loads(acc_resolved.read_text(encoding="utf-8"))
    except Exception:
        return fail(["FAILURE_MATRIX_ACCEPTANCE_JSON_INVALID"])
    if not isinstance(acceptance, dict):
        return fail(["FAILURE_MATRIX_ACCEPTANCE_JSON_INVALID"])

    acceptance_status = str(acceptance.get("acceptance_status") or "")
    if acceptance_status == "blocked":
        return fail(["FAILURE_MATRIX_ACCEPTANCE_BLOCKED"])
    if acceptance_status not in ("accepted", "review_required"):
        return fail(["FAILURE_MATRIX_ACCEPTANCE_INVALID"])

    cases: list[dict[str, Any]] = []
    for c in _FAILURE_CASES:
        failure_type = str(c["failure_type"])
        cases.append(
            {
                "failure_type": failure_type,
                "expected_detection_layer": str(c["expected_detection_layer"]),
                "expected_status": str(c["expected_status"]),
                "rollback_required": failure_type in _ROLLBACK_REQUIRED_TYPES,
                "destructive": False,
            }
        )

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "matrix_schema_version": 1,
        "strict_mode": "real_hardware_failure_injection_matrix",
        "generated_at": generated_at,
        "failure_cases": cases,
        "warnings": [],
        "blocked_reasons": [],
    }
    text = json.dumps(payload, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return fail(["FAILURE_MATRIX_OUTPUT_TOO_LARGE"])

    try:
        _atomic_write(out_resolved, text)
    except OSError:
        return fail(["FAILURE_MATRIX_WRITE_FAILED"])

    matrix_status = "review_required" if acceptance_status == "review_required" else "ok"
    return {
        "matrix_status": matrix_status,
        "matrix_file_path": _MATRIX_REL,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
        "blocked_reasons": [],
    }
