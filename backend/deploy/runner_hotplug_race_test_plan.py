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


def _race_case(code: str, trigger_point: str, result_code: str, gate_behavior: str) -> dict[str, Any]:
    return {
        "code": code,
        "trigger_point": trigger_point,
        "expected_result_code": result_code,
        "expected_gate_behavior": gate_behavior,
        "manual_operator_required": True,
        "auto_allowed": False,
        "required_evidence": [
            "race_case_code",
            "trigger_point",
            "target_device",
            "snapshot_before_after",
            "fingerprint_before_after",
            "mount_state_before_after",
            "readonly_state_before_after",
            "audit_jsonl",
            "lock_cleanup_proof",
            "expected_abort_code",
            "actual_abort_code",
        ],
    }


def build_runner_hotplug_race_test_plan() -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    preconditions = [
        _manual_step("PRECONDITION_DEVICE_REENUM_PLAN_PRESENT", "device_reenumeration_plan_available", requires_root=False),
        _manual_step("PRECONDITION_FAILURE_INJECTION_HW_PLAN_PRESENT", "failure_injection_plan_available", requires_root=False),
        _manual_step("PRECONDITION_REAL_WRITE_HW_E2E_PLAN_PRESENT", "real_write_hw_e2e_plan_available", requires_root=False),
        _manual_step("PRECONDITION_DISPOSABLE_MEDIA_AVAILABLE", "disposable_media_available", requires_root=False),
        _manual_step("PRECONDITION_MEDIA_PHYSICALLY_LABELED", "media_label_confirmed", requires_root=False),
        _manual_step("PRECONDITION_FULL_BACKUP_AVAILABLE", "backup_confirmed", requires_root=False),
        _manual_step("PRECONDITION_HARDWARE_GATE_TEST_READY", "hardware_gate_test_ready", requires_root=False),
        _manual_step("PRECONDITION_REAL_WRITE_GUARD_READY", "real_write_guard_ready", requires_root=False),
        _manual_step("PRECONDITION_OPERATOR_MANUAL_CONFIRMATION", "operator_confirmed_manual_execution", requires_root=False),
    ]

    test_steps = [
        _manual_step("HOTPLUG_STEP_IDENTIFY_UNIQUE_TEST_MEDIA", "test_media_unique", requires_root=False),
        _manual_step("HOTPLUG_STEP_CAPTURE_BASELINE_LSBLK_FINDMNT_MOUNT", "baseline_state_documented", requires_root=False),
        _manual_step("HOTPLUG_STEP_DOCUMENT_HW_GATE_AND_GUARD", "gate_and_guard_documented", requires_root=False),
        _manual_step("HOTPLUG_STEP_DOCUMENT_SNAPSHOT_FINGERPRINT", "snapshot_fingerprint_documented", requires_root=False),
        _manual_step("HOTPLUG_STEP_PLAN_RACE_CASES_INDIVIDUALLY", "race_cases_planned_individually", requires_root=False),
        _manual_step("HOTPLUG_STEP_DOCUMENT_TRIGGER_POINT_PER_CASE", "trigger_point_documented_per_case", requires_root=False),
        _manual_step("HOTPLUG_STEP_DOCUMENT_EXPECTED_ABORT_BLOCK_CODE_PER_CASE", "expected_abort_block_code_documented", requires_root=False),
        _manual_step("HOTPLUG_STEP_DOCUMENT_AUDIT_LOCK_STOPCODE_PER_CASE", "audit_lock_stopcode_documented", requires_root=False),
        _manual_step("HOTPLUG_STEP_DOCUMENT_MEDIA_MOUNT_STATE_PER_CASE", "media_mount_state_documented", requires_root=False),
        _manual_step("HOTPLUG_STEP_DOCUMENT_RESULT_PER_CASE", "result_documented_per_case", requires_root=False),
    ]

    race_cases = [
        _race_case("RACE_CASE_HOTPLUG_DURING_PREWRITE_RECHECK", "pre_write_recheck", "RUNNER_RACE_PREWRITE_RECHECK_ABORTED", "abort"),
        _race_case("RACE_CASE_HOTPLUG_AFTER_DEVICE_OPEN", "after_device_open", "RUNNER_RACE_AFTER_OPEN_ABORTED", "failed"),
        _race_case("RACE_CASE_HOTPLUG_DURING_WRITE_CHUNK", "during_write_chunk", "RUNNER_RACE_DURING_CHUNK_ABORTED", "failed"),
        _race_case("RACE_CASE_HOTPLUG_BEFORE_FSYNC", "before_fsync", "RUNNER_RACE_BEFORE_FSYNC_ABORTED", "failed"),
        _race_case("RACE_CASE_HOTPLUG_DURING_VERIFY", "during_verify", "RUNNER_RACE_DURING_VERIFY_ABORTED", "abort"),
        _race_case("RACE_CASE_UNEXPECTED_MOUNT_BEFORE_WRITE", "before_write", "RUNNER_RACE_UNEXPECTED_MOUNT_BEFORE_WRITE_BLOCKED", "blocked"),
        _race_case("RACE_CASE_UNEXPECTED_MOUNT_AFTER_OPEN", "after_open", "RUNNER_RACE_UNEXPECTED_MOUNT_AFTER_OPEN_ABORTED", "abort"),
        _race_case("RACE_CASE_UNEXPECTED_MOUNT_BEFORE_VERIFY", "before_verify", "RUNNER_RACE_UNEXPECTED_MOUNT_BEFORE_VERIFY_ABORTED", "abort"),
        _race_case("RACE_CASE_READONLY_FLIP_BEFORE_WRITE", "before_write", "RUNNER_RACE_READONLY_BEFORE_WRITE_BLOCKED", "blocked"),
        _race_case("RACE_CASE_READONLY_FLIP_DURING_WRITE", "during_write", "RUNNER_RACE_READONLY_DURING_WRITE_ABORTED", "failed"),
        _race_case("RACE_CASE_LOCK_STALE_AFTER_ABORT", "post_abort_lock_cleanup", "RUNNER_RACE_STALE_LOCK_CLEANUP_REQUIRED", "review_required"),
        _race_case("RACE_CASE_PARALLEL_RUNNER_STARTS_DURING_RACE", "during_race_parallel_start", "RUNNER_RACE_PARALLEL_RUNNER_BLOCKED", "blocked"),
    ]

    required_evidence = [
        "race_case_code",
        "trigger_point",
        "target_device",
        "lsblk_before_after",
        "findmnt_before_after",
        "mount_before_after",
        "snapshot_before_after",
        "fingerprint_before_after",
        "mount_state_before_after",
        "readonly_state_before_after",
        "runner_stdout_json_if_present",
        "runner_stderr",
        "audit_jsonl",
        "lock_cleanup_proof",
        "expected_abort_code",
        "actual_abort_code",
        "proof_no_retry",
        "proof_no_unexpected_internal_drive_access",
        "proof_no_untracked_mount_change",
    ]

    risk_controls = [
        "disposable_media_only",
        "no_productive_media",
        "no_remote_test_without_local_control",
        "run_race_cases_individually",
        "no_parallel_runner_except_planned_negative_case",
        "no_retry_after_race_abort",
        "abort_on_device_change",
        "abort_on_unexpected_mount",
        "abort_on_stale_lock",
        "reassess_state_after_each_race_case",
    ]

    stop_conditions = [
        "test_media_not_unique",
        "multiple_possible_removable_media",
        "hardware_gate_not_test_ready",
        "real_write_guard_not_ready",
        "unexpected_mount_state",
        "unexpected_readonly_flip",
        "device_changed",
        "audit_missing",
        "lock_not_released",
        "internal_drive_becomes_target",
        "operator_unsure",
    ]

    rollback_steps = [
        {"code": "ROLLBACK_DELETE_TEST_JOB", "auto_allowed": False},
        {"code": "ROLLBACK_REMOVE_STALE_LOCKFILE_IF_PRESENT", "auto_allowed": False},
        {"code": "ROLLBACK_ARCHIVE_AUDIT", "auto_allowed": False},
        {"code": "ROLLBACK_DOCUMENT_RESULT", "auto_allowed": False},
        {"code": "ROLLBACK_REIDENTIFY_MEDIA", "auto_allowed": False},
        {"code": "ROLLBACK_MARK_MEDIA_OVERWRITTEN_OR_INCONSISTENT", "auto_allowed": False},
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
        "gap_code": "RUNNER_GAP_HOTPLUG_RACE_OPEN",
        "preconditions": preconditions,
        "test_steps": test_steps,
        "race_cases": race_cases,
        "required_evidence": required_evidence,
        "risk_controls": risk_controls,
        "stop_conditions": stop_conditions,
        "rollback_steps": rollback_steps,
        "warnings": warnings,
        "errors": errors,
    }
