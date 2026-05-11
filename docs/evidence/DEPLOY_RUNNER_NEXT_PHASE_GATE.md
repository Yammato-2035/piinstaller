# Evidence: Deploy Runner Next Phase Gate

## Scope

Read-only Next-Phase-Entscheidungsgate fuer Deploy-Runner-Lab.

## Nachweise

- Gate-Statusmodell (`hold|manual_runtime_allowed|repeat_required|blocked`)
- Allowed/Blocked Next Phases mit harten Blockcodes
- Required Inputs und Operator Requirements
- Keine Produktions- oder Automationsfreigabe

## Kommandos

```bash
python3 -m py_compile backend/deploy/runner_next_phase_gate.py backend/deploy/routes.py
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_next_phase_gate_v1 -v
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_lab_phase_consolidation_v1 -v
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_lab_acceptance_report_export_v1 -v
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_lab_acceptance_aggregator_v1 -v
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_runtime_result_validator_v1 -v
```
