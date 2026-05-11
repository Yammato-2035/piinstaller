# Evidence: Deploy Runner Sudoers Runtime Dry-run Test Plan

## Scope

Nur Testdesign/Validierungsplan, keine Ausfuehrung.

## Nachweise

- `build_runner_sudoers_runtime_test_plan(...)` mit Preconditions, Steps, Negativtests
- explizite Evidence-/Risk-/Stop-/Rollback-Listen
- Read-only API-Route ohne execute/apply/install Endpunkte

## Kommandos

```bash
python3 -m py_compile backend/deploy/runner_sudoers_runtime_test_plan.py backend/deploy/routes.py
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_sudoers_runtime_test_plan_v1 -v
```
