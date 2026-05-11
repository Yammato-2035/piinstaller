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


def build_runner_privileged_validation_test_plan() -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    preconditions = [
        _manual_step("PRECONDITION_SUDOERS_RUNTIME_PLAN_PRESENT", "sudoers_runtime_test_plan_available", requires_root=False),
        _manual_step("PRECONDITION_INSTALL_VALIDATOR_NOT_BLOCKED", "install_validator_ok_or_review", requires_root=False),
        _manual_step("PRECONDITION_INSTALL_CONSISTENCY_NOT_BLOCKED", "install_consistency_ok_or_review", requires_root=False),
        _manual_step("PRECONDITION_PACKAGE_BLUEPRINT_PRESENT", "package_blueprint_available", requires_root=False),
        _manual_step("PRECONDITION_PERMISSION_BOUNDARY_NOT_BLOCKED", "permission_boundary_ok_or_review", requires_root=False),
        _manual_step("PRECONDITION_SANDBOX_POLICY_PRESENT", "sandbox_policy_available", requires_root=False),
        _manual_step("PRECONDITION_ROOTLESS_E2E_SUCCESSFUL", "rootless_e2e_confirmed", requires_root=False),
        _manual_step("PRECONDITION_LOCAL_TESTHOST_AVAILABLE", "local_host_available", requires_root=False),
        _manual_step("PRECONDITION_FULL_BACKUP_AVAILABLE", "backup_confirmed", requires_root=False),
        _manual_step("PRECONDITION_OPERATOR_MANUAL_CONFIRMATION", "operator_confirmed_manual_execution", requires_root=False),
    ]

    test_steps = [
        _manual_step("PRIV_VALID_STEP_CREATE_VALID_RUNNER_JOB", "valid_job_created", requires_root=False),
        _manual_step("PRIV_VALID_STEP_DOCUMENT_JOB_HASH", "job_hash_recorded", requires_root=False),
        _manual_step("PRIV_VALID_STEP_MANUAL_PRIVILEGED_DRYRUN_START", "runner_started_with_planned_privileged_path", requires_root=True),
        _manual_step("PRIV_VALID_STEP_DOCUMENT_EFFECTIVE_UID_GID", "effective_uid_gid_documented", requires_root=False),
        _manual_step("PRIV_VALID_STEP_VERIFY_DRY_RUN_ENFORCED", "dry_run_flag_verified", requires_root=False),
        _manual_step("PRIV_VALID_STEP_VERIFY_NO_DEVICE_OPEN", "no_device_open_verified", requires_root=False),
        _manual_step("PRIV_VALID_STEP_VERIFY_LIFECYCLE_COMPLETED", "lifecycle_completed_state_verified", requires_root=False),
        _manual_step("PRIV_VALID_STEP_VERIFY_LOCK_RELEASED", "lock_released_verified", requires_root=False),
        _manual_step("PRIV_VALID_STEP_VERIFY_AUDIT_JSONL_WRITTEN", "audit_jsonl_verified", requires_root=False),
        _manual_step("PRIV_VALID_STEP_VERIFY_MINIMAL_ENVIRONMENT", "minimal_environment_verified", requires_root=False),
        _manual_step("PRIV_VALID_STEP_DOCUMENT_RESULT", "result_documented", requires_root=False),
    ]

    negative_tests = [
        _manual_step("PRIV_VALID_NEGATIVE_NO_DRY_RUN_FLAG", "blocked", requires_root=True),
        _manual_step("PRIV_VALID_NEGATIVE_JOB_HASH_MISMATCH", "blocked", requires_root=False),
        _manual_step("PRIV_VALID_NEGATIVE_EXPIRED_JOB", "blocked", requires_root=False),
        _manual_step("PRIV_VALID_NEGATIVE_JOB_OUTSIDE_ALLOWED_PREFIX", "blocked", requires_root=False),
        _manual_step("PRIV_VALID_NEGATIVE_SYMLINK_JOBFILE", "blocked", requires_root=False),
        _manual_step("PRIV_VALID_NEGATIVE_UNAPPROVED_EXTRA_PARAMETER", "blocked", requires_root=True),
        _manual_step("PRIV_VALID_NEGATIVE_ENV_LD_PRELOAD", "blocked", requires_root=False),
        _manual_step("PRIV_VALID_NEGATIVE_ENV_PYTHONPATH", "blocked", requires_root=False),
        _manual_step("PRIV_VALID_NEGATIVE_RUNNER_PATH_TAMPERED", "blocked", requires_root=True),
        _manual_step("PRIV_VALID_NEGATIVE_PARALLEL_RUNNER_LOCK_CONFLICT", "blocked", requires_root=False),
        _manual_step("PRIV_VALID_NEGATIVE_STALE_LOCK", "blocked_or_cleanup_required", requires_root=False),
    ]

    required_evidence = [
        "jobfile_path",
        "jobfile_hash",
        "runner_stdout_json",
        "runner_stderr",
        "effective_uid_gid_in_runner_context",
        "environment_snapshot",
        "lifecycle_audit_jsonl",
        "lock_cleanup_proof",
        "proof_no_device_open",
        "proof_no_device_write",
        "proof_no_mount_changes",
        "negative_test_results",
        "rollback_confirmation",
    ]

    risk_controls = [
        "dry_run_only",
        "no_test_without_local_control",
        "no_production_media",
        "no_parallel_runners",
        "short_ttl_test_job",
        "abort_on_device_open",
        "abort_on_non_json_stdout",
        "abort_on_interactive_prompt",
        "no_retry_after_unexpected_error",
    ]

    stop_conditions = [
        "runner_started_without_dry_run",
        "device_open_detected",
        "stdout_not_json",
        "audit_missing",
        "lock_not_released",
        "environment_contains_blocked_variables",
        "job_hash_mismatch",
        "operator_unsure",
    ]

    rollback_steps = [
        {"code": "ROLLBACK_DELETE_TEST_JOB", "auto_allowed": False},
        {"code": "ROLLBACK_REMOVE_STALE_LOCKFILE_IF_PRESENT", "auto_allowed": False},
        {"code": "ROLLBACK_ARCHIVE_AUDIT", "auto_allowed": False},
        {"code": "ROLLBACK_REMOVE_TEMP_RUNNER_TEST_ARTIFACTS", "auto_allowed": False},
        {"code": "ROLLBACK_DOCUMENT_RESULT", "auto_allowed": False},
        {"code": "ROLLBACK_CONFIRM_NO_PERSISTENT_SUDOERS_CHANGE", "auto_allowed": False},
    ]

    plan_status = "ok"
    if errors:
        plan_status = "blocked"
    elif warnings:
        plan_status = "review_required"

    return {
        "plan_status": plan_status,
        "gap_code": "RUNNER_GAP_PRIVILEGED_RUNNER_VALIDATION_OPEN",
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
