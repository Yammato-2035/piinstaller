from __future__ import annotations

from typing import Any

_GAPS = [
    "RUNNER_GAP_SUDOERS_RUNTIME_OPEN",
    "RUNNER_GAP_PRIVILEGED_RUNNER_VALIDATION_OPEN",
    "RUNNER_GAP_REAL_WRITE_HARDWARE_E2E_OPEN",
    "RUNNER_GAP_FAILURE_INJECTION_HW_OPEN",
    "RUNNER_GAP_DEVICE_REENUMERATION_OPEN",
    "RUNNER_GAP_HOTPLUG_RACE_OPEN",
    "RUNNER_GAP_ROLLBACK_RUNTIME_OPEN",
]

_DESIGN_EVIDENCE_MAP = {
    "RUNNER_GAP_SUDOERS_RUNTIME_OPEN": ["docs/evidence/DEPLOY_RUNNER_SUDOERS_RUNTIME_TEST_PLAN.md"],
    "RUNNER_GAP_PRIVILEGED_RUNNER_VALIDATION_OPEN": ["docs/evidence/DEPLOY_RUNNER_PRIVILEGED_VALIDATION_TEST_PLAN.md"],
    "RUNNER_GAP_REAL_WRITE_HARDWARE_E2E_OPEN": ["docs/evidence/DEPLOY_RUNNER_REAL_WRITE_HARDWARE_E2E_TEST_PLAN.md"],
    "RUNNER_GAP_FAILURE_INJECTION_HW_OPEN": ["docs/evidence/DEPLOY_RUNNER_FAILURE_INJECTION_HW_TEST_PLAN.md"],
    "RUNNER_GAP_DEVICE_REENUMERATION_OPEN": ["docs/evidence/DEPLOY_RUNNER_DEVICE_REENUMERATION_TEST_PLAN.md"],
    "RUNNER_GAP_HOTPLUG_RACE_OPEN": ["docs/evidence/DEPLOY_RUNNER_HOTPLUG_RACE_TEST_PLAN.md"],
    "RUNNER_GAP_ROLLBACK_RUNTIME_OPEN": ["docs/evidence/DEPLOY_RUNNER_ROLLBACK_RUNTIME_TEST_PLAN.md"],
}

_RUNTIME_ACTIONS = {
    "RUNNER_GAP_SUDOERS_RUNTIME_OPEN": "Sudoers Runtime Dry-run manuell",
    "RUNNER_GAP_PRIVILEGED_RUNNER_VALIDATION_OPEN": "Privileged Runner Validation Dry-run manuell",
    "RUNNER_GAP_REAL_WRITE_HARDWARE_E2E_OPEN": "Real Write Hardware E2E manuell",
    "RUNNER_GAP_FAILURE_INJECTION_HW_OPEN": "Failure Injection Hardware E2E manuell",
    "RUNNER_GAP_DEVICE_REENUMERATION_OPEN": "Device Reenumeration manuell",
    "RUNNER_GAP_HOTPLUG_RACE_OPEN": "Hotplug / Unmount Race manuell",
    "RUNNER_GAP_ROLLBACK_RUNTIME_OPEN": "Rollback Runtime manuell",
}


def build_runner_lab_readiness_status(
    *,
    design_evidence: dict[str, list[str]] | None = None,
    runtime_evidence: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    design_src = dict(design_evidence or _DESIGN_EVIDENCE_MAP)
    runtime_src = dict(runtime_evidence or {})
    warnings: list[str] = []
    errors: list[str] = []

    gap_statuses: list[dict[str, Any]] = []
    design_completed_gaps: list[str] = []
    remaining_runtime_gaps: list[str] = []

    for gap in _GAPS:
        design_files = list(design_src.get(gap) or [])
        runtime_files = list(runtime_src.get(gap) or [])
        design_status = "ready" if design_files else "missing"
        runtime_status = "passed" if runtime_files else "not_started"
        if design_status == "ready":
            design_completed_gaps.append(gap)
        else:
            warnings.append(f"design_missing:{gap}")
        if runtime_status != "passed":
            remaining_runtime_gaps.append(gap)

        gap_statuses.append(
            {
                "gap_code": gap,
                "design_status": design_status,
                "runtime_status": runtime_status,
                "release_impact": "blocking",
                "evidence_files": design_files + runtime_files,
                "next_required_action": _RUNTIME_ACTIONS.get(gap, "Runtime-Ausfuehrung manuell"),
            }
        )

    required_runtime_executions = [
        {
            "gap_code": gap,
            "action": _RUNTIME_ACTIONS[gap],
            "auto_allowed": False,
            "manual_operator_required": True,
        }
        for gap in _GAPS
    ]

    if len(design_completed_gaps) == len(_GAPS):
        lab_status = "test_design_ready"
    elif len(design_completed_gaps) == 0:
        lab_status = "runtime_blocked"
    else:
        lab_status = "review_required"

    # Nie lab_ready/production_ready behaupten.
    if lab_status not in {"test_design_ready", "runtime_blocked", "review_required"}:
        errors.append("invalid_lab_readiness_status")
        lab_status = "runtime_blocked"

    return {
        "lab_readiness_status": lab_status,
        "gap_statuses": gap_statuses,
        "remaining_runtime_gaps": remaining_runtime_gaps,
        "design_completed_gaps": design_completed_gaps,
        "required_runtime_executions": required_runtime_executions,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
    }
