# Evidence: Deploy Runner Lab Acceptance Aggregator

## Scope

Read-only Aggregation validierter Runtime-Ergebnisse zur manuellen Lab-Abnahme.

## Nachweise

- Aggregator-Modul mit stabiler Summary-Ausgabe
- Acceptance-Regeln (candidate/repeat_required/blocked)
- Runbook-Outcomes fuer alle 7 Pflicht-Runbooks
- Evidence-Summary Kennzahlen
- Residual-Risks immer sichtbar
- Operatorentscheidung immer erforderlich

## Kommandos

```bash
python3 -m py_compile backend/deploy/runner_lab_acceptance_aggregator.py backend/deploy/routes.py
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_lab_acceptance_aggregator_v1 -v
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_runtime_result_validator_v1 -v
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_runtime_runbook_export_v1 -v
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_runtime_runbook_bundle_v1 -v
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_lab_readiness_status_v1 -v
```
