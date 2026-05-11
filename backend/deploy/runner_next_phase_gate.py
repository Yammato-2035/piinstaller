from __future__ import annotations

from typing import Any

from deploy.runner_lab_acceptance_aggregator import build_runner_lab_acceptance_summary
from deploy.runner_lab_phase_consolidation import build_runner_lab_phase_consolidation
from deploy.runner_runtime_result_validator import validate_runner_runtime_result_bundle
from deploy.runner_runtime_runbook_export import build_runner_runtime_runbook_export_package

_ALWAYS_BLOCKED = [
    "NEXT_PHASE_BLOCKED_PRODUCTION_RELEASE",
    "NEXT_PHASE_BLOCKED_AUTOMATED_DEPLOY",
    "NEXT_PHASE_BLOCKED_UNATTENDED_WRITE",
    "NEXT_PHASE_BLOCKED_SKIP_RUNTIME_TESTS",
    "NEXT_PHASE_BLOCKED_REAL_WRITE_WITHOUT_EVIDENCE",
    "NEXT_PHASE_BLOCKED_ROOT_BACKEND",
    "NEXT_PHASE_BLOCKED_PRIVILEGED_DAEMON",
]


def evaluate_runner_next_phase_gate(
    *,
    consolidation: dict[str, Any] | None = None,
    runtime_validation: dict[str, Any] | None = None,
    acceptance: dict[str, Any] | None = None,
    runbook_export: dict[str, Any] | None = None,
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    decision_reasons: list[str] = []

    consolidation_data = dict(consolidation or build_runner_lab_phase_consolidation(include_artifact_existence=False))
    validation_data = dict(runtime_validation or validate_runner_runtime_result_bundle(result_files=[], acceptance_decision="blocked"))
    acceptance_data = dict(acceptance or build_runner_lab_acceptance_summary(validated_runtime_results=validation_data))
    export_data = dict(runbook_export or build_runner_runtime_runbook_export_package())

    operator_requirements = [
        {"code": "manual_operator_required", "value": True},
        {"code": "local_control_required", "value": True},
        {"code": "physical_test_media_required", "value": True},
        {"code": "full_backup_required", "value": True},
        {"code": "single_test_media_required", "value": True},
        {"code": "stop_conditions_acknowledged", "value": True},
        {"code": "automatic_execution_allowed", "value": False},
    ]

    required_inputs = [
        {"code": "INPUT_FINAL_CONSOLIDATION", "present": consolidation_data.get("consolidation_status") in {"ok", "review_required"}},
        {"code": "INPUT_RUNTIME_RUNBOOK_EXPORT", "present": export_data.get("export_status") == "ok"},
        {"code": "INPUT_RUNTIME_RESULT_VALIDATOR", "present": validation_data.get("validation_status") in {"ok", "review_required", "blocked"}},
        {"code": "INPUT_LAB_ACCEPTANCE_AGGREGATOR", "present": bool(acceptance_data)},
        {"code": "INPUT_RUNBOOKS_PRESENT", "present": True},
        {"code": "INPUT_OPERATOR_CHECKLIST_PRESENT", "present": True},
        {"code": "INPUT_EVIDENCE_TEMPLATES_PRESENT", "present": True},
        {"code": "INPUT_VALIDATED_RUNTIME_RESULTS_OK", "present": validation_data.get("validation_status") == "ok"},
        {"code": "INPUT_ACCEPTANCE_STATUS_CANDIDATE", "present": acceptance_data.get("acceptance_status") == "lab_ready_candidate"},
        {"code": "INPUT_RESIDUAL_RISKS_VISIBLE", "present": bool(acceptance_data.get("residual_risks"))},
        {"code": "INPUT_OPERATOR_DECISION_REQUIRED", "present": bool(acceptance_data.get("operator_decision_required") is True)},
        {"code": "INPUT_ACCEPTANCE_REPORT_EXPORTED", "present": True},
    ]

    gate_status = "hold"
    allowed_next_phases: list[str] = []
    blocked_next_phases = list(_ALWAYS_BLOCKED)

    acceptance_status = str(acceptance_data.get("acceptance_status") or "blocked")
    runtime_open = bool(consolidation_data.get("runtime_open_items"))
    validator_ok = validation_data.get("validation_status") == "ok"
    export_ok = export_data.get("export_status") == "ok"

    if acceptance_status == "blocked":
        gate_status = "blocked"
        decision_reasons.append("acceptance_aggregator_blocked")
    elif acceptance_status == "repeat_required":
        gate_status = "repeat_required"
        allowed_next_phases.append("NEXT_PHASE_REPEAT_RUNTIME_TESTS")
        decision_reasons.append("acceptance_aggregator_repeat_required")
    elif acceptance_status == "lab_ready_candidate":
        gate_status = "hold"
        allowed_next_phases.append("NEXT_PHASE_LAB_READY_CANDIDATE_REVIEW")
        decision_reasons.append("lab_candidate_requires_manual_operator_review")
    elif runtime_open and not validator_ok:
        gate_status = "manual_runtime_allowed"
        allowed_next_phases.append("NEXT_PHASE_MANUAL_RUNTIME_TESTS")
        decision_reasons.append("runtime_open_items_present_without_validated_results")

    if not export_ok:
        if gate_status == "manual_runtime_allowed":
            gate_status = "hold"
        decision_reasons.append("runbook_export_missing_or_not_ok")
        warnings.append("missing_runtime_runbook_export_ok")

    if consolidation_data.get("consolidation_status") not in {"ok", "review_required"}:
        gate_status = "blocked"
        decision_reasons.append("consolidation_not_available")

    risk_summary = [
        "PRODUCTION_RELEASE_BLOCKED",
        "AUTOMATED_DEPLOY_BLOCKED",
        "UNATTENDED_WRITE_BLOCKED",
        "SKIP_RUNTIME_TESTS_BLOCKED",
        "ROOT_BACKEND_BLOCKED",
        "PRIVILEGED_DAEMON_BLOCKED",
        "LAB_READY_CANDIDATE_NOT_PRODUCTION_RELEASE",
        "MANUAL_OPERATOR_GATE_REQUIRED",
    ]

    return {
        "gate_status": gate_status,
        "allowed_next_phases": list(dict.fromkeys(allowed_next_phases)),
        "blocked_next_phases": blocked_next_phases,
        "required_inputs": required_inputs,
        "decision_reasons": list(dict.fromkeys(decision_reasons)),
        "risk_summary": risk_summary,
        "operator_requirements": operator_requirements,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
    }
