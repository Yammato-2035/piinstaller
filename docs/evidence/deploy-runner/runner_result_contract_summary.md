# Deploy Runner Result Contract Summary (generated)

**Contract version:** 1
**Empty results buildable:** 115/115
**Validation failures:** 0
**Registry policy warnings:** 4

## Example results by risk class

### `destructive`

- runner_id: `runner_rescue_build_readiness_gate`
- status: `skipped`
- kind: `readiness_gate`
- valid: `True`

### `evidence_write`

- runner_id: `runner_handoff`
- status: `skipped`
- kind: `unknown`
- valid: `True`

### `local_runtime_change`

- runner_id: `runner_device_reenumeration_test_plan`
- status: `skipped`
- kind: `unknown`
- valid: `True`

### `read_only`

- runner_id: `runner_next_phase_gate`
- status: `skipped`
- kind: `readiness_gate`
- valid: `True`

### `system_change`

- runner_id: `runner_manual_runtime_result_edit_checker`
- status: `skipped`
- kind: `readiness_gate`
- valid: `True`

### `template_write`

- runner_id: `runner_manual_runtime_final_export_package`
- status: `skipped`
- kind: `template_generation`
- valid: `True`

## Policy warnings (sample)

- `runner_sudo_without_operator_policy:runner_laptop_failure_test_execution_readiness_final_gate`
- `runner_sudo_without_operator_policy:runner_laptop_live_probe_execution_handoff`
- `runner_sudo_without_operator_policy:runner_manual_runtime_result_template`
- `runner_sudo_without_operator_policy:runner_runtime_runbook_export`
