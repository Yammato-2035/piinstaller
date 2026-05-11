from __future__ import annotations

from pathlib import Path
from typing import Any

from deploy.runner_lab_acceptance_aggregator import build_runner_lab_acceptance_summary
from deploy.runner_lab_acceptance_report_export import build_runner_lab_acceptance_report_export
from deploy.runner_lab_readiness_status import build_runner_lab_readiness_status
from deploy.runner_release_readiness import build_runner_release_readiness_matrix
from deploy.runner_runtime_result_validator import validate_runner_runtime_result_bundle
from deploy.runner_runtime_runbook_export import build_runner_runtime_runbook_export_package

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _components() -> list[dict[str, Any]]:
    return [
        {"component_id": "RUNNER_COMPONENT_REAL_WRITE_GUARD", "category": "guard", "status": "implemented", "primary_files": ["backend/deploy/real_write_guard.py"], "test_files": ["backend/tests/test_deploy_real_write_guard_v1.py"], "evidence_files": ["docs/evidence/DEPLOY_REAL_WRITE_GUARD.md"], "notes": []},
        {"component_id": "RUNNER_COMPONENT_HARDWARE_GATE", "category": "guard", "status": "implemented", "primary_files": ["backend/deploy/hardware_gate.py"], "test_files": ["backend/tests/test_deploy_hardware_gate_v1.py"], "evidence_files": ["docs/evidence/DEPLOY_HARDWARE_GATE.md"], "notes": []},
        {"component_id": "RUNNER_COMPONENT_REAL_WRITE_PROTOTYPE", "category": "guard", "status": "implemented", "primary_files": ["backend/deploy/real_write_prototype.py"], "test_files": ["backend/tests/test_deploy_real_write_prototype_v1.py"], "evidence_files": ["docs/evidence/DEPLOY_REAL_WRITE_PROTOTYPE.md"], "notes": []},
        {"component_id": "RUNNER_COMPONENT_FAILURE_INJECTION", "category": "guard", "status": "implemented", "primary_files": ["backend/deploy/runner_failure_injection_hardware_test_plan.py"], "test_files": ["backend/tests/test_deploy_runner_failure_injection_hardware_test_plan_v1.py"], "evidence_files": ["docs/evidence/DEPLOY_RUNNER_FAILURE_INJECTION_HW_TEST_PLAN.md"], "notes": []},
        {"component_id": "RUNNER_COMPONENT_RUNNER_CONTRACT", "category": "runner", "status": "tested", "primary_files": ["backend/deploy/runner_contract.py"], "test_files": ["backend/tests/test_deploy_runner_contract_v1.py"], "evidence_files": ["docs/evidence/DEPLOY_WRITE_RUNNER_CONTRACT.md"], "notes": []},
        {"component_id": "RUNNER_COMPONENT_RUNNER_RUNTIME_VALIDATION", "category": "runner", "status": "tested", "primary_files": ["backend/deploy/runner_runtime_validation.py"], "test_files": ["backend/tests/test_deploy_runner_runtime_validation_v1.py"], "evidence_files": ["docs/evidence/DEPLOY_WRITE_RUNNER_RUNTIME_VALIDATION.md"], "notes": []},
        {"component_id": "RUNNER_COMPONENT_RUNNER_LIFECYCLE", "category": "runner", "status": "tested", "primary_files": ["backend/deploy/runner_lifecycle.py"], "test_files": ["backend/tests/test_deploy_runner_lifecycle_v1.py"], "evidence_files": ["docs/evidence/DEPLOY_RUNNER_LIFECYCLE.md"], "notes": []},
        {"component_id": "RUNNER_COMPONENT_RUNNER_HANDOFF", "category": "runner", "status": "tested", "primary_files": ["backend/deploy/runner_handoff.py"], "test_files": ["backend/tests/test_deploy_runner_handoff_v1.py"], "evidence_files": ["docs/evidence/DEPLOY_RUNNER_HANDOFF.md"], "notes": []},
        {"component_id": "RUNNER_COMPONENT_PERMISSION_BOUNDARY", "category": "runner", "status": "tested", "primary_files": ["backend/deploy/runner_permission_boundary.py"], "test_files": ["backend/tests/test_deploy_runner_permission_boundary_v1.py"], "evidence_files": ["docs/evidence/DEPLOY_RUNNER_PERMISSION_BOUNDARY.md"], "notes": []},
        {"component_id": "RUNNER_COMPONENT_SANDBOX", "category": "runner", "status": "tested", "primary_files": ["backend/deploy/runner_sandbox.py"], "test_files": ["backend/tests/test_deploy_runner_sandbox_v1.py"], "evidence_files": ["docs/evidence/DEPLOY_RUNNER_SANDBOX.md"], "notes": []},
        {"component_id": "RUNNER_COMPONENT_ROOTLESS_E2E", "category": "runner", "status": "tested", "primary_files": ["backend/tests/test_deploy_runner_rootless_e2e_v1.py"], "test_files": ["backend/tests/test_deploy_runner_rootless_e2e_v1.py"], "evidence_files": ["docs/evidence/DEPLOY_RUNNER_ROOTLESS_E2E.md"], "notes": []},
        {"component_id": "RUNNER_COMPONENT_INSTALL_PLAN", "category": "install", "status": "implemented", "primary_files": ["backend/deploy/runner_install_plan.py"], "test_files": ["backend/tests/test_deploy_runner_install_plan_v1.py"], "evidence_files": ["docs/evidence/DEPLOY_RUNNER_INSTALL_PLAN.md"], "notes": []},
        {"component_id": "RUNNER_COMPONENT_INSTALL_VALIDATOR", "category": "install", "status": "implemented", "primary_files": ["backend/deploy/runner_install_validator.py"], "test_files": ["backend/tests/test_deploy_runner_install_validator_v1.py"], "evidence_files": ["docs/evidence/DEPLOY_RUNNER_INSTALL_VALIDATOR.md"], "notes": []},
        {"component_id": "RUNNER_COMPONENT_PACKAGE_BLUEPRINT", "category": "install", "status": "implemented", "primary_files": ["backend/deploy/runner_package_blueprint.py"], "test_files": ["backend/tests/test_deploy_runner_package_blueprint_v1.py"], "evidence_files": ["docs/evidence/DEPLOY_RUNNER_PACKAGE_BLUEPRINT.md"], "notes": []},
        {"component_id": "RUNNER_COMPONENT_INSTALL_CONSISTENCY", "category": "install", "status": "implemented", "primary_files": ["backend/deploy/runner_install_consistency.py"], "test_files": ["backend/tests/test_deploy_runner_install_consistency_v1.py"], "evidence_files": ["docs/evidence/DEPLOY_RUNNER_INSTALL_CONSISTENCY.md"], "notes": []},
        {"component_id": "RUNNER_COMPONENT_RELEASE_READINESS", "category": "readiness", "status": "implemented", "primary_files": ["backend/deploy/runner_release_readiness.py"], "test_files": ["backend/tests/test_deploy_runner_release_readiness_v1.py"], "evidence_files": ["docs/evidence/DEPLOY_RUNNER_RELEASE_READINESS.md"], "notes": []},
        {"component_id": "RUNNER_COMPONENT_LAB_READINESS_UNBLOCK_PLAN", "category": "readiness", "status": "implemented", "primary_files": ["backend/deploy/runner_lab_readiness_plan.py"], "test_files": ["backend/tests/test_deploy_runner_lab_readiness_plan_v1.py"], "evidence_files": ["docs/evidence/DEPLOY_RUNNER_LAB_READINESS_PLAN.md"], "notes": []},
        {"component_id": "RUNNER_COMPONENT_SEVEN_RUNTIME_TEST_DESIGNS", "category": "runbook", "status": "planned_only", "primary_files": ["backend/deploy/runner_sudoers_runtime_test_plan.py", "backend/deploy/runner_privileged_validation_test_plan.py", "backend/deploy/runner_real_write_hardware_e2e_test_plan.py", "backend/deploy/runner_failure_injection_hardware_test_plan.py", "backend/deploy/runner_device_reenumeration_test_plan.py", "backend/deploy/runner_hotplug_race_test_plan.py", "backend/deploy/runner_rollback_runtime_test_plan.py"], "test_files": [], "evidence_files": [], "notes": ["runtime execution remains open"]},
        {"component_id": "RUNNER_COMPONENT_LAB_READINESS_STATUS", "category": "readiness", "status": "implemented", "primary_files": ["backend/deploy/runner_lab_readiness_status.py"], "test_files": ["backend/tests/test_deploy_runner_lab_readiness_status_v1.py"], "evidence_files": ["docs/evidence/DEPLOY_RUNNER_LAB_READINESS_STATUS.md"], "notes": []},
        {"component_id": "RUNNER_COMPONENT_RUNTIME_RUNBOOK_BUNDLE", "category": "runbook", "status": "implemented", "primary_files": ["backend/deploy/runner_runtime_runbook_bundle.py"], "test_files": ["backend/tests/test_deploy_runner_runtime_runbook_bundle_v1.py"], "evidence_files": ["docs/evidence/DEPLOY_RUNNER_RUNTIME_RUNBOOK_BUNDLE.md"], "notes": []},
        {"component_id": "RUNNER_COMPONENT_RUNTIME_RUNBOOK_EXPORT", "category": "runbook", "status": "tested", "primary_files": ["backend/deploy/runner_runtime_runbook_export.py"], "test_files": ["backend/tests/test_deploy_runner_runtime_runbook_export_v1.py"], "evidence_files": ["docs/evidence/DEPLOY_RUNNER_RUNTIME_RUNBOOK_EXPORT.md"], "notes": []},
        {"component_id": "RUNNER_COMPONENT_RUNTIME_RESULT_VALIDATOR", "category": "acceptance", "status": "tested", "primary_files": ["backend/deploy/runner_runtime_result_validator.py"], "test_files": ["backend/tests/test_deploy_runner_runtime_result_validator_v1.py"], "evidence_files": ["docs/evidence/DEPLOY_RUNNER_RUNTIME_RESULT_VALIDATOR.md"], "notes": []},
        {"component_id": "RUNNER_COMPONENT_LAB_ACCEPTANCE_AGGREGATOR", "category": "acceptance", "status": "tested", "primary_files": ["backend/deploy/runner_lab_acceptance_aggregator.py"], "test_files": ["backend/tests/test_deploy_runner_lab_acceptance_aggregator_v1.py"], "evidence_files": ["docs/evidence/DEPLOY_RUNNER_LAB_ACCEPTANCE_AGGREGATOR.md"], "notes": []},
        {"component_id": "RUNNER_COMPONENT_LAB_ACCEPTANCE_REPORT_EXPORT", "category": "documentation", "status": "tested", "primary_files": ["backend/deploy/runner_lab_acceptance_report_export.py"], "test_files": ["backend/tests/test_deploy_runner_lab_acceptance_report_export_v1.py"], "evidence_files": ["docs/evidence/DEPLOY_RUNNER_LAB_ACCEPTANCE_REPORT_EXPORT.md"], "notes": []},
    ]


def _artifact_index() -> list[dict[str, Any]]:
    artifacts = [
        ("backend_module", "backend/deploy/runner_lab_phase_consolidation.py", "Final consolidation module", True),
        ("test", "backend/tests/test_deploy_runner_lab_phase_consolidation_v1.py", "Consolidation validation tests", True),
        ("deploy_doc", "docs/deploy/DEPLOY_RUNNER_LAB_PHASE_CONSOLIDATION_DE.md", "DE consolidation overview", True),
        ("deploy_doc", "docs/deploy/DEPLOY_RUNNER_LAB_PHASE_CONSOLIDATION_EN.md", "EN consolidation overview", True),
        ("kb", "docs/knowledge-base/deploy/DEPLOY_RUNNER_LAB_PHASE_CONSOLIDATION.md", "KB consolidation reference", False),
        ("evidence", "docs/evidence/DEPLOY_RUNNER_LAB_PHASE_CONSOLIDATION.md", "Evidence for consolidation phase", True),
        ("runbook_export", "docs/runbooks/deploy-runner/LAB_PHASE_FINAL_INDEX_DE.md", "DE final index", True),
        ("runbook_export", "docs/runbooks/deploy-runner/LAB_PHASE_FINAL_INDEX_EN.md", "EN final index", True),
        ("template", "docs/evidence/templates/RUNNER_RUNTIME_RESULT_TEMPLATE.md", "Runtime result template", True),
        ("template", "docs/evidence/templates/RUNNER_RUNTIME_RESULT_SCHEMA.json", "Runtime result schema", True),
        ("report", "docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT_DE.md", "Lab acceptance report DE", False),
        ("report", "docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT_EN.md", "Lab acceptance report EN", False),
        ("report", "docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT.json", "Lab acceptance report JSON", False),
        ("runbook_export", "docs/runbooks/deploy-runner/reports/LAB_ACCEPTANCE_SUMMARY_DE.md", "Lab acceptance summary DE", False),
        ("runbook_export", "docs/runbooks/deploy-runner/reports/LAB_ACCEPTANCE_SUMMARY_EN.md", "Lab acceptance summary EN", False),
    ]
    return [
        {"artifact_type": t, "path": p, "purpose": purpose, "required_for_lab": req}
        for (t, p, purpose, req) in artifacts
    ]


def _runtime_open_items() -> list[dict[str, Any]]:
    return [
        {"code": "RUNBOOK_SUDOERS_RUNTIME_DRYRUN", "manual_operator_required": True, "auto_allowed": False, "blocks_production": True},
        {"code": "RUNBOOK_PRIVILEGED_RUNNER_VALIDATION_DRYRUN", "manual_operator_required": True, "auto_allowed": False, "blocks_production": True},
        {"code": "RUNBOOK_REAL_WRITE_HARDWARE_E2E", "manual_operator_required": True, "auto_allowed": False, "blocks_production": True},
        {"code": "RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E", "manual_operator_required": True, "auto_allowed": False, "blocks_production": True},
        {"code": "RUNBOOK_DEVICE_REENUMERATION", "manual_operator_required": True, "auto_allowed": False, "blocks_production": True},
        {"code": "RUNBOOK_HOTPLUG_UNMOUNT_RACE", "manual_operator_required": True, "auto_allowed": False, "blocks_production": True},
        {"code": "RUNBOOK_ROLLBACK_RUNTIME", "manual_operator_required": True, "auto_allowed": False, "blocks_production": True},
    ]


def build_runner_lab_phase_consolidation(*, include_artifact_existence: bool = True) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    components = _components()
    artifact_index = _artifact_index()
    runtime_open_items = _runtime_open_items()

    validated_items = [
        "CODE_AND_CONTRACT_TESTS",
        "ROOTLESS_E2E",
        "READ_ONLY_EXPORT_VALIDATOR_AGGREGATOR_PATHS",
        "RUNTIME_RUNBOOK_EXPORT",
        "LAB_ACCEPTANCE_REPORT_EXPORT",
    ]
    planned_only_items = [
        "RUNBOOK_SUDOERS_RUNTIME_DRYRUN",
        "RUNBOOK_PRIVILEGED_RUNNER_VALIDATION_DRYRUN",
        "RUNBOOK_REAL_WRITE_HARDWARE_E2E",
        "RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E",
        "RUNBOOK_DEVICE_REENUMERATION",
        "RUNBOOK_HOTPLUG_UNMOUNT_RACE",
        "RUNBOOK_ROLLBACK_RUNTIME",
        "SUDOERS_RUNTIME_REAL_VALIDATION",
        "PRIVILEGED_RUNNER_RUNTIME_VALIDATION",
        "HARDWARE_WRITE_E2E_RUNTIME",
        "ROLLBACK_RUNTIME_EXECUTION",
    ]
    risk_summary = [
        "NOT_PRODUCTION_READY",
        "RUNTIME_TESTS_MISSING",
        "PRIVILEGED_RUNNER_NOT_REAL_VALIDATED",
        "SUDOERS_NOT_REAL_VALIDATED",
        "HARDWARE_WRITE_E2E_OPEN",
        "OPERATOR_DEPENDENT",
        "SINGLE_HOST_SINGLE_MEDIA_RISK",
        "NO_AUTOMATIC_RELEASE",
    ]

    validator = validate_runner_runtime_result_bundle(result_files=[], acceptance_decision="blocked")
    acceptance = build_runner_lab_acceptance_summary(validated_runtime_results=validator)
    export = build_runner_runtime_runbook_export_package()
    report_export = build_runner_lab_acceptance_report_export(acceptance=acceptance)
    lab_status = build_runner_lab_readiness_status()
    release = build_runner_release_readiness_matrix()

    if include_artifact_existence:
        for a in artifact_index:
            p = _REPO_ROOT / str(a["path"])
            if not p.exists():
                warnings.append(f"artifact_missing:{a['path']}")

    phase_status = "runtime_execution_open"
    if release.get("readiness_status") == "blocked":
        phase_status = "runtime_execution_open"

    release_statement = {
        "production_ready": False,
        "lab_ready_candidate_possible": bool(acceptance.get("acceptance_status") == "lab_ready_candidate"),
        "requires_manual_runtime_execution": True,
        "requires_operator_decision": True,
        "automatic_release_allowed": False,
        "reason": "Runtime tests and privileged/sudoers/hardware validations remain open; no automatic release allowed.",
    }

    test_summary = {
        "validator_status": validator.get("validation_status"),
        "acceptance_status": acceptance.get("acceptance_status"),
        "runbook_export_status": export.get("export_status"),
        "report_export_status": report_export.get("export_status"),
        "lab_readiness_status": lab_status.get("lab_readiness_status"),
        "release_readiness_status": release.get("readiness_status"),
    }

    consolidation_status = "ok"
    if errors:
        consolidation_status = "blocked"
    elif warnings:
        consolidation_status = "review_required"

    return {
        "consolidation_status": consolidation_status,
        "phase_status": phase_status,
        "components": components,
        "artifact_index": artifact_index,
        "runtime_open_items": runtime_open_items,
        "validated_items": validated_items,
        "planned_only_items": planned_only_items,
        "risk_summary": risk_summary,
        "test_summary": test_summary,
        "release_statement": release_statement,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
    }
