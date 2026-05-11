from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_MATRIX_REL = "docs/evidence/runtime-results/handoff/failure_injection_matrix.json"
_PREVIEW_REL = "docs/evidence/runtime-results/handoff/failure_execution_preview.json"
_MAX_OUTPUT_BYTES = 512 * 1024


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "FAILURE_PREVIEW_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "FAILURE_PREVIEW_PATH_INVALID"
    if ".." in p.parts:
        return None, "FAILURE_PREVIEW_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "FAILURE_PREVIEW_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "FAILURE_PREVIEW_OUTSIDE_HANDOFF"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _build_case(case: dict[str, Any]) -> dict[str, Any]:
    failure_type = str(case.get("failure_type") or "")
    layer = str(case.get("expected_detection_layer") or "runtime_guard")
    expected_status = str(case.get("expected_status") or "review_required")
    rollback_required = bool(case.get("rollback_required"))
    return {
        "failure_type": failure_type,
        "execution_mode": "manual_preview_only",
        "required_media": ["external_usb_test_drive", "test_nvme_or_vm_disk"],
        "required_preconditions": [
            "non_production_test_environment_confirmed",
            "no_internal_os_volume_targeted",
            "operator_manual_confirmation_required",
        ],
        "expected_detection_layer": layer,
        "expected_runtime_status": expected_status if expected_status in ("blocked", "review_required") else "review_required",
        "rollback_required": rollback_required,
        "destructive": False,
        "operator_steps": [
            "Prepare isolated test media only; never use productive partitions.",
            f"Inject controlled case '{failure_type}' manually without destructive commands.",
            "Run only preview/detection workflow and capture runtime evidence.",
            "Stop immediately if target identity or mount path changes unexpectedly.",
        ],
        "evidence_expectations": [
            "runtime logs show expected detection layer decision",
            "status is blocked or review_required",
            "operator notes include medium identity and reversibility",
        ],
    }


def build_manual_runtime_failure_execution_preview(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    blocked_reasons: list[str] = []

    def fail(codes: list[str]) -> dict[str, Any]:
        blocked_reasons.extend(c for c in codes if c not in blocked_reasons)
        return {
            "preview_status": "blocked",
            "preview_file_path": _PREVIEW_REL,
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors + blocked_reasons)),
            "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        }

    out_resolved, oerr = _resolve_handoff(_PREVIEW_REL)
    if oerr or out_resolved is None:
        return fail([oerr or "FAILURE_PREVIEW_OUTPUT_PATH_INVALID"])
    if out_resolved.exists() and out_resolved.is_file() and not explicit_overwrite:
        return fail(["FAILURE_PREVIEW_EXISTS_NO_OVERWRITE"])

    matrix_resolved, merr = _resolve_handoff(_MATRIX_REL)
    if merr or matrix_resolved is None:
        return fail([merr or "FAILURE_PREVIEW_MATRIX_PATH_INVALID"])
    if not matrix_resolved.is_file():
        return fail(["FAILURE_PREVIEW_MATRIX_MISSING"])

    try:
        matrix = json.loads(matrix_resolved.read_text(encoding="utf-8"))
    except Exception:
        return fail(["FAILURE_PREVIEW_MATRIX_JSON_INVALID"])
    if not isinstance(matrix, dict):
        return fail(["FAILURE_PREVIEW_MATRIX_JSON_INVALID"])

    raw_cases = matrix.get("failure_cases")
    if not isinstance(raw_cases, list) or len(raw_cases) == 0:
        return fail(["FAILURE_PREVIEW_CASES_MISSING"])

    preview_cases = []
    for c in raw_cases:
        if not isinstance(c, dict):
            return fail(["FAILURE_PREVIEW_CASE_INVALID"])
        preview_cases.append(_build_case(c))

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = {
        "preview_schema_version": 1,
        "strict_mode": "real_laptop_failure_execution_preview",
        "generated_at": generated_at,
        "preview_cases": preview_cases,
        "warnings": [],
        "blocked_reasons": [],
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return fail(["FAILURE_PREVIEW_OUTPUT_TOO_LARGE"])

    try:
        _atomic_write(out_resolved, text)
    except OSError:
        return fail(["FAILURE_PREVIEW_WRITE_FAILED"])

    matrix_warnings = matrix.get("warnings")
    preview_status = "review_required" if isinstance(matrix_warnings, list) and len(matrix_warnings) > 0 else "ok"
    return {
        "preview_status": preview_status,
        "preview_file_path": _PREVIEW_REL,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
        "blocked_reasons": [],
    }
