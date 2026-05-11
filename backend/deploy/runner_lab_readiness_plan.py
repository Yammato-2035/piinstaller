from __future__ import annotations

from typing import Any

_BLOCKING_GAPS = [
    "RUNNER_GAP_REAL_WRITE_HARDWARE_E2E_OPEN",
    "RUNNER_GAP_PRIVILEGED_RUNNER_VALIDATION_OPEN",
    "RUNNER_GAP_SUDOERS_RUNTIME_OPEN",
    "RUNNER_GAP_FAILURE_INJECTION_HW_OPEN",
    "RUNNER_GAP_ROLLBACK_RUNTIME_OPEN",
    "RUNNER_GAP_DEVICE_REENUMERATION_OPEN",
    "RUNNER_GAP_HOTPLUG_RACE_OPEN",
]

_STOP_CONDITIONS = [
    "STOP_TEST_MEDIA_NOT_UNIQUE",
    "STOP_MULTIPLE_REMOVABLE_MEDIA",
    "STOP_SYSTEM_DISK_TARGET_DETECTED",
    "STOP_HARDWARE_GATE_NOT_READY",
    "STOP_SNAPSHOT_FINGERPRINT_CHANGED",
    "STOP_MOUNT_STATE_UNEXPECTED_CHANGE",
    "STOP_VERIFY_MISMATCH",
    "STOP_RUNNER_AUDIT_MISSING",
    "STOP_OPERATOR_UNSURE",
]


def _gap_item(
    gap_code: str,
    priority: int,
    lab_action: str,
    *,
    requires_root: bool,
    requires_test_media: bool,
    requires_physical_access: bool,
) -> dict[str, Any]:
    return {
        "gap_code": gap_code,
        "priority": int(priority),
        "lab_action": lab_action,
        "requires_root": bool(requires_root),
        "requires_test_media": bool(requires_test_media),
        "requires_physical_access": bool(requires_physical_access),
        "auto_allowed": False,
        "expected_evidence": [
            "lsblk_before_after",
            "findmnt_before_after",
            "runner_audit_jsonl",
            "jobfile_hash",
            "snapshot_fingerprint",
            "verify_sha256",
            "per_test_result_file",
        ],
        "stop_conditions": list(_STOP_CONDITIONS),
    }


def _exec_step(order: int, code: str, action: str) -> dict[str, Any]:
    return {
        "order": int(order),
        "code": code,
        "action": action,
        "auto_allowed": False,
        "manual_operator_required": True,
    }


def build_runner_lab_readiness_unblock_plan(
    *,
    blocking_gaps: list[str] | None = None,
) -> dict[str, Any]:
    gaps = list(blocking_gaps or _BLOCKING_GAPS)
    warnings: list[str] = []
    errors: list[str] = []

    required_gap_set = set(_BLOCKING_GAPS)
    present_gap_set = set(gaps)
    missing = sorted(required_gap_set - present_gap_set)
    if missing:
        errors.append("missing_blocking_gap_coverage")

    gap_plan = [
        _gap_item("RUNNER_GAP_SUDOERS_RUNTIME_OPEN", 1, "Sudoers Runtime Dry-run against fixed runner invocation", requires_root=True, requires_test_media=False, requires_physical_access=True),
        _gap_item("RUNNER_GAP_PRIVILEGED_RUNNER_VALIDATION_OPEN", 2, "Privileged Runner Validation Dry-run with strict path/env checks", requires_root=True, requires_test_media=False, requires_physical_access=True),
        _gap_item("RUNNER_GAP_REAL_WRITE_HARDWARE_E2E_OPEN", 3, "Real Write Hardware E2E on disposable media with pre/post evidence", requires_root=True, requires_test_media=True, requires_physical_access=True),
        _gap_item("RUNNER_GAP_FAILURE_INJECTION_HW_OPEN", 4, "Failure Injection Hardware E2E for interruption/retry paths", requires_root=True, requires_test_media=True, requires_physical_access=True),
        _gap_item("RUNNER_GAP_DEVICE_REENUMERATION_OPEN", 5, "Device reenumeration behavior test under controlled lab sequence", requires_root=True, requires_test_media=True, requires_physical_access=True),
        _gap_item("RUNNER_GAP_HOTPLUG_RACE_OPEN", 6, "Hotplug/unmount race test with strict stop conditions", requires_root=True, requires_test_media=True, requires_physical_access=True),
        _gap_item("RUNNER_GAP_ROLLBACK_RUNTIME_OPEN", 7, "Rollback runtime test and post-rollback audit verification", requires_root=True, requires_test_media=True, requires_physical_access=True),
    ]

    mapped_gaps = {str(x.get("gap_code") or "") for x in gap_plan}
    if set(_BLOCKING_GAPS) - mapped_gaps:
        errors.append("gap_plan_mapping_incomplete")

    execution_order = [
        _exec_step(1, "LAB_STEP_SUDOERS_RUNTIME_DRYRUN", "Sudoers Runtime Dry-run"),
        _exec_step(2, "LAB_STEP_PRIVILEGED_RUNNER_VALIDATION_DRYRUN", "Privileged Runner Validation Dry-run"),
        _exec_step(3, "LAB_STEP_REAL_WRITE_HARDWARE_E2E_DISPOSABLE_MEDIA", "Real Write Hardware E2E on disposable media"),
        _exec_step(4, "LAB_STEP_FAILURE_INJECTION_HARDWARE_E2E", "Failure Injection Hardware E2E"),
        _exec_step(5, "LAB_STEP_DEVICE_REENUMERATION_TEST", "Device Reenumeration Test"),
        _exec_step(6, "LAB_STEP_HOTPLUG_UNMOUNT_RACE_TEST", "Hotplug/Unmount Race Test"),
        _exec_step(7, "LAB_STEP_ROLLBACK_RUNTIME_TEST", "Rollback Runtime Test"),
    ]

    required_equipment = [
        "disposable_usb_or_sd_test_media",
        "second_control_terminal",
        "stable_power_supply",
        "local_host_access",
        "full_backup_available",
        "no_productive_media_except_system_disk",
        "physical_test_media_labeling",
    ]
    required_evidence = [
        "lsblk_before_after_each_test",
        "findmnt_before_after_each_test",
        "hardware_gate_report",
        "real_write_guard_report",
        "runner_audit_jsonl",
        "jobfile_hash",
        "snapshot_fingerprint",
        "verify_sha256",
        "media_label_photo_or_note_optional",
        "per_test_result_file",
    ]
    risk_controls = [
        "single_test_media_only",
        "physically_labeled_test_media",
        "no_parallel_runners",
        "no_remote_test_without_local_control",
        "abort_on_device_change",
        "abort_on_mount_change",
        "no_retry_after_verify_mismatch",
        "no_productive_data_test",
    ]
    stop_conditions = [
        "test_media_not_unique",
        "multiple_possible_removable_media",
        "system_disk_appears_as_target",
        "hardware_gate_not_test_ready",
        "snapshot_fingerprint_changes",
        "mount_state_changes_unexpected",
        "verify_mismatch",
        "runner_audit_missing",
        "operator_unsure",
    ]

    plan_status = "ok"
    target_status = "lab_ready_candidate"
    if errors:
        plan_status = "blocked"
        target_status = "not_lab_ready"
    elif warnings:
        plan_status = "review_required"

    return {
        "plan_status": plan_status,
        "target_status": target_status,
        "gap_plan": gap_plan,
        "execution_order": execution_order,
        "required_equipment": required_equipment,
        "required_evidence": required_evidence,
        "risk_controls": risk_controls,
        "stop_conditions": stop_conditions,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
    }
