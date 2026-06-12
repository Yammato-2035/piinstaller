# Boundary Warnings — Module Catalog (M.1)

**Datum:** 2026-06-10  
**HEAD vorher:** `0427de6`  
**Branch:** `main`  
**Script:** `./scripts/check-module-boundaries.sh`  
**Exit:** 0 (WARN-only, `review_required`)

## Runtime-Gate

`./scripts/check-runtime-deploy-gate.sh` — Exit 0 (release-Profil, dev-dashboard 404 erwartet)

## Neue M.1-Warnungen (Module Catalog Guard)

| Code | Count / Detail |
|------|----------------|
| `duplicate_storage_discovery_detected` | 1 |
| `duplicate_lsblk_usage_detected` | 11 |
| `duplicate_findmnt_usage_detected` | 8 |
| `duplicate_blkid_usage_detected` | 5 |
| `duplicate_write_target_validation_detected` | 2 |
| `duplicate_mount_logic_detected` | 2 |
| `duplicate_runner_result_status_detected` | 11 |
| `duplicate_runner_risk_logic_detected` | (none in this run) |
| `new_runner_route_in_routes_py_detected` | (none) |
| `module_catalog_missing` | (none — docs present) |
| `function_ownership_matrix_missing` | (none) |
| `do_not_duplicate_rules_missing` | (none) |

## Vollständige JSON-Ausgabe

```json
{"status":"review_required","line_count":17857,"include_router_count":18,"warnings":["token_in_app:mkfs","token_in_app: dd ","app_line_count_high:17857","facade_boundary_safe_device:backend/app.py","runner_sudo_without_operator_policy:runner_laptop_failure_test_execution_readiness_final_gate","runner_sudo_without_operator_policy:runner_laptop_live_probe_execution_handoff","runner_sudo_without_operator_policy:runner_manual_runtime_result_template","runner_sudo_without_operator_policy:runner_runtime_runbook_export","runner_result_no_evidence_reference:runner_device_reenumeration_test_plan.py","runner_result_no_evidence_reference:runner_failure_injection_hardware_test_plan.py","runner_result_no_evidence_reference:runner_hotplug_race_test_plan.py","runner_result_no_evidence_reference:runner_lab_acceptance_report_export.py","runner_result_unknown_status_token:runner_lab_phase_consolidation.py:implemented","runner_result_unknown_status_token:runner_lab_phase_consolidation.py:tested","runner_result_unknown_status_token:runner_lab_phase_consolidation.py:planned_only","runner_result_no_evidence_reference:runner_laptop_failure_test_execution_readiness_final_gate.py","runner_result_no_evidence_reference:runner_laptop_live_probe_execution_handoff.py","runner_result_no_evidence_reference:runner_legacy_identifier_cleanup_classifier.py","runner_result_no_evidence_reference:runner_legacy_identifier_hotspot_analysis.py","runner_result_no_evidence_reference:runner_legacy_identifier_inventory.py","runner_result_no_evidence_reference:runner_legacy_runtime_compatibility_validation.py","runner_result_no_evidence_reference:runner_manual_runtime_evidence_final_snapshot.py","runner_result_no_evidence_reference:runner_manual_runtime_evidence_timeline.py","runner_result_no_evidence_reference:runner_manual_runtime_failure_execution_preview.py","runner_result_no_evidence_reference:runner_manual_runtime_failure_injection_matrix.py","runner_result_no_evidence_reference:runner_manual_runtime_failure_operator_checklists.py","runner_result_no_evidence_reference:runner_manual_runtime_failure_readiness_gate.py","runner_result_no_evidence_reference:runner_manual_runtime_failure_result_evaluation.py","runner_result_no_evidence_reference:runner_manual_runtime_failure_test_result_capture.py","runner_result_no_evidence_reference:runner_manual_runtime_failure_test_sessions.py","runner_result_no_evidence_reference:runner_manual_runtime_final_acceptance_gate.py","runner_result_no_evidence_reference:runner_manual_runtime_final_export_package.py","runner_result_no_evidence_reference:runner_manual_runtime_laptop_failure_evidence_timeline.py","runner_result_no_evidence_reference:runner_manual_runtime_laptop_failure_execution_log_template.py","runner_result_no_evidence_reference:runner_manual_runtime_laptop_failure_execution_log_validator.py","runner_result_no_evidence_reference:runner_manual_runtime_laptop_failure_final_acceptance_gate.py","runner_result_no_evidence_reference:runner_manual_runtime_laptop_failure_final_export_package.py","runner_result_no_evidence_reference:runner_manual_runtime_laptop_failure_final_report.py","runner_result_no_evidence_reference:runner_manual_runtime_laptop_failure_final_snapshot.py","runner_result_no_evidence_reference:runner_manual_runtime_laptop_failure_finalized_export_package.py","runner_result_no_evidence_reference:runner_manual_runtime_laptop_failure_operator_runorder.py","runner_result_no_evidence_reference:runner_manual_runtime_laptop_failure_run_selector.py","runner_result_no_evidence_reference:runner_manual_runtime_laptop_failure_test_summary.py","runner_result_no_evidence_reference:runner_manual_runtime_result_bundle_checker.py","runner_result_unknown_status_token:runner_manual_runtime_result_edit_checker.py:invalid","runner_result_unknown_status_token:runner_manual_runtime_result_edit_checker.py:filled","runner_result_no_evidence_reference:runner_manual_runtime_result_edit_checker.py","runner_result_no_evidence_reference:runner_manual_runtime_result_template.py","runner_api_route_without_contract:backend/deploy/routes.py","routes_direct_runner_import_count:93","routes_direct_runner_import_reduced:113_to_93","routes_direct_runner_import_reduced_c6:109_to_93","deploy_routes_notifications_skipped_d9:no_safe_slice","deploy_routes_py_too_large:4523","deploy_routes_direct_runner_import_count:93","deploy_routes_direct_runner_import_reduced_d7:103_to_93","deploy_routes_line_count_reduced_d7:4821_to_4523","deploy_routes_direct_runner_import_reduced_d8:99_to_93","deploy_routes_line_count_reduced_d8:4671_to_4523","duplicate_storage_discovery_detected:1","duplicate_lsblk_usage_detected:11","duplicate_findmnt_usage_detected:8","duplicate_blkid_usage_detected:5","duplicate_write_target_validation_detected:2","duplicate_mount_logic_detected:2","duplicate_runner_result_status_detected:11"]}
```

## Hinweis

M.1-Checks sind **WARN-only** — kein harter Blocker. Duplikat-Zähler dienen der schrittweisen Migration auf Facades (siehe `DO_NOT_DUPLICATE_RULES.md`).
