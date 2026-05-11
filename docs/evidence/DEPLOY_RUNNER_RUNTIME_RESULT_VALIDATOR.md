# Evidence: Deploy Runner Runtime Result Validator

## Scope

Read-only Validierung von Runtime-Ergebnisdateien aus erlaubtem Evidence-Pfad.

## Nachweise

- Validator-Modul mit Pfadschutz (`docs/evidence/runtime-results/` only)
- Schema-Pflichtfeldpruefung via `RUNNER_RUNTIME_RESULT_SCHEMA.json`
- Sequenzpruefung fuer 7 Runbooks inkl. Follow-up-Blockierung
- Evidence-Feldpruefung inkl. Verify-Mismatch/Internal-Drive/Mount-Drift
- Acceptance-Gate ohne automatische Freigabe

## Kommandos

```bash
python3 -m py_compile backend/deploy/runner_runtime_result_validator.py backend/deploy/routes.py
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_runtime_result_validator_v1 -v
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_runtime_runbook_export_v1 -v
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_runtime_runbook_bundle_v1 -v
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_lab_readiness_status_v1 -v
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_release_readiness_v1 -v
```
