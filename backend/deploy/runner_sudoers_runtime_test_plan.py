from __future__ import annotations

from typing import Any


def _manual_item(
    code: str,
    *,
    requires_root: bool,
    expected_result: str = "",
) -> dict[str, Any]:
    out = {
        "code": code,
        "requires_root": bool(requires_root),
        "manual_operator_required": True,
        "auto_allowed": False,
    }
    if expected_result:
        out["expected_result"] = expected_result
    return out


def build_runner_sudoers_runtime_test_plan() -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    preconditions = [
        _manual_item("PRECONDITION_INSTALL_PLAN_PRESENT", requires_root=False, expected_result="install_plan_available"),
        _manual_item("PRECONDITION_INSTALL_VALIDATOR_NOT_BLOCKED", requires_root=False, expected_result="validator_status_ok_or_review"),
        _manual_item("PRECONDITION_INSTALL_CONSISTENCY_NOT_BLOCKED", requires_root=False, expected_result="consistency_status_ok_or_review"),
        _manual_item("PRECONDITION_PACKAGE_BLUEPRINT_PRESENT", requires_root=False, expected_result="package_blueprint_available"),
        _manual_item("PRECONDITION_LAB_READINESS_PLAN_PRESENT", requires_root=False, expected_result="lab_readiness_plan_available"),
        _manual_item("PRECONDITION_LOCAL_TESTHOST_AVAILABLE", requires_root=False, expected_result="local_host_confirmed"),
        _manual_item("PRECONDITION_FULL_BACKUP_AVAILABLE", requires_root=False, expected_result="backup_confirmed"),
        _manual_item("PRECONDITION_OPERATOR_CONFIRMS_MANUAL_EXECUTION", requires_root=False, expected_result="operator_confirmed"),
    ]

    test_steps = [
        _manual_item("SUDOERS_TEST_STEP_PREPARE_TEMP_SNIPPET", requires_root=True, expected_result="temporary_snippet_prepared"),
        _manual_item("SUDOERS_TEST_STEP_MANUAL_VISUDO_CHECK", requires_root=True, expected_result="visudo_cf_passed"),
        _manual_item("SUDOERS_TEST_STEP_MANUAL_DRYRUN_CALL", requires_root=True, expected_result="dryrun_call_matches_planned_invocation"),
        _manual_item("SUDOERS_TEST_STEP_ENV_VALIDATION", requires_root=False, expected_result="blocked_env_not_present"),
        _manual_item("SUDOERS_TEST_STEP_STDOUT_STDERR_REVIEW", requires_root=False, expected_result="stdout_json_and_stderr_documented"),
        _manual_item("SUDOERS_TEST_STEP_AUDIT_REVIEW", requires_root=False, expected_result="audit_entries_present"),
        _manual_item("SUDOERS_TEST_STEP_PROOF_NO_DEVICE_OPERATION", requires_root=False, expected_result="no_device_write_proven"),
        _manual_item("SUDOERS_TEST_STEP_REMOVE_TEMP_SNIPPET", requires_root=True, expected_result="temporary_snippet_removed"),
    ]

    negative_tests = [
        _manual_item("SUDOERS_NEGATIVE_MISSING_ENV_RESET", requires_root=True, expected_result="blocked"),
        _manual_item("SUDOERS_NEGATIVE_ENV_KEEP_PYTHONPATH", requires_root=True, expected_result="blocked"),
        _manual_item("SUDOERS_NEGATIVE_ENV_KEEP_LD_PRELOAD", requires_root=True, expected_result="blocked"),
        _manual_item("SUDOERS_NEGATIVE_WILDCARD_JOB_PATH", requires_root=True, expected_result="blocked"),
        _manual_item("SUDOERS_NEGATIVE_GENERIC_PYTHON3_CALL", requires_root=True, expected_result="blocked"),
        _manual_item("SUDOERS_NEGATIVE_RELATIVE_RUNNER_PATH", requires_root=True, expected_result="blocked"),
        _manual_item("SUDOERS_NEGATIVE_WRONG_JOBDIR_PREFIX", requires_root=True, expected_result="blocked"),
        _manual_item("SUDOERS_NEGATIVE_MISSING_DRY_RUN_FLAG", requires_root=True, expected_result="blocked"),
        _manual_item("SUDOERS_NEGATIVE_UNAPPROVED_EXTRA_PARAMETER", requires_root=True, expected_result="blocked"),
    ]

    required_evidence = [
        "sudoers_snippet_text",
        "visudo_cf_result",
        "dry_run_runner_stdout_json",
        "stderr_empty_or_documented",
        "environment_snapshot",
        "runner_audit_jsonl",
        "jobfile_hash",
        "proof_no_device_write",
        "proof_no_mount_changes",
        "proof_no_persistent_sudoers_change",
        "rollback_confirmation",
    ]

    risk_controls = [
        "temporary_sudoers_test_snippet_only",
        "no_change_to_production_sudoers",
        "no_real_write",
        "dry_run_only",
        "minimal_environment_only",
        "no_remote_test_without_local_control",
        "no_test_with_production_media",
        "abort_on_unexpected_password_or_prompt",
    ]

    stop_conditions = [
        "visudo_validation_fails",
        "sudo_requests_interactive_password_unexpected",
        "runner_not_in_dry_run",
        "runner_opens_device",
        "stdout_not_json",
        "audit_missing",
        "environment_contains_blocked_variables",
        "operator_unsure",
    ]

    rollback_steps = [
        {"code": "ROLLBACK_REMOVE_TEMP_SUDOERS_TEST_SNIPPET", "auto_allowed": False},
        {"code": "ROLLBACK_VERIFY_NO_PERSISTENT_SUDOERS_CHANGE", "auto_allowed": False},
        {"code": "ROLLBACK_ARCHIVE_AUDIT", "auto_allowed": False},
        {"code": "ROLLBACK_DELETE_TEST_JOB", "auto_allowed": False},
        {"code": "ROLLBACK_DOCUMENT_RESULT", "auto_allowed": False},
    ]

    plan_status = "ok"
    if errors:
        plan_status = "blocked"
    elif warnings:
        plan_status = "review_required"

    return {
        "plan_status": plan_status,
        "gap_code": "RUNNER_GAP_SUDOERS_RUNTIME_OPEN",
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
