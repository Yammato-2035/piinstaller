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


def build_runner_real_write_hardware_e2e_test_plan() -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    preconditions = [
        _manual_step("PRECONDITION_PRIVILEGED_VALIDATION_PLAN_PRESENT", "privileged_validation_plan_available", requires_root=False),
        _manual_step("PRECONDITION_SUDOERS_RUNTIME_PLAN_PRESENT", "sudoers_runtime_plan_available", requires_root=False),
        _manual_step("PRECONDITION_HARDWARE_GATE_TEST_READY_CAPABLE", "hardware_gate_can_report_test_ready", requires_root=False),
        _manual_step("PRECONDITION_REAL_WRITE_GUARD_READY_CAPABLE", "real_write_guard_can_report_ready", requires_root=False),
        _manual_step("PRECONDITION_FINAL_CONFIRMATION_PRESENT", "final_confirmation_available", requires_root=False),
        _manual_step("PRECONDITION_HARNESS_PROOF_PRESENT", "harness_proof_available", requires_root=False),
        _manual_step("PRECONDITION_DISPOSABLE_MEDIA_AVAILABLE", "disposable_media_present", requires_root=False),
        _manual_step("PRECONDITION_MEDIA_PHYSICALLY_LABELED", "media_label_verified", requires_root=False),
        _manual_step("PRECONDITION_FULL_BACKUP_AVAILABLE", "backup_confirmed", requires_root=False),
        _manual_step("PRECONDITION_NO_PRODUCTIVE_MEDIA_ATTACHED", "only_system_disk_and_test_media_attached", requires_root=False),
        _manual_step("PRECONDITION_OPERATOR_MANUAL_CONFIRMATION", "operator_confirmed_manual_execution", requires_root=False),
    ]

    test_steps = [
        _manual_step("HW_E2E_STEP_IDENTIFY_TEST_MEDIA_UNIQUE", "single_target_media_identified", requires_root=False),
        _manual_step("HW_E2E_STEP_CAPTURE_LSBLK_FINDMNT_MOUNT_BEFORE", "pre_state_documented", requires_root=False),
        _manual_step("HW_E2E_STEP_HARDWARE_GATE_TEST_READY", "hardware_gate_test_ready", requires_root=False),
        _manual_step("HW_E2E_STEP_PREPARE_SMALL_TEST_IMAGE", "small_test_image_prepared", requires_root=False),
        _manual_step("HW_E2E_STEP_DOCUMENT_IMAGE_INSPECT", "image_inspect_report_documented", requires_root=False),
        _manual_step("HW_E2E_STEP_CREATE_FINAL_CONFIRMATION", "final_confirmation_created", requires_root=False),
        _manual_step("HW_E2E_STEP_CREATE_HARNESS_PROOF", "harness_proof_created", requires_root=False),
        _manual_step("HW_E2E_STEP_DOCUMENT_REAL_WRITE_GUARD_READY", "real_write_guard_ready_documented", requires_root=False),
        _manual_step("HW_E2E_STEP_MANUAL_PRIVILEGED_REAL_WRITE", "manual_real_write_step_planned_and_controlled", requires_root=True),
        _manual_step("HW_E2E_STEP_DOCUMENT_VERIFY_SHA256", "sha256_verify_documented", requires_root=False),
        _manual_step("HW_E2E_STEP_CAPTURE_LSBLK_FINDMNT_MOUNT_AFTER", "post_state_documented", requires_root=False),
        _manual_step("HW_E2E_STEP_VALIDATE_AUDIT_JOBFILE_LOCK", "audit_jobfile_lock_validated", requires_root=False),
        _manual_step("HW_E2E_STEP_DOCUMENT_RESULT", "result_documented", requires_root=False),
    ]

    negative_tests = [
        _manual_step("HW_E2E_NEGATIVE_WRONG_TARGET_MEDIA", "blocked", requires_root=False),
        _manual_step("HW_E2E_NEGATIVE_HARDWARE_GATE_NOT_READY", "blocked", requires_root=False),
        _manual_step("HW_E2E_NEGATIVE_FINAL_CONFIRMATION_MISSING", "blocked", requires_root=False),
        _manual_step("HW_E2E_NEGATIVE_HARNESS_PROOF_MISSING", "blocked", requires_root=False),
        _manual_step("HW_E2E_NEGATIVE_REAL_WRITE_GUARD_NOT_READY", "blocked", requires_root=False),
        _manual_step("HW_E2E_NEGATIVE_IMAGE_OVER_512MB", "blocked_or_review", requires_root=False),
        _manual_step("HW_E2E_NEGATIVE_MEDIA_SUDDENLY_MOUNTED", "abort", requires_root=False),
        _manual_step("HW_E2E_NEGATIVE_MEDIA_READONLY", "blocked", requires_root=False),
        _manual_step("HW_E2E_NEGATIVE_SNAPSHOT_FINGERPRINT_MISMATCH", "abort", requires_root=False),
        _manual_step("HW_E2E_NEGATIVE_VERIFY_MISMATCH", "abort_no_retry", requires_root=False),
    ]

    required_evidence = [
        "physical_test_media_label",
        "lsblk_before_after",
        "findmnt_before_after",
        "mount_before_after",
        "hardware_gate_report",
        "image_inspect_report",
        "final_confirmation_report",
        "harness_proof",
        "real_write_guard_report",
        "runner_jobfile_hash",
        "runner_audit_jsonl",
        "bytes_written",
        "expected_sha256",
        "actual_sha256",
        "verify_status",
        "proof_no_internal_drives_affected",
        "negative_test_results",
        "rollback_confirmation",
    ]

    risk_controls = [
        "single_disposable_test_media_only",
        "physically_labeled_test_media",
        "no_remote_test_without_local_control",
        "no_productive_media",
        "no_parallel_runners",
        "no_retry_after_verify_mismatch",
        "abort_on_device_change",
        "abort_on_mount_state_change",
        "abort_on_operator_uncertainty",
    ]

    stop_conditions = [
        "multiple_possible_removable_media",
        "test_media_not_unique",
        "hardware_gate_not_test_ready",
        "system_disk_as_target",
        "snapshot_fingerprint_changes",
        "mount_state_changes_unexpected",
        "verify_mismatch",
        "audit_missing",
        "operator_unsure",
    ]

    rollback_steps = [
        {"code": "ROLLBACK_DELETE_TEST_JOB", "auto_allowed": False},
        {"code": "ROLLBACK_REMOVE_STALE_LOCKFILE_IF_PRESENT", "auto_allowed": False},
        {"code": "ROLLBACK_ARCHIVE_AUDIT", "auto_allowed": False},
        {"code": "ROLLBACK_DOCUMENT_RESULT", "auto_allowed": False},
        {"code": "ROLLBACK_MARK_TEST_MEDIA_AS_OVERWRITTEN", "auto_allowed": False},
        {"code": "ROLLBACK_NO_AUTOMATED_RECOVERY_CLAIM", "auto_allowed": False},
    ]

    plan_status = "ok"
    if errors:
        plan_status = "blocked"
    elif warnings:
        plan_status = "review_required"

    return {
        "plan_status": plan_status,
        "gap_code": "RUNNER_GAP_REAL_WRITE_HARDWARE_E2E_OPEN",
        "preconditions": preconditions,
        "test_steps": test_steps,
        "negative_tests": negative_tests,
        "required_evidence": required_evidence,
        "risk_controls": risk_controls,
        "stop_conditions": stop_conditions,
        "rollback_steps": rollback_steps,
        "warnings": warnings,
        "errors": errors,
    }
