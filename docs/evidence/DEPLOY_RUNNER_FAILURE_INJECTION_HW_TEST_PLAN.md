# Evidence: Deploy Runner Failure Injection Hardware Test Plan

## Scope

Nur Testdesign/Planung, keine Ausfuehrung.

## Nachweise

- `build_runner_failure_injection_hardware_test_plan(...)` erstellt vollständigen Failure-Plan
- alle Pflicht-Failure-Cases enthalten
- Read-only Route ohne execute/apply/install/write Endpunkte

## Kommandos

```bash
python3 -m py_compile backend/deploy/runner_failure_injection_hardware_test_plan.py backend/deploy/routes.py
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_failure_injection_hardware_test_plan_v1 -v
```
