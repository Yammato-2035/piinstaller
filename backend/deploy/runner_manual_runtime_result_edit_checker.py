from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ALLOWED_ROOT = (_REPO_ROOT / "docs" / "evidence" / "runtime-results").resolve(strict=False)
_MAX_FILE_SIZE = 2 * 1024 * 1024
_WRITE_RUNBOOKS = {
    "RUNBOOK_REAL_WRITE_HARDWARE_E2E",
    "RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E",
    "RUNBOOK_DEVICE_REENUMERATION",
    "RUNBOOK_HOTPLUG_UNMOUNT_RACE",
    "RUNBOOK_ROLLBACK_RUNTIME",
}
_ALLOWED_PASS_FAIL = {"pass", "failed", "repeat_required", "skipped"}


def _resolve_allowed_result_file(path: str) -> tuple[Path | None, str | None]:
    raw = str(path or "").strip()
    if not raw:
        return None, "RESULT_PATH_OUTSIDE_ALLOWED_ROOT"
    p = Path(raw)
    if p.is_absolute():
        return None, "RESULT_PATH_OUTSIDE_ALLOWED_ROOT"
    if ".." in p.parts:
        return None, "RESULT_PATH_OUTSIDE_ALLOWED_ROOT"
    if p.suffix.lower() != ".json":
        return None, "RESULT_PATH_OUTSIDE_ALLOWED_ROOT"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "RESULT_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_ALLOWED_ROOT) + "/") or str(resolved) == str(_ALLOWED_ROOT)):
        return None, "RESULT_PATH_OUTSIDE_ALLOWED_ROOT"
    return resolved, None


def _field_status(value: Any) -> tuple[str, str]:
    if value is None:
        return "missing", "blocking"
    if isinstance(value, str) and value.strip() == "":
        return "empty", "warning"
    return "filled", "info"


def _nested(data: dict[str, Any], path: list[str]) -> tuple[bool, Any]:
    cur: Any = data
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return False, None
        cur = cur[key]
    return True, cur


def check_manual_runtime_result_file(*, result_file: str) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    blocking_findings: list[str] = []
    field_checks: list[dict[str, str]] = []
    evidence_checks: list[dict[str, str]] = []
    safety_checks: list[dict[str, str]] = []

    resolved, path_err = _resolve_allowed_result_file(result_file)
    if path_err or resolved is None:
        return {
            "check_status": "blocked",
            "result_file_path": result_file,
            "runbook_id": "",
            "field_checks": [],
            "evidence_checks": [],
            "safety_checks": [],
            "validator_readiness": {
                "ready_for_ingestion_validator": False,
                "expected_validator_status": "blocked",
                "expected_blockers": [path_err or "RESULT_PATH_OUTSIDE_ALLOWED_ROOT"],
                "missing_required_fields": [],
                "missing_evidence_fields": [],
            },
            "blocking_findings": [path_err or "RESULT_PATH_OUTSIDE_ALLOWED_ROOT"],
            "warnings": [],
            "errors": [path_err or "RESULT_PATH_OUTSIDE_ALLOWED_ROOT"],
        }

    if not resolved.exists() or not resolved.is_file() or resolved.stat().st_size > _MAX_FILE_SIZE:
        return {
            "check_status": "blocked",
            "result_file_path": result_file,
            "runbook_id": "",
            "field_checks": [],
            "evidence_checks": [],
            "safety_checks": [],
            "validator_readiness": {
                "ready_for_ingestion_validator": False,
                "expected_validator_status": "blocked",
                "expected_blockers": ["RESULT_JSON_INVALID"],
                "missing_required_fields": [],
                "missing_evidence_fields": [],
            },
            "blocking_findings": ["RESULT_JSON_INVALID"],
            "warnings": [],
            "errors": ["RESULT_JSON_INVALID"],
        }

    try:
        data = json.loads(resolved.read_text(encoding="utf-8"))
    except Exception:
        return {
            "check_status": "blocked",
            "result_file_path": result_file,
            "runbook_id": "",
            "field_checks": [],
            "evidence_checks": [],
            "safety_checks": [],
            "validator_readiness": {
                "ready_for_ingestion_validator": False,
                "expected_validator_status": "blocked",
                "expected_blockers": ["RESULT_JSON_INVALID"],
                "missing_required_fields": [],
                "missing_evidence_fields": [],
            },
            "blocking_findings": ["RESULT_JSON_INVALID"],
            "warnings": [],
            "errors": ["RESULT_JSON_INVALID"],
        }

    required_field_paths = [
        ["runbook_id"],
        ["started_at"],
        ["completed_at"],
        ["operator"],
        ["host"],
        ["target_device"],
        ["pre_state", "lsblk"],
        ["pre_state", "findmnt"],
        ["pre_state", "mount"],
        ["post_state", "lsblk"],
        ["post_state", "findmnt"],
        ["post_state", "mount"],
        ["runner_result", "stdout_json"],
        ["runner_result", "stderr"],
        ["evidence", "audit_jsonl_excerpt"],
        ["evidence", "jobfile_hash"],
        ["evidence", "snapshot_fingerprint"],
        ["pass_fail"],
        ["rollback_status"],
    ]

    missing_required_fields: list[str] = []
    missing_evidence_fields: list[str] = []
    for p in required_field_paths:
        exists, value = _nested(data, p)
        field_name = ".".join(p)
        if not exists:
            status = "missing"
            severity = "blocking"
            missing_required_fields.append(field_name)
        else:
            status, severity = _field_status(value)
            if status == "empty":
                warnings.append(f"empty_field:{field_name}")
        field_checks.append({"field": field_name, "status": status, "severity": severity})

    runbook_id = str(data.get("runbook_id") or "")
    evidence = data.get("evidence") if isinstance(data.get("evidence"), dict) else {}

    def add_evidence_check(name: str, ok: bool, blocking: bool = False) -> None:
        status = "filled" if ok else "missing"
        severity = "blocking" if (blocking and not ok) else ("warning" if not ok else "info")
        evidence_checks.append({"field": name, "status": status, "severity": severity})
        if not ok and blocking:
            missing_evidence_fields.append(name)

    add_evidence_check("lsblk_before_after", bool(data.get("pre_state", {}).get("lsblk")) and bool(data.get("post_state", {}).get("lsblk")), blocking=True)
    add_evidence_check("findmnt_before_after", bool(data.get("pre_state", {}).get("findmnt")) and bool(data.get("post_state", {}).get("findmnt")), blocking=True)
    add_evidence_check("mount_before_after", bool(data.get("pre_state", {}).get("mount")) and bool(data.get("post_state", {}).get("mount")), blocking=True)
    add_evidence_check("runner_stdout_json_is_object", isinstance(data.get("runner_result", {}).get("stdout_json"), dict), blocking=True)
    add_evidence_check("audit_jsonl_excerpt", bool(evidence.get("audit_jsonl_excerpt")), blocking=True)
    add_evidence_check("jobfile_hash", bool(evidence.get("jobfile_hash")), blocking=True)
    add_evidence_check("snapshot_fingerprint", bool(evidence.get("snapshot_fingerprint")), blocking=True)
    add_evidence_check("pass_fail_allowed", str(data.get("pass_fail") or "") in _ALLOWED_PASS_FAIL, blocking=True)
    add_evidence_check("rollback_status", bool(str(data.get("rollback_status") or "").strip()), blocking=True)

    if runbook_id in _WRITE_RUNBOOKS:
        add_evidence_check("bytes_written_or_null", "bytes_written" in evidence, blocking=True)
        add_evidence_check("expected_sha256", bool(evidence.get("expected_sha256")), blocking=True)
        add_evidence_check("actual_sha256", bool(evidence.get("actual_sha256")), blocking=True)
        add_evidence_check("verify_status", bool(str(evidence.get("verify_status") or "").strip()), blocking=True)
        add_evidence_check("verify_status_not_mismatch", str(evidence.get("verify_status") or "").lower() != "mismatch", blocking=True)

    def add_safety(code: str, condition: bool, blocking: bool = True) -> None:
        if condition:
            safety_checks.append({"field": code, "status": "invalid", "severity": "blocking" if blocking else "warning"})
            if blocking:
                blocking_findings.append(code)
        else:
            safety_checks.append({"field": code, "status": "filled", "severity": "info"})

    add_safety("MANUAL_RESULT_INTERNAL_DRIVE_TOUCHED", bool(evidence.get("internal_drive_touched")))
    add_safety("MANUAL_RESULT_UNTRACKED_MOUNT_CHANGE", bool(evidence.get("untracked_mount_change")))
    add_safety("MANUAL_RESULT_VERIFY_MISMATCH", str(evidence.get("verify_status") or "").lower() == "mismatch")
    add_safety("MANUAL_RESULT_FAILED", str(data.get("pass_fail") or "").lower() == "failed")
    add_safety("MANUAL_RESULT_ROLLBACK_INCOMPLETE", str(data.get("rollback_status") or "").strip().lower() in {"", "incomplete"})
    add_safety("MANUAL_RESULT_STDOUT_NOT_JSON", not isinstance(data.get("runner_result", {}).get("stdout_json"), dict))
    add_safety("MANUAL_RESULT_TARGET_DEVICE_MISSING", not bool(str(data.get("target_device") or "").strip()))

    target_device = str(data.get("target_device") or "")
    suspicious_target = target_device.startswith("/dev/sda") or target_device.startswith("/dev/nvme0n1")
    if suspicious_target:
        safety_checks.append({"field": "MANUAL_RESULT_TARGET_DEVICE_SUSPICIOUS", "status": "invalid", "severity": "warning"})
        warnings.append("MANUAL_RESULT_TARGET_DEVICE_SUSPICIOUS")

    if missing_required_fields:
        blocking_findings.append("RESULT_SCHEMA_MISSING_FIELD")
    if missing_evidence_fields:
        blocking_findings.append("RESULT_EVIDENCE_MISSING")

    expected_validator_status = "ok"
    if blocking_findings:
        expected_validator_status = "blocked"
    elif warnings:
        expected_validator_status = "review_required"

    check_status = "ok"
    if blocking_findings:
        check_status = "blocked"
    elif warnings:
        check_status = "review_required"

    validator_readiness = {
        "ready_for_ingestion_validator": check_status != "blocked",
        "expected_validator_status": expected_validator_status,
        "expected_blockers": list(dict.fromkeys(blocking_findings)),
        "missing_required_fields": missing_required_fields,
        "missing_evidence_fields": missing_evidence_fields,
    }

    return {
        "check_status": check_status,
        "result_file_path": result_file,
        "runbook_id": runbook_id,
        "field_checks": field_checks,
        "evidence_checks": evidence_checks,
        "safety_checks": safety_checks,
        "validator_readiness": validator_readiness,
        "blocking_findings": list(dict.fromkeys(blocking_findings)),
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
    }
