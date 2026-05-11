from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from deploy.runner_manual_runtime_precheck import build_runner_manual_runtime_precheck

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ALLOWED_ROOT = (_REPO_ROOT / "docs" / "evidence" / "runtime-results").resolve(strict=False)
_ALLOWED_RUNBOOKS = {
    "RUNBOOK_SUDOERS_RUNTIME_DRYRUN",
    "RUNBOOK_PRIVILEGED_RUNNER_VALIDATION_DRYRUN",
    "RUNBOOK_REAL_WRITE_HARDWARE_E2E",
    "RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E",
    "RUNBOOK_DEVICE_REENUMERATION",
    "RUNBOOK_HOTPLUG_UNMOUNT_RACE",
    "RUNBOOK_ROLLBACK_RUNTIME",
}


def _resolve_safe_target(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "empty_result_file_path"
    p = Path(raw)
    if p.is_absolute():
        return None, "absolute_result_file_path_forbidden"
    if ".." in p.parts:
        return None, "traversal_result_file_path_forbidden"
    if p.suffix.lower() != ".json":
        return None, "result_file_must_be_json"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "result_file_symlink_forbidden"
        if cur.parent == cur:
            break
        cur = cur.parent
    target = unresolved.resolve(strict=False)
    if not (str(target).startswith(str(_ALLOWED_ROOT) + os.sep) or str(target) == str(_ALLOWED_ROOT)):
        return None, "result_file_outside_allowed_root"
    return target, None


def _atomic_write(path: Path, content: str) -> None:
    os.makedirs(str(path.parent), exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _template_for(runbook_id: str) -> dict[str, Any]:
    return {
        "runbook_id": runbook_id,
        "started_at": "",
        "completed_at": "",
        "operator": "",
        "host": "",
        "target_device": "",
        "pre_state": {"lsblk": "", "findmnt": "", "mount": ""},
        "post_state": {"lsblk": "", "findmnt": "", "mount": ""},
        "runner_result": {"stdout_json": {}, "stderr": ""},
        "evidence": {
            "audit_jsonl_excerpt": "",
            "jobfile_hash": "",
            "snapshot_fingerprint": "",
            "bytes_written": None,
            "expected_sha256": "",
            "actual_sha256": "",
            "verify_status": "",
            "internal_drive_touched": False,
            "untracked_mount_change": False,
        },
        "pass_fail": "",
        "rollback_status": "",
    }


def create_manual_runtime_result_template(
    *,
    precheck: dict[str, Any] | None = None,
    explicit_overwrite: bool = False,
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    pre = dict(precheck or {})
    if not pre:
        pre = build_runner_manual_runtime_precheck(
            selected_runbook="RUNBOOK_SUDOERS_RUNTIME_DRYRUN",
            next_phase_gate={"allowed_next_phases": ["NEXT_PHASE_MANUAL_RUNTIME_TESTS"]},
            operator_confirmations={"full_backup_confirmed": True, "local_control_confirmed": True, "single_test_media_confirmed": True, "stop_conditions_acknowledged": True, "operator_understands_data_loss": True},
        )

    st = str(pre.get("precheck_status") or "blocked")
    if st not in {"ready_for_manual_runtime", "review_required"}:
        return {
            "template_status": "blocked",
            "result_file_path": "",
            "runbook_id": str(pre.get("selected_runbook") or ""),
            "template": {},
            "warnings": [],
            "errors": ["precheck_not_ready_or_review_required"],
        }
    if st == "review_required":
        warnings.append("precheck_review_required")

    runbook_id = str(pre.get("selected_runbook") or "")
    if runbook_id not in _ALLOWED_RUNBOOKS:
        return {
            "template_status": "blocked",
            "result_file_path": "",
            "runbook_id": runbook_id,
            "template": {},
            "warnings": warnings,
            "errors": ["unknown_runbook"],
        }

    result_path = ""
    for item in list(pre.get("evidence_plan") or []):
        if str((item or {}).get("code") or "") == "EVIDENCE_RESULT_FILE_PATH":
            result_path = str((item or {}).get("value") or "").strip()
            break
    if not result_path:
        return {
            "template_status": "blocked",
            "result_file_path": "",
            "runbook_id": runbook_id,
            "template": {},
            "warnings": warnings,
            "errors": ["missing_result_file_path_in_evidence_plan"],
        }

    resolved, path_err = _resolve_safe_target(result_path)
    if path_err or resolved is None:
        return {
            "template_status": "blocked",
            "result_file_path": result_path,
            "runbook_id": runbook_id,
            "template": {},
            "warnings": warnings,
            "errors": [path_err or "invalid_result_file_path"],
        }

    if resolved.exists() and not explicit_overwrite:
        return {
            "template_status": "blocked",
            "result_file_path": result_path,
            "runbook_id": runbook_id,
            "template": {},
            "warnings": warnings,
            "errors": ["result_file_exists_explicit_overwrite_required"],
        }

    tpl = _template_for(runbook_id)
    _atomic_write(resolved, json.dumps(tpl, ensure_ascii=True, indent=2) + "\n")
    status = "created" if not warnings else "review_required"
    return {
        "template_status": status,
        "result_file_path": result_path,
        "runbook_id": runbook_id,
        "template": tpl,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
    }
