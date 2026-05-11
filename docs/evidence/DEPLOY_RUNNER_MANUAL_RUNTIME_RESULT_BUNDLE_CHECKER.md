# Evidence: DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_BUNDLE_CHECKER

## Modul

- `backend/deploy/runner_manual_runtime_result_bundle_checker.py`

## Tests

```bash
python3 -m py_compile backend/deploy/runner_manual_runtime_result_bundle_checker.py backend/deploy/routes.py
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_manual_runtime_result_bundle_checker_v1 -v
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_manual_runtime_result_edit_checker_v1 -v
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_manual_runtime_result_template_v1 -v
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_runtime_result_validator_v1 -v
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_lab_acceptance_aggregator_v1 -v
```

Falls `./venv/bin/python3` fehlt: `PYTHONPATH=backend python3 -m unittest ...`

## STRICT MODE

Nur Lesen unter dem erlaubten Evidence-Pfad; keine Ausfuehrung, keine Korrektur, keine Freigabe.
