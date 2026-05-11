# Evidence: Deploy Runner Lab Acceptance Report Export

## Scope

Read-only Export von Lab-Abnahmeberichten in erlaubte Docs-/Evidence-Pfade.

## Nachweise

- Exportmodul mit Pfadschutz und atomischem Schreiben
- DE/EN Report + JSON Report + DE/EN Summary
- JSON mit Pflichtfeldern fuer Acceptance-Auswertung
- Residual Risks und Operator Decision Required bleiben sichtbar
- keine Produktionsfreigabe und keine automatische Freigabe

## Kommandos

```bash
python3 -m py_compile backend/deploy/runner_lab_acceptance_report_export.py backend/deploy/routes.py
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_lab_acceptance_report_export_v1 -v
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_lab_acceptance_aggregator_v1 -v
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_runtime_result_validator_v1 -v
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_runtime_runbook_export_v1 -v
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_lab_readiness_status_v1 -v
```
