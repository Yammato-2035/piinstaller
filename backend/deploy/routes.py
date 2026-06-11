from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from deploy.cache_execute import create_deploy_cache_session, execute_deploy_cache
from deploy.execute import create_deploy_session, execute_deploy
from deploy.cache_plan import generate_deploy_cache_plan
from deploy.image_inspect import inspect_deploy_image
from deploy.plan import generate_deploy_plan
from deploy.preview import preview_deploy
from deploy.source_registry import (
    evaluate_source_compatibility,
    get_deploy_source_registry,
    validate_local_image_entry,
    validate_remote_image_metadata,
)
from deploy.write_plan import generate_deploy_write_plan
from deploy.write_execute import create_deploy_write_session, execute_deploy_write_dryrun
from deploy.final_confirmation import create_final_confirmation_session, check_final_confirmation_dryrun
from deploy.write_harness import create_deploy_write_harness_session, execute_deploy_write_harness
from deploy.real_write_guard import create_real_write_guard_session, check_real_write_guard
from deploy.real_write_prototype import execute_deploy_real_write_prototype
from deploy.hardware_gate import build_hardware_gate_report, build_operator_protocol
from deploy.runner_handoff import execute_runner_dryrun_handoff
from deploy.runner_permission_boundary import (
    audit_runner_binary_path,
    audit_runner_environment,
    audit_runner_job_directory,
    build_runner_sudoers_policy_example,
)
from deploy.runner_sandbox import (
    build_runner_privilege_model,
    build_runner_recovery_analysis,
    build_runner_sandbox_policy,
    build_runner_stdio_policy,
    build_runner_timeout_model,
    build_sandbox_environment,
)
from deploy.runner_install_plan import build_runner_install_plan
from deploy.runner_install_validator import validate_runner_installation_dryrun
from deploy.runner_package_blueprint import build_runner_package_blueprint
from deploy.runner_install_consistency import validate_runner_install_consistency
from deploy.runner_release_readiness import build_runner_release_readiness_matrix
from deploy.runner_lab_readiness_plan import build_runner_lab_readiness_unblock_plan
from deploy.runner_sudoers_runtime_test_plan import build_runner_sudoers_runtime_test_plan
from deploy.runner_privileged_validation_test_plan import build_runner_privileged_validation_test_plan
from deploy.runner_real_write_hardware_e2e_test_plan import build_runner_real_write_hardware_e2e_test_plan
from deploy.runner_failure_injection_hardware_test_plan import build_runner_failure_injection_hardware_test_plan
from deploy.runner_device_reenumeration_test_plan import build_runner_device_reenumeration_test_plan
from deploy.runner_hotplug_race_test_plan import build_runner_hotplug_race_test_plan
from deploy.runner_rollback_runtime_test_plan import build_runner_rollback_runtime_test_plan
from deploy.runner_lab_readiness_status import build_runner_lab_readiness_status
from deploy.runner_runtime_runbook_bundle import build_runner_runtime_runbook_bundle
from deploy.runner_runtime_runbook_export import build_runner_runtime_runbook_export_package
from deploy.runner_runtime_result_validator import validate_runner_runtime_result_bundle
from deploy.runner_lab_acceptance_aggregator import build_runner_lab_acceptance_summary
from deploy.runner_lab_acceptance_report_export import build_runner_lab_acceptance_report_export
from deploy.runner_lab_phase_consolidation import build_runner_lab_phase_consolidation
from deploy.runner_next_phase_gate import evaluate_runner_next_phase_gate
from deploy.runner_manual_runtime_precheck import build_runner_manual_runtime_precheck
from deploy.runner_manual_runtime_result_template import create_manual_runtime_result_template
from deploy.runner_manual_runtime_result_edit_checker import check_manual_runtime_result_file
from deploy.runner_manual_runtime_result_bundle_checker import check_manual_runtime_result_bundle
from deploy.runner_manual_runtime_result_validator_handoff_gate import build_manual_runtime_result_validator_handoff
from deploy.runner_manual_runtime_result_validator_dryrun_from_handoff import run_manual_runtime_result_validator_dryrun_from_handoff
from deploy.runner_manual_runtime_validator_report_seal import seal_manual_runtime_validator_report
from deploy.runner_manual_runtime_validator_seal_index import build_validator_report_seal_index
from deploy.runner_manual_runtime_validator_seal_consistency_audit import run_validator_seal_consistency_audit
from deploy.runner_manual_runtime_evidence_timeline import build_manual_runtime_evidence_timeline
from deploy.runner_manual_runtime_evidence_final_snapshot import build_manual_runtime_evidence_final_snapshot
from deploy.runner_manual_runtime_final_acceptance_gate import evaluate_manual_runtime_final_acceptance
from deploy.runner_manual_runtime_final_export_package import build_manual_runtime_final_export_package
from deploy.runner_manual_runtime_failure_injection_matrix import build_manual_runtime_failure_injection_matrix
from deploy.runner_manual_runtime_failure_execution_preview import build_manual_runtime_failure_execution_preview
from deploy.runner_manual_runtime_failure_operator_checklists import build_manual_runtime_failure_operator_checklists
from deploy.runner_manual_runtime_failure_test_sessions import build_manual_runtime_failure_test_sessions
from deploy.runner_manual_runtime_failure_test_result_capture import capture_manual_runtime_failure_test_results
from deploy.runner_manual_runtime_failure_result_evaluation import evaluate_manual_runtime_failure_results
from deploy.runner_manual_runtime_failure_readiness_gate import evaluate_manual_runtime_failure_readiness
from deploy.runner_manual_runtime_laptop_failure_run_selector import select_manual_laptop_failure_test_runs
from deploy.runner_manual_runtime_laptop_failure_operator_runorder import build_manual_laptop_failure_operator_runorder
from deploy.runner_manual_runtime_laptop_failure_execution_log_template import (
    build_manual_laptop_failure_execution_log_template,
)
from deploy.runner_manual_runtime_laptop_failure_execution_log_validator import (
    validate_manual_laptop_failure_execution_log,
)
from deploy.runner_manual_runtime_laptop_failure_test_summary import (
    build_manual_laptop_failure_test_summary,
)
from deploy.runner_manual_runtime_laptop_failure_final_report import (
    build_manual_laptop_failure_final_report,
)
from deploy.runner_manual_runtime_laptop_failure_final_export_package import (
    build_manual_laptop_failure_final_export_package,
)
from deploy.runner_manual_runtime_laptop_failure_evidence_timeline import (
    build_manual_laptop_failure_evidence_timeline,
)
from deploy.runner_manual_runtime_laptop_failure_final_snapshot import (
    build_manual_laptop_failure_final_snapshot,
)
from deploy.runner_manual_runtime_laptop_failure_final_acceptance_gate import (
    evaluate_manual_laptop_failure_final_acceptance,
)
from deploy.runner_manual_runtime_laptop_failure_finalized_export_package import (
    build_manual_laptop_failure_finalized_export_package,
)
from deploy.runner_laptop_failure_test_execution_readiness_final_gate import (
    build_laptop_failure_test_execution_readiness_final_gate,
)
from deploy.runner_laptop_live_probe_execution_handoff import (
    build_laptop_live_probe_final_gate,
    build_laptop_live_probe_plan,
    execute_laptop_live_probe_readonly,
)
from deploy.runner_version_governance import build_version_governance_state
from deploy.runner_version_source_of_truth_check import check_version_source_of_truth_consistency
from deploy.runner_legacy_identifier_inventory import build_legacy_identifier_inventory
from deploy.runner_setuphelfer_runtime_identifier_migration import build_runtime_identifier_migration_plan
from deploy.runner_setuphelfer_identifier_consistency_check import check_setuphelfer_identifier_consistency
from deploy.runner_legacy_identifier_cleanup_classifier import classify_active_legacy_identifiers
from deploy.runner_setuphelfer_safe_rewrite_plan import build_setuphelfer_safe_rewrite_plan
from deploy.runner_setuphelfer_controlled_rewrite_apply import apply_setuphelfer_controlled_rewrite
from deploy.runner_setuphelfer_identifier_cleanup_cycle import (
    apply_setuphelfer_identifier_cleanup_cycle,
    build_setuphelfer_identifier_cleanup_cycle,
    build_setuphelfer_identifier_cleanup_cycle_postcheck,
)
from deploy.runner_legacy_identifier_hotspot_analysis import build_legacy_identifier_hotspot_analysis
from deploy.runner_setuphelfer_identifier_hotspot_cleanup_cycle import (
    apply_setuphelfer_identifier_hotspot_cleanup_cycle,
    build_setuphelfer_identifier_hotspot_cleanup_cycle,
    build_setuphelfer_identifier_hotspot_cleanup_cycle_postcheck,
)
from deploy.runner_setuphelfer_runtime_identifier_elimination import (
    apply_runtime_identifier_elimination,
    build_runtime_identifier_elimination_plan,
    build_runtime_identifier_elimination_postcheck,
    build_runtime_identifier_elimination_targets,
    validate_runtime_compatibility_aliases,
)
from deploy.runner_runtime_identifier_zero_state_verification import verify_runtime_identifier_zero_state
from deploy.runner_setuphelfer_branding_guard import build_setuphelfer_branding_guard_report
from deploy.runner_legacy_runtime_compatibility_validation import (
    analyze_legacy_runtime_coexistence,
    build_legacy_runtime_compatibility_inventory,
    build_legacy_upgrade_path_matrix,
    build_safe_legacy_runtime_migration_recommendations,
)
from deploy.runner_runtime_identifier_patch_bump_preparation import prepare_runtime_identifier_patch_bump
from deploy.runner_runtime_identifier_patch_bump_apply import (
    apply_runtime_identifier_patch_bump,
    build_runtime_identifier_patch_bump_postcheck,
)
from deploy.runner_rescue_live_os_base_decision import build_rescue_live_os_base_decision
from deploy.runner_rescue_stick_component_inventory import build_rescue_stick_component_inventory
from deploy.runner_rescue_mvp_scope_gate import build_rescue_mvp_scope_gate
from deploy.runner_rescue_debian_live_build_plan import build_rescue_debian_live_build_plan
from deploy.runner_rescue_debian_live_build_inputs import (
    build_debian_live_bootloader_templates,
    build_debian_live_build_inputs_final_gate,
    build_debian_live_config_structure,
    build_debian_live_hook_templates,
    build_debian_live_includes_ch_root,
    build_debian_live_package_lists,
    validate_debian_live_build_inputs_safety,
)
from deploy.runner_rescue_dry_build_orchestration import (
    build_rescue_dry_build_final_gate,
    build_rescue_dry_build_input_resolution,
    build_rescue_dry_build_stage_graph,
    build_rescue_package_resolution_plan,
    simulate_rescue_dry_build_execution,
    validate_rescue_build_order,
    validate_rescue_dry_build_safety,
)
from deploy.runner_rescue_build_sandbox_preparation import (
    build_rescue_build_cleanup_plan,
    build_rescue_build_sandbox_final_gate,
    build_rescue_build_sandbox_root,
    build_rescue_overlay_workspace_plan,
    build_rescue_sandbox_config_copy_plan,
    build_rescue_sandbox_runtime_copy_plan,
    validate_rescue_build_sandbox_safety,
)
from deploy.runner_rescue_sandbox_controlled_copy import (
    build_rescue_sandbox_copy_execution_precheck,
    build_rescue_sandbox_copy_final_gate,
    build_rescue_sandbox_copy_seal,
    execute_rescue_sandbox_config_copy,
    execute_rescue_sandbox_runtime_copy,
    verify_rescue_sandbox_copy_results,
)
from deploy.runner_rescue_build_environment_emulation import (
    build_rescue_build_emulation_final_gate,
    build_rescue_build_emulation_seal,
    build_rescue_build_environment_snapshot,
    build_rescue_overlay_persistence_emulation,
    build_rescue_simulated_build_logs,
    build_rescue_simulated_build_outputs,
    build_rescue_simulated_build_workspace,
    verify_rescue_build_emulation,
)
from deploy.runner_rescue_stick_readonly_build_emulation import (
    build_rescue_stick_build_workspace_snapshot,
    build_rescue_stick_evidence_manifest,
    build_rescue_stick_expected_debian_live_tree,
    build_rescue_stick_frontend_bundle_preview,
    build_rescue_stick_network_webui_preview,
    build_rescue_stick_package_list_preview,
    build_rescue_stick_readonly_build_final_gate,
    build_rescue_stick_runtime_bundle_preview,
    build_rescue_stick_systemd_service_preview,
    run_rescue_stick_readonly_build_emulation_all,
)
from deploy.runner_rescue_iso_test_matrix import build_rescue_iso_test_matrix
from deploy.runner_rescue_build_readiness_gate import build_rescue_build_readiness_gate
from deploy.runner_rescue_live_build_config_generator import build_rescue_live_build_config
from deploy.runner_rescue_iso_build_execution_plan import build_rescue_iso_execution_plan
from deploy.runner_rescue_iso_build_execution import build_rescue_iso_build_precheck, execute_rescue_iso_build
from deploy.runner_rescue_vm_test_orchestrator import build_rescue_vm_test_plan, execute_rescue_vm_boot_validation
from deploy.runner_rescue_iso_live_runtime_probe import (
    build_rescue_iso_live_runtime_probe_plan,
    build_rescue_iso_live_runtime_probe_result,
    execute_rescue_iso_live_runtime_probe,
)
from deploy.runner_rescue_iso_readiness_gate import build_rescue_iso_readiness_gate
from deploy.runner_rescue_storage_discovery import (
    build_rescue_storage_discovery_plan,
    build_rescue_storage_discovery_result,
    execute_rescue_storage_discovery,
)
from deploy.runner_rescue_readonly_mount_orchestrator import (
    build_readonly_mount_plan,
    build_readonly_mount_result,
    execute_readonly_mount_validation,
)
from rescue.backup_orchestrator import build_rescue_offline_backup_plan
from rescue.boot_context import build_rescue_boot_context
from rescue.restore_preview_orchestrator import build_rescue_restore_preview_plan
from deploy.runner_rescue_efi_boot_analyzer import build_rescue_efi_boot_analysis
from deploy.runner_rescue_persistent_evidence_export import (
    build_rescue_evidence_export_plan,
    build_rescue_evidence_export_result,
    execute_rescue_evidence_export,
)
from deploy.runner_rescue_remote_help_preparation import build_rescue_remote_help_plan, build_rescue_remote_help_result
from deploy.runner_rescue_live_hardware_matrix import build_rescue_live_hardware_matrix
from deploy.runner_rescue_live_runtime_safety_gate import build_rescue_live_runtime_safety_gate
from deploy.runner_rescue_recovery_scenario_matrix import build_rescue_recovery_scenario_matrix
from deploy.runner_rescue_recovery_target_validation import (
    build_rescue_recovery_target_validation_plan,
    build_rescue_recovery_target_validation_result,
    execute_rescue_recovery_target_validation,
)
from deploy.runner_rescue_backup_discovery_verify import (
    build_rescue_backup_discovery_plan,
    build_rescue_backup_verify_result,
    execute_rescue_backup_discovery,
    execute_rescue_backup_verify,
)
from deploy.runner_rescue_restore_preview_orchestrator import (
    build_rescue_restore_preview_plan,
    build_rescue_restore_preview_result,
    execute_rescue_restore_preview,
)
from deploy.runner_rescue_hardware_recovery_test_chain import build_rescue_hardware_recovery_test_chain
from deploy.runner_rescue_final_recovery_readiness_gate import build_rescue_final_recovery_readiness_gate
from deploy.runner_rescue_manual_recovery_operator_guides import build_rescue_manual_recovery_operator_guides
from deploy.runner_rescue_recovery_evidence_timeline import build_rescue_recovery_evidence_timeline
from deploy.runner_rescue_iso_readiness_pipeline import (
    build_rescue_iso_baseline,
    build_rescue_bootflow_simulation,
    build_rescue_iso_build_plan,
    build_rescue_iso_filesystem_layout,
    build_rescue_iso_final_readiness_gate,
    validate_offline_recovery_runtime,
    validate_rescue_iso_safety,
)
from deploy.runner_rescue_iso_artifact_preparation import (
    build_offline_frontend_artifacts,
    build_rescue_artifact_readiness_gate,
    build_rescue_backend_artifacts,
    build_rescue_boot_artifact_structure,
    build_rescue_overlay_persistence_strategy,
    build_rescue_rootfs_artifact,
)
from deploy.runner_rescue_pseudo_boot_integration import (
    build_rescue_backend_health_integration,
    build_rescue_overlay_boot_strategy,
    build_rescue_pseudo_boot_final_readiness,
    build_rescue_pseudo_boot_manifest,
    build_rescue_recovery_ui_integration,
    build_rescue_service_startup_simulation,
    validate_rescue_pseudo_boot_safety,
)
from deploy.runner_rescue_runtime_assembly_pipeline import (
    build_rescue_backend_runtime_assembly,
    build_rescue_frontend_runtime_assembly,
    build_rescue_offline_configuration_assembly,
    build_rescue_recovery_runtime_assembly,
    build_rescue_runtime_assembly_final_gate,
    build_rescue_runtime_root,
    build_rescue_startup_script_assembly,
    validate_rescue_runtime_assembly_safety,
)
from deploy.runner_rescue_runtime_bundle_manifest import (
    build_rescue_runtime_bundle_hash_manifest,
    build_rescue_runtime_bundle_inventory,
    build_rescue_runtime_bundle_seal,
    check_rescue_runtime_bundle_consistency,
)
from deploy.runner_api_facade import (
    build_runner_catalog,
    build_runner_catalog_summary,
    build_runner_policy_warnings,
    build_runner_risk_gate_summary,
    get_runner_empty_result,
    get_runner_registry_entry,
    get_runner_risk_gate_decision,
    list_runner_never_auto,
    list_runner_operator_required,
    list_runner_plan_allowed,
)

router = APIRouter(prefix="/api/deploy", tags=["deploy-plan"])


class DeployPlanRequest(BaseModel):
    inspect_result: dict[str, Any] = Field(default_factory=dict)
    safety_summary: dict[str, Any] = Field(default_factory=dict)
    classification: dict[str, Any] = Field(default_factory=dict)


DeployPlanRequest.model_rebuild()


class DeploySessionRequest(BaseModel):
    target_device: str = Field(..., min_length=3)
    selected_profile: str = Field(..., min_length=3)
    plan: dict[str, Any] = Field(default_factory=dict)


class DeployExecuteRequest(BaseModel):
    deploy_session_id: str = Field(..., min_length=6)
    confirmation_token: str = Field(..., min_length=8)
    target_device: str = Field(..., min_length=3)
    selected_profile: str = Field(..., min_length=3)
    plan: dict[str, Any] = Field(default_factory=dict)


class DeployPreviewRequest(BaseModel):
    deploy_session_id: str = Field(..., min_length=6)
    confirmation_token: str = Field(..., min_length=8)
    target_device: str = Field(..., min_length=3)
    selected_profile: str = Field(..., min_length=3)
    plan: dict[str, Any] = Field(default_factory=dict)
    os_source: dict[str, Any] = Field(default_factory=dict)


class DeploySourceEvaluateRequest(BaseModel):
    source_id: str = Field(..., min_length=3)
    inspect_result: dict[str, Any] = Field(default_factory=dict)
    deploy_plan: dict[str, Any] = Field(default_factory=dict)


class DeployCachePlanRequest(BaseModel):
    source: dict[str, Any] = Field(default_factory=dict)
    deploy_plan: dict[str, Any] = Field(default_factory=dict)
    inspect_result: dict[str, Any] = Field(default_factory=dict)


class DeployCacheSessionRequest(BaseModel):
    source: dict[str, Any] = Field(default_factory=dict)
    cache_plan: dict[str, Any] = Field(default_factory=dict)


class DeployCacheExecuteRequest(BaseModel):
    cache_session_id: str = Field(..., min_length=6)
    confirmation_token: str = Field(..., min_length=8)
    source: dict[str, Any] = Field(default_factory=dict)
    cache_plan: dict[str, Any] = Field(default_factory=dict)


class DeployImageInspectRequest(BaseModel):
    image_path: str = Field(..., min_length=1)
    expected_checksum: str = ""
    expected_architecture: str = "unknown"
    expected_type: str = "unknown"


class DeployWritePlanRequest(BaseModel):
    deploy_session: dict[str, Any] = Field(default_factory=dict)
    deploy_preview: dict[str, Any] = Field(default_factory=dict)
    image_inspect: dict[str, Any] = Field(default_factory=dict)
    inspect_result: dict[str, Any] = Field(default_factory=dict)
    safety_summary: dict[str, Any] = Field(default_factory=dict)


class DeployWriteSessionRequest(BaseModel):
    target_device: str = Field(..., min_length=3)
    selected_profile: str = Field(..., min_length=3)
    image_inspect: dict[str, Any] = Field(default_factory=dict)
    write_plan: dict[str, Any] = Field(default_factory=dict)
    confirmations: list[str] = Field(default_factory=list)


class DeployWriteExecuteRequest(BaseModel):
    write_session_id: str = Field(..., min_length=6)
    confirmation_token: str = Field(..., min_length=8)
    target_device: str = Field(..., min_length=3)
    selected_profile: str = Field(..., min_length=3)
    image_path: str = Field(..., min_length=1)
    write_plan: dict[str, Any] = Field(default_factory=dict)


class DeployFinalConfirmationSessionRequest(BaseModel):
    write_execute_result: dict[str, Any] = Field(default_factory=dict)
    write_plan: dict[str, Any] = Field(default_factory=dict)
    inspect_result: dict[str, Any] = Field(default_factory=dict)
    confirmations: list[str] = Field(default_factory=list)


class DeployFinalConfirmationCheckRequest(BaseModel):
    final_confirmation_id: str = Field(..., min_length=6)
    confirmation_token: str = Field(..., min_length=8)
    target_snapshot: dict[str, Any] = Field(default_factory=dict)


class DeployWriteHarnessSessionRequest(BaseModel):
    final_confirmation_result: dict[str, Any] = Field(default_factory=dict)
    image_inspect: dict[str, Any] = Field(default_factory=dict)
    test_target_path: str = Field(..., min_length=8)


class DeployWriteHarnessExecuteRequest(BaseModel):
    harness_session_id: str = Field(..., min_length=6)
    confirmation_token: str = Field(..., min_length=8)
    image_path: str = Field(..., min_length=1)
    test_target_path: str = Field(..., min_length=8)
    max_bytes: int = Field(..., gt=0)


class DeployRealWriteGuardSessionRequest(BaseModel):
    final_confirmation_result: dict[str, Any] = Field(default_factory=dict)
    write_session_result: dict[str, Any] = Field(default_factory=dict)
    write_execute_result: dict[str, Any] = Field(default_factory=dict)
    write_plan: dict[str, Any] = Field(default_factory=dict)
    inspect_result: dict[str, Any] = Field(default_factory=dict)
    safety_summary: dict[str, Any] = Field(default_factory=dict)
    write_harness_result: dict[str, Any] = Field(default_factory=dict)


class DeployRealWriteGuardCheckRequest(BaseModel):
    real_write_guard_id: str = Field(..., min_length=6)
    confirmation_token: str = Field(..., min_length=8)
    snapshot: dict[str, Any] = Field(default_factory=dict)
    inspect_result: dict[str, Any] = Field(default_factory=dict)
    safety_summary: dict[str, Any] = Field(default_factory=dict)
    write_plan: dict[str, Any] = Field(default_factory=dict)
    write_harness_result: dict[str, Any] = Field(default_factory=dict)


class DeployHardwareGateReportRequest(BaseModel):
    target_device: str = Field(..., min_length=3)
    inspect_result: dict[str, Any] = Field(default_factory=dict)
    safety_summary: dict[str, Any] = Field(default_factory=dict)
    write_harness_result: dict[str, Any] = Field(default_factory=dict)
    final_confirmation_result: dict[str, Any] = Field(default_factory=dict)
    real_write_guard_result: dict[str, Any] = Field(default_factory=dict)


class DeployHardwareGateOperatorProtocolRequest(BaseModel):
    target_device: str = Field(..., min_length=3)
    hardware_gate_report: dict[str, Any] = Field(default_factory=dict)


class DeployRealWritePrototypeRequest(BaseModel):
    target_device: str = Field(..., min_length=3)
    image_path: str = Field(..., min_length=1)
    expected_checksum: str = Field(..., min_length=16)
    inspect_result: dict[str, Any] = Field(default_factory=dict)
    safety_summary: dict[str, Any] = Field(default_factory=dict)
    write_harness_result: dict[str, Any] = Field(default_factory=dict)
    real_write_guard_result: dict[str, Any] = Field(default_factory=dict)
    guard_snapshot: dict[str, Any] = Field(default_factory=dict)
    final_confirmation_id: str = Field(..., min_length=6)
    confirmation_token: str = Field(..., min_length=8)
    target_snapshot: dict[str, Any] = Field(default_factory=dict)


class DeployRunnerHandoffRequest(BaseModel):
    final_confirmation_result: dict[str, Any] = Field(default_factory=dict)
    real_write_guard_result: dict[str, Any] = Field(default_factory=dict)
    hardware_gate_report: dict[str, Any] = Field(default_factory=dict)
    image_inspect_result: dict[str, Any] = Field(default_factory=dict)
    write_plan: dict[str, Any] = Field(default_factory=dict)
    write_execute_result: dict[str, Any] = Field(default_factory=dict)


class DeployRunnerSudoersAuditRequest(BaseModel):
    allowed_runner_path: str = "/opt/setuphelfer/backend/tools/deploy_write_runner.py"
    allowed_job_directory: str = "/var/lib/setuphelfer/deploy-jobs"
    allowed_environment: list[str] = Field(default_factory=list)


class DeployRunnerEnvironmentAuditRequest(BaseModel):
    environment: dict[str, str] = Field(default_factory=dict)


class DeployRunnerPathAuditRequest(BaseModel):
    runner_path: str = Field(..., min_length=1)


class DeployRunnerJobDirAuditRequest(BaseModel):
    job_directory: str = Field(..., min_length=1)
    allowed_prefixes: list[str] = Field(default_factory=list)


class DeployRunnerSandboxPolicyRequest(BaseModel):
    environment: dict[str, str] = Field(default_factory=dict)
    runner_path: str = "/opt/setuphelfer/backend/tools/deploy_write_runner.py"
    job_directory: str = "/var/lib/setuphelfer/deploy-jobs"


class DeployRunnerSandboxEnvironmentRequest(BaseModel):
    environment: dict[str, str] = Field(default_factory=dict)


class DeployRunnerSandboxTimeoutRequest(BaseModel):
    max_runtime_seconds: int = 30
    graceful_shutdown_timeout: int = 5
    hard_kill_timeout: int = 2
    stale_runner_timeout: int = 60
    lock_cleanup_timeout: int = 120


class DeployRunnerSandboxPrivilegeRequest(BaseModel):
    recommended_runner_user: str = "setuphelfer-runner"


class DeployRunnerInstallPlanRequest(BaseModel):
    runner_binary_path: str = "/opt/setuphelfer/backend/tools/deploy_write_runner.py"
    interpreter_path: str = "/usr/bin/python3"
    job_directory: str = "/var/lib/setuphelfer/deploy-jobs"
    backend_runs_as_root: bool = False
    daemon_mode_requested: bool = False
    sudoers_contains_wildcard: bool = False
    runner_path_is_symlink: bool = False
    runner_parent_world_writable: bool = False
    env_injection_risk: bool = False


class DeployRunnerInstallValidateRequest(BaseModel):
    install_plan: dict[str, Any] = Field(default_factory=dict)
    sudoers_snippet_text: str = ""
    environment: dict[str, str] = Field(default_factory=dict)


class DeployRunnerPackageBlueprintRequest(BaseModel):
    package_type: str = "manual_install_bundle"
    allow_daemon_mode: bool = False
    allow_service_mode: bool = False
    allow_socket_mode: bool = False


class DeployRunnerInstallConsistencyRequest(BaseModel):
    install_plan: dict[str, Any] = Field(default_factory=dict)
    install_validation: dict[str, Any] = Field(default_factory=dict)
    package_blueprint: dict[str, Any] = Field(default_factory=dict)


class DeployRunnerReleaseReadinessRequest(BaseModel):
    components: list[dict[str, Any]] = Field(default_factory=list)
    blocking_gaps: list[str] = Field(default_factory=list)
    non_blocking_gaps: list[str] = Field(default_factory=list)
    required_evidence: list[str] = Field(default_factory=list)
    required_next_validations: list[str] = Field(default_factory=list)


class DeployRunnerLabReadinessPlanRequest(BaseModel):
    blocking_gaps: list[str] = Field(default_factory=list)


class DeployRunnerSudoersRuntimeTestPlanRequest(BaseModel):
    placeholder: dict[str, Any] = Field(default_factory=dict)


class DeployRunnerPrivilegedValidationTestPlanRequest(BaseModel):
    placeholder: dict[str, Any] = Field(default_factory=dict)


class DeployRunnerRealWriteHardwareE2ETestPlanRequest(BaseModel):
    placeholder: dict[str, Any] = Field(default_factory=dict)


class DeployRunnerFailureInjectionHardwareTestPlanRequest(BaseModel):
    placeholder: dict[str, Any] = Field(default_factory=dict)


class DeployRunnerDeviceReenumerationTestPlanRequest(BaseModel):
    placeholder: dict[str, Any] = Field(default_factory=dict)


class DeployRunnerHotplugRaceTestPlanRequest(BaseModel):
    placeholder: dict[str, Any] = Field(default_factory=dict)


class DeployRunnerRollbackRuntimeTestPlanRequest(BaseModel):
    placeholder: dict[str, Any] = Field(default_factory=dict)


class DeployRunnerLabReadinessStatusRequest(BaseModel):
    design_evidence: dict[str, list[str]] = Field(default_factory=dict)
    runtime_evidence: dict[str, list[str]] = Field(default_factory=dict)


class DeployRunnerRuntimeRunbookBundleRequest(BaseModel):
    placeholder: dict[str, Any] = Field(default_factory=dict)


class DeployRunnerRuntimeRunbookExportRequest(BaseModel):
    target_files: dict[str, str] = Field(default_factory=dict)


class DeployRunnerRuntimeResultsValidateRequest(BaseModel):
    result_files: list[str] = Field(default_factory=list)
    acceptance_decision: str = "blocked"


class DeployRunnerLabAcceptanceRequest(BaseModel):
    validated_runtime_results: dict[str, Any] = Field(default_factory=dict)


class DeployRunnerLabAcceptanceExportRequest(BaseModel):
    acceptance: dict[str, Any] = Field(default_factory=dict)


class DeployRunnerLabPhaseConsolidationRequest(BaseModel):
    placeholder: dict[str, Any] = Field(default_factory=dict)


class DeployRunnerNextPhaseGateRequest(BaseModel):
    placeholder: dict[str, Any] = Field(default_factory=dict)


class DeployRunnerManualRuntimePrecheckRequest(BaseModel):
    selected_runbook: str = Field(..., min_length=3)
    next_phase_gate: dict[str, Any] = Field(default_factory=dict)
    operator_confirmations: dict[str, bool] = Field(default_factory=dict)
    hardware_gate_report: dict[str, Any] = Field(default_factory=dict)
    real_write_guard_report: dict[str, Any] = Field(default_factory=dict)
    runtime_context: dict[str, Any] = Field(default_factory=dict)


class DeployRunnerManualRuntimeResultTemplateRequest(BaseModel):
    precheck: dict[str, Any] = Field(default_factory=dict)
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeResultCheckRequest(BaseModel):
    result_file: str = Field(..., min_length=1)


class DeployRunnerManualRuntimeResultBundleCheckRequest(BaseModel):
    result_files: list[str] = Field(default_factory=list)


class DeployRunnerManualRuntimeResultValidatorHandoffRequest(BaseModel):
    bundle_check_result: dict[str, Any] = Field(default_factory=dict)
    result_files: list[str] = Field(default_factory=list)
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeResultValidatorDryrunFromHandoffRequest(BaseModel):
    handoff_manifest_path: str = Field(..., min_length=1)
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeResultValidatorReportSealRequest(BaseModel):
    dryrun_report_path: str = Field(..., min_length=1)
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeValidatorSealIndexRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeValidatorSealConsistencyAuditRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeEvidenceTimelineRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeEvidenceFinalSnapshotRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeFinalAcceptanceRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeFinalExportPackageRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeFailureInjectionMatrixRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeFailureExecutionPreviewRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeFailureOperatorChecklistsRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeFailureTestSessionsRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeFailureTestResultsRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeFailureResultEvaluationRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeFailureReadinessGateRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeLaptopFailureRunSelectionRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeLaptopFailureOperatorRunorderRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeLaptopFailureExecutionLogTemplateRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeLaptopFailureExecutionLogValidationRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeLaptopFailureTestSummaryRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeLaptopFailureFinalReportRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeLaptopFailureFinalExportPackageRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeLaptopFailureEvidenceTimelineRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeLaptopFailureFinalSnapshotRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeLaptopFailureFinalAcceptanceRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRunnerManualRuntimeLaptopFailureFinalizedExportPackageRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployVersionGovernanceStateRequest(BaseModel):
    previous_version: str = "1.5.0"
    strict_mode_phase: str = "laptop_failure_finalization_chain"
    phase_status: str = "completed"
    release_readiness: str = "internal_testing"
    completed_modules: list[str] = Field(default_factory=list)
    evidence_artifacts: list[str] = Field(default_factory=list)
    test_status: str = "green"
    changes: list[str] = Field(default_factory=list)
    explicit_overwrite: bool = False


class DeployVersionSourceOfTruthCheckRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployLegacyIdentifierInventoryRequest(BaseModel):
    explicit_overwrite: bool = False


class DeploySetuphelferRuntimeIdentifierMigrationRequest(BaseModel):
    explicit_overwrite: bool = False


class DeploySetuphelferIdentifierConsistencyCheckRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployLegacyIdentifierCleanupClassificationRequest(BaseModel):
    explicit_overwrite: bool = False


class DeploySetuphelferSafeRewritePlanRequest(BaseModel):
    explicit_overwrite: bool = False


class DeploySetuphelferControlledRewriteApplyRequest(BaseModel):
    explicit_overwrite: bool = False
    run_post_consistency_check: bool = True


class DeploySetuphelferIdentifierCleanupCyclePlanRequest(BaseModel):
    explicit_overwrite: bool = False


class DeploySetuphelferIdentifierCleanupCycleApplyRequest(BaseModel):
    explicit_overwrite: bool = False


class DeploySetuphelferIdentifierCleanupCyclePostcheckRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployLegacyIdentifierHotspotAnalysisRequest(BaseModel):
    explicit_overwrite: bool = False


class DeploySetuphelferIdentifierHotspotCleanupCyclePlanRequest(BaseModel):
    explicit_overwrite: bool = False


class DeploySetuphelferIdentifierHotspotCleanupCycleApplyRequest(BaseModel):
    explicit_overwrite: bool = False


class DeploySetuphelferIdentifierHotspotCleanupCyclePostcheckRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRuntimeIdentifierEliminationTargetsRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRuntimeIdentifierEliminationPlanRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRuntimeIdentifierEliminationApplyRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRuntimeCompatibilityAliasValidationRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRuntimeIdentifierEliminationPostcheckRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRuntimeIdentifierZeroStateVerificationRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRuntimeIdentifierPatchBumpPreparationRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRuntimeIdentifierPatchBumpApplyRequest(BaseModel):
    explicit_overwrite: bool = False
    explicit_apply_patch_bump: bool = False


class DeployRuntimeIdentifierPatchBumpPostcheckRequest(BaseModel):
    explicit_overwrite: bool = False


class DeploySetuphelferBrandingGuardCheckRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployLegacyRuntimeCompatibilityInventoryRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployLegacyRuntimeCoexistenceAnalysisRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployLegacyRuntimeSafeMigrationRecommendationsRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployLegacyUpgradePathMatrixRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployLaptopFailureTestExecutionReadinessFinalGateRequest(BaseModel):
    explicit_overwrite: bool = False
    probe_live_system: bool = False
    live_base_url: str | None = Field(default=None, max_length=256)


class DeployLaptopLiveProbePlanRequest(BaseModel):
    explicit_overwrite: bool = False
    live_base_url: str | None = Field(default=None, max_length=256)


class DeployLaptopLiveProbeExecuteReadonlyRequest(BaseModel):
    explicit_overwrite: bool = False
    explicit_execute_live_probe: bool = False
    allow_real_verify_path: bool = False
    live_base_url: str | None = Field(default=None, max_length=256)


class DeployLaptopLiveProbeFinalGateRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRescueHandoffOverwriteRequest(BaseModel):
    explicit_overwrite: bool = False


class DeployRescueIsoBuildPrecheckRequest(BaseModel):
    explicit_overwrite: bool = False
    min_free_disk_bytes: int | None = Field(default=None, ge=1)


class DeployRescueIsoBuildExecuteRequest(BaseModel):
    explicit_overwrite: bool = False
    explicit_execute_iso_build: bool = False
    explicit_rescue_build_approved: bool = False
    build_timeout_seconds: int = Field(default=7200, ge=60, le=86400)


class DeployRescueVmTestExecuteRequest(BaseModel):
    explicit_overwrite: bool = False
    explicit_execute_vm_boot: bool = False


class DeployRescueIsoLiveRuntimeProbeRequest(BaseModel):
    explicit_overwrite: bool = False
    action: str = Field(default="plan", min_length=3, max_length=16)
    explicit_execute_iso_live_runtime_probe: bool = False
    live_base_url: str | None = Field(default=None, max_length=256)


class DeployRescueStorageDiscoveryRequest(BaseModel):
    explicit_overwrite: bool = False
    action: str = Field(default="plan", min_length=3, max_length=16)
    explicit_execute_storage_discovery: bool = False


class DeployRescueReadonlyMountRequest(BaseModel):
    explicit_overwrite: bool = False
    action: str = Field(default="plan", min_length=3, max_length=16)
    explicit_execute_readonly_mount: bool = False


class DeployRescueBootContextPreviewRequest(BaseModel):
    source_root: str | None = Field(default=None, max_length=512)
    storage_snapshot_ref: str | None = Field(default=None, max_length=256)
    mount_snapshot_ref: str | None = Field(default=None, max_length=256)
    rescue_mode_hint: bool | None = None
    live_system_hint: bool | None = None
    network_available_hint: bool | None = None
    ui_mode_hint: str | None = Field(default=None, max_length=32)


class DeployRescueOfflineBackupPlanRequest(BaseModel):
    source_root: str | None = Field(default=None, max_length=512)
    target_path: str | None = Field(default=None, max_length=512)
    backup_profile_id: str = Field(default="offline-full", max_length=64)
    boot_context: dict[str, Any] | None = None


class DeployRescueRestorePreviewPlanRequest(BaseModel):
    source_root: str | None = Field(default=None, max_length=512)
    backup_archive_path: str | None = Field(default=None, max_length=512)
    manifest_path: str | None = Field(default=None, max_length=512)
    target_device_or_path: str | None = Field(default=None, max_length=512)
    restore_profile_id: str = Field(default="offline-full-restore-preview", max_length=64)
    boot_context: dict[str, Any] | None = None
    verify_status: str | None = Field(default=None, max_length=32)
    target_classification: str | None = Field(default=None, max_length=64)
    operator_override: bool = False
    existing_filesystems: bool | None = None
    existing_os_indicators: bool | None = None
    user_data_indicators: bool | None = None


class DeployRescueEvidenceExportRequest(BaseModel):
    explicit_overwrite: bool = False
    action: str = Field(default="plan", min_length=3, max_length=16)
    explicit_execute_evidence_export: bool = False
    export_target: str | None = Field(default=None, max_length=512)


class DeployRescueRemoteHelpRequest(BaseModel):
    explicit_overwrite: bool = False
    action: str = Field(default="plan", min_length=3, max_length=16)


class DeployRescueRecoveryTargetValidationRequest(BaseModel):
    explicit_overwrite: bool = False
    action: str = Field(default="plan", min_length=3, max_length=16)
    explicit_execute_recovery_target_validation: bool = False
    proposed_recovery_target: str | None = Field(default=None, max_length=512)


class DeployRescueBackupDiscoveryVerifyRequest(BaseModel):
    explicit_overwrite: bool = False
    action: str = Field(default="plan", min_length=3, max_length=16)
    explicit_execute_backup_discovery: bool = False
    explicit_execute_backup_verify: bool = False
    backup_scan_root: str | None = Field(default=None, max_length=512)


class DeployRescueRestorePreviewRequest(BaseModel):
    explicit_overwrite: bool = False
    action: str = Field(default="plan", min_length=3, max_length=16)
    explicit_execute_restore_preview: bool = False


DeploySessionRequest.model_rebuild()
DeployExecuteRequest.model_rebuild()
DeployPreviewRequest.model_rebuild()
DeploySourceEvaluateRequest.model_rebuild()
DeployCachePlanRequest.model_rebuild()
DeployCacheSessionRequest.model_rebuild()
DeployCacheExecuteRequest.model_rebuild()
DeployImageInspectRequest.model_rebuild()
DeployWritePlanRequest.model_rebuild()
DeployWriteSessionRequest.model_rebuild()
DeployWriteExecuteRequest.model_rebuild()
DeployFinalConfirmationSessionRequest.model_rebuild()
DeployFinalConfirmationCheckRequest.model_rebuild()
DeployWriteHarnessSessionRequest.model_rebuild()
DeployWriteHarnessExecuteRequest.model_rebuild()
DeployRealWriteGuardSessionRequest.model_rebuild()
DeployRealWriteGuardCheckRequest.model_rebuild()
DeployHardwareGateReportRequest.model_rebuild()
DeployHardwareGateOperatorProtocolRequest.model_rebuild()
DeployRealWritePrototypeRequest.model_rebuild()
DeployRunnerHandoffRequest.model_rebuild()
DeployRunnerSudoersAuditRequest.model_rebuild()
DeployRunnerEnvironmentAuditRequest.model_rebuild()
DeployRunnerPathAuditRequest.model_rebuild()
DeployRunnerJobDirAuditRequest.model_rebuild()
DeployRunnerSandboxPolicyRequest.model_rebuild()
DeployRunnerSandboxEnvironmentRequest.model_rebuild()
DeployRunnerSandboxTimeoutRequest.model_rebuild()
DeployRunnerSandboxPrivilegeRequest.model_rebuild()
DeployRunnerInstallPlanRequest.model_rebuild()
DeployRunnerInstallValidateRequest.model_rebuild()
DeployRunnerPackageBlueprintRequest.model_rebuild()
DeployRunnerInstallConsistencyRequest.model_rebuild()
DeployRunnerReleaseReadinessRequest.model_rebuild()
DeployRunnerLabReadinessPlanRequest.model_rebuild()
DeployRunnerSudoersRuntimeTestPlanRequest.model_rebuild()
DeployRunnerPrivilegedValidationTestPlanRequest.model_rebuild()
DeployRunnerRealWriteHardwareE2ETestPlanRequest.model_rebuild()
DeployRunnerFailureInjectionHardwareTestPlanRequest.model_rebuild()
DeployRunnerDeviceReenumerationTestPlanRequest.model_rebuild()
DeployRunnerHotplugRaceTestPlanRequest.model_rebuild()
DeployRunnerRollbackRuntimeTestPlanRequest.model_rebuild()
DeployRunnerLabReadinessStatusRequest.model_rebuild()
DeployRunnerRuntimeRunbookBundleRequest.model_rebuild()
DeployRunnerRuntimeRunbookExportRequest.model_rebuild()
DeployRunnerRuntimeResultsValidateRequest.model_rebuild()
DeployRunnerLabAcceptanceRequest.model_rebuild()
DeployRunnerLabAcceptanceExportRequest.model_rebuild()
DeployRunnerLabPhaseConsolidationRequest.model_rebuild()
DeployRunnerNextPhaseGateRequest.model_rebuild()
DeployRunnerManualRuntimePrecheckRequest.model_rebuild()
DeployRunnerManualRuntimeResultTemplateRequest.model_rebuild()
DeployRunnerManualRuntimeResultCheckRequest.model_rebuild()
DeployRunnerManualRuntimeResultBundleCheckRequest.model_rebuild()
DeployRunnerManualRuntimeResultValidatorHandoffRequest.model_rebuild()
DeployRunnerManualRuntimeResultValidatorDryrunFromHandoffRequest.model_rebuild()
DeployRunnerManualRuntimeResultValidatorReportSealRequest.model_rebuild()
DeployRunnerManualRuntimeValidatorSealIndexRequest.model_rebuild()
DeployRunnerManualRuntimeValidatorSealConsistencyAuditRequest.model_rebuild()
DeployRunnerManualRuntimeEvidenceTimelineRequest.model_rebuild()
DeployRunnerManualRuntimeEvidenceFinalSnapshotRequest.model_rebuild()
DeployRunnerManualRuntimeFinalAcceptanceRequest.model_rebuild()
DeployRunnerManualRuntimeFinalExportPackageRequest.model_rebuild()
DeployRunnerManualRuntimeFailureInjectionMatrixRequest.model_rebuild()
DeployRunnerManualRuntimeFailureExecutionPreviewRequest.model_rebuild()
DeployRunnerManualRuntimeFailureOperatorChecklistsRequest.model_rebuild()
DeployRunnerManualRuntimeFailureTestSessionsRequest.model_rebuild()
DeployRunnerManualRuntimeFailureTestResultsRequest.model_rebuild()
DeployRunnerManualRuntimeFailureResultEvaluationRequest.model_rebuild()
DeployRunnerManualRuntimeFailureReadinessGateRequest.model_rebuild()
DeployRunnerManualRuntimeLaptopFailureRunSelectionRequest.model_rebuild()
DeployRunnerManualRuntimeLaptopFailureOperatorRunorderRequest.model_rebuild()
DeployRunnerManualRuntimeLaptopFailureExecutionLogTemplateRequest.model_rebuild()
DeployRunnerManualRuntimeLaptopFailureExecutionLogValidationRequest.model_rebuild()
DeployRunnerManualRuntimeLaptopFailureTestSummaryRequest.model_rebuild()
DeployRunnerManualRuntimeLaptopFailureFinalReportRequest.model_rebuild()
DeployRunnerManualRuntimeLaptopFailureFinalExportPackageRequest.model_rebuild()
DeployRunnerManualRuntimeLaptopFailureEvidenceTimelineRequest.model_rebuild()
DeployRunnerManualRuntimeLaptopFailureFinalSnapshotRequest.model_rebuild()
DeployRunnerManualRuntimeLaptopFailureFinalAcceptanceRequest.model_rebuild()
DeployRunnerManualRuntimeLaptopFailureFinalizedExportPackageRequest.model_rebuild()
DeployVersionGovernanceStateRequest.model_rebuild()
DeployVersionSourceOfTruthCheckRequest.model_rebuild()
DeployLegacyIdentifierInventoryRequest.model_rebuild()
DeploySetuphelferRuntimeIdentifierMigrationRequest.model_rebuild()
DeploySetuphelferIdentifierConsistencyCheckRequest.model_rebuild()
DeployLegacyIdentifierCleanupClassificationRequest.model_rebuild()
DeploySetuphelferSafeRewritePlanRequest.model_rebuild()
DeploySetuphelferControlledRewriteApplyRequest.model_rebuild()
DeploySetuphelferIdentifierCleanupCyclePlanRequest.model_rebuild()
DeploySetuphelferIdentifierCleanupCycleApplyRequest.model_rebuild()
DeploySetuphelferIdentifierCleanupCyclePostcheckRequest.model_rebuild()
DeployLegacyIdentifierHotspotAnalysisRequest.model_rebuild()
DeploySetuphelferIdentifierHotspotCleanupCyclePlanRequest.model_rebuild()
DeploySetuphelferIdentifierHotspotCleanupCycleApplyRequest.model_rebuild()
DeploySetuphelferIdentifierHotspotCleanupCyclePostcheckRequest.model_rebuild()
DeployRuntimeIdentifierEliminationTargetsRequest.model_rebuild()
DeployRuntimeIdentifierEliminationPlanRequest.model_rebuild()
DeployRuntimeIdentifierEliminationApplyRequest.model_rebuild()
DeployRuntimeCompatibilityAliasValidationRequest.model_rebuild()
DeployRuntimeIdentifierEliminationPostcheckRequest.model_rebuild()
DeployRuntimeIdentifierZeroStateVerificationRequest.model_rebuild()
DeployRuntimeIdentifierPatchBumpPreparationRequest.model_rebuild()
DeployRuntimeIdentifierPatchBumpApplyRequest.model_rebuild()
DeployRuntimeIdentifierPatchBumpPostcheckRequest.model_rebuild()
DeploySetuphelferBrandingGuardCheckRequest.model_rebuild()
DeployLegacyRuntimeCompatibilityInventoryRequest.model_rebuild()
DeployLegacyRuntimeCoexistenceAnalysisRequest.model_rebuild()
DeployLegacyRuntimeSafeMigrationRecommendationsRequest.model_rebuild()
DeployLegacyUpgradePathMatrixRequest.model_rebuild()
DeployLaptopFailureTestExecutionReadinessFinalGateRequest.model_rebuild()
DeployLaptopLiveProbePlanRequest.model_rebuild()
DeployLaptopLiveProbeExecuteReadonlyRequest.model_rebuild()
DeployLaptopLiveProbeFinalGateRequest.model_rebuild()
DeployRescueHandoffOverwriteRequest.model_rebuild()
DeployRescueIsoBuildPrecheckRequest.model_rebuild()
DeployRescueIsoBuildExecuteRequest.model_rebuild()
DeployRescueVmTestExecuteRequest.model_rebuild()
DeployRescueIsoLiveRuntimeProbeRequest.model_rebuild()
DeployRescueStorageDiscoveryRequest.model_rebuild()
DeployRescueReadonlyMountRequest.model_rebuild()
DeployRescueBootContextPreviewRequest.model_rebuild()
DeployRescueOfflineBackupPlanRequest.model_rebuild()
DeployRescueRestorePreviewPlanRequest.model_rebuild()
DeployRescueRecoveryTargetValidationRequest.model_rebuild()
DeployRescueBackupDiscoveryVerifyRequest.model_rebuild()
DeployRescueRestorePreviewRequest.model_rebuild()
DeployRescueEvidenceExportRequest.model_rebuild()
DeployRescueRemoteHelpRequest.model_rebuild()


@router.post("/plan")
async def post_deploy_plan(body: DeployPlanRequest) -> dict[str, Any]:
    plan = generate_deploy_plan(
        body.inspect_result or {},
        body.safety_summary or {},
        body.classification or None,
    )
    st = str(plan.get("plan_status") or "not_applicable")
    code = "DEPLOY_PLAN_NOT_APPLICABLE"
    if st == "ok":
        code = "DEPLOY_PLAN_OK"
    elif st == "review_required":
        code = "DEPLOY_PLAN_REVIEW_REQUIRED"
    elif st == "blocked":
        code = "DEPLOY_PLAN_BLOCKED"
    return {
        "code": code,
        "plan": plan,
        "warnings": plan.get("warnings") or [],
        "errors": plan.get("errors") or [],
    }


@router.post("/session")
async def post_deploy_session(body: DeploySessionRequest) -> dict[str, Any]:
    return create_deploy_session(body.model_dump())


@router.post("/execute")
async def post_deploy_execute(body: DeployExecuteRequest) -> dict[str, Any]:
    return execute_deploy(body.model_dump())


@router.post("/preview")
async def post_deploy_preview(body: DeployPreviewRequest) -> dict[str, Any]:
    return preview_deploy(body.model_dump())


@router.get("/sources")
async def get_deploy_sources() -> dict[str, Any]:
    registry = get_deploy_source_registry()
    return {
        "code": "DEPLOY_SOURCE_REGISTRY_OK",
        "registry": registry,
        "warnings": [],
        "errors": [],
    }


@router.post("/source/evaluate")
async def post_deploy_source_evaluate(body: DeploySourceEvaluateRequest) -> dict[str, Any]:
    registry = get_deploy_source_registry()
    sources = registry.get("sources") if isinstance(registry.get("sources"), list) else []
    source = next((s for s in sources if isinstance(s, dict) and str(s.get("source_id") or "") == body.source_id), None)
    if source is None:
        return {
            "code": "DEPLOY_SOURCE_EVALUATED",
            "source": {},
            "compatibility": {"compatible": False, "risk_level": "high", "warnings": [], "errors": ["DEPLOY_SOURCE_NOT_FOUND"], "reasons": ["source_not_found"]},
            "warnings": [],
            "errors": ["DEPLOY_SOURCE_NOT_FOUND"],
        }

    warnings: list[str] = []
    errors: list[str] = []
    source_view = dict(source)

    st = str(source.get("type") or "")
    if st == "local_image":
        v = validate_local_image_entry(source)
        code = str(v.get("code") or "")
        if code != "DEPLOY_SOURCE_LOCAL_IMAGE_VALID":
            errors.append(code)
        source_view.setdefault("warnings", [])
        source_view.setdefault("errors", [])
        if code:
            if code.endswith("_VALID"):
                warnings.append(code)
            else:
                source_view["errors"] = list(source_view.get("errors") or []) + [code]
    elif st == "remote_image":
        v = validate_remote_image_metadata(source)
        code = str(v.get("code") or "")
        warn = str(v.get("warning") or "")
        if code != "DEPLOY_SOURCE_REMOTE_METADATA_VALID":
            errors.append(code)
            source_view["status"] = "blocked"
        if warn:
            warnings.append(warn)

    compat = evaluate_source_compatibility(source_view, body.inspect_result or {}, body.deploy_plan or {})
    return {
        "code": "DEPLOY_SOURCE_EVALUATED",
        "source": source_view,
        "compatibility": compat,
        "warnings": warnings + list(compat.get("warnings") or []),
        "errors": errors + list(compat.get("errors") or []),
    }


@router.post("/cache/plan")
async def post_deploy_cache_plan(body: DeployCachePlanRequest) -> dict[str, Any]:
    plan = generate_deploy_cache_plan(
        body.source or {},
        body.deploy_plan or {},
        body.inspect_result or {},
    )
    st = str(plan.get("plan_status") or "not_applicable")
    code = "DEPLOY_CACHE_PLAN_NOT_APPLICABLE"
    if st == "ok":
        code = "DEPLOY_CACHE_PLAN_OK"
    elif st == "review_required":
        code = "DEPLOY_CACHE_PLAN_REVIEW_REQUIRED"
    elif st == "blocked":
        code = "DEPLOY_CACHE_PLAN_BLOCKED"
    return {
        "code": code,
        "plan": plan,
        "warnings": plan.get("warnings") or [],
        "errors": plan.get("errors") or [],
    }


@router.post("/cache/session")
async def post_deploy_cache_session(body: DeployCacheSessionRequest) -> dict[str, Any]:
    return create_deploy_cache_session(body.model_dump())


@router.post("/cache/execute")
async def post_deploy_cache_execute(body: DeployCacheExecuteRequest) -> dict[str, Any]:
    return execute_deploy_cache(body.model_dump())


@router.post("/image/inspect")
async def post_deploy_image_inspect(body: DeployImageInspectRequest) -> dict[str, Any]:
    return inspect_deploy_image(body.model_dump())


@router.post("/write/plan")
async def post_deploy_write_plan(body: DeployWritePlanRequest) -> dict[str, Any]:
    plan = generate_deploy_write_plan(
        body.deploy_session or {},
        body.deploy_preview or {},
        body.image_inspect or {},
        body.inspect_result or {},
        body.safety_summary or {},
    )
    st = str(plan.get("plan_status") or "not_applicable")
    code = "DEPLOY_WRITE_PLAN_NOT_APPLICABLE"
    if st == "ok":
        code = "DEPLOY_WRITE_PLAN_OK"
    elif st == "review_required":
        code = "DEPLOY_WRITE_PLAN_REVIEW_REQUIRED"
    elif st == "blocked":
        code = "DEPLOY_WRITE_PLAN_BLOCKED"
    return {
        "code": code,
        "plan": plan,
        "warnings": plan.get("warnings") or [],
        "errors": plan.get("errors") or [],
    }


@router.post("/write/session")
async def post_deploy_write_session(body: DeployWriteSessionRequest) -> dict[str, Any]:
    return create_deploy_write_session(body.model_dump())


@router.post("/write/execute")
async def post_deploy_write_execute(body: DeployWriteExecuteRequest) -> dict[str, Any]:
    return execute_deploy_write_dryrun(body.model_dump())


@router.post("/write/prototype")
async def post_deploy_write_prototype(body: DeployRealWritePrototypeRequest) -> dict[str, Any]:
    return execute_deploy_real_write_prototype(body.model_dump())


@router.post("/final-confirmation/session")
async def post_deploy_final_confirmation_session(body: DeployFinalConfirmationSessionRequest) -> dict[str, Any]:
    return create_final_confirmation_session(body.model_dump())


@router.post("/final-confirmation/check")
async def post_deploy_final_confirmation_check(body: DeployFinalConfirmationCheckRequest) -> dict[str, Any]:
    return check_final_confirmation_dryrun(body.model_dump())


@router.post("/write/harness/session")
async def post_deploy_write_harness_session(body: DeployWriteHarnessSessionRequest) -> dict[str, Any]:
    return create_deploy_write_harness_session(body.model_dump())


@router.post("/write/harness/execute")
async def post_deploy_write_harness_execute(body: DeployWriteHarnessExecuteRequest) -> dict[str, Any]:
    return execute_deploy_write_harness(body.model_dump())


@router.post("/real-write/session")
async def post_deploy_real_write_session(body: DeployRealWriteGuardSessionRequest) -> dict[str, Any]:
    return create_real_write_guard_session(body.model_dump())


@router.post("/real-write/check")
async def post_deploy_real_write_check(body: DeployRealWriteGuardCheckRequest) -> dict[str, Any]:
    return check_real_write_guard(body.model_dump())


@router.post("/hardware-gate/report")
async def post_deploy_hardware_gate_report(body: DeployHardwareGateReportRequest) -> dict[str, Any]:
    report = build_hardware_gate_report(body.model_dump())
    st = str(report.get("report_status") or "blocked")
    code = "DEPLOY_HARDWARE_GATE_BLOCKED"
    if st == "ok":
        code = "DEPLOY_HARDWARE_GATE_OK"
    elif st == "review_required":
        code = "DEPLOY_HARDWARE_GATE_REVIEW_REQUIRED"
    return {"code": code, "report": report, "warnings": report.get("warnings") or [], "errors": report.get("errors") or []}


@router.post("/hardware-gate/operator-protocol")
async def post_deploy_hardware_gate_operator_protocol(body: DeployHardwareGateOperatorProtocolRequest) -> dict[str, Any]:
    protocol = build_operator_protocol(body.model_dump())
    return {"code": "DEPLOY_HARDWARE_GATE_OPERATOR_PROTOCOL_OK", "protocol": protocol, "warnings": protocol.get("warnings") or [], "errors": protocol.get("errors") or []}


@router.post("/runner/handoff")
async def post_deploy_runner_handoff(body: DeployRunnerHandoffRequest) -> dict[str, Any]:
    return execute_runner_dryrun_handoff(body.model_dump())


@router.post("/runner/audit/sudoers")
async def post_deploy_runner_audit_sudoers(body: DeployRunnerSudoersAuditRequest) -> dict[str, Any]:
    return build_runner_sudoers_policy_example(
        allowed_runner_path=body.allowed_runner_path,
        allowed_job_directory=body.allowed_job_directory,
        allowed_environment=body.allowed_environment,
    )


@router.post("/runner/audit/environment")
async def post_deploy_runner_audit_environment(body: DeployRunnerEnvironmentAuditRequest) -> dict[str, Any]:
    env = body.environment or {}
    return audit_runner_environment(env=env if env else None)


@router.post("/runner/audit/path")
async def post_deploy_runner_audit_path(body: DeployRunnerPathAuditRequest) -> dict[str, Any]:
    return audit_runner_binary_path(body.runner_path)


@router.post("/runner/audit/jobdir")
async def post_deploy_runner_audit_jobdir(body: DeployRunnerJobDirAuditRequest) -> dict[str, Any]:
    prefixes = body.allowed_prefixes if body.allowed_prefixes else None
    return audit_runner_job_directory(body.job_directory, allowed_prefixes=prefixes)


@router.post("/runner/sandbox/policy")
async def post_deploy_runner_sandbox_policy(body: DeployRunnerSandboxPolicyRequest) -> dict[str, Any]:
    return build_runner_sandbox_policy(
        source_environment=body.environment or {},
        runner_path=body.runner_path,
        job_directory=body.job_directory,
    )


@router.post("/runner/sandbox/environment")
async def post_deploy_runner_sandbox_environment(body: DeployRunnerSandboxEnvironmentRequest) -> dict[str, Any]:
    return build_sandbox_environment(source_environment=body.environment or {})


@router.post("/runner/sandbox/stdio")
async def post_deploy_runner_sandbox_stdio() -> dict[str, Any]:
    return build_runner_stdio_policy()


@router.post("/runner/sandbox/timeout")
async def post_deploy_runner_sandbox_timeout(body: DeployRunnerSandboxTimeoutRequest) -> dict[str, Any]:
    return build_runner_timeout_model(
        max_runtime_seconds=body.max_runtime_seconds,
        graceful_shutdown_timeout=body.graceful_shutdown_timeout,
        hard_kill_timeout=body.hard_kill_timeout,
        stale_runner_timeout=body.stale_runner_timeout,
        lock_cleanup_timeout=body.lock_cleanup_timeout,
    )


@router.post("/runner/sandbox/privileges")
async def post_deploy_runner_sandbox_privileges(body: DeployRunnerSandboxPrivilegeRequest) -> dict[str, Any]:
    return build_runner_privilege_model(recommended_runner_user=body.recommended_runner_user)


@router.post("/runner/sandbox/recovery")
async def post_deploy_runner_sandbox_recovery() -> dict[str, Any]:
    return build_runner_recovery_analysis()


@router.post("/runner/install/plan")
async def post_deploy_runner_install_plan(body: DeployRunnerInstallPlanRequest) -> dict[str, Any]:
    plan = build_runner_install_plan(**body.model_dump())
    st = str(plan.get("plan_status") or "review_required")
    code = "DEPLOY_RUNNER_INSTALL_PLAN_REVIEW_REQUIRED"
    if st == "ok":
        code = "DEPLOY_RUNNER_INSTALL_PLAN_OK"
    elif st == "blocked":
        code = "DEPLOY_RUNNER_INSTALL_PLAN_BLOCKED"
    return {
        "code": code,
        "plan": plan,
        "warnings": list(plan.get("warnings") or []),
        "errors": list(plan.get("errors") or []),
    }


@router.post("/runner/install/validate")
async def post_deploy_runner_install_validate(body: DeployRunnerInstallValidateRequest) -> dict[str, Any]:
    validation = validate_runner_installation_dryrun(
        install_plan=body.install_plan or {},
        sudoers_snippet_text=body.sudoers_snippet_text or "",
        environment=body.environment or {},
    )
    st = str(validation.get("validation_status") or "review_required")
    code = "DEPLOY_RUNNER_INSTALL_VALIDATE_REVIEW_REQUIRED"
    if st == "ok":
        code = "DEPLOY_RUNNER_INSTALL_VALIDATE_OK"
    elif st == "blocked":
        code = "DEPLOY_RUNNER_INSTALL_VALIDATE_BLOCKED"
    return {
        "code": code,
        "validation": validation,
        "warnings": list(validation.get("warnings") or []),
        "errors": list(validation.get("errors") or []),
    }


@router.post("/runner/package/blueprint")
async def post_deploy_runner_package_blueprint(body: DeployRunnerPackageBlueprintRequest) -> dict[str, Any]:
    blueprint = build_runner_package_blueprint(**body.model_dump())
    st = str(blueprint.get("blueprint_status") or "review_required")
    code = "DEPLOY_RUNNER_PACKAGE_BLUEPRINT_REVIEW_REQUIRED"
    if st == "ok":
        code = "DEPLOY_RUNNER_PACKAGE_BLUEPRINT_OK"
    elif st == "blocked":
        code = "DEPLOY_RUNNER_PACKAGE_BLUEPRINT_BLOCKED"
    return {
        "code": code,
        "blueprint": blueprint,
        "warnings": list(blueprint.get("warnings") or []),
        "errors": list(blueprint.get("errors") or []),
    }


@router.post("/runner/install/consistency")
async def post_deploy_runner_install_consistency(body: DeployRunnerInstallConsistencyRequest) -> dict[str, Any]:
    consistency = validate_runner_install_consistency(
        install_plan=body.install_plan or {},
        install_validation=body.install_validation or {},
        package_blueprint=body.package_blueprint or {},
    )
    st = str(consistency.get("consistency_status") or "review_required")
    code = "DEPLOY_RUNNER_INSTALL_CONSISTENCY_REVIEW_REQUIRED"
    if st == "ok":
        code = "DEPLOY_RUNNER_INSTALL_CONSISTENCY_OK"
    elif st == "blocked":
        code = "DEPLOY_RUNNER_INSTALL_CONSISTENCY_BLOCKED"
    return {
        "code": code,
        "consistency": consistency,
        "warnings": list(consistency.get("warnings") or []),
        "errors": list(consistency.get("errors") or []),
    }


@router.post("/runner/release/readiness")
async def post_deploy_runner_release_readiness(body: DeployRunnerReleaseReadinessRequest) -> dict[str, Any]:
    readiness = build_runner_release_readiness_matrix(
        components=body.components or None,
        blocking_gaps=body.blocking_gaps or None,
        non_blocking_gaps=body.non_blocking_gaps or None,
        required_evidence=body.required_evidence or None,
        required_next_validations=body.required_next_validations or None,
    )
    st = str(readiness.get("readiness_status") or "review_required")
    code = "DEPLOY_RUNNER_RELEASE_REVIEW_REQUIRED"
    if st == "ready_for_lab":
        code = "DEPLOY_RUNNER_RELEASE_READY_FOR_LAB"
    elif st == "blocked":
        code = "DEPLOY_RUNNER_RELEASE_BLOCKED"
    return {
        "code": code,
        "readiness": readiness,
        "warnings": list(readiness.get("warnings") or []),
        "errors": list(readiness.get("errors") or []),
    }


@router.post("/runner/lab-readiness/unblock-plan")
async def post_deploy_runner_lab_readiness_unblock_plan(body: DeployRunnerLabReadinessPlanRequest) -> dict[str, Any]:
    plan = build_runner_lab_readiness_unblock_plan(blocking_gaps=body.blocking_gaps or None)
    st = str(plan.get("plan_status") or "review_required")
    code = "DEPLOY_RUNNER_LAB_UNBLOCK_PLAN_REVIEW_REQUIRED"
    if st == "ok":
        code = "DEPLOY_RUNNER_LAB_UNBLOCK_PLAN_OK"
    elif st == "blocked":
        code = "DEPLOY_RUNNER_LAB_UNBLOCK_PLAN_BLOCKED"
    return {
        "code": code,
        "plan": plan,
        "warnings": list(plan.get("warnings") or []),
        "errors": list(plan.get("errors") or []),
    }


@router.post("/runner/sudoers/runtime-test-plan")
async def post_deploy_runner_sudoers_runtime_test_plan(body: DeployRunnerSudoersRuntimeTestPlanRequest) -> dict[str, Any]:
    _ = body.placeholder or {}
    plan = build_runner_sudoers_runtime_test_plan()
    st = str(plan.get("plan_status") or "review_required")
    code = "DEPLOY_RUNNER_SUDOERS_RUNTIME_TEST_PLAN_REVIEW_REQUIRED"
    if st == "ok":
        code = "DEPLOY_RUNNER_SUDOERS_RUNTIME_TEST_PLAN_OK"
    elif st == "blocked":
        code = "DEPLOY_RUNNER_SUDOERS_RUNTIME_TEST_PLAN_BLOCKED"
    return {
        "code": code,
        "plan": plan,
        "warnings": list(plan.get("warnings") or []),
        "errors": list(plan.get("errors") or []),
    }


@router.post("/runner/privileged-validation/test-plan")
async def post_deploy_runner_privileged_validation_test_plan(body: DeployRunnerPrivilegedValidationTestPlanRequest) -> dict[str, Any]:
    _ = body.placeholder or {}
    plan = build_runner_privileged_validation_test_plan()
    st = str(plan.get("plan_status") or "review_required")
    code = "DEPLOY_RUNNER_PRIVILEGED_VALIDATION_TEST_PLAN_REVIEW_REQUIRED"
    if st == "ok":
        code = "DEPLOY_RUNNER_PRIVILEGED_VALIDATION_TEST_PLAN_OK"
    elif st == "blocked":
        code = "DEPLOY_RUNNER_PRIVILEGED_VALIDATION_TEST_PLAN_BLOCKED"
    return {
        "code": code,
        "plan": plan,
        "warnings": list(plan.get("warnings") or []),
        "errors": list(plan.get("errors") or []),
    }


@router.post("/runner/real-write-hardware-e2e/test-plan")
async def post_deploy_runner_real_write_hardware_e2e_test_plan(body: DeployRunnerRealWriteHardwareE2ETestPlanRequest) -> dict[str, Any]:
    _ = body.placeholder or {}
    plan = build_runner_real_write_hardware_e2e_test_plan()
    st = str(plan.get("plan_status") or "review_required")
    code = "DEPLOY_RUNNER_REAL_WRITE_HW_E2E_TEST_PLAN_REVIEW_REQUIRED"
    if st == "ok":
        code = "DEPLOY_RUNNER_REAL_WRITE_HW_E2E_TEST_PLAN_OK"
    elif st == "blocked":
        code = "DEPLOY_RUNNER_REAL_WRITE_HW_E2E_TEST_PLAN_BLOCKED"
    return {
        "code": code,
        "plan": plan,
        "warnings": list(plan.get("warnings") or []),
        "errors": list(plan.get("errors") or []),
    }


@router.post("/runner/failure-injection-hardware/test-plan")
async def post_deploy_runner_failure_injection_hardware_test_plan(body: DeployRunnerFailureInjectionHardwareTestPlanRequest) -> dict[str, Any]:
    _ = body.placeholder or {}
    plan = build_runner_failure_injection_hardware_test_plan()
    st = str(plan.get("plan_status") or "review_required")
    code = "DEPLOY_RUNNER_FAILURE_INJECTION_HW_TEST_PLAN_REVIEW_REQUIRED"
    if st == "ok":
        code = "DEPLOY_RUNNER_FAILURE_INJECTION_HW_TEST_PLAN_OK"
    elif st == "blocked":
        code = "DEPLOY_RUNNER_FAILURE_INJECTION_HW_TEST_PLAN_BLOCKED"
    return {
        "code": code,
        "plan": plan,
        "warnings": list(plan.get("warnings") or []),
        "errors": list(plan.get("errors") or []),
    }


@router.post("/runner/device-reenumeration/test-plan")
async def post_deploy_runner_device_reenumeration_test_plan(body: DeployRunnerDeviceReenumerationTestPlanRequest) -> dict[str, Any]:
    _ = body.placeholder or {}
    plan = build_runner_device_reenumeration_test_plan()
    st = str(plan.get("plan_status") or "review_required")
    code = "DEPLOY_RUNNER_DEVICE_REENUMERATION_TEST_PLAN_REVIEW_REQUIRED"
    if st == "ok":
        code = "DEPLOY_RUNNER_DEVICE_REENUMERATION_TEST_PLAN_OK"
    elif st == "blocked":
        code = "DEPLOY_RUNNER_DEVICE_REENUMERATION_TEST_PLAN_BLOCKED"
    return {
        "code": code,
        "plan": plan,
        "warnings": list(plan.get("warnings") or []),
        "errors": list(plan.get("errors") or []),
    }


@router.post("/runner/hotplug-race/test-plan")
async def post_deploy_runner_hotplug_race_test_plan(body: DeployRunnerHotplugRaceTestPlanRequest) -> dict[str, Any]:
    _ = body.placeholder or {}
    plan = build_runner_hotplug_race_test_plan()
    st = str(plan.get("plan_status") or "review_required")
    code = "DEPLOY_RUNNER_HOTPLUG_RACE_TEST_PLAN_REVIEW_REQUIRED"
    if st == "ok":
        code = "DEPLOY_RUNNER_HOTPLUG_RACE_TEST_PLAN_OK"
    elif st == "blocked":
        code = "DEPLOY_RUNNER_HOTPLUG_RACE_TEST_PLAN_BLOCKED"
    return {
        "code": code,
        "plan": plan,
        "warnings": list(plan.get("warnings") or []),
        "errors": list(plan.get("errors") or []),
    }


@router.post("/runner/rollback-runtime/test-plan")
async def post_deploy_runner_rollback_runtime_test_plan(body: DeployRunnerRollbackRuntimeTestPlanRequest) -> dict[str, Any]:
    _ = body.placeholder or {}
    plan = build_runner_rollback_runtime_test_plan()
    st = str(plan.get("plan_status") or "review_required")
    code = "DEPLOY_RUNNER_ROLLBACK_RUNTIME_TEST_PLAN_REVIEW_REQUIRED"
    if st == "ok":
        code = "DEPLOY_RUNNER_ROLLBACK_RUNTIME_TEST_PLAN_OK"
    elif st == "blocked":
        code = "DEPLOY_RUNNER_ROLLBACK_RUNTIME_TEST_PLAN_BLOCKED"
    return {
        "code": code,
        "plan": plan,
        "warnings": list(plan.get("warnings") or []),
        "errors": list(plan.get("errors") or []),
    }


@router.post("/runner/lab-readiness/status")
async def post_deploy_runner_lab_readiness_status(body: DeployRunnerLabReadinessStatusRequest) -> dict[str, Any]:
    status = build_runner_lab_readiness_status(
        design_evidence=body.design_evidence or None,
        runtime_evidence=body.runtime_evidence or None,
    )
    st = str(status.get("lab_readiness_status") or "review_required")
    code = "DEPLOY_RUNNER_LAB_READINESS_REVIEW_REQUIRED"
    if st == "test_design_ready":
        code = "DEPLOY_RUNNER_LAB_READINESS_TEST_DESIGN_READY"
    elif st == "runtime_blocked":
        code = "DEPLOY_RUNNER_LAB_READINESS_RUNTIME_BLOCKED"
    return {
        "code": code,
        "status": status,
        "warnings": list(status.get("warnings") or []),
        "errors": list(status.get("errors") or []),
    }


@router.post("/runner/runtime-runbook/bundle")
async def post_deploy_runner_runtime_runbook_bundle(body: DeployRunnerRuntimeRunbookBundleRequest) -> dict[str, Any]:
    _ = body.placeholder or {}
    bundle = build_runner_runtime_runbook_bundle()
    st = str(bundle.get("bundle_status") or "review_required")
    code = "DEPLOY_RUNNER_RUNTIME_RUNBOOK_BUNDLE_REVIEW_REQUIRED"
    if st == "ok":
        code = "DEPLOY_RUNNER_RUNTIME_RUNBOOK_BUNDLE_OK"
    elif st == "blocked":
        code = "DEPLOY_RUNNER_RUNTIME_RUNBOOK_BUNDLE_BLOCKED"
    return {
        "code": code,
        "bundle": bundle,
        "warnings": list(bundle.get("warnings") or []),
        "errors": list(bundle.get("errors") or []),
    }


@router.post("/runner/runtime-runbook/export")
async def post_deploy_runner_runtime_runbook_export(body: DeployRunnerRuntimeRunbookExportRequest) -> dict[str, Any]:
    export = build_runner_runtime_runbook_export_package(target_files=body.target_files or None)
    st = str(export.get("export_status") or "review_required")
    code = "DEPLOY_RUNNER_RUNTIME_RUNBOOK_EXPORT_REVIEW_REQUIRED"
    if st == "ok":
        code = "DEPLOY_RUNNER_RUNTIME_RUNBOOK_EXPORT_OK"
    elif st == "blocked":
        code = "DEPLOY_RUNNER_RUNTIME_RUNBOOK_EXPORT_BLOCKED"
    return {
        "code": code,
        "export": export,
        "warnings": list(export.get("warnings") or []),
        "errors": list(export.get("errors") or []),
    }


@router.post("/runner/runtime-results/validate")
async def post_deploy_runner_runtime_results_validate(body: DeployRunnerRuntimeResultsValidateRequest) -> dict[str, Any]:
    validation = validate_runner_runtime_result_bundle(
        result_files=body.result_files or [],
        acceptance_decision=body.acceptance_decision or "blocked",
    )
    st = str(validation.get("validation_status") or "review_required")
    code = "DEPLOY_RUNNER_RUNTIME_RESULTS_VALIDATE_REVIEW_REQUIRED"
    if st == "ok":
        code = "DEPLOY_RUNNER_RUNTIME_RESULTS_VALIDATE_OK"
    elif st == "blocked":
        code = "DEPLOY_RUNNER_RUNTIME_RESULTS_VALIDATE_BLOCKED"
    return {
        "code": code,
        "validation": validation,
        "warnings": list(validation.get("warnings") or []),
        "errors": list(validation.get("errors") or []),
    }


@router.post("/runner/lab-readiness/acceptance")
async def post_deploy_runner_lab_readiness_acceptance(body: DeployRunnerLabAcceptanceRequest) -> dict[str, Any]:
    acceptance = build_runner_lab_acceptance_summary(
        validated_runtime_results=body.validated_runtime_results or {},
    )
    st = str(acceptance.get("acceptance_status") or "blocked")
    code = "DEPLOY_RUNNER_LAB_ACCEPTANCE_BLOCKED"
    if st == "lab_ready_candidate":
        code = "DEPLOY_RUNNER_LAB_ACCEPTANCE_CANDIDATE"
    elif st == "repeat_required":
        code = "DEPLOY_RUNNER_LAB_ACCEPTANCE_REPEAT_REQUIRED"
    return {
        "code": code,
        "acceptance": acceptance,
        "warnings": list(acceptance.get("warnings") or []),
        "errors": list(acceptance.get("errors") or []),
    }


@router.post("/runner/lab-readiness/acceptance/export")
async def post_deploy_runner_lab_readiness_acceptance_export(body: DeployRunnerLabAcceptanceExportRequest) -> dict[str, Any]:
    export = build_runner_lab_acceptance_report_export(acceptance=body.acceptance or {})
    st = str(export.get("export_status") or "review_required")
    code = "DEPLOY_RUNNER_LAB_ACCEPTANCE_EXPORT_REVIEW_REQUIRED"
    if st == "ok":
        code = "DEPLOY_RUNNER_LAB_ACCEPTANCE_EXPORT_OK"
    elif st == "blocked":
        code = "DEPLOY_RUNNER_LAB_ACCEPTANCE_EXPORT_BLOCKED"
    return {
        "code": code,
        "export": export,
        "warnings": list(export.get("warnings") or []),
        "errors": list(export.get("errors") or []),
    }


@router.post("/runner/lab-phase/consolidation")
async def post_deploy_runner_lab_phase_consolidation(body: DeployRunnerLabPhaseConsolidationRequest) -> dict[str, Any]:
    _ = body.placeholder or {}
    consolidation = build_runner_lab_phase_consolidation()
    st = str(consolidation.get("consolidation_status") or "review_required")
    code = "DEPLOY_RUNNER_LAB_PHASE_CONSOLIDATION_REVIEW_REQUIRED"
    if st == "ok":
        code = "DEPLOY_RUNNER_LAB_PHASE_CONSOLIDATION_OK"
    elif st == "blocked":
        code = "DEPLOY_RUNNER_LAB_PHASE_CONSOLIDATION_BLOCKED"
    return {
        "code": code,
        "consolidation": consolidation,
        "warnings": list(consolidation.get("warnings") or []),
        "errors": list(consolidation.get("errors") or []),
    }


@router.post("/runner/next-phase/gate")
async def post_deploy_runner_next_phase_gate(body: DeployRunnerNextPhaseGateRequest) -> dict[str, Any]:
    _ = body.placeholder or {}
    gate = evaluate_runner_next_phase_gate()
    st = str(gate.get("gate_status") or "hold")
    code = "DEPLOY_RUNNER_NEXT_PHASE_HOLD"
    if st == "manual_runtime_allowed":
        code = "DEPLOY_RUNNER_NEXT_PHASE_MANUAL_RUNTIME_ALLOWED"
    elif st == "repeat_required":
        code = "DEPLOY_RUNNER_NEXT_PHASE_REPEAT_REQUIRED"
    elif st == "blocked":
        code = "DEPLOY_RUNNER_NEXT_PHASE_BLOCKED"
    return {
        "code": code,
        "gate": gate,
        "warnings": list(gate.get("warnings") or []),
        "errors": list(gate.get("errors") or []),
    }


@router.post("/runner/manual-runtime/precheck")
async def post_deploy_runner_manual_runtime_precheck(body: DeployRunnerManualRuntimePrecheckRequest) -> dict[str, Any]:
    precheck = build_runner_manual_runtime_precheck(
        selected_runbook=body.selected_runbook,
        next_phase_gate=body.next_phase_gate or None,
        operator_confirmations=body.operator_confirmations or None,
        hardware_gate_report=body.hardware_gate_report or None,
        real_write_guard_report=body.real_write_guard_report or None,
        runtime_context=body.runtime_context or None,
    )
    st = str(precheck.get("precheck_status") or "review_required")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_PRECHECK_REVIEW_REQUIRED"
    if st == "ready_for_manual_runtime":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_PRECHECK_READY"
    elif st == "blocked":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_PRECHECK_BLOCKED"
    return {
        "code": code,
        "precheck": precheck,
        "warnings": list(precheck.get("warnings") or []),
        "errors": list(precheck.get("errors") or []),
    }


@router.post("/runner/manual-runtime/result-template")
async def post_deploy_runner_manual_runtime_result_template(body: DeployRunnerManualRuntimeResultTemplateRequest) -> dict[str, Any]:
    template_result = create_manual_runtime_result_template(
        precheck=body.precheck or None,
        explicit_overwrite=bool(body.explicit_overwrite),
    )
    st = str(template_result.get("template_status") or "review_required")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_TEMPLATE_REVIEW_REQUIRED"
    if st == "created":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_TEMPLATE_CREATED"
    elif st == "blocked":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_TEMPLATE_BLOCKED"
    return {
        "code": code,
        "template_result": template_result,
        "warnings": list(template_result.get("warnings") or []),
        "errors": list(template_result.get("errors") or []),
    }


@router.post("/runner/manual-runtime/result-check")
async def post_deploy_runner_manual_runtime_result_check(body: DeployRunnerManualRuntimeResultCheckRequest) -> dict[str, Any]:
    check = check_manual_runtime_result_file(result_file=body.result_file)
    st = str(check.get("check_status") or "review_required")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_CHECK_REVIEW_REQUIRED"
    if st == "ok":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_CHECK_OK"
    elif st == "blocked":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_CHECK_BLOCKED"
    return {
        "code": code,
        "check": check,
        "warnings": list(check.get("warnings") or []),
        "errors": list(check.get("errors") or []),
    }


@router.post("/runner/manual-runtime/result-bundle-check")
async def post_deploy_runner_manual_runtime_result_bundle_check(body: DeployRunnerManualRuntimeResultBundleCheckRequest) -> dict[str, Any]:
    bundle_check = check_manual_runtime_result_bundle(result_files=body.result_files)
    st = str(bundle_check.get("bundle_check_status") or "review_required")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_BUNDLE_CHECK_REVIEW_REQUIRED"
    if st == "ok":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_BUNDLE_CHECK_OK"
    elif st == "blocked":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_BUNDLE_CHECK_BLOCKED"
    return {
        "code": code,
        "bundle_check": bundle_check,
        "warnings": list(bundle_check.get("warnings") or []),
        "errors": list(bundle_check.get("errors") or []),
    }


@router.post("/runner/manual-runtime/result-validator-handoff")
async def post_deploy_runner_manual_runtime_result_validator_handoff(body: DeployRunnerManualRuntimeResultValidatorHandoffRequest) -> dict[str, Any]:
    handoff = build_manual_runtime_result_validator_handoff(
        bundle_check_result=body.bundle_check_result or {},
        result_files=body.result_files or [],
        explicit_overwrite=bool(body.explicit_overwrite),
    )
    st = str(handoff.get("handoff_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_VALIDATOR_HANDOFF_BLOCKED"
    if st == "ready":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_VALIDATOR_HANDOFF_READY"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_VALIDATOR_HANDOFF_REVIEW_REQUIRED"
    return {
        "code": code,
        "handoff": handoff,
        "warnings": list(handoff.get("warnings") or []),
        "errors": list(handoff.get("errors") or []),
    }


@router.post("/runner/manual-runtime/result-validator-dryrun-from-handoff")
async def post_deploy_runner_manual_runtime_result_validator_dryrun_from_handoff(
    body: DeployRunnerManualRuntimeResultValidatorDryrunFromHandoffRequest,
) -> dict[str, Any]:
    dry = run_manual_runtime_result_validator_dryrun_from_handoff(
        handoff_manifest_path=body.handoff_manifest_path,
        explicit_overwrite=bool(body.explicit_overwrite),
    )
    st = str(dry.get("dryrun_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_VALIDATOR_DRYRUN_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_VALIDATOR_DRYRUN_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_VALIDATOR_DRYRUN_REVIEW_REQUIRED"
    return {
        "code": code,
        "dryrun": dry,
        "warnings": list(dry.get("warnings") or []),
        "errors": list(dry.get("errors") or []),
    }


@router.post("/runner/manual-runtime/result-validator-report-seal")
async def post_deploy_runner_manual_runtime_result_validator_report_seal(
    body: DeployRunnerManualRuntimeResultValidatorReportSealRequest,
) -> dict[str, Any]:
    sealed = seal_manual_runtime_validator_report(
        dryrun_report_path=body.dryrun_report_path,
        explicit_overwrite=bool(body.explicit_overwrite),
    )
    st = str(sealed.get("seal_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_VALIDATOR_REPORT_SEAL_BLOCKED"
    if st == "sealed":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_VALIDATOR_REPORT_SEAL_CREATED"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_VALIDATOR_REPORT_SEAL_REVIEW_REQUIRED"
    return {
        "code": code,
        "seal": sealed,
        "warnings": list(sealed.get("warnings") or []),
        "errors": list(sealed.get("errors") or []),
    }


@router.post("/runner/manual-runtime/result-validator-seal-index")
async def post_deploy_runner_manual_runtime_validator_seal_index(
    body: DeployRunnerManualRuntimeValidatorSealIndexRequest,
) -> dict[str, Any]:
    idx = build_validator_report_seal_index(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(idx.get("index_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_VALIDATOR_SEAL_INDEX_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_VALIDATOR_SEAL_INDEX_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_VALIDATOR_SEAL_INDEX_REVIEW_REQUIRED"
    return {
        "code": code,
        "index": idx,
        "warnings": list(idx.get("warnings") or []),
        "errors": list(idx.get("errors") or []),
    }


@router.post("/runner/manual-runtime/result-validator-seal-consistency-audit")
async def post_deploy_runner_manual_runtime_validator_seal_consistency_audit(
    body: DeployRunnerManualRuntimeValidatorSealConsistencyAuditRequest,
) -> dict[str, Any]:
    aud = run_validator_seal_consistency_audit(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(aud.get("audit_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_VALIDATOR_SEAL_CONSISTENCY_AUDIT_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_VALIDATOR_SEAL_CONSISTENCY_AUDIT_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_VALIDATOR_SEAL_CONSISTENCY_AUDIT_REVIEW_REQUIRED"
    return {
        "code": code,
        "audit": aud,
        "warnings": list(aud.get("warnings") or []),
        "errors": list(aud.get("errors") or []),
    }


@router.post("/runner/manual-runtime/evidence-timeline")
async def post_deploy_runner_manual_runtime_evidence_timeline(
    body: DeployRunnerManualRuntimeEvidenceTimelineRequest,
) -> dict[str, Any]:
    tl = build_manual_runtime_evidence_timeline(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(tl.get("timeline_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_EVIDENCE_TIMELINE_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_EVIDENCE_TIMELINE_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_EVIDENCE_TIMELINE_REVIEW_REQUIRED"
    return {
        "code": code,
        "timeline": tl,
        "warnings": list(tl.get("warnings") or []),
        "errors": list(tl.get("errors") or []),
    }


@router.post("/runner/manual-runtime/evidence-final-snapshot")
async def post_deploy_runner_manual_runtime_evidence_final_snapshot(
    body: DeployRunnerManualRuntimeEvidenceFinalSnapshotRequest,
) -> dict[str, Any]:
    snap = build_manual_runtime_evidence_final_snapshot(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(snap.get("snapshot_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_EVIDENCE_FINAL_SNAPSHOT_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_EVIDENCE_FINAL_SNAPSHOT_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_EVIDENCE_FINAL_SNAPSHOT_REVIEW_REQUIRED"
    return {
        "code": code,
        "snapshot": snap,
        "warnings": list(snap.get("warnings") or []),
        "errors": list(snap.get("errors") or []),
    }


@router.post("/runner/manual-runtime/final-acceptance")
async def post_deploy_runner_manual_runtime_final_acceptance(
    body: DeployRunnerManualRuntimeFinalAcceptanceRequest,
) -> dict[str, Any]:
    acc = evaluate_manual_runtime_final_acceptance(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(acc.get("acceptance_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FINAL_ACCEPTANCE_BLOCKED"
    if st == "accepted":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FINAL_ACCEPTANCE_ACCEPTED"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FINAL_ACCEPTANCE_REVIEW_REQUIRED"
    return {
        "code": code,
        "acceptance": acc,
        "warnings": list(acc.get("warnings") or []),
        "errors": list(acc.get("errors") or []),
    }


@router.post("/runner/manual-runtime/final-export-package")
async def post_deploy_runner_manual_runtime_final_export_package(
    body: DeployRunnerManualRuntimeFinalExportPackageRequest,
) -> dict[str, Any]:
    pkg = build_manual_runtime_final_export_package(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(pkg.get("export_package_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FINAL_EXPORT_PACKAGE_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FINAL_EXPORT_PACKAGE_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FINAL_EXPORT_PACKAGE_REVIEW_REQUIRED"
    return {
        "code": code,
        "export_package": pkg,
        "warnings": list(pkg.get("warnings") or []),
        "errors": list(pkg.get("errors") or []),
    }


@router.post("/runner/manual-runtime/failure-injection-matrix")
async def post_deploy_runner_manual_runtime_failure_injection_matrix(
    body: DeployRunnerManualRuntimeFailureInjectionMatrixRequest,
) -> dict[str, Any]:
    matrix = build_manual_runtime_failure_injection_matrix(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(matrix.get("matrix_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_INJECTION_MATRIX_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_INJECTION_MATRIX_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_INJECTION_MATRIX_REVIEW_REQUIRED"
    return {
        "code": code,
        "matrix": matrix,
        "warnings": list(matrix.get("warnings") or []),
        "errors": list(matrix.get("errors") or []),
    }


@router.post("/runner/manual-runtime/failure-execution-preview")
async def post_deploy_runner_manual_runtime_failure_execution_preview(
    body: DeployRunnerManualRuntimeFailureExecutionPreviewRequest,
) -> dict[str, Any]:
    preview = build_manual_runtime_failure_execution_preview(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(preview.get("preview_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_EXECUTION_PREVIEW_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_EXECUTION_PREVIEW_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_EXECUTION_PREVIEW_REVIEW_REQUIRED"
    return {
        "code": code,
        "preview": preview,
        "warnings": list(preview.get("warnings") or []),
        "errors": list(preview.get("errors") or []),
    }


@router.post("/runner/manual-runtime/failure-operator-checklists")
async def post_deploy_runner_manual_runtime_failure_operator_checklists(
    body: DeployRunnerManualRuntimeFailureOperatorChecklistsRequest,
) -> dict[str, Any]:
    ch = build_manual_runtime_failure_operator_checklists(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(ch.get("checklist_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_OPERATOR_CHECKLISTS_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_OPERATOR_CHECKLISTS_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_OPERATOR_CHECKLISTS_REVIEW_REQUIRED"
    return {
        "code": code,
        "checklists": ch,
        "warnings": list(ch.get("warnings") or []),
        "errors": list(ch.get("errors") or []),
    }


@router.post("/runner/manual-runtime/failure-test-sessions")
async def post_deploy_runner_manual_runtime_failure_test_sessions(
    body: DeployRunnerManualRuntimeFailureTestSessionsRequest,
) -> dict[str, Any]:
    sess = build_manual_runtime_failure_test_sessions(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(sess.get("sessions_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_TEST_SESSIONS_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_TEST_SESSIONS_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_TEST_SESSIONS_REVIEW_REQUIRED"
    return {
        "code": code,
        "sessions": sess,
        "warnings": list(sess.get("warnings") or []),
        "errors": list(sess.get("errors") or []),
    }


@router.post("/runner/manual-runtime/failure-test-results")
async def post_deploy_runner_manual_runtime_failure_test_results(
    body: DeployRunnerManualRuntimeFailureTestResultsRequest,
) -> dict[str, Any]:
    cap = capture_manual_runtime_failure_test_results(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(cap.get("capture_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_TEST_RESULTS_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_TEST_RESULTS_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_TEST_RESULTS_REVIEW_REQUIRED"
    return {
        "code": code,
        "capture": cap,
        "warnings": list(cap.get("warnings") or []),
        "errors": list(cap.get("errors") or []),
    }


@router.post("/runner/manual-runtime/failure-result-evaluation")
async def post_deploy_runner_manual_runtime_failure_result_evaluation(
    body: DeployRunnerManualRuntimeFailureResultEvaluationRequest,
) -> dict[str, Any]:
    ev = evaluate_manual_runtime_failure_results(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(ev.get("evaluation_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_RESULT_EVALUATION_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_RESULT_EVALUATION_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_RESULT_EVALUATION_REVIEW_REQUIRED"
    return {
        "code": code,
        "evaluation": ev,
        "warnings": list(ev.get("warnings") or []),
        "errors": list(ev.get("errors") or []),
    }


@router.post("/runner/manual-runtime/failure-readiness-gate")
async def post_deploy_runner_manual_runtime_failure_readiness_gate(
    body: DeployRunnerManualRuntimeFailureReadinessGateRequest,
) -> dict[str, Any]:
    rd = evaluate_manual_runtime_failure_readiness(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(rd.get("readiness_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_READINESS_GATE_BLOCKED"
    if st == "ready":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_READINESS_GATE_READY"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_READINESS_GATE_REVIEW_REQUIRED"
    return {
        "code": code,
        "readiness": rd,
        "warnings": list(rd.get("warnings") or []),
        "errors": list(rd.get("errors") or []),
    }


@router.post("/runner/manual-runtime/laptop-failure-run-selection")
async def post_deploy_runner_manual_runtime_laptop_failure_run_selection(
    body: DeployRunnerManualRuntimeLaptopFailureRunSelectionRequest,
) -> dict[str, Any]:
    sel = select_manual_laptop_failure_test_runs(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(sel.get("selection_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_RUN_SELECTION_BLOCKED"
    if st == "ready":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_RUN_SELECTION_READY"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_RUN_SELECTION_REVIEW_REQUIRED"
    return {
        "code": code,
        "selection": sel,
        "warnings": list(sel.get("warnings") or []),
        "errors": list(sel.get("errors") or []),
    }


@router.post("/runner/manual-runtime/laptop-failure-operator-runorder")
async def post_deploy_runner_manual_runtime_laptop_failure_operator_runorder(
    body: DeployRunnerManualRuntimeLaptopFailureOperatorRunorderRequest,
) -> dict[str, Any]:
    ro = build_manual_laptop_failure_operator_runorder(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(ro.get("runorder_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_OPERATOR_RUNORDER_BLOCKED"
    if st == "ready":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_OPERATOR_RUNORDER_READY"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_OPERATOR_RUNORDER_REVIEW_REQUIRED"
    return {
        "code": code,
        "runorder": ro,
        "warnings": list(ro.get("warnings") or []),
        "errors": list(ro.get("errors") or []),
    }


@router.post("/runner/manual-runtime/laptop-failure-execution-log-template")
async def post_deploy_runner_manual_runtime_laptop_failure_execution_log_template(
    body: DeployRunnerManualRuntimeLaptopFailureExecutionLogTemplateRequest,
) -> dict[str, Any]:
    tpl = build_manual_laptop_failure_execution_log_template(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(tpl.get("template_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_EXECUTION_LOG_TEMPLATE_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_EXECUTION_LOG_TEMPLATE_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_EXECUTION_LOG_TEMPLATE_REVIEW_REQUIRED"
    return {
        "code": code,
        "execution_log_template": tpl,
        "warnings": list(tpl.get("warnings") or []),
        "errors": list(tpl.get("errors") or []),
    }


@router.post("/runner/manual-runtime/laptop-failure-execution-log-validation")
async def post_deploy_runner_manual_runtime_laptop_failure_execution_log_validation(
    body: DeployRunnerManualRuntimeLaptopFailureExecutionLogValidationRequest,
) -> dict[str, Any]:
    val = validate_manual_laptop_failure_execution_log(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(val.get("validation_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_EXECUTION_LOG_VALIDATION_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_EXECUTION_LOG_VALIDATION_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_EXECUTION_LOG_VALIDATION_REVIEW_REQUIRED"
    return {
        "code": code,
        "execution_log_validation": val,
        "warnings": list(val.get("warnings") or []),
        "errors": list(val.get("errors") or []),
    }


@router.post("/runner/manual-runtime/laptop-failure-test-summary")
async def post_deploy_runner_manual_runtime_laptop_failure_test_summary(
    body: DeployRunnerManualRuntimeLaptopFailureTestSummaryRequest,
) -> dict[str, Any]:
    sm = build_manual_laptop_failure_test_summary(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(sm.get("summary_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_TEST_SUMMARY_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_TEST_SUMMARY_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_TEST_SUMMARY_REVIEW_REQUIRED"
    return {
        "code": code,
        "summary": sm,
        "warnings": list(sm.get("warnings") or []),
        "errors": list(sm.get("errors") or []),
    }


@router.post("/runner/manual-runtime/laptop-failure-final-report")
async def post_deploy_runner_manual_runtime_laptop_failure_final_report(
    body: DeployRunnerManualRuntimeLaptopFailureFinalReportRequest,
) -> dict[str, Any]:
    rep = build_manual_laptop_failure_final_report(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(rep.get("report_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_REPORT_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_REPORT_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_REPORT_REVIEW_REQUIRED"
    return {
        "code": code,
        "final_report": rep,
        "warnings": list(rep.get("warnings") or []),
        "errors": list(rep.get("errors") or []),
    }


@router.post("/runner/manual-runtime/laptop-failure-final-export-package")
async def post_deploy_runner_manual_runtime_laptop_failure_final_export_package(
    body: DeployRunnerManualRuntimeLaptopFailureFinalExportPackageRequest,
) -> dict[str, Any]:
    pkg = build_manual_laptop_failure_final_export_package(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(pkg.get("export_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_EXPORT_PACKAGE_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_EXPORT_PACKAGE_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_EXPORT_PACKAGE_REVIEW_REQUIRED"
    return {
        "code": code,
        "final_export_package": pkg,
        "warnings": list(pkg.get("warnings") or []),
        "errors": list(pkg.get("errors") or []),
    }


@router.post("/runner/manual-runtime/laptop-failure-evidence-timeline")
async def post_deploy_runner_manual_runtime_laptop_failure_evidence_timeline(
    body: DeployRunnerManualRuntimeLaptopFailureEvidenceTimelineRequest,
) -> dict[str, Any]:
    tl = build_manual_laptop_failure_evidence_timeline(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(tl.get("timeline_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_EVIDENCE_TIMELINE_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_EVIDENCE_TIMELINE_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_EVIDENCE_TIMELINE_REVIEW_REQUIRED"
    return {
        "code": code,
        "evidence_timeline": tl,
        "warnings": list(tl.get("warnings") or []),
        "errors": list(tl.get("errors") or []),
    }


@router.post("/runner/manual-runtime/laptop-failure-final-snapshot")
async def post_deploy_runner_manual_runtime_laptop_failure_final_snapshot(
    body: DeployRunnerManualRuntimeLaptopFailureFinalSnapshotRequest,
) -> dict[str, Any]:
    snap = build_manual_laptop_failure_final_snapshot(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(snap.get("snapshot_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_SNAPSHOT_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_SNAPSHOT_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_SNAPSHOT_REVIEW_REQUIRED"
    return {
        "code": code,
        "final_snapshot": snap,
        "warnings": list(snap.get("warnings") or []),
        "errors": list(snap.get("errors") or []),
    }


@router.post("/runner/manual-runtime/laptop-failure-final-acceptance")
async def post_deploy_runner_manual_runtime_laptop_failure_final_acceptance(
    body: DeployRunnerManualRuntimeLaptopFailureFinalAcceptanceRequest,
) -> dict[str, Any]:
    acc = evaluate_manual_laptop_failure_final_acceptance(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(acc.get("acceptance_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_ACCEPTANCE_BLOCKED"
    if st == "accepted":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_ACCEPTANCE_ACCEPTED"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINAL_ACCEPTANCE_REVIEW_REQUIRED"
    return {
        "code": code,
        "final_acceptance": acc,
        "warnings": list(acc.get("warnings") or []),
        "errors": list(acc.get("errors") or []),
    }


@router.post("/runner/manual-runtime/laptop-failure-finalized-export-package")
async def post_deploy_runner_manual_runtime_laptop_failure_finalized_export_package(
    body: DeployRunnerManualRuntimeLaptopFailureFinalizedExportPackageRequest,
) -> dict[str, Any]:
    pkg = build_manual_laptop_failure_finalized_export_package(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(pkg.get("export_status") or "blocked")
    code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINALIZED_EXPORT_PACKAGE_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINALIZED_EXPORT_PACKAGE_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNNER_MANUAL_RUNTIME_LAPTOP_FAILURE_FINALIZED_EXPORT_PACKAGE_REVIEW_REQUIRED"
    return {
        "code": code,
        "finalized_export_package": pkg,
        "warnings": list(pkg.get("warnings") or []),
        "errors": list(pkg.get("errors") or []),
    }


@router.post("/version-governance/state")
async def post_deploy_version_governance_state(
    body: DeployVersionGovernanceStateRequest,
) -> dict[str, Any]:
    st = build_version_governance_state(
        previous_version=body.previous_version,
        strict_mode_phase=body.strict_mode_phase,
        phase_status=body.phase_status,
        release_readiness=body.release_readiness,
        completed_modules=list(body.completed_modules or []),
        evidence_artifacts=list(body.evidence_artifacts or []),
        test_status=body.test_status,
        changes=list(body.changes or []),
        explicit_overwrite=bool(body.explicit_overwrite),
    )
    code = "DEPLOY_VERSION_GOVERNANCE_STATE_BLOCKED"
    state_status = str(st.get("state_status") or "blocked")
    if state_status == "ok":
        code = "DEPLOY_VERSION_GOVERNANCE_STATE_OK"
    elif state_status == "review_required":
        code = "DEPLOY_VERSION_GOVERNANCE_STATE_REVIEW_REQUIRED"
    return {
        "code": code,
        "version_governance_state": st,
        "warnings": list(st.get("warnings") or []),
        "errors": list(st.get("errors") or []),
    }


@router.post("/version-source-of-truth-check")
async def post_deploy_version_source_of_truth_check(
    body: DeployVersionSourceOfTruthCheckRequest,
) -> dict[str, Any]:
    chk = check_version_source_of_truth_consistency(explicit_overwrite=bool(body.explicit_overwrite))
    check_status = str(chk.get("check_status") or "blocked")
    code = "DEPLOY_VERSION_SOURCE_OF_TRUTH_CHECK_BLOCKED"
    if check_status == "ok":
        code = "DEPLOY_VERSION_SOURCE_OF_TRUTH_CHECK_OK"
    elif check_status == "review_required":
        code = "DEPLOY_VERSION_SOURCE_OF_TRUTH_CHECK_REVIEW_REQUIRED"
    return {
        "code": code,
        "version_source_of_truth_check": chk,
        "warnings": list(chk.get("warnings") or []),
        "errors": list(chk.get("errors") or []),
    }


@router.post("/legacy-identifier-inventory")
async def post_deploy_legacy_identifier_inventory(
    body: DeployLegacyIdentifierInventoryRequest,
) -> dict[str, Any]:
    inv = build_legacy_identifier_inventory(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(inv.get("inventory_status") or "blocked")
    code = "DEPLOY_LEGACY_IDENTIFIER_INVENTORY_BLOCKED"
    if st == "ok":
        code = "DEPLOY_LEGACY_IDENTIFIER_INVENTORY_OK"
    elif st == "review_required":
        code = "DEPLOY_LEGACY_IDENTIFIER_INVENTORY_REVIEW_REQUIRED"
    return {
        "code": code,
        "legacy_identifier_inventory": inv,
        "warnings": list(inv.get("warnings") or []),
        "errors": list(inv.get("errors") or []),
    }


@router.post("/setuphelfer-runtime-identifier-migration")
async def post_deploy_setuphelfer_runtime_identifier_migration(
    body: DeploySetuphelferRuntimeIdentifierMigrationRequest,
) -> dict[str, Any]:
    plan = build_runtime_identifier_migration_plan(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(plan.get("migration_status") or "blocked")
    code = "DEPLOY_SETUPHELFER_RUNTIME_IDENTIFIER_MIGRATION_BLOCKED"
    if st == "ok":
        code = "DEPLOY_SETUPHELFER_RUNTIME_IDENTIFIER_MIGRATION_OK"
    elif st == "review_required":
        code = "DEPLOY_SETUPHELFER_RUNTIME_IDENTIFIER_MIGRATION_REVIEW_REQUIRED"
    return {
        "code": code,
        "setuphelfer_runtime_identifier_migration": plan,
        "warnings": list(plan.get("warnings") or []),
        "errors": list(plan.get("errors") or []),
    }


@router.post("/setuphelfer-identifier-consistency-check")
async def post_deploy_setuphelfer_identifier_consistency_check(
    body: DeploySetuphelferIdentifierConsistencyCheckRequest,
) -> dict[str, Any]:
    chk = check_setuphelfer_identifier_consistency(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(chk.get("check_status") or "blocked")
    code = "DEPLOY_SETUPHELFER_IDENTIFIER_CONSISTENCY_CHECK_BLOCKED"
    if st == "ok":
        code = "DEPLOY_SETUPHELFER_IDENTIFIER_CONSISTENCY_CHECK_OK"
    elif st == "review_required":
        code = "DEPLOY_SETUPHELFER_IDENTIFIER_CONSISTENCY_CHECK_REVIEW_REQUIRED"
    return {
        "code": code,
        "setuphelfer_identifier_consistency_check": chk,
        "warnings": list(chk.get("warnings") or []),
        "errors": list(chk.get("errors") or []),
    }


@router.post("/legacy-identifier-cleanup-classification")
async def post_deploy_legacy_identifier_cleanup_classification(
    body: DeployLegacyIdentifierCleanupClassificationRequest,
) -> dict[str, Any]:
    res = classify_active_legacy_identifiers(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("classification_status") or "blocked")
    code = "DEPLOY_LEGACY_IDENTIFIER_CLEANUP_CLASSIFICATION_BLOCKED"
    if st == "ok":
        code = "DEPLOY_LEGACY_IDENTIFIER_CLEANUP_CLASSIFICATION_OK"
    elif st == "review_required":
        code = "DEPLOY_LEGACY_IDENTIFIER_CLEANUP_CLASSIFICATION_REVIEW_REQUIRED"
    return {
        "code": code,
        "legacy_identifier_cleanup_classification": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/setuphelfer-safe-rewrite-plan")
async def post_deploy_setuphelfer_safe_rewrite_plan(
    body: DeploySetuphelferSafeRewritePlanRequest,
) -> dict[str, Any]:
    res = build_setuphelfer_safe_rewrite_plan(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("plan_status") or "blocked")
    code = "DEPLOY_SETUPHELFER_SAFE_REWRITE_PLAN_BLOCKED"
    if st == "ok":
        code = "DEPLOY_SETUPHELFER_SAFE_REWRITE_PLAN_OK"
    elif st == "review_required":
        code = "DEPLOY_SETUPHELFER_SAFE_REWRITE_PLAN_REVIEW_REQUIRED"
    return {
        "code": code,
        "setuphelfer_safe_rewrite_plan": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/setuphelfer-controlled-rewrite-apply")
async def post_deploy_setuphelfer_controlled_rewrite_apply(
    body: DeploySetuphelferControlledRewriteApplyRequest,
) -> dict[str, Any]:
    res = apply_setuphelfer_controlled_rewrite(
        explicit_overwrite=bool(body.explicit_overwrite),
        run_post_consistency_check=bool(body.run_post_consistency_check),
    )
    st = str(res.get("apply_status") or "blocked")
    code = "DEPLOY_SETUPHELFER_CONTROLLED_REWRITE_APPLY_BLOCKED"
    if st == "ok":
        code = "DEPLOY_SETUPHELFER_CONTROLLED_REWRITE_APPLY_OK"
    elif st == "review_required":
        code = "DEPLOY_SETUPHELFER_CONTROLLED_REWRITE_APPLY_REVIEW_REQUIRED"
    return {
        "code": code,
        "setuphelfer_controlled_rewrite_apply": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/setuphelfer-identifier-cleanup-cycle-plan")
async def post_deploy_setuphelfer_identifier_cleanup_cycle_plan(
    body: DeploySetuphelferIdentifierCleanupCyclePlanRequest,
) -> dict[str, Any]:
    res = build_setuphelfer_identifier_cleanup_cycle(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("cycle_plan_status") or "blocked")
    code = "DEPLOY_SETUPHELFER_IDENTIFIER_CLEANUP_CYCLE_PLAN_BLOCKED"
    if st == "ok":
        code = "DEPLOY_SETUPHELFER_IDENTIFIER_CLEANUP_CYCLE_PLAN_OK"
    elif st == "review_required":
        code = "DEPLOY_SETUPHELFER_IDENTIFIER_CLEANUP_CYCLE_PLAN_REVIEW_REQUIRED"
    return {
        "code": code,
        "setuphelfer_identifier_cleanup_cycle_plan": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/setuphelfer-identifier-cleanup-cycle-apply")
async def post_deploy_setuphelfer_identifier_cleanup_cycle_apply(
    body: DeploySetuphelferIdentifierCleanupCycleApplyRequest,
) -> dict[str, Any]:
    res = apply_setuphelfer_identifier_cleanup_cycle(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("cycle_apply_status") or "blocked")
    code = "DEPLOY_SETUPHELFER_IDENTIFIER_CLEANUP_CYCLE_APPLY_BLOCKED"
    if st == "ok":
        code = "DEPLOY_SETUPHELFER_IDENTIFIER_CLEANUP_CYCLE_APPLY_OK"
    elif st == "review_required":
        code = "DEPLOY_SETUPHELFER_IDENTIFIER_CLEANUP_CYCLE_APPLY_REVIEW_REQUIRED"
    return {
        "code": code,
        "setuphelfer_identifier_cleanup_cycle_apply": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/setuphelfer-identifier-cleanup-cycle-postcheck")
async def post_deploy_setuphelfer_identifier_cleanup_cycle_postcheck(
    body: DeploySetuphelferIdentifierCleanupCyclePostcheckRequest,
) -> dict[str, Any]:
    res = build_setuphelfer_identifier_cleanup_cycle_postcheck(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("cycle_postcheck_status") or "blocked")
    code = "DEPLOY_SETUPHELFER_IDENTIFIER_CLEANUP_CYCLE_POSTCHECK_BLOCKED"
    if st == "ok":
        code = "DEPLOY_SETUPHELFER_IDENTIFIER_CLEANUP_CYCLE_POSTCHECK_OK"
    elif st == "review_required":
        code = "DEPLOY_SETUPHELFER_IDENTIFIER_CLEANUP_CYCLE_POSTCHECK_REVIEW_REQUIRED"
    return {
        "code": code,
        "setuphelfer_identifier_cleanup_cycle_postcheck": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/legacy-identifier-hotspot-analysis")
async def post_deploy_legacy_identifier_hotspot_analysis(
    body: DeployLegacyIdentifierHotspotAnalysisRequest,
) -> dict[str, Any]:
    res = build_legacy_identifier_hotspot_analysis(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("analysis_status") or "blocked")
    code = "DEPLOY_LEGACY_IDENTIFIER_HOTSPOT_ANALYSIS_BLOCKED"
    if st == "ok":
        code = "DEPLOY_LEGACY_IDENTIFIER_HOTSPOT_ANALYSIS_OK"
    elif st == "review_required":
        code = "DEPLOY_LEGACY_IDENTIFIER_HOTSPOT_ANALYSIS_REVIEW_REQUIRED"
    return {
        "code": code,
        "legacy_identifier_hotspot_analysis": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/setuphelfer-identifier-hotspot-cleanup-cycle-plan")
async def post_deploy_setuphelfer_identifier_hotspot_cleanup_cycle_plan(
    body: DeploySetuphelferIdentifierHotspotCleanupCyclePlanRequest,
) -> dict[str, Any]:
    res = build_setuphelfer_identifier_hotspot_cleanup_cycle(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("hotspot_cleanup_cycle_plan_status") or "blocked")
    code = "DEPLOY_SETUPHELFER_IDENTIFIER_HOTSPOT_CLEANUP_CYCLE_PLAN_BLOCKED"
    if st == "ok":
        code = "DEPLOY_SETUPHELFER_IDENTIFIER_HOTSPOT_CLEANUP_CYCLE_PLAN_OK"
    elif st == "review_required":
        code = "DEPLOY_SETUPHELFER_IDENTIFIER_HOTSPOT_CLEANUP_CYCLE_PLAN_REVIEW_REQUIRED"
    return {
        "code": code,
        "setuphelfer_identifier_hotspot_cleanup_cycle_plan": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/setuphelfer-identifier-hotspot-cleanup-cycle-apply")
async def post_deploy_setuphelfer_identifier_hotspot_cleanup_cycle_apply(
    body: DeploySetuphelferIdentifierHotspotCleanupCycleApplyRequest,
) -> dict[str, Any]:
    res = apply_setuphelfer_identifier_hotspot_cleanup_cycle(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("hotspot_cleanup_cycle_apply_status") or "blocked")
    code = "DEPLOY_SETUPHELFER_IDENTIFIER_HOTSPOT_CLEANUP_CYCLE_APPLY_BLOCKED"
    if st == "ok":
        code = "DEPLOY_SETUPHELFER_IDENTIFIER_HOTSPOT_CLEANUP_CYCLE_APPLY_OK"
    elif st == "review_required":
        code = "DEPLOY_SETUPHELFER_IDENTIFIER_HOTSPOT_CLEANUP_CYCLE_APPLY_REVIEW_REQUIRED"
    return {
        "code": code,
        "setuphelfer_identifier_hotspot_cleanup_cycle_apply": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/setuphelfer-identifier-hotspot-cleanup-cycle-postcheck")
async def post_deploy_setuphelfer_identifier_hotspot_cleanup_cycle_postcheck(
    body: DeploySetuphelferIdentifierHotspotCleanupCyclePostcheckRequest,
) -> dict[str, Any]:
    res = build_setuphelfer_identifier_hotspot_cleanup_cycle_postcheck(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("hotspot_cleanup_cycle_postcheck_status") or "blocked")
    code = "DEPLOY_SETUPHELFER_IDENTIFIER_HOTSPOT_CLEANUP_CYCLE_POSTCHECK_BLOCKED"
    if st == "ok":
        code = "DEPLOY_SETUPHELFER_IDENTIFIER_HOTSPOT_CLEANUP_CYCLE_POSTCHECK_OK"
    elif st == "review_required":
        code = "DEPLOY_SETUPHELFER_IDENTIFIER_HOTSPOT_CLEANUP_CYCLE_POSTCHECK_REVIEW_REQUIRED"
    return {
        "code": code,
        "setuphelfer_identifier_hotspot_cleanup_cycle_postcheck": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/runtime-identifier-elimination-targets")
async def post_deploy_runtime_identifier_elimination_targets(
    body: DeployRuntimeIdentifierEliminationTargetsRequest,
) -> dict[str, Any]:
    res = build_runtime_identifier_elimination_targets(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("runtime_identifier_elimination_targets_status") or "blocked")
    code = "DEPLOY_RUNTIME_IDENTIFIER_ELIMINATION_TARGETS_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNTIME_IDENTIFIER_ELIMINATION_TARGETS_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNTIME_IDENTIFIER_ELIMINATION_TARGETS_REVIEW_REQUIRED"
    return {
        "code": code,
        "runtime_identifier_elimination_targets": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/runtime-identifier-elimination-plan")
async def post_deploy_runtime_identifier_elimination_plan(
    body: DeployRuntimeIdentifierEliminationPlanRequest,
) -> dict[str, Any]:
    res = build_runtime_identifier_elimination_plan(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("runtime_identifier_elimination_plan_status") or "blocked")
    code = "DEPLOY_RUNTIME_IDENTIFIER_ELIMINATION_PLAN_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNTIME_IDENTIFIER_ELIMINATION_PLAN_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNTIME_IDENTIFIER_ELIMINATION_PLAN_REVIEW_REQUIRED"
    return {
        "code": code,
        "runtime_identifier_elimination_plan": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/runtime-identifier-elimination-apply")
async def post_deploy_runtime_identifier_elimination_apply(
    body: DeployRuntimeIdentifierEliminationApplyRequest,
) -> dict[str, Any]:
    res = apply_runtime_identifier_elimination(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("runtime_identifier_elimination_apply_status") or "blocked")
    code = "DEPLOY_RUNTIME_IDENTIFIER_ELIMINATION_APPLY_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNTIME_IDENTIFIER_ELIMINATION_APPLY_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNTIME_IDENTIFIER_ELIMINATION_APPLY_REVIEW_REQUIRED"
    return {
        "code": code,
        "runtime_identifier_elimination_apply": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/runtime-compatibility-alias-validation")
async def post_deploy_runtime_compatibility_alias_validation(
    body: DeployRuntimeCompatibilityAliasValidationRequest,
) -> dict[str, Any]:
    res = validate_runtime_compatibility_aliases(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("runtime_compatibility_alias_validation_status") or "blocked")
    code = "DEPLOY_RUNTIME_COMPATIBILITY_ALIAS_VALIDATION_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNTIME_COMPATIBILITY_ALIAS_VALIDATION_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNTIME_COMPATIBILITY_ALIAS_VALIDATION_REVIEW_REQUIRED"
    return {
        "code": code,
        "runtime_compatibility_alias_validation": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/runtime-identifier-elimination-postcheck")
async def post_deploy_runtime_identifier_elimination_postcheck(
    body: DeployRuntimeIdentifierEliminationPostcheckRequest,
) -> dict[str, Any]:
    res = build_runtime_identifier_elimination_postcheck(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("runtime_identifier_elimination_postcheck_status") or "blocked")
    code = "DEPLOY_RUNTIME_IDENTIFIER_ELIMINATION_POSTCHECK_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNTIME_IDENTIFIER_ELIMINATION_POSTCHECK_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNTIME_IDENTIFIER_ELIMINATION_POSTCHECK_REVIEW_REQUIRED"
    return {
        "code": code,
        "runtime_identifier_elimination_postcheck": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/runtime-identifier-zero-state-verification")
async def post_deploy_runtime_identifier_zero_state_verification(
    body: DeployRuntimeIdentifierZeroStateVerificationRequest,
) -> dict[str, Any]:
    res = verify_runtime_identifier_zero_state(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("runtime_identifier_zero_state_verification_status") or "blocked")
    code = "DEPLOY_RUNTIME_IDENTIFIER_ZERO_STATE_VERIFICATION_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNTIME_IDENTIFIER_ZERO_STATE_VERIFICATION_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNTIME_IDENTIFIER_ZERO_STATE_VERIFICATION_REVIEW_REQUIRED"
    return {
        "code": code,
        "runtime_identifier_zero_state_verification": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/runtime-identifier-patch-bump-preparation")
async def post_deploy_runtime_identifier_patch_bump_preparation(
    body: DeployRuntimeIdentifierPatchBumpPreparationRequest,
) -> dict[str, Any]:
    res = prepare_runtime_identifier_patch_bump(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("runtime_identifier_patch_bump_preparation_status") or "blocked")
    code = "DEPLOY_RUNTIME_IDENTIFIER_PATCH_BUMP_PREPARATION_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNTIME_IDENTIFIER_PATCH_BUMP_PREPARATION_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNTIME_IDENTIFIER_PATCH_BUMP_PREPARATION_REVIEW_REQUIRED"
    return {
        "code": code,
        "runtime_identifier_patch_bump_preparation": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/runtime-identifier-patch-bump-apply")
async def post_deploy_runtime_identifier_patch_bump_apply(
    body: DeployRuntimeIdentifierPatchBumpApplyRequest,
) -> dict[str, Any]:
    res = apply_runtime_identifier_patch_bump(
        explicit_overwrite=bool(body.explicit_overwrite),
        explicit_apply_patch_bump=bool(body.explicit_apply_patch_bump),
    )
    st = str(res.get("runtime_identifier_patch_bump_apply_status") or "blocked")
    code = "DEPLOY_RUNTIME_IDENTIFIER_PATCH_BUMP_APPLY_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNTIME_IDENTIFIER_PATCH_BUMP_APPLY_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNTIME_IDENTIFIER_PATCH_BUMP_APPLY_REVIEW_REQUIRED"
    return {
        "code": code,
        "runtime_identifier_patch_bump_apply": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/runtime-identifier-patch-bump-postcheck")
async def post_deploy_runtime_identifier_patch_bump_postcheck(
    body: DeployRuntimeIdentifierPatchBumpPostcheckRequest,
) -> dict[str, Any]:
    res = build_runtime_identifier_patch_bump_postcheck(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("runtime_identifier_patch_bump_postcheck_status") or "blocked")
    code = "DEPLOY_RUNTIME_IDENTIFIER_PATCH_BUMP_POSTCHECK_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RUNTIME_IDENTIFIER_PATCH_BUMP_POSTCHECK_OK"
    elif st == "review_required":
        code = "DEPLOY_RUNTIME_IDENTIFIER_PATCH_BUMP_POSTCHECK_REVIEW_REQUIRED"
    return {
        "code": code,
        "runtime_identifier_patch_bump_postcheck": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/setuphelfer-branding-guard-check")
async def post_deploy_setuphelfer_branding_guard_check(
    body: DeploySetuphelferBrandingGuardCheckRequest,
) -> dict[str, Any]:
    res = build_setuphelfer_branding_guard_report(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("setuphelfer_branding_guard_check_status") or "blocked")
    code = "DEPLOY_SETUPHELFER_BRANDING_GUARD_CHECK_BLOCKED"
    if st == "ok":
        code = "DEPLOY_SETUPHELFER_BRANDING_GUARD_CHECK_OK"
    elif st == "review_required":
        code = "DEPLOY_SETUPHELFER_BRANDING_GUARD_CHECK_REVIEW_REQUIRED"
    return {
        "code": code,
        "setuphelfer_branding_guard_check": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/legacy-runtime-compatibility-inventory")
async def post_deploy_legacy_runtime_compatibility_inventory(
    body: DeployLegacyRuntimeCompatibilityInventoryRequest,
) -> dict[str, Any]:
    res = build_legacy_runtime_compatibility_inventory(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("legacy_runtime_compatibility_inventory_status") or "blocked")
    code = "DEPLOY_LEGACY_RUNTIME_COMPATIBILITY_INVENTORY_BLOCKED"
    if st == "ok":
        code = "DEPLOY_LEGACY_RUNTIME_COMPATIBILITY_INVENTORY_OK"
    elif st == "review_required":
        code = "DEPLOY_LEGACY_RUNTIME_COMPATIBILITY_INVENTORY_REVIEW_REQUIRED"
    return {
        "code": code,
        "legacy_runtime_compatibility_inventory": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/legacy-runtime-coexistence-analysis")
async def post_deploy_legacy_runtime_coexistence_analysis(
    body: DeployLegacyRuntimeCoexistenceAnalysisRequest,
) -> dict[str, Any]:
    res = analyze_legacy_runtime_coexistence(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("legacy_runtime_coexistence_analysis_status") or "blocked")
    code = "DEPLOY_LEGACY_RUNTIME_COEXISTENCE_ANALYSIS_BLOCKED"
    if st == "ok":
        code = "DEPLOY_LEGACY_RUNTIME_COEXISTENCE_ANALYSIS_OK"
    elif st == "review_required":
        code = "DEPLOY_LEGACY_RUNTIME_COEXISTENCE_ANALYSIS_REVIEW_REQUIRED"
    return {
        "code": code,
        "legacy_runtime_coexistence_analysis": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/legacy-runtime-safe-migration-recommendations")
async def post_deploy_legacy_runtime_safe_migration_recommendations(
    body: DeployLegacyRuntimeSafeMigrationRecommendationsRequest,
) -> dict[str, Any]:
    res = build_safe_legacy_runtime_migration_recommendations(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("legacy_runtime_safe_migration_recommendations_status") or "blocked")
    code = "DEPLOY_LEGACY_RUNTIME_SAFE_MIGRATION_RECOMMENDATIONS_BLOCKED"
    if st == "ok":
        code = "DEPLOY_LEGACY_RUNTIME_SAFE_MIGRATION_RECOMMENDATIONS_OK"
    elif st == "review_required":
        code = "DEPLOY_LEGACY_RUNTIME_SAFE_MIGRATION_RECOMMENDATIONS_REVIEW_REQUIRED"
    return {
        "code": code,
        "legacy_runtime_safe_migration_recommendations": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/legacy-upgrade-path-matrix")
async def post_deploy_legacy_upgrade_path_matrix(
    body: DeployLegacyUpgradePathMatrixRequest,
) -> dict[str, Any]:
    res = build_legacy_upgrade_path_matrix(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("legacy_upgrade_path_matrix_status") or "blocked")
    code = "DEPLOY_LEGACY_UPGRADE_PATH_MATRIX_BLOCKED"
    if st == "ok":
        code = "DEPLOY_LEGACY_UPGRADE_PATH_MATRIX_OK"
    elif st == "review_required":
        code = "DEPLOY_LEGACY_UPGRADE_PATH_MATRIX_REVIEW_REQUIRED"
    return {
        "code": code,
        "legacy_upgrade_path_matrix": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/runner/manual-runtime/laptop-failure-test-execution-readiness-final-gate")
async def post_deploy_laptop_failure_test_execution_readiness_final_gate(
    body: DeployLaptopFailureTestExecutionReadinessFinalGateRequest,
) -> dict[str, Any]:
    res = build_laptop_failure_test_execution_readiness_final_gate(
        explicit_overwrite=bool(body.explicit_overwrite),
        probe_live_system=bool(body.probe_live_system),
        live_base_url=body.live_base_url,
    )
    st = str(res.get("laptop_failure_test_execution_readiness_gate_status") or "blocked")
    code = "DEPLOY_LAPTOP_FAILURE_TEST_EXECUTION_READINESS_FINAL_GATE_BLOCKED"
    if st == "ok":
        code = "DEPLOY_LAPTOP_FAILURE_TEST_EXECUTION_READINESS_FINAL_GATE_OK"
    elif st == "review_required":
        code = "DEPLOY_LAPTOP_FAILURE_TEST_EXECUTION_READINESS_FINAL_GATE_REVIEW_REQUIRED"
    return {
        "code": code,
        "laptop_failure_test_execution_readiness_final_gate": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/runner/manual-runtime/laptop-live-probe-plan")
async def post_deploy_laptop_live_probe_plan(body: DeployLaptopLiveProbePlanRequest) -> dict[str, Any]:
    res = build_laptop_live_probe_plan(
        explicit_overwrite=bool(body.explicit_overwrite),
        live_base_url=body.live_base_url,
    )
    st = str(res.get("laptop_live_probe_plan_status") or "blocked")
    code = "DEPLOY_LAPTOP_LIVE_PROBE_PLAN_BLOCKED"
    if st == "ok":
        code = "DEPLOY_LAPTOP_LIVE_PROBE_PLAN_OK"
    elif st == "review_required":
        code = "DEPLOY_LAPTOP_LIVE_PROBE_PLAN_REVIEW_REQUIRED"
    return {
        "code": code,
        "laptop_live_probe_plan": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/runner/manual-runtime/laptop-live-probe-execute-readonly")
async def post_deploy_laptop_live_probe_execute_readonly(
    body: DeployLaptopLiveProbeExecuteReadonlyRequest,
) -> dict[str, Any]:
    res = execute_laptop_live_probe_readonly(
        explicit_overwrite=bool(body.explicit_overwrite),
        explicit_execute_live_probe=bool(body.explicit_execute_live_probe),
        allow_real_verify_path=bool(body.allow_real_verify_path),
        live_base_url=body.live_base_url,
    )
    st_exec = str(
        res.get("laptop_live_probe_result_status")
        or res.get("laptop_live_probe_execute_readonly_status")
        or "blocked"
    )
    code = "DEPLOY_LAPTOP_LIVE_PROBE_EXECUTE_READONLY_BLOCKED"
    if st_exec == "ok":
        code = "DEPLOY_LAPTOP_LIVE_PROBE_EXECUTE_READONLY_OK"
    elif st_exec == "review_required":
        code = "DEPLOY_LAPTOP_LIVE_PROBE_EXECUTE_READONLY_REVIEW_REQUIRED"
    return {
        "code": code,
        "laptop_live_probe_execute_readonly": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/runner/manual-runtime/laptop-live-probe-final-gate")
async def post_deploy_laptop_live_probe_final_gate(body: DeployLaptopLiveProbeFinalGateRequest) -> dict[str, Any]:
    res = build_laptop_live_probe_final_gate(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("laptop_live_probe_final_gate_status") or "blocked")
    code = "DEPLOY_LAPTOP_LIVE_PROBE_FINAL_GATE_BLOCKED"
    if st == "ok":
        code = "DEPLOY_LAPTOP_LIVE_PROBE_FINAL_GATE_OK"
    elif st == "review_required":
        code = "DEPLOY_LAPTOP_LIVE_PROBE_FINAL_GATE_REVIEW_REQUIRED"
    return {
        "code": code,
        "laptop_live_probe_final_gate": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/live-os-base-decision")
async def post_deploy_rescue_live_os_base_decision(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_live_os_base_decision(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_live_os_base_decision_status") or "blocked")
    code = "DEPLOY_RESCUE_LIVE_OS_BASE_DECISION_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_LIVE_OS_BASE_DECISION_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_LIVE_OS_BASE_DECISION_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_live_os_base_decision": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/component-inventory")
async def post_deploy_rescue_component_inventory(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_stick_component_inventory(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_stick_component_inventory_status") or "blocked")
    code = "DEPLOY_RESCUE_COMPONENT_INVENTORY_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_COMPONENT_INVENTORY_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_COMPONENT_INVENTORY_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_stick_component_inventory": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/mvp-scope-gate")
async def post_deploy_rescue_mvp_scope_gate(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_mvp_scope_gate(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_mvp_scope_gate_status") or "blocked")
    code = "DEPLOY_RESCUE_MVP_SCOPE_GATE_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_MVP_SCOPE_GATE_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_MVP_SCOPE_GATE_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_mvp_scope_gate": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/debian-live-build-plan")
async def post_deploy_rescue_debian_live_build_plan(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_debian_live_build_plan(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_debian_live_build_plan_status") or "blocked")
    code = "DEPLOY_RESCUE_DEBIAN_LIVE_BUILD_PLAN_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_BUILD_PLAN_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_BUILD_PLAN_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_debian_live_build_plan": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/debian-live/config-structure")
async def post_deploy_rescue_debian_live_config_structure(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_debian_live_config_structure(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_debian_live_config_structure_status") or "blocked")
    code = "DEPLOY_RESCUE_DEBIAN_LIVE_CONFIG_STRUCTURE_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_CONFIG_STRUCTURE_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_CONFIG_STRUCTURE_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_debian_live_config_structure": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/debian-live/package-lists")
async def post_deploy_rescue_debian_live_package_lists(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_debian_live_package_lists(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_debian_live_package_lists_status") or "blocked")
    code = "DEPLOY_RESCUE_DEBIAN_LIVE_PACKAGE_LISTS_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_PACKAGE_LISTS_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_PACKAGE_LISTS_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_debian_live_package_lists": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/debian-live/includes-chroot")
async def post_deploy_rescue_debian_live_includes_ch_root(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_debian_live_includes_ch_root(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_debian_live_includes_chroot_status") or "blocked")
    code = "DEPLOY_RESCUE_DEBIAN_LIVE_INCLUDES_CHROOT_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_INCLUDES_CHROOT_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_INCLUDES_CHROOT_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_debian_live_includes_chroot": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/debian-live/bootloader-templates")
async def post_deploy_rescue_debian_live_bootloader_templates(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_debian_live_bootloader_templates(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_debian_live_bootloader_templates_status") or "blocked")
    code = "DEPLOY_RESCUE_DEBIAN_LIVE_BOOTLOADER_TEMPLATES_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_BOOTLOADER_TEMPLATES_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_BOOTLOADER_TEMPLATES_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_debian_live_bootloader_templates": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/debian-live/hook-templates")
async def post_deploy_rescue_debian_live_hook_templates(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_debian_live_hook_templates(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_debian_live_hook_templates_status") or "blocked")
    code = "DEPLOY_RESCUE_DEBIAN_LIVE_HOOK_TEMPLATES_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_HOOK_TEMPLATES_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_HOOK_TEMPLATES_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_debian_live_hook_templates": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/debian-live/input-safety")
async def post_deploy_rescue_debian_live_input_safety(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = validate_debian_live_build_inputs_safety(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_debian_live_build_inputs_safety_status") or "blocked")
    code = "DEPLOY_RESCUE_DEBIAN_LIVE_INPUT_SAFETY_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_INPUT_SAFETY_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_INPUT_SAFETY_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_debian_live_build_inputs_safety": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/debian-live/final-gate")
async def post_deploy_rescue_debian_live_final_gate(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_debian_live_build_inputs_final_gate(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_debian_live_build_inputs_final_gate_status") or "blocked")
    code = "DEPLOY_RESCUE_DEBIAN_LIVE_FINAL_GATE_BLOCKED"
    if st == "ready":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_FINAL_GATE_READY"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_FINAL_GATE_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_debian_live_build_inputs_final_gate": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/dry-build/stage-graph")
async def post_deploy_rescue_dry_build_stage_graph(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_dry_build_stage_graph(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_dry_build_stage_graph_status") or "blocked")
    code = "DEPLOY_RESCUE_DRY_BUILD_STAGE_GRAPH_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_DRY_BUILD_STAGE_GRAPH_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DRY_BUILD_STAGE_GRAPH_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_dry_build_stage_graph": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/dry-build/input-resolution")
async def post_deploy_rescue_dry_build_input_resolution(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_dry_build_input_resolution(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_dry_build_input_resolution_status") or "blocked")
    code = "DEPLOY_RESCUE_DRY_BUILD_INPUT_RESOLUTION_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_DRY_BUILD_INPUT_RESOLUTION_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DRY_BUILD_INPUT_RESOLUTION_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_dry_build_input_resolution": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/dry-build/package-resolution")
async def post_deploy_rescue_dry_build_package_resolution(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_package_resolution_plan(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_dry_build_package_resolution_status") or "blocked")
    code = "DEPLOY_RESCUE_DRY_BUILD_PACKAGE_RESOLUTION_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_DRY_BUILD_PACKAGE_RESOLUTION_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DRY_BUILD_PACKAGE_RESOLUTION_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_dry_build_package_resolution": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/dry-build/build-order-validation")
async def post_deploy_rescue_dry_build_build_order_validation(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = validate_rescue_build_order(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_dry_build_build_order_validation_status") or "blocked")
    code = "DEPLOY_RESCUE_DRY_BUILD_BUILD_ORDER_VALIDATION_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_DRY_BUILD_BUILD_ORDER_VALIDATION_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DRY_BUILD_BUILD_ORDER_VALIDATION_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_dry_build_build_order_validation": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/dry-build/execution-simulation")
async def post_deploy_rescue_dry_build_execution_simulation(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = simulate_rescue_dry_build_execution(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_dry_build_execution_simulation_status") or "blocked")
    code = "DEPLOY_RESCUE_DRY_BUILD_EXECUTION_SIMULATION_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_DRY_BUILD_EXECUTION_SIMULATION_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DRY_BUILD_EXECUTION_SIMULATION_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_dry_build_execution_simulation": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/dry-build/final-gate")
async def post_deploy_rescue_dry_build_final_gate(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_dry_build_final_gate(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_dry_build_final_gate_status") or "blocked")
    code = "DEPLOY_RESCUE_DRY_BUILD_FINAL_GATE_BLOCKED"
    if st == "ready":
        code = "DEPLOY_RESCUE_DRY_BUILD_FINAL_GATE_READY"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DRY_BUILD_FINAL_GATE_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_dry_build_final_gate": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/dry-build/safety-validation")
async def post_deploy_rescue_dry_build_safety_validation(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = validate_rescue_dry_build_safety(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_dry_build_safety_validation_status") or "blocked")
    code = "DEPLOY_RESCUE_DRY_BUILD_SAFETY_VALIDATION_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_DRY_BUILD_SAFETY_VALIDATION_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DRY_BUILD_SAFETY_VALIDATION_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_dry_build_safety_validation": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/build-sandbox/root")
async def post_deploy_rescue_build_sandbox_root(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_build_sandbox_root(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_build_sandbox_root_status") or "blocked")
    code = "DEPLOY_RESCUE_BUILD_SANDBOX_ROOT_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_ROOT_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_ROOT_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_build_sandbox_root": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/build-sandbox/config-copy-plan")
async def post_deploy_rescue_build_sandbox_config_copy_plan(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_sandbox_config_copy_plan(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_build_sandbox_config_copy_plan_status") or "blocked")
    code = "DEPLOY_RESCUE_BUILD_SANDBOX_CONFIG_COPY_PLAN_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_CONFIG_COPY_PLAN_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_CONFIG_COPY_PLAN_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_build_sandbox_config_copy_plan": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/build-sandbox/runtime-copy-plan")
async def post_deploy_rescue_build_sandbox_runtime_copy_plan(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_sandbox_runtime_copy_plan(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_build_sandbox_runtime_copy_plan_status") or "blocked")
    code = "DEPLOY_RESCUE_BUILD_SANDBOX_RUNTIME_COPY_PLAN_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_RUNTIME_COPY_PLAN_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_RUNTIME_COPY_PLAN_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_build_sandbox_runtime_copy_plan": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/build-sandbox/overlay-workspace-plan")
async def post_deploy_rescue_build_sandbox_overlay_workspace_plan(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_overlay_workspace_plan(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_build_sandbox_overlay_workspace_plan_status") or "blocked")
    code = "DEPLOY_RESCUE_BUILD_SANDBOX_OVERLAY_WORKSPACE_PLAN_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_OVERLAY_WORKSPACE_PLAN_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_OVERLAY_WORKSPACE_PLAN_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_build_sandbox_overlay_workspace_plan": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/build-sandbox/cleanup-plan")
async def post_deploy_rescue_build_sandbox_cleanup_plan(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_build_cleanup_plan(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_build_cleanup_plan_status") or "blocked")
    code = "DEPLOY_RESCUE_BUILD_SANDBOX_CLEANUP_PLAN_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_CLEANUP_PLAN_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_CLEANUP_PLAN_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_build_cleanup_plan": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/build-sandbox/safety-validation")
async def post_deploy_rescue_build_sandbox_safety_validation(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = validate_rescue_build_sandbox_safety(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_build_sandbox_safety_validation_status") or "blocked")
    code = "DEPLOY_RESCUE_BUILD_SANDBOX_SAFETY_VALIDATION_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_SAFETY_VALIDATION_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_SAFETY_VALIDATION_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_build_sandbox_safety_validation": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/build-sandbox/final-gate")
async def post_deploy_rescue_build_sandbox_final_gate(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_build_sandbox_final_gate(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_build_sandbox_final_gate_status") or "blocked")
    code = "DEPLOY_RESCUE_BUILD_SANDBOX_FINAL_GATE_BLOCKED"
    if st == "ready":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_FINAL_GATE_READY"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_FINAL_GATE_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_build_sandbox_final_gate": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/sandbox-copy/precheck")
async def post_deploy_rescue_sandbox_copy_precheck(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_sandbox_copy_execution_precheck(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_sandbox_copy_execution_precheck_status") or "blocked")
    code = "DEPLOY_RESCUE_SANDBOX_COPY_PRECHECK_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_SANDBOX_COPY_PRECHECK_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_SANDBOX_COPY_PRECHECK_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_sandbox_copy_execution_precheck": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/sandbox-copy/config")
async def post_deploy_rescue_sandbox_copy_config(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = execute_rescue_sandbox_config_copy(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_sandbox_copy_config_status") or "blocked")
    code = "DEPLOY_RESCUE_SANDBOX_COPY_CONFIG_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_SANDBOX_COPY_CONFIG_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_SANDBOX_COPY_CONFIG_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_sandbox_copy_config": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/sandbox-copy/runtime")
async def post_deploy_rescue_sandbox_copy_runtime(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = execute_rescue_sandbox_runtime_copy(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_sandbox_copy_runtime_status") or "blocked")
    code = "DEPLOY_RESCUE_SANDBOX_COPY_RUNTIME_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_SANDBOX_COPY_RUNTIME_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_SANDBOX_COPY_RUNTIME_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_sandbox_copy_runtime": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/sandbox-copy/verify")
async def post_deploy_rescue_sandbox_copy_verify(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = verify_rescue_sandbox_copy_results(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_sandbox_copy_verify_status") or "blocked")
    code = "DEPLOY_RESCUE_SANDBOX_COPY_VERIFY_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_SANDBOX_COPY_VERIFY_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_SANDBOX_COPY_VERIFY_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_sandbox_copy_verify": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/sandbox-copy/seal")
async def post_deploy_rescue_sandbox_copy_seal(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_sandbox_copy_seal(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_sandbox_copy_seal_status") or "blocked")
    code = "DEPLOY_RESCUE_SANDBOX_COPY_SEAL_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_SANDBOX_COPY_SEAL_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_SANDBOX_COPY_SEAL_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_sandbox_copy_seal": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/sandbox-copy/final-gate")
async def post_deploy_rescue_sandbox_copy_final_gate(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_sandbox_copy_final_gate(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_sandbox_copy_final_gate_status") or "blocked")
    code = "DEPLOY_RESCUE_SANDBOX_COPY_FINAL_GATE_BLOCKED"
    if st == "ready":
        code = "DEPLOY_RESCUE_SANDBOX_COPY_FINAL_GATE_READY"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_SANDBOX_COPY_FINAL_GATE_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_sandbox_copy_final_gate": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/build-emulation/environment-snapshot")
async def post_deploy_rescue_build_emulation_environment_snapshot(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_build_environment_snapshot(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_build_emulation_environment_snapshot_status") or "blocked")
    code = "DEPLOY_RESCUE_BUILD_EMULATION_ENVIRONMENT_SNAPSHOT_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_BUILD_EMULATION_ENVIRONMENT_SNAPSHOT_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_BUILD_EMULATION_ENVIRONMENT_SNAPSHOT_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_build_emulation_environment_snapshot": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/build-emulation/workspace")
async def post_deploy_rescue_build_emulation_workspace(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_simulated_build_workspace(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_build_emulation_workspace_status") or "blocked")
    code = "DEPLOY_RESCUE_BUILD_EMULATION_WORKSPACE_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_BUILD_EMULATION_WORKSPACE_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_BUILD_EMULATION_WORKSPACE_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_build_emulation_workspace": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/build-emulation/outputs")
async def post_deploy_rescue_build_emulation_outputs(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_simulated_build_outputs(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_build_emulation_outputs_status") or "blocked")
    code = "DEPLOY_RESCUE_BUILD_EMULATION_OUTPUTS_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_BUILD_EMULATION_OUTPUTS_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_BUILD_EMULATION_OUTPUTS_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_build_emulation_outputs": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/build-emulation/logs")
async def post_deploy_rescue_build_emulation_logs(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_simulated_build_logs(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_build_emulation_logs_status") or "blocked")
    code = "DEPLOY_RESCUE_BUILD_EMULATION_LOGS_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_BUILD_EMULATION_LOGS_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_BUILD_EMULATION_LOGS_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_build_emulation_logs": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/build-emulation/overlay")
async def post_deploy_rescue_build_emulation_overlay(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_overlay_persistence_emulation(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_build_emulation_overlay_status") or "blocked")
    code = "DEPLOY_RESCUE_BUILD_EMULATION_OVERLAY_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_BUILD_EMULATION_OVERLAY_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_BUILD_EMULATION_OVERLAY_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_build_emulation_overlay": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/build-emulation/verify")
async def post_deploy_rescue_build_emulation_verify(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = verify_rescue_build_emulation(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_build_emulation_verify_status") or "blocked")
    code = "DEPLOY_RESCUE_BUILD_EMULATION_VERIFY_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_BUILD_EMULATION_VERIFY_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_BUILD_EMULATION_VERIFY_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_build_emulation_verify": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/build-emulation/seal")
async def post_deploy_rescue_build_emulation_seal(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_build_emulation_seal(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_build_emulation_seal_status") or "blocked")
    code = "DEPLOY_RESCUE_BUILD_EMULATION_SEAL_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_BUILD_EMULATION_SEAL_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_BUILD_EMULATION_SEAL_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_build_emulation_seal": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/build-emulation/final-gate")
async def post_deploy_rescue_build_emulation_final_gate(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_build_emulation_final_gate(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_build_emulation_final_gate_status") or "blocked")
    code = "DEPLOY_RESCUE_BUILD_EMULATION_FINAL_GATE_BLOCKED"
    if st == "ready":
        code = "DEPLOY_RESCUE_BUILD_EMULATION_FINAL_GATE_READY"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_BUILD_EMULATION_FINAL_GATE_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_build_emulation_final_gate": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue-stick/build-emulation/workspace-snapshot")
async def post_deploy_rescue_stick_build_emulation_workspace_snapshot(
    body: DeployRescueHandoffOverwriteRequest,
) -> dict[str, Any]:
    res = build_rescue_stick_build_workspace_snapshot(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_stick_build_workspace_snapshot_status") or "blocked")
    code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_WORKSPACE_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_WORKSPACE_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_WORKSPACE_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_stick_build_workspace_snapshot": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue-stick/build-emulation/debian-live-tree")
async def post_deploy_rescue_stick_build_emulation_debian_live_tree(
    body: DeployRescueHandoffOverwriteRequest,
) -> dict[str, Any]:
    res = build_rescue_stick_expected_debian_live_tree(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_stick_expected_debian_live_tree_status") or "blocked")
    code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_DEBIAN_TREE_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_DEBIAN_TREE_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_DEBIAN_TREE_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_stick_expected_debian_live_tree": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue-stick/build-emulation/package-list")
async def post_deploy_rescue_stick_build_emulation_package_list(
    body: DeployRescueHandoffOverwriteRequest,
) -> dict[str, Any]:
    res = build_rescue_stick_package_list_preview(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_stick_package_list_preview_status") or "blocked")
    code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_PACKAGE_LIST_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_PACKAGE_LIST_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_PACKAGE_LIST_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_stick_package_list_preview": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue-stick/build-emulation/runtime-bundle")
async def post_deploy_rescue_stick_build_emulation_runtime_bundle(
    body: DeployRescueHandoffOverwriteRequest,
) -> dict[str, Any]:
    res = build_rescue_stick_runtime_bundle_preview(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_stick_runtime_bundle_preview_status") or "blocked")
    code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_RUNTIME_BUNDLE_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_RUNTIME_BUNDLE_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_RUNTIME_BUNDLE_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_stick_runtime_bundle_preview": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue-stick/build-emulation/frontend-bundle")
async def post_deploy_rescue_stick_build_emulation_frontend_bundle(
    body: DeployRescueHandoffOverwriteRequest,
) -> dict[str, Any]:
    res = build_rescue_stick_frontend_bundle_preview(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_stick_frontend_bundle_preview_status") or "blocked")
    code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_FRONTEND_BUNDLE_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_FRONTEND_BUNDLE_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_FRONTEND_BUNDLE_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_stick_frontend_bundle_preview": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue-stick/build-emulation/systemd-services")
async def post_deploy_rescue_stick_build_emulation_systemd_services(
    body: DeployRescueHandoffOverwriteRequest,
) -> dict[str, Any]:
    res = build_rescue_stick_systemd_service_preview(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_stick_systemd_service_preview_status") or "blocked")
    code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_SYSTEMD_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_SYSTEMD_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_SYSTEMD_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_stick_systemd_service_preview": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue-stick/build-emulation/network-webui")
async def post_deploy_rescue_stick_build_emulation_network_webui(
    body: DeployRescueHandoffOverwriteRequest,
) -> dict[str, Any]:
    res = build_rescue_stick_network_webui_preview(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_stick_network_webui_preview_status") or "blocked")
    code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_NETWORK_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_NETWORK_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_NETWORK_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_stick_network_webui_preview": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue-stick/build-emulation/evidence-manifest")
async def post_deploy_rescue_stick_build_emulation_evidence_manifest(
    body: DeployRescueHandoffOverwriteRequest,
) -> dict[str, Any]:
    res = build_rescue_stick_evidence_manifest(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_stick_evidence_manifest_status") or "blocked")
    code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_MANIFEST_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_MANIFEST_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_MANIFEST_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_stick_evidence_manifest": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue-stick/build-emulation/final-gate")
async def post_deploy_rescue_stick_build_emulation_final_gate(
    body: DeployRescueHandoffOverwriteRequest,
) -> dict[str, Any]:
    res = build_rescue_stick_readonly_build_final_gate(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_stick_readonly_build_final_gate_status") or "blocked")
    code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_FINAL_GATE_BLOCKED"
    if st == "ready":
        code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_FINAL_GATE_READY"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_FINAL_GATE_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_stick_readonly_build_final_gate": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue-stick/build-emulation/run-all")
async def post_deploy_rescue_stick_build_emulation_run_all(
    body: DeployRescueHandoffOverwriteRequest,
) -> dict[str, Any]:
    res = run_rescue_stick_readonly_build_emulation_all(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_stick_readonly_build_emulation_all_status") or "blocked")
    code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_FINAL_GATE_BLOCKED"
    if st == "ready":
        code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_FINAL_GATE_READY"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_STICK_BUILD_EMULATION_FINAL_GATE_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_stick_readonly_build_emulation_all": res,
        "warnings": [],
        "errors": [],
    }


@router.post("/rescue/iso-test-matrix")
async def post_deploy_rescue_iso_test_matrix(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_iso_test_matrix(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_iso_test_matrix_status") or "blocked")
    code = "DEPLOY_RESCUE_ISO_TEST_MATRIX_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_ISO_TEST_MATRIX_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_ISO_TEST_MATRIX_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_iso_test_matrix": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/build-readiness-gate")
async def post_deploy_rescue_build_readiness_gate(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_build_readiness_gate(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_build_readiness_gate_status") or "blocked")
    code = "DEPLOY_RESCUE_BUILD_READINESS_GATE_BLOCKED"
    if st == "ready":
        code = "DEPLOY_RESCUE_BUILD_READINESS_GATE_READY"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_BUILD_READINESS_GATE_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_build_readiness_gate": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/live-build-config")
async def post_deploy_rescue_live_build_config(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_live_build_config(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_live_build_config_status") or "blocked")
    code = "DEPLOY_RESCUE_LIVE_BUILD_CONFIG_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_LIVE_BUILD_CONFIG_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_LIVE_BUILD_CONFIG_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_live_build_config": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/iso-execution-plan")
async def post_deploy_rescue_iso_execution_plan(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_iso_execution_plan(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_iso_execution_plan_status") or "blocked")
    code = "DEPLOY_RESCUE_ISO_EXECUTION_PLAN_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_ISO_EXECUTION_PLAN_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_ISO_EXECUTION_PLAN_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_iso_execution_plan": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/iso-build-precheck")
async def post_deploy_rescue_iso_build_precheck(body: DeployRescueIsoBuildPrecheckRequest) -> dict[str, Any]:
    res = build_rescue_iso_build_precheck(
        explicit_overwrite=bool(body.explicit_overwrite),
        min_free_disk_bytes=body.min_free_disk_bytes,
    )
    st = str(res.get("rescue_iso_build_precheck_status") or "blocked")
    code = "DEPLOY_RESCUE_ISO_BUILD_PRECHECK_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_ISO_BUILD_PRECHECK_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_ISO_BUILD_PRECHECK_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_iso_build_precheck": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/iso-build-execute")
async def post_deploy_rescue_iso_build_execute(body: DeployRescueIsoBuildExecuteRequest) -> dict[str, Any]:
    res = execute_rescue_iso_build(
        explicit_overwrite=bool(body.explicit_overwrite),
        explicit_execute_iso_build=bool(body.explicit_execute_iso_build),
        explicit_rescue_build_approved=bool(body.explicit_rescue_build_approved),
        build_timeout_seconds=int(body.build_timeout_seconds),
    )
    st = str(res.get("rescue_iso_build_result_status") or "blocked")
    code = "DEPLOY_RESCUE_ISO_BUILD_EXECUTE_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_ISO_BUILD_EXECUTE_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_ISO_BUILD_EXECUTE_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_iso_build_execute": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/vm-test-plan")
async def post_deploy_rescue_vm_test_plan(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_vm_test_plan(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_vm_test_plan_status") or "blocked")
    code = "DEPLOY_RESCUE_VM_TEST_PLAN_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_VM_TEST_PLAN_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_VM_TEST_PLAN_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_vm_test_plan": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/vm-test-execute")
async def post_deploy_rescue_vm_test_execute(body: DeployRescueVmTestExecuteRequest) -> dict[str, Any]:
    res = execute_rescue_vm_boot_validation(
        explicit_overwrite=bool(body.explicit_overwrite),
        explicit_execute_vm_boot=bool(body.explicit_execute_vm_boot),
    )
    st = str(res.get("rescue_vm_test_result_status") or "blocked")
    code = "DEPLOY_RESCUE_VM_TEST_EXECUTE_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_VM_TEST_EXECUTE_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_VM_TEST_EXECUTE_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_vm_test_execute": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/iso-live-runtime-probe")
async def post_deploy_rescue_iso_live_runtime_probe(body: DeployRescueIsoLiveRuntimeProbeRequest) -> dict[str, Any]:
    act = str(body.action or "plan").strip().lower()
    if act == "plan":
        res = build_rescue_iso_live_runtime_probe_plan(
            explicit_overwrite=bool(body.explicit_overwrite),
            live_base_url=body.live_base_url,
        )
        st = str(res.get("rescue_iso_live_runtime_probe_plan_status") or "blocked")
        code = "DEPLOY_RESCUE_ISO_LIVE_RUNTIME_PROBE_BLOCKED"
        if st == "ok":
            code = "DEPLOY_RESCUE_ISO_LIVE_RUNTIME_PROBE_OK"
        elif st == "review_required":
            code = "DEPLOY_RESCUE_ISO_LIVE_RUNTIME_PROBE_REVIEW_REQUIRED"
        return {"code": code, "rescue_iso_live_runtime_probe": res, "warnings": list(res.get("warnings") or []), "errors": list(res.get("errors") or [])}
    if act == "execute":
        res = execute_rescue_iso_live_runtime_probe(
            explicit_overwrite=bool(body.explicit_overwrite),
            explicit_execute_iso_live_runtime_probe=bool(body.explicit_execute_iso_live_runtime_probe),
            live_base_url=body.live_base_url,
        )
        st = str(res.get("rescue_iso_live_runtime_probe_execute_status") or res.get("rescue_iso_live_runtime_probe_result_status") or "blocked")
        code = "DEPLOY_RESCUE_ISO_LIVE_RUNTIME_PROBE_BLOCKED"
        if st == "ok":
            code = "DEPLOY_RESCUE_ISO_LIVE_RUNTIME_PROBE_OK"
        elif st == "review_required":
            code = "DEPLOY_RESCUE_ISO_LIVE_RUNTIME_PROBE_REVIEW_REQUIRED"
        return {"code": code, "rescue_iso_live_runtime_probe": res, "warnings": list(res.get("warnings") or []), "errors": list(res.get("errors") or [])}
    if act == "result":
        res = build_rescue_iso_live_runtime_probe_result(explicit_overwrite=bool(body.explicit_overwrite))
        st = str(res.get("rescue_iso_live_runtime_probe_result_status") or "blocked")
        code = "DEPLOY_RESCUE_ISO_LIVE_RUNTIME_PROBE_BLOCKED"
        if st == "ok":
            code = "DEPLOY_RESCUE_ISO_LIVE_RUNTIME_PROBE_OK"
        elif st == "review_required":
            code = "DEPLOY_RESCUE_ISO_LIVE_RUNTIME_PROBE_REVIEW_REQUIRED"
        return {"code": code, "rescue_iso_live_runtime_probe": res, "warnings": list(res.get("warnings") or []), "errors": list(res.get("errors") or [])}
    return {
        "code": "DEPLOY_RESCUE_ISO_LIVE_RUNTIME_PROBE_BLOCKED",
        "rescue_iso_live_runtime_probe": {"error": "INVALID_ACTION", "allowed": ["plan", "execute", "result"]},
        "warnings": [],
        "errors": ["RESCUE_ISO_LIVE_RUNTIME_PROBE_INVALID_ACTION"],
    }


@router.post("/rescue/iso-readiness-gate")
async def post_deploy_rescue_iso_readiness_gate(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_iso_readiness_gate(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_iso_readiness_gate_status") or "blocked")
    code = "DEPLOY_RESCUE_ISO_READINESS_GATE_BLOCKED"
    if st == "ready":
        code = "DEPLOY_RESCUE_ISO_READINESS_GATE_READY"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_ISO_READINESS_GATE_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_iso_readiness_gate": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


def _rescue_deploy_code(prefix: str, st: str) -> str:
    b = f"DEPLOY_RESCUE_{prefix}_BLOCKED"
    if st in ("ok", "ready"):
        return f"DEPLOY_RESCUE_{prefix}_OK"
    if st == "review_required":
        return f"DEPLOY_RESCUE_{prefix}_REVIEW_REQUIRED"
    return b


def _offline_backup_plan_deploy_code(st: str) -> str:
    if st == "ready":
        return "DEPLOY_RESCUE_OFFLINE_BACKUP_PLAN_READY"
    if st == "review_required":
        return "DEPLOY_RESCUE_OFFLINE_BACKUP_PLAN_REVIEW_REQUIRED"
    return "DEPLOY_RESCUE_OFFLINE_BACKUP_PLAN_BLOCKED"


def _restore_preview_plan_deploy_code(st: str) -> str:
    if st == "ready":
        return "DEPLOY_RESCUE_RESTORE_PREVIEW_PLAN_READY"
    if st == "review_required":
        return "DEPLOY_RESCUE_RESTORE_PREVIEW_PLAN_REVIEW_REQUIRED"
    return "DEPLOY_RESCUE_RESTORE_PREVIEW_PLAN_BLOCKED"


def _iso_readiness_pipeline_code(prefix: str, status: str) -> str:
    if status == "blocked":
        return f"DEPLOY_RESCUE_{prefix}_BLOCKED"
    if status == "review_required":
        return f"DEPLOY_RESCUE_{prefix}_REVIEW_REQUIRED"
    if prefix == "ISO_FINAL_READINESS_GATE" and status == "ready":
        return "DEPLOY_RESCUE_ISO_FINAL_READINESS_GATE_READY"
    return f"DEPLOY_RESCUE_{prefix}_OK"


def _artifact_preparation_code(prefix: str, status: str) -> str:
    if status == "blocked":
        return f"DEPLOY_RESCUE_{prefix}_BLOCKED"
    if status == "review_required":
        return f"DEPLOY_RESCUE_{prefix}_REVIEW_REQUIRED"
    if prefix == "ARTIFACT_READINESS_GATE" and status == "ready":
        return "DEPLOY_RESCUE_ARTIFACT_READINESS_GATE_READY"
    return f"DEPLOY_RESCUE_{prefix}_OK"


def _pseudo_boot_code(prefix: str, status: str) -> str:
    if status == "blocked":
        return f"DEPLOY_RESCUE_{prefix}_BLOCKED"
    if status == "review_required":
        return f"DEPLOY_RESCUE_{prefix}_REVIEW_REQUIRED"
    if prefix == "PSEUDO_BOOT_FINAL_READINESS" and status == "ready":
        return "DEPLOY_RESCUE_PSEUDO_BOOT_FINAL_READINESS_READY"
    return f"DEPLOY_RESCUE_{prefix}_OK"


def _runtime_assembly_code(prefix: str, status: str) -> str:
    if status == "blocked":
        return f"DEPLOY_RESCUE_{prefix}_BLOCKED"
    if status == "review_required":
        return f"DEPLOY_RESCUE_{prefix}_REVIEW_REQUIRED"
    if prefix == "RUNTIME_FINAL_GATE" and status == "ready":
        return "DEPLOY_RESCUE_RUNTIME_FINAL_GATE_READY"
    return f"DEPLOY_RESCUE_{prefix}_OK"


def _runtime_bundle_code(prefix: str, status: str) -> str:
    if status == "blocked":
        return f"DEPLOY_RESCUE_{prefix}_BLOCKED"
    if status == "review_required":
        return f"DEPLOY_RESCUE_{prefix}_REVIEW_REQUIRED"
    return f"DEPLOY_RESCUE_{prefix}_OK"


@router.post("/rescue/storage-discovery")
async def post_deploy_rescue_storage_discovery(body: DeployRescueStorageDiscoveryRequest) -> dict[str, Any]:
    act = str(body.action or "plan").strip().lower()
    if act == "plan":
        res = build_rescue_storage_discovery_plan(explicit_overwrite=bool(body.explicit_overwrite))
        st = str(res.get("rescue_storage_discovery_plan_status") or "blocked")
    elif act == "execute":
        res = execute_rescue_storage_discovery(
            explicit_overwrite=bool(body.explicit_overwrite),
            explicit_execute_storage_discovery=bool(body.explicit_execute_storage_discovery),
        )
        st = str(res.get("rescue_storage_discovery_result_status") or res.get("rescue_storage_discovery_plan_status") or "blocked")
    elif act == "result":
        res = build_rescue_storage_discovery_result(explicit_overwrite=bool(body.explicit_overwrite))
        st = str(res.get("rescue_storage_discovery_result_status") or "blocked")
    else:
        return {
            "code": "DEPLOY_RESCUE_STORAGE_DISCOVERY_BLOCKED",
            "rescue_storage_discovery": {"error": "INVALID_ACTION"},
            "warnings": [],
            "errors": ["INVALID_ACTION"],
        }
    return {
        "code": _rescue_deploy_code("STORAGE_DISCOVERY", st),
        "rescue_storage_discovery": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/readonly-mount-validation")
async def post_deploy_rescue_readonly_mount_validation(body: DeployRescueReadonlyMountRequest) -> dict[str, Any]:
    act = str(body.action or "plan").strip().lower()
    if act == "plan":
        res = build_readonly_mount_plan(explicit_overwrite=bool(body.explicit_overwrite))
        st = str(res.get("readonly_mount_plan_status") or "blocked")
    elif act == "execute":
        res = execute_readonly_mount_validation(
            explicit_overwrite=bool(body.explicit_overwrite),
            explicit_execute_readonly_mount=bool(body.explicit_execute_readonly_mount),
        )
        st = str(res.get("readonly_mount_result_status") or "blocked")
    elif act == "result":
        res = build_readonly_mount_result(explicit_overwrite=bool(body.explicit_overwrite))
        st = str(res.get("readonly_mount_result_status") or "blocked")
    else:
        return {
            "code": "DEPLOY_RESCUE_READONLY_MOUNT_VALIDATION_BLOCKED",
            "rescue_readonly_mount": {"error": "INVALID_ACTION"},
            "warnings": [],
            "errors": ["INVALID_ACTION"],
        }
    return {
        "code": _rescue_deploy_code("READONLY_MOUNT_VALIDATION", st),
        "rescue_readonly_mount": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/boot-context/preview")
async def post_deploy_rescue_boot_context_preview(
    body: DeployRescueBootContextPreviewRequest,
) -> dict[str, Any]:
    res = build_rescue_boot_context(
        source_root=body.source_root,
        storage_snapshot_ref=body.storage_snapshot_ref,
        mount_snapshot_ref=body.mount_snapshot_ref,
        rescue_mode_hint=body.rescue_mode_hint,
        live_system_hint=body.live_system_hint,
        network_available_hint=body.network_available_hint,
        ui_mode_hint=body.ui_mode_hint,
    )
    st = str(res.get("status") or "blocked")
    return {
        "code": _rescue_deploy_code("BOOT_CONTEXT", st),
        "rescue_boot_context": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/offline-backup-plan")
async def post_deploy_rescue_offline_backup_plan(
    body: DeployRescueOfflineBackupPlanRequest,
) -> dict[str, Any]:
    res = build_rescue_offline_backup_plan(
        source_root=body.source_root,
        target_path=body.target_path,
        boot_context=body.boot_context,
        backup_profile_id=body.backup_profile_id,
    )
    st = str(res.get("status") or "blocked")
    return {
        "code": _offline_backup_plan_deploy_code(st),
        "rescue_offline_backup_plan": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
        "blocked_reasons": list(res.get("blocked_reasons") or []),
    }


@router.post("/rescue/restore-preview-plan")
async def post_deploy_rescue_restore_preview_plan(
    body: DeployRescueRestorePreviewPlanRequest,
) -> dict[str, Any]:
    res = build_rescue_restore_preview_plan(
        source_root=body.source_root,
        boot_context=body.boot_context,
        restore_profile_id=body.restore_profile_id,
        backup_archive_path=body.backup_archive_path,
        manifest_path=body.manifest_path,
        target_device_or_path=body.target_device_or_path,
        target_classification=body.target_classification,
        verify_status=body.verify_status,
        operator_override=body.operator_override,
        existing_filesystems=body.existing_filesystems,
        existing_os_indicators=body.existing_os_indicators,
        user_data_indicators=body.user_data_indicators,
    )
    st = str(res.get("status") or "blocked")
    return {
        "code": _restore_preview_plan_deploy_code(st),
        "rescue_restore_preview_plan": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
        "blocked_reasons": list(res.get("blocked_reasons") or []),
    }


@router.post("/rescue/efi-boot-analysis")
async def post_deploy_rescue_efi_boot_analysis(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_efi_boot_analysis(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_efi_boot_analysis_status") or "blocked")
    return {
        "code": _rescue_deploy_code("EFI_BOOT_ANALYSIS", st),
        "rescue_efi_boot_analysis": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/evidence-export")
async def post_deploy_rescue_evidence_export(body: DeployRescueEvidenceExportRequest) -> dict[str, Any]:
    act = str(body.action or "plan").strip().lower()
    if act == "plan":
        res = build_rescue_evidence_export_plan(explicit_overwrite=bool(body.explicit_overwrite))
        st = str(res.get("rescue_evidence_export_plan_status") or "blocked")
    elif act == "execute":
        res = execute_rescue_evidence_export(
            explicit_overwrite=bool(body.explicit_overwrite),
            explicit_execute_evidence_export=bool(body.explicit_execute_evidence_export),
            export_target=body.export_target,
        )
        st = str(res.get("rescue_evidence_export_result_status") or "blocked")
    elif act == "result":
        res = build_rescue_evidence_export_result(explicit_overwrite=bool(body.explicit_overwrite))
        st = str(res.get("rescue_evidence_export_result_status") or "blocked")
    else:
        return {
            "code": "DEPLOY_RESCUE_EVIDENCE_EXPORT_BLOCKED",
            "rescue_evidence_export": {"error": "INVALID_ACTION"},
            "warnings": [],
            "errors": ["INVALID_ACTION"],
        }
    return {
        "code": _rescue_deploy_code("EVIDENCE_EXPORT", st),
        "rescue_evidence_export": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/remote-help-preparation")
async def post_deploy_rescue_remote_help_preparation(body: DeployRescueRemoteHelpRequest) -> dict[str, Any]:
    act = str(body.action or "plan").strip().lower()
    if act == "plan":
        res = build_rescue_remote_help_plan(explicit_overwrite=bool(body.explicit_overwrite))
        st = str(res.get("rescue_remote_help_plan_status") or "blocked")
    elif act == "result":
        res = build_rescue_remote_help_result(explicit_overwrite=bool(body.explicit_overwrite))
        st = str(res.get("rescue_remote_help_result_status") or "blocked")
    else:
        return {
            "code": "DEPLOY_RESCUE_REMOTE_HELP_PREPARATION_BLOCKED",
            "rescue_remote_help": {"error": "INVALID_ACTION", "allowed": ["plan", "result"]},
            "warnings": [],
            "errors": ["INVALID_ACTION"],
        }
    return {
        "code": _rescue_deploy_code("REMOTE_HELP_PREPARATION", st),
        "rescue_remote_help": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/live-hardware-matrix")
async def post_deploy_rescue_live_hardware_matrix(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_live_hardware_matrix(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_live_hardware_matrix_status") or "blocked")
    return {
        "code": _rescue_deploy_code("LIVE_HARDWARE_MATRIX", st),
        "rescue_live_hardware_matrix": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/live-runtime-safety-gate")
async def post_deploy_rescue_live_runtime_safety_gate(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_live_runtime_safety_gate(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_live_runtime_safety_gate_status") or "blocked")
    code = "DEPLOY_RESCUE_LIVE_RUNTIME_SAFETY_GATE_BLOCKED"
    if st == "ready":
        code = "DEPLOY_RESCUE_LIVE_RUNTIME_SAFETY_GATE_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_LIVE_RUNTIME_SAFETY_GATE_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_live_runtime_safety_gate": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/recovery-scenario-matrix")
async def post_deploy_rescue_recovery_scenario_matrix(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_recovery_scenario_matrix(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_recovery_scenario_matrix_status") or "blocked")
    return {
        "code": _rescue_deploy_code("RECOVERY_SCENARIO_MATRIX", st),
        "rescue_recovery_scenario_matrix": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/recovery-target-validation")
async def post_deploy_rescue_recovery_target_validation(body: DeployRescueRecoveryTargetValidationRequest) -> dict[str, Any]:
    act = str(body.action or "plan").strip().lower()
    if act == "plan":
        res = build_rescue_recovery_target_validation_plan(
            explicit_overwrite=bool(body.explicit_overwrite),
            proposed_recovery_target=body.proposed_recovery_target,
        )
        st = str(res.get("rescue_recovery_target_validation_plan_status") or "blocked")
    elif act == "execute":
        res = execute_rescue_recovery_target_validation(
            explicit_overwrite=bool(body.explicit_overwrite),
            explicit_execute_recovery_target_validation=bool(body.explicit_execute_recovery_target_validation),
        )
        st = str(res.get("rescue_recovery_target_validation_result_status") or "blocked")
    elif act == "result":
        res = build_rescue_recovery_target_validation_result(explicit_overwrite=bool(body.explicit_overwrite))
        st = str(res.get("rescue_recovery_target_validation_result_status") or "blocked")
    else:
        return {
            "code": "DEPLOY_RESCUE_RECOVERY_TARGET_VALIDATION_BLOCKED",
            "rescue_recovery_target_validation": {"error": "INVALID_ACTION"},
            "warnings": [],
            "errors": ["INVALID_ACTION"],
        }
    return {
        "code": _rescue_deploy_code("RECOVERY_TARGET_VALIDATION", st),
        "rescue_recovery_target_validation": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/backup-discovery-verify")
async def post_deploy_rescue_backup_discovery_verify(body: DeployRescueBackupDiscoveryVerifyRequest) -> dict[str, Any]:
    act = str(body.action or "plan").strip().lower()
    if act == "plan":
        res = build_rescue_backup_discovery_plan(
            explicit_overwrite=bool(body.explicit_overwrite),
            backup_scan_root=body.backup_scan_root,
        )
        st = str(res.get("rescue_backup_discovery_plan_status") or "blocked")
    elif act == "discover":
        res = execute_rescue_backup_discovery(
            explicit_overwrite=bool(body.explicit_overwrite),
            explicit_execute_backup_discovery=bool(body.explicit_execute_backup_discovery),
        )
        st = str(res.get("rescue_backup_verify_result_status") or "blocked")
    elif act == "verify":
        res = execute_rescue_backup_verify(
            explicit_overwrite=bool(body.explicit_overwrite),
            explicit_execute_backup_verify=bool(body.explicit_execute_backup_verify),
        )
        st = str(res.get("rescue_backup_verify_result_status") or "blocked")
    elif act == "result":
        res = build_rescue_backup_verify_result(explicit_overwrite=bool(body.explicit_overwrite))
        st = str(res.get("rescue_backup_verify_result_status") or "blocked")
    else:
        return {
            "code": "DEPLOY_RESCUE_BACKUP_DISCOVERY_VERIFY_BLOCKED",
            "rescue_backup_discovery_verify": {"error": "INVALID_ACTION", "allowed": ["plan", "discover", "verify", "result"]},
            "warnings": [],
            "errors": ["INVALID_ACTION"],
        }
    return {
        "code": _rescue_deploy_code("BACKUP_DISCOVERY_VERIFY", st),
        "rescue_backup_discovery_verify": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/restore-preview")
async def post_deploy_rescue_restore_preview(body: DeployRescueRestorePreviewRequest) -> dict[str, Any]:
    act = str(body.action or "plan").strip().lower()
    if act == "plan":
        res = build_rescue_restore_preview_plan(explicit_overwrite=bool(body.explicit_overwrite))
        st = str(res.get("rescue_restore_preview_plan_status") or "blocked")
    elif act == "execute":
        res = execute_rescue_restore_preview(
            explicit_overwrite=bool(body.explicit_overwrite),
            explicit_execute_restore_preview=bool(body.explicit_execute_restore_preview),
        )
        st = str(res.get("rescue_restore_preview_result_status") or "blocked")
    elif act == "result":
        res = build_rescue_restore_preview_result(explicit_overwrite=bool(body.explicit_overwrite))
        st = str(res.get("rescue_restore_preview_result_status") or "blocked")
    else:
        return {
            "code": "DEPLOY_RESCUE_RESTORE_PREVIEW_BLOCKED",
            "rescue_restore_preview": {"error": "INVALID_ACTION"},
            "warnings": [],
            "errors": ["INVALID_ACTION"],
        }
    return {
        "code": _rescue_deploy_code("RESTORE_PREVIEW", st),
        "rescue_restore_preview": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/hardware-recovery-test-chain")
async def post_deploy_rescue_hardware_recovery_test_chain(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_hardware_recovery_test_chain(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_hardware_recovery_test_chain_status") or "blocked")
    return {
        "code": _rescue_deploy_code("HARDWARE_RECOVERY_TEST_CHAIN", st),
        "rescue_hardware_recovery_test_chain": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/final-recovery-readiness-gate")
async def post_deploy_rescue_final_recovery_readiness_gate(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_final_recovery_readiness_gate(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_final_recovery_readiness_gate_status") or "blocked")
    return {
        "code": _rescue_deploy_code("FINAL_RECOVERY_READINESS_GATE", st),
        "rescue_final_recovery_readiness_gate": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/manual-recovery-operator-guides")
async def post_deploy_rescue_manual_recovery_operator_guides(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_manual_recovery_operator_guides(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_manual_recovery_operator_guides_status") or "blocked")
    return {
        "code": _rescue_deploy_code("MANUAL_RECOVERY_OPERATOR_GUIDES", st),
        "rescue_manual_recovery_operator_guides": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/recovery-evidence-timeline")
async def post_deploy_rescue_recovery_evidence_timeline(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_recovery_evidence_timeline(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_recovery_evidence_timeline_status") or "blocked")
    return {
        "code": _rescue_deploy_code("RECOVERY_EVIDENCE_TIMELINE", st),
        "rescue_recovery_evidence_timeline": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/iso-baseline")
async def post_deploy_rescue_iso_baseline(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_iso_baseline(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_iso_baseline_status") or "blocked")
    return {
        "code": _iso_readiness_pipeline_code("ISO_BASELINE", st),
        "rescue_iso_baseline": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/iso-filesystem-layout")
async def post_deploy_rescue_iso_filesystem_layout(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_iso_filesystem_layout(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_iso_filesystem_layout_status") or "blocked")
    return {
        "code": _iso_readiness_pipeline_code("ISO_FILESYSTEM_LAYOUT", st),
        "rescue_iso_filesystem_layout": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/offline-runtime-validation")
async def post_deploy_rescue_offline_runtime_validation(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = validate_offline_recovery_runtime(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("offline_recovery_runtime_validation_status") or "blocked")
    return {
        "code": _iso_readiness_pipeline_code("OFFLINE_RUNTIME_VALIDATION", st),
        "offline_recovery_runtime_validation": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/bootflow-simulation")
async def post_deploy_rescue_bootflow_simulation(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_bootflow_simulation(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_bootflow_simulation_status") or "blocked")
    return {
        "code": _iso_readiness_pipeline_code("BOOTFLOW_SIMULATION", st),
        "rescue_bootflow_simulation": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/iso-safety-validation")
async def post_deploy_rescue_iso_safety_validation(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = validate_rescue_iso_safety(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_iso_safety_validation_status") or "blocked")
    return {
        "code": _iso_readiness_pipeline_code("ISO_SAFETY_VALIDATION", st),
        "rescue_iso_safety_validation": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/iso-final-readiness-gate")
async def post_deploy_rescue_iso_final_readiness_gate(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_iso_final_readiness_gate(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_iso_final_readiness_gate_status") or "blocked")
    return {
        "code": _iso_readiness_pipeline_code("ISO_FINAL_READINESS_GATE", st),
        "rescue_iso_final_readiness_gate": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/iso-build-plan")
async def post_deploy_rescue_iso_build_plan(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_iso_build_plan(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_iso_build_plan_status") or "blocked")
    return {
        "code": _iso_readiness_pipeline_code("ISO_BUILD_PLAN", st),
        "rescue_iso_build_plan": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/artifact/rootfs")
async def post_deploy_rescue_artifact_rootfs(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_rootfs_artifact(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_artifact_rootfs_status") or "blocked")
    return {
        "code": _artifact_preparation_code("ARTIFACT_ROOTFS", st),
        "rescue_artifact_rootfs": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/artifact/frontend")
async def post_deploy_rescue_artifact_frontend(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_offline_frontend_artifacts(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_artifact_frontend_status") or "blocked")
    return {
        "code": _artifact_preparation_code("ARTIFACT_FRONTEND", st),
        "rescue_artifact_frontend": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/artifact/backend")
async def post_deploy_rescue_artifact_backend(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_backend_artifacts(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_artifact_backend_status") or "blocked")
    return {
        "code": _artifact_preparation_code("ARTIFACT_BACKEND", st),
        "rescue_artifact_backend": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/artifact/boot-structure")
async def post_deploy_rescue_artifact_boot_structure(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_boot_artifact_structure(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_artifact_boot_structure_status") or "blocked")
    return {
        "code": _artifact_preparation_code("ARTIFACT_BOOT_STRUCTURE", st),
        "rescue_artifact_boot_structure": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/artifact/overlay-strategy")
async def post_deploy_rescue_artifact_overlay_strategy(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_overlay_persistence_strategy(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_artifact_overlay_strategy_status") or "blocked")
    return {
        "code": _artifact_preparation_code("ARTIFACT_OVERLAY_STRATEGY", st),
        "rescue_artifact_overlay_strategy": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/artifact/readiness-gate")
async def post_deploy_rescue_artifact_readiness_gate(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_artifact_readiness_gate(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_artifact_readiness_gate_status") or "blocked")
    return {
        "code": _artifact_preparation_code("ARTIFACT_READINESS_GATE", st),
        "rescue_artifact_readiness_gate": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/pseudo-boot/manifest")
async def post_deploy_rescue_pseudo_boot_manifest(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_pseudo_boot_manifest(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_pseudo_boot_manifest_status") or "blocked")
    return {
        "code": _pseudo_boot_code("PSEUDO_BOOT_MANIFEST", st),
        "rescue_pseudo_boot_manifest": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/pseudo-boot/service-startup")
async def post_deploy_rescue_pseudo_boot_service_startup(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_service_startup_simulation(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_pseudo_boot_service_startup_status") or "blocked")
    return {
        "code": _pseudo_boot_code("PSEUDO_BOOT_SERVICE_STARTUP", st),
        "rescue_pseudo_boot_service_startup": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/pseudo-boot/overlay-strategy")
async def post_deploy_rescue_pseudo_boot_overlay_strategy(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_overlay_boot_strategy(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_pseudo_boot_overlay_strategy_status") or "blocked")
    return {
        "code": _pseudo_boot_code("PSEUDO_BOOT_OVERLAY_STRATEGY", st),
        "rescue_pseudo_boot_overlay_strategy": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/pseudo-boot/backend-health")
async def post_deploy_rescue_pseudo_boot_backend_health(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_backend_health_integration(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_pseudo_boot_backend_health_status") or "blocked")
    return {
        "code": _pseudo_boot_code("PSEUDO_BOOT_BACKEND_HEALTH", st),
        "rescue_pseudo_boot_backend_health": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/pseudo-boot/recovery-ui")
async def post_deploy_rescue_pseudo_boot_recovery_ui(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_recovery_ui_integration(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_pseudo_boot_recovery_ui_status") or "blocked")
    return {
        "code": _pseudo_boot_code("PSEUDO_BOOT_RECOVERY_UI", st),
        "rescue_pseudo_boot_recovery_ui": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/pseudo-boot/safety-validation")
async def post_deploy_rescue_pseudo_boot_safety_validation(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = validate_rescue_pseudo_boot_safety(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_pseudo_boot_safety_validation_status") or "blocked")
    return {
        "code": _pseudo_boot_code("PSEUDO_BOOT_SAFETY_VALIDATION", st),
        "rescue_pseudo_boot_safety_validation": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/pseudo-boot/final-readiness")
async def post_deploy_rescue_pseudo_boot_final_readiness(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_pseudo_boot_final_readiness(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_pseudo_boot_final_readiness_status") or "blocked")
    return {
        "code": _pseudo_boot_code("PSEUDO_BOOT_FINAL_READINESS", st),
        "rescue_pseudo_boot_final_readiness": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/runtime/root")
async def post_deploy_rescue_runtime_root(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_runtime_root(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_runtime_root_status") or "blocked")
    return {
        "code": _runtime_assembly_code("RUNTIME_ROOT", st),
        "rescue_runtime_root": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/runtime/backend")
async def post_deploy_rescue_runtime_backend(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_backend_runtime_assembly(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_runtime_backend_status") or "blocked")
    return {
        "code": _runtime_assembly_code("RUNTIME_BACKEND", st),
        "rescue_runtime_backend": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/runtime/frontend")
async def post_deploy_rescue_runtime_frontend(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_frontend_runtime_assembly(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_runtime_frontend_status") or "blocked")
    return {
        "code": _runtime_assembly_code("RUNTIME_FRONTEND", st),
        "rescue_runtime_frontend": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/runtime/recovery")
async def post_deploy_rescue_runtime_recovery(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_recovery_runtime_assembly(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_runtime_recovery_status") or "blocked")
    return {
        "code": _runtime_assembly_code("RUNTIME_RECOVERY", st),
        "rescue_runtime_recovery": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/runtime/offline-config")
async def post_deploy_rescue_runtime_offline_config(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_offline_configuration_assembly(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_runtime_offline_config_status") or "blocked")
    return {
        "code": _runtime_assembly_code("RUNTIME_OFFLINE_CONFIG", st),
        "rescue_runtime_offline_config": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/runtime/startup-scripts")
async def post_deploy_rescue_runtime_startup_scripts(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_startup_script_assembly(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_runtime_startup_scripts_status") or "blocked")
    return {
        "code": _runtime_assembly_code("RUNTIME_STARTUP_SCRIPTS", st),
        "rescue_runtime_startup_scripts": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/runtime/final-gate")
async def post_deploy_rescue_runtime_final_gate(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_runtime_assembly_final_gate(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_runtime_final_gate_status") or "blocked")
    return {
        "code": _runtime_assembly_code("RUNTIME_FINAL_GATE", st),
        "rescue_runtime_final_gate": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/runtime/safety-validation")
async def post_deploy_rescue_runtime_safety_validation(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = validate_rescue_runtime_assembly_safety(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_runtime_safety_validation_status") or "blocked")
    return {
        "code": _runtime_assembly_code("RUNTIME_SAFETY_VALIDATION", st),
        "rescue_runtime_safety_validation": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/runtime-bundle/inventory")
async def post_deploy_rescue_runtime_bundle_inventory(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_runtime_bundle_inventory(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_runtime_bundle_inventory_status") or "blocked")
    return {
        "code": _runtime_bundle_code("RUNTIME_BUNDLE_INVENTORY", st),
        "rescue_runtime_bundle_inventory": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/runtime-bundle/hash-manifest")
async def post_deploy_rescue_runtime_bundle_hash_manifest(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_runtime_bundle_hash_manifest(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_runtime_bundle_hash_manifest_status") or "blocked")
    return {
        "code": _runtime_bundle_code("RUNTIME_BUNDLE_HASH_MANIFEST", st),
        "rescue_runtime_bundle_hash_manifest": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/runtime-bundle/seal")
async def post_deploy_rescue_runtime_bundle_seal(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_runtime_bundle_seal(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_runtime_bundle_seal_status") or "blocked")
    return {
        "code": _runtime_bundle_code("RUNTIME_BUNDLE_SEAL", st),
        "rescue_runtime_bundle_seal": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/runtime-bundle/consistency-check")
async def post_deploy_rescue_runtime_bundle_consistency_check(body: DeployRescueHandoffOverwriteRequest) -> dict[str, Any]:
    res = check_rescue_runtime_bundle_consistency(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_runtime_bundle_consistency_check_status") or "blocked")
    return {
        "code": _runtime_bundle_code("RUNTIME_BUNDLE_CONSISTENCY_CHECK", st),
        "rescue_runtime_bundle_consistency_check": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


# --- Phase C.3: read-only runner API facade (no runner imports, no execution) ---


@router.get("/runners/catalog")
async def get_deploy_runners_catalog() -> dict[str, Any]:
    return build_runner_catalog()


@router.get("/runners/summary")
async def get_deploy_runners_summary() -> dict[str, Any]:
    return build_runner_catalog_summary()


@router.get("/runners/policy-warnings")
async def get_deploy_runners_policy_warnings() -> dict[str, Any]:
    return build_runner_policy_warnings()


@router.get("/runners/risk-gate/summary")
async def get_deploy_runners_risk_gate_summary() -> dict[str, Any]:
    return build_runner_risk_gate_summary()


@router.get("/runners/risk-gate/operator-required")
async def get_deploy_runners_operator_required() -> dict[str, Any]:
    return list_runner_operator_required()


@router.get("/runners/risk-gate/never-auto")
async def get_deploy_runners_never_auto() -> dict[str, Any]:
    return list_runner_never_auto()


@router.get("/runners/risk-gate/plan-allowed")
async def get_deploy_runners_plan_allowed() -> dict[str, Any]:
    return list_runner_plan_allowed()


@router.get("/runners/{runner_id}")
async def get_deploy_runner_registry_entry(runner_id: str) -> dict[str, Any]:
    return get_runner_registry_entry(runner_id)


@router.get("/runners/{runner_id}/empty-result")
async def get_deploy_runner_empty_result(runner_id: str) -> dict[str, Any]:
    return get_runner_empty_result(runner_id)


@router.get("/runners/{runner_id}/risk-gate")
async def get_deploy_runner_risk_gate(runner_id: str) -> dict[str, Any]:
    return get_runner_risk_gate_decision(runner_id)
