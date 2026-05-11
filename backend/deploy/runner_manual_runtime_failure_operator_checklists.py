from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_PREVIEW_REL = "docs/evidence/runtime-results/handoff/failure_execution_preview.json"
_CHECKLIST_REL = "docs/evidence/runtime-results/handoff/failure_operator_checklists.json"
_MAX_OUTPUT_BYTES = 512 * 1024


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "OP_CHECKLIST_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute():
        return None, "OP_CHECKLIST_PATH_INVALID"
    if ".." in p.parts:
        return None, "OP_CHECKLIST_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "OP_CHECKLIST_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "OP_CHECKLIST_OUTSIDE_HANDOFF"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _build_checklist(case: dict[str, Any]) -> dict[str, Any]:
    failure_type = str(case.get("failure_type") or "")
    rollback_required = bool(case.get("rollback_required"))
    expected_detection_layer = str(case.get("expected_detection_layer") or "runtime_guard")
    risk_level = "medium" if rollback_required else "low"
    return {
        "failure_type": failure_type,
        "risk_level": risk_level,
        "destructive": False,
        "rollback_required": rollback_required,
        "required_media": ["external_usb_test_drive", "test_nvme_or_vm_disk"],
        "operator_checklist": [
            "Nur Testmedien verwenden; keine produktiven Datentraeger oder internen OS-Partitionen.",
            f"Failure-Typ '{failure_type}' kontrolliert und reversibel vorbereiten.",
            "Nur Preview-/Read-only-Validierungen ausfuehren; keine destruktiven Kommandos.",
            "Alle Beobachtungen und Zeitpunkte fuer Evidence dokumentieren.",
        ],
        "expected_detection_points": [
            expected_detection_layer,
            "manual_preview_only_gate",
            "permission_boundary_guard",
        ],
        "required_evidence": [
            "operator_log",
            "runtime_detection_output",
            "target_media_identity_note",
        ],
        "abort_conditions": [
            "target_is_productive_or_unknown",
            "internal_os_partition_detected",
            "unexpected_device_reenumeration_without_confirmation",
            "any_destructive_operation_requested",
        ],
    }


def build_manual_runtime_failure_operator_checklists(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    blocked_reasons: list[str] = []

    def fail(codes: list[str]) -> dict[str, Any]:
        blocked_reasons.extend(c for c in codes if c not in blocked_reasons)
        return {
            "checklist_status": "blocked",
            "checklist_file_path": _CHECKLIST_REL,
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors + blocked_reasons)),
            "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        }

    out_resolved, oerr = _resolve_handoff(_CHECKLIST_REL)
    if oerr or out_resolved is None:
        return fail([oerr or "OP_CHECKLIST_OUTPUT_PATH_INVALID"])
    if out_resolved.exists() and out_resolved.is_file() and not explicit_overwrite:
        return fail(["OP_CHECKLIST_EXISTS_NO_OVERWRITE"])

    preview_resolved, perr = _resolve_handoff(_PREVIEW_REL)
    if perr or preview_resolved is None:
        return fail([perr or "OP_CHECKLIST_PREVIEW_PATH_INVALID"])
    if not preview_resolved.is_file():
        return fail(["OP_CHECKLIST_PREVIEW_MISSING"])

    try:
        preview = json.loads(preview_resolved.read_text(encoding="utf-8"))
    except Exception:
        return fail(["OP_CHECKLIST_PREVIEW_JSON_INVALID"])
    if not isinstance(preview, dict):
        return fail(["OP_CHECKLIST_PREVIEW_JSON_INVALID"])

    preview_cases = preview.get("preview_cases")
    if not isinstance(preview_cases, list) or len(preview_cases) == 0:
        return fail(["OP_CHECKLIST_PREVIEW_CASES_MISSING"])

    checklists: list[dict[str, Any]] = []
    for c in preview_cases:
        if not isinstance(c, dict):
            return fail(["OP_CHECKLIST_CASE_INVALID"])
        checklists.append(_build_checklist(c))

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = {
        "checklist_schema_version": 1,
        "strict_mode": "real_laptop_failure_operator_checklists",
        "generated_at": generated_at,
        "checklists": checklists,
        "warnings": [],
        "blocked_reasons": [],
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return fail(["OP_CHECKLIST_OUTPUT_TOO_LARGE"])

    try:
        _atomic_write(out_resolved, text)
    except OSError:
        return fail(["OP_CHECKLIST_WRITE_FAILED"])

    preview_status = str(preview.get("preview_status") or "ok")
    checklist_status = "review_required" if preview_status == "review_required" else "ok"
    return {
        "checklist_status": checklist_status,
        "checklist_file_path": _CHECKLIST_REL,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
        "blocked_reasons": [],
    }
