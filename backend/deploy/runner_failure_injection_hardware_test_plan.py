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


def _failure_case(code: str, result_code: str, write_behavior: str, verify_behavior: str) -> dict[str, Any]:
    return {
        "code": code,
        "expected_result_code": result_code,
        "expected_write_behavior": write_behavior,
        "expected_verify_behavior": verify_behavior,
        "requires_testmode": True,
        "manual_operator_required": True,
        "auto_allowed": False,
        "required_evidence": [
            "failure_case_code",
            "testmode_flag",
            "runner_stdout_json",
            "runner_stderr",
            "audit_jsonl",
            "lock_cleanup_proof",
            "bytes_written",
            "verify_result",
            "expected_sha256",
            "actual_sha256",
            "mismatch_offset_if_present",
        ],
    }


def build_runner_failure_injection_hardware_test_plan() -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    preconditions = [
        _manual_step("PRECONDITION_REAL_WRITE_HW_E2E_PLAN_PRESENT", "real_write_hw_e2e_plan_available", requires_root=False),
        _manual_step("PRECONDITION_PRIVILEGED_VALIDATION_PLAN_PRESENT", "privileged_validation_plan_available", requires_root=False),
        _manual_step("PRECONDITION_DISPOSABLE_MEDIA_AVAILABLE", "disposable_media_available", requires_root=False),
        _manual_step("PRECONDITION_MEDIA_PHYSICALLY_LABELED", "media_label_confirmed", requires_root=False),
        _manual_step("PRECONDITION_FULL_BACKUP_AVAILABLE", "backup_confirmed", requires_root=False),
        _manual_step("PRECONDITION_HARDWARE_GATE_TEST_READY", "hardware_gate_test_ready", requires_root=False),
        _manual_step("PRECONDITION_REAL_WRITE_GUARD_READY", "real_write_guard_ready", requires_root=False),
        _manual_step("PRECONDITION_FAILURE_INJECTION_HOOKS_AVAILABLE", "failure_injection_hooks_confirmed", requires_root=False),
        _manual_step("PRECONDITION_OPERATOR_MANUAL_CONFIRMATION", "operator_confirmed_manual_execution", requires_root=False),
    ]

    test_steps = [
        _manual_step("FI_HW_STEP_IDENTIFY_UNIQUE_TEST_MEDIA", "test_media_unique", requires_root=False),
        _manual_step("FI_HW_STEP_CAPTURE_BASELINE_LSBLK_FINDMNT_MOUNT", "baseline_state_documented", requires_root=False),
        _manual_step("FI_HW_STEP_DOCUMENT_HW_GATE_AND_GUARD", "gate_and_guard_documented", requires_root=False),
        _manual_step("FI_HW_STEP_PREPARE_SMALL_TEST_IMAGE", "small_test_image_prepared", requires_root=False),
        _manual_step("FI_HW_STEP_CONFIRM_HAPPY_PATH_REFERENCE", "happy_path_reference_confirmed", requires_root=False),
        _manual_step("FI_HW_STEP_PLAN_FAILURE_CASE_RUNS_INDIVIDUALLY", "failure_runs_planned_individually", requires_root=False),
        _manual_step("FI_HW_STEP_DOCUMENT_AUDIT_LOCK_VERIFY_PER_CASE", "audit_lock_verify_documented_per_case", requires_root=False),
        _manual_step("FI_HW_STEP_DOCUMENT_MEDIA_MOUNT_STATE_PER_CASE", "media_mount_state_documented_per_case", requires_root=False),
        _manual_step("FI_HW_STEP_DOCUMENT_RESULT_PER_CASE", "result_documented_per_case", requires_root=False),
    ]

    failure_cases = [
        _failure_case("FAIL_BEFORE_OPEN", "RUNNER_FAIL_BEFORE_OPEN_HANDLED", "no_write_started", "verify_not_started"),
        _failure_case("FAIL_AFTER_OPEN", "RUNNER_FAIL_AFTER_OPEN_HANDLED", "write_aborted_early", "verify_blocked"),
        _failure_case("FAIL_AFTER_CHUNKS", "RUNNER_FAIL_AFTER_CHUNKS_HANDLED", "partial_write_detected", "verify_fails"),
        _failure_case("FAIL_DURING_FSYNC", "RUNNER_FAIL_DURING_FSYNC_HANDLED", "write_sync_failed", "verify_fails"),
        _failure_case("FAIL_VERIFY_MISMATCH", "RUNNER_FAIL_VERIFY_MISMATCH_HANDLED", "write_completed_verify_failed", "verify_mismatch"),
        _failure_case("FAIL_DEVICE_CHANGED", "RUNNER_FAIL_DEVICE_CHANGED_HANDLED", "write_aborted_device_changed", "verify_blocked"),
        _failure_case("SIMULATED_READONLY_FLIP", "RUNNER_FAIL_READONLY_FLIP_HANDLED", "write_blocked_readonly", "verify_blocked"),
        _failure_case("SIMULATED_MOUNTED_FLIP", "RUNNER_FAIL_MOUNTED_FLIP_HANDLED", "write_aborted_on_mount_change", "verify_blocked"),
        _failure_case("VERIFY_SHORT_READ", "RUNNER_FAIL_VERIFY_SHORT_READ_HANDLED", "write_completed", "verify_short_read_detected"),
        _failure_case("VERIFY_MISMATCH", "RUNNER_FAIL_VERIFY_MISMATCH_HANDLED", "write_completed", "verify_mismatch_detected"),
    ]

    required_evidence = [
        "failure_case_code",
        "testmode_flag",
        "target_device",
        "lsblk_before_after",
        "findmnt_before_after",
        "mount_before_after",
        "runner_stdout_json",
        "runner_stderr",
        "audit_jsonl",
        "lock_cleanup_proof",
        "bytes_written",
        "verify_result",
        "expected_sha256",
        "actual_sha256",
        "mismatch_offset_if_present",
        "proof_no_retry_after_mismatch",
        "proof_no_unexpected_mount_changes",
        "proof_no_internal_drives_touched",
    ]

    risk_controls = [
        "single_disposable_test_media_only",
        "no_productive_media",
        "no_remote_test_without_local_control",
        "run_failure_cases_individually",
        "no_retry_after_failure",
        "no_parallel_runner",
        "abort_on_device_change",
        "abort_on_unexpected_mount_change",
        "abort_on_operator_uncertainty",
        "reassess_state_after_each_failure_case",
    ]

    stop_conditions = [
        "test_media_not_unique",
        "multiple_possible_removable_media",
        "hardware_gate_not_test_ready",
        "real_write_guard_not_ready",
        "testmode_not_clearly_set",
        "audit_missing",
        "lock_not_released",
        "verify_mismatch_unexplained",
        "device_changed",
        "mount_state_unexpected_change",
        "operator_unsure",
    ]

    rollback_steps = [
        {"code": "ROLLBACK_DELETE_TEST_JOB", "auto_allowed": False},
        {"code": "ROLLBACK_REMOVE_STALE_LOCKFILE_IF_PRESENT", "auto_allowed": False},
        {"code": "ROLLBACK_ARCHIVE_AUDIT", "auto_allowed": False},
        {"code": "ROLLBACK_DOCUMENT_RESULT", "auto_allowed": False},
        {"code": "ROLLBACK_MARK_MEDIA_OVERWRITTEN_OR_INCONSISTENT", "auto_allowed": False},
        {"code": "ROLLBACK_NO_AUTOMATED_REPAIR_CLAIM", "auto_allowed": False},
        {"code": "ROLLBACK_NO_REUSE_WITHOUT_NEW_HARDWARE_GATE_CHECK", "auto_allowed": False},
    ]

    plan_status = "ok"
    if errors:
        plan_status = "blocked"
    elif warnings:
        plan_status = "review_required"

    return {
        "plan_status": plan_status,
        "gap_code": "RUNNER_GAP_FAILURE_INJECTION_HW_OPEN",
        "preconditions": preconditions,
        "test_steps": test_steps,
        "failure_cases": failure_cases,
        "required_evidence": required_evidence,
        "risk_controls": risk_controls,
        "stop_conditions": stop_conditions,
        "rollback_steps": rollback_steps,
        "warnings": warnings,
        "errors": errors,
    }
