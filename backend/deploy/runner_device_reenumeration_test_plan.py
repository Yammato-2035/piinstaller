from __future__ import annotations

from typing import Any


def _manual_step(code: str, expected_result: str, *, requires_root: bool) -> dict[str, Any]:
    return {
        "code": code,
        "requires_root": bool(requires_root),
        "manual_operator_required": True,
        "auto_allowed": False,
        "expected_result": expected_result,
    }


def _case(code: str, result_code: str, gate_behavior: str) -> dict[str, Any]:
    return {
        "code": code,
        "expected_result_code": result_code,
        "expected_gate_behavior": gate_behavior,
        "manual_operator_required": True,
        "auto_allowed": False,
        "required_evidence": [
            "case_code",
            "target_device_before",
            "target_device_after",
            "realpath_before",
            "realpath_after",
            "snapshot_before",
            "snapshot_after",
            "fingerprint_before",
            "fingerprint_after",
            "audit_jsonl",
            "lock_cleanup_proof",
        ],
    }


def build_runner_device_reenumeration_test_plan() -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    preconditions = [
        _manual_step("PRECONDITION_REAL_WRITE_HW_E2E_PLAN_PRESENT", "real_write_hw_e2e_plan_available", requires_root=False),
        _manual_step("PRECONDITION_FAILURE_INJECTION_HW_PLAN_PRESENT", "failure_injection_hw_plan_available", requires_root=False),
        _manual_step("PRECONDITION_DISPOSABLE_MEDIA_AVAILABLE", "disposable_media_available", requires_root=False),
        _manual_step("PRECONDITION_MEDIA_PHYSICALLY_LABELED", "media_label_confirmed", requires_root=False),
        _manual_step("PRECONDITION_FULL_BACKUP_AVAILABLE", "backup_confirmed", requires_root=False),
        _manual_step("PRECONDITION_HARDWARE_GATE_TEST_READY", "hardware_gate_test_ready", requires_root=False),
        _manual_step("PRECONDITION_REAL_WRITE_GUARD_READY", "real_write_guard_ready", requires_root=False),
        _manual_step("PRECONDITION_SNAPSHOT_FINGERPRINT_AVAILABLE", "snapshot_and_fingerprint_available", requires_root=False),
        _manual_step("PRECONDITION_OPERATOR_MANUAL_CONFIRMATION", "operator_confirmed_manual_execution", requires_root=False),
    ]

    test_steps = [
        _manual_step("REENUM_STEP_IDENTIFY_UNIQUE_TEST_MEDIA", "test_media_unique", requires_root=False),
        _manual_step("REENUM_STEP_CAPTURE_BASELINE_LSBLK_FINDMNT_MOUNT", "baseline_state_documented", requires_root=False),
        _manual_step("REENUM_STEP_DOCUMENT_HW_GATE_AND_GUARD", "gate_and_guard_documented", requires_root=False),
        _manual_step("REENUM_STEP_DOCUMENT_SNAPSHOT_FINGERPRINT", "snapshot_fingerprint_documented", requires_root=False),
        _manual_step("REENUM_STEP_PLAN_CASES_INDIVIDUALLY", "cases_planned_individually", requires_root=False),
        _manual_step("REENUM_STEP_COMPARE_TARGET_REALPATH_FINGERPRINT_AFTER_EACH_CASE", "target_realpath_fingerprint_compared", requires_root=False),
        _manual_step("REENUM_STEP_DOCUMENT_AUDIT_LOCK_STOPCODE_AFTER_EACH_CASE", "audit_lock_stopcode_documented", requires_root=False),
        _manual_step("REENUM_STEP_DOCUMENT_MEDIA_MOUNT_STATE_AFTER_EACH_CASE", "media_mount_state_documented", requires_root=False),
        _manual_step("REENUM_STEP_DOCUMENT_RESULT_PER_CASE", "result_documented_per_case", requires_root=False),
    ]

    reenumeration_cases = [
        _case("REENUM_CASE_USB_REPLUG_SHORT", "RUNNER_REENUM_USB_REPLUG_HANDLED", "abort"),
        _case("REENUM_CASE_TARGET_PATH_CHANGED_SDB_TO_SDC", "RUNNER_REENUM_PATH_CHANGED_HANDLED", "blocked"),
        _case("REENUM_CASE_SAME_MEDIA_NEW_KERNEL_NAME", "RUNNER_REENUM_KERNEL_NAME_CHANGED_HANDLED", "review_required"),
        _case("REENUM_CASE_OTHER_MEDIA_ON_OLD_PATH", "RUNNER_REENUM_OLD_PATH_REBOUND_OTHER_MEDIA", "abort"),
        _case("REENUM_CASE_MEDIA_DISAPPEARS_PREWRITE_RECHECK", "RUNNER_REENUM_DISAPPEAR_PREWRITE_HANDLED", "abort"),
        _case("REENUM_CASE_MEDIA_DISAPPEARS_PREVERIFY", "RUNNER_REENUM_DISAPPEAR_PREVERIFY_HANDLED", "abort"),
        _case("REENUM_CASE_TWO_SIMILAR_USB_MEDIA", "RUNNER_REENUM_AMBIGUOUS_MEDIA_HANDLED", "blocked"),
        _case("REENUM_CASE_PARTITION_VS_DISK_PATH_CONFUSION", "RUNNER_REENUM_PARTITION_DISK_CONFUSION_HANDLED", "blocked"),
    ]

    required_evidence = [
        "case_code",
        "target_device_before",
        "target_device_after",
        "realpath_before",
        "realpath_after",
        "lsblk_before_after",
        "findmnt_before_after",
        "mount_before_after",
        "snapshot_before",
        "snapshot_after",
        "fingerprint_before",
        "fingerprint_after",
        "hardware_gate_report",
        "real_write_guard_report",
        "runner_stdout_json_if_present",
        "audit_jsonl",
        "lock_cleanup_proof",
        "proof_no_device_write",
        "proof_no_mount_changes_except_physical_reconnect",
        "proof_no_internal_drives_touched",
    ]

    risk_controls = [
        "disposable_media_only",
        "no_productive_media",
        "no_remote_test_without_local_control",
        "run_reenumeration_cases_individually",
        "no_parallel_runner",
        "no_retry_after_device_change",
        "abort_on_unclear_media_identity",
        "abort_on_multiple_candidate_media",
        "reassess_state_after_each_case",
    ]

    stop_conditions = [
        "test_media_not_unique",
        "multiple_possible_removable_media",
        "other_media_on_old_path",
        "snapshot_fingerprint_mismatch",
        "hardware_gate_not_test_ready",
        "real_write_guard_not_ready",
        "audit_missing",
        "lock_not_released",
        "operator_unsure",
    ]

    rollback_steps = [
        {"code": "ROLLBACK_DELETE_TEST_JOB", "auto_allowed": False},
        {"code": "ROLLBACK_REMOVE_STALE_LOCKFILE_IF_PRESENT", "auto_allowed": False},
        {"code": "ROLLBACK_ARCHIVE_AUDIT", "auto_allowed": False},
        {"code": "ROLLBACK_DOCUMENT_RESULT", "auto_allowed": False},
        {"code": "ROLLBACK_REIDENTIFY_MEDIA", "auto_allowed": False},
        {"code": "ROLLBACK_NO_REUSE_WITHOUT_NEW_HARDWARE_GATE_CHECK", "auto_allowed": False},
        {"code": "ROLLBACK_NO_AUTOMATED_REPAIR_CLAIM", "auto_allowed": False},
    ]

    plan_status = "ok"
    if errors:
        plan_status = "blocked"
    elif warnings:
        plan_status = "review_required"

    return {
        "plan_status": plan_status,
        "gap_code": "RUNNER_GAP_DEVICE_REENUMERATION_OPEN",
        "preconditions": preconditions,
        "test_steps": test_steps,
        "reenumeration_cases": reenumeration_cases,
        "required_evidence": required_evidence,
        "risk_controls": risk_controls,
        "stop_conditions": stop_conditions,
        "rollback_steps": rollback_steps,
        "warnings": warnings,
        "errors": errors,
    }
