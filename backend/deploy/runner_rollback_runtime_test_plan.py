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


def _rollback_case(code: str, cleanup_behavior: str, preservation_behavior: str) -> dict[str, Any]:
    return {
        "code": code,
        "expected_cleanup_behavior": cleanup_behavior,
        "expected_preservation_behavior": preservation_behavior,
        "manual_operator_required": True,
        "auto_allowed": False,
        "required_evidence": [
            "rollback_case_code",
            "artifact_baseline",
            "artifact_after_case",
            "audit_jsonl_before_after",
            "lock_directory_before_after",
            "job_directory_before_after",
            "tempfile_list_before_after",
        ],
    }


def _cleanup_boundary(path_hint: str) -> dict[str, Any]:
    return {
        "path_hint": path_hint,
        "auto_allowed": False,
        "manual_operator_required": True,
        "requires_prefix_check": True,
        "forbid_symlinks": True,
    }


def build_runner_rollback_runtime_test_plan() -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    preconditions = [
        _manual_step("PRECONDITION_HOTPLUG_RACE_PLAN_PRESENT", "hotplug_race_plan_available", requires_root=False),
        _manual_step("PRECONDITION_DEVICE_REENUMERATION_PLAN_PRESENT", "device_reenumeration_plan_available", requires_root=False),
        _manual_step("PRECONDITION_FAILURE_INJECTION_PLAN_PRESENT", "failure_injection_plan_available", requires_root=False),
        _manual_step("PRECONDITION_INSTALL_CONSISTENCY_PRESENT", "install_consistency_available", requires_root=False),
        _manual_step("PRECONDITION_ROLLBACK_MANIFEST_PRESENT", "rollback_manifest_available", requires_root=False),
        _manual_step("PRECONDITION_DISPOSABLE_TEST_MEDIA_AVAILABLE", "disposable_test_media_available", requires_root=False),
        _manual_step("PRECONDITION_FULL_BACKUP_AVAILABLE", "backup_confirmed", requires_root=False),
        _manual_step("PRECONDITION_OPERATOR_MANUAL_CONFIRMATION", "operator_confirmed_manual_execution", requires_root=False),
    ]

    test_steps = [
        _manual_step("ROLLBACK_STEP_DOCUMENT_ROLLBACK_MANIFEST", "rollback_manifest_documented", requires_root=False),
        _manual_step("ROLLBACK_STEP_DEFINE_ALLOWED_ARTIFACT_PATHS", "allowed_artifact_paths_defined", requires_root=False),
        _manual_step("ROLLBACK_STEP_CAPTURE_ARTIFACT_BASELINE", "artifact_baseline_documented", requires_root=False),
        _manual_step("ROLLBACK_STEP_PLAN_CASES_INDIVIDUALLY", "rollback_cases_planned_individually", requires_root=False),
        _manual_step("ROLLBACK_STEP_VALIDATE_AUDIT_LOCK_JOB_TMP_PER_CASE", "audit_lock_job_tmp_validated_per_case", requires_root=False),
        _manual_step("ROLLBACK_STEP_VALIDATE_NO_SYSTEM_PATH_CHANGES_PER_CASE", "no_system_path_changes_verified", requires_root=False),
        _manual_step("ROLLBACK_STEP_DOCUMENT_RESULT_PER_CASE", "result_documented_per_case", requires_root=False),
    ]

    rollback_cases = [
        _rollback_case("ROLLBACK_CASE_STALE_LOCK_CLEANUP", "stale_lock_removed_in_allowed_test_scope", "audit_preserved"),
        _rollback_case("ROLLBACK_CASE_EXPIRED_JOB_CLEANUP", "expired_job_removed_in_allowed_test_scope", "audit_preserved"),
        _rollback_case("ROLLBACK_CASE_TEMP_JOBFILE_CLEANUP", "temporary_jobfile_removed_in_allowed_test_scope", "audit_preserved"),
        _rollback_case("ROLLBACK_CASE_AUDIT_PRESERVATION_AFTER_ABORT", "cleanup_without_audit_delete", "audit_archived_or_marked"),
        _rollback_case("ROLLBACK_CASE_FAILED_RUNNER_LEAVES_LOCK", "lock_cleanup_required", "audit_preserved"),
        _rollback_case("ROLLBACK_CASE_FAILED_RUNNER_LEAVES_TMP_JOB", "tmp_job_cleanup_required", "audit_preserved"),
        _rollback_case("ROLLBACK_CASE_FAILED_RUNNER_LEAVES_PARTIAL_AUDIT", "partial_audit_marked_not_deleted", "audit_preserved"),
        _rollback_case("ROLLBACK_CASE_AFTER_TIMEOUT", "timeout_artifacts_cleaned_in_test_scope", "audit_preserved"),
        _rollback_case("ROLLBACK_CASE_AFTER_INVALID_JSON", "invalid_json_artifacts_cleaned_in_test_scope", "audit_preserved"),
        _rollback_case("ROLLBACK_CASE_AFTER_OPERATOR_ABORT", "operator_abort_artifacts_cleaned_in_test_scope", "audit_preserved"),
        _rollback_case("ROLLBACK_CASE_AFTER_FAILURE_INJECTION_ABORT", "failure_injection_abort_artifacts_cleaned", "audit_preserved"),
        _rollback_case("ROLLBACK_CASE_AFTER_HOTPLUG_RACE_ABORT", "hotplug_race_abort_artifacts_cleaned", "audit_preserved"),
    ]

    required_evidence = [
        "rollback_case_code",
        "artifact_baseline",
        "artifact_after_case",
        "allowed_cleanup_paths",
        "forbidden_cleanup_paths",
        "audit_jsonl_before_after",
        "lock_directory_before_after",
        "job_directory_before_after",
        "tempfile_list_before_after",
        "proof_no_etc_changes",
        "proof_no_opt_changes",
        "proof_no_var_lib_changes_except_allowed_testjobdir",
        "proof_no_sudoers_changes",
        "proof_no_device_write",
        "proof_no_mount_changes",
    ]

    risk_controls = [
        "cleanup_only_on_allowed_test_artifacts",
        "no_system_path_deletion",
        "no_recursive_delete_without_prefix_check",
        "no_symlink_following",
        "no_productive_jobdirs",
        "never_delete_audit_only_archive_or_mark",
        "run_cases_individually",
        "reassess_state_after_each_case",
    ]

    stop_conditions = [
        "allowed_cleanup_prefix_not_unique",
        "symlink_in_cleanup_path",
        "cleanup_path_points_to_system_or_root",
        "audit_missing",
        "jobdir_unclear",
        "lockdir_unclear",
        "operator_unsure",
    ]

    cleanup_boundaries = [
        _cleanup_boundary("allowed_test_job_directories"),
        _cleanup_boundary("allowed_test_lock_directories"),
        _cleanup_boundary("allowed_test_tmp_directories"),
        _cleanup_boundary("allowed_test_audit_directories"),
    ]

    plan_status = "ok"
    if errors:
        plan_status = "blocked"
    elif warnings:
        plan_status = "review_required"

    return {
        "plan_status": plan_status,
        "gap_code": "RUNNER_GAP_ROLLBACK_RUNTIME_OPEN",
        "preconditions": preconditions,
        "test_steps": test_steps,
        "rollback_cases": rollback_cases,
        "required_evidence": required_evidence,
        "risk_controls": risk_controls,
        "stop_conditions": stop_conditions,
        "cleanup_boundaries": cleanup_boundaries,
        "warnings": warnings,
        "errors": errors,
    }
