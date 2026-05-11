# Evidence: Deploy Runner Manual Runtime Precheck

## Scope

Read-only Startbereitschaftspruefung fuer manuelle Runtime-Runbooks.

## Nachweise

- unbekannte Runbooks werden blockiert
- Write-bezogene Runbooks verlangen Hardware-Gate und Guard
- Dry-run-Runbooks koennen ohne Testmedium als not_applicable laufen
- Evidence-Plan zeigt auf `docs/evidence/runtime-results/`
- automatische Ausfuehrung bleibt deaktiviert

## Kommandos

```bash
python3 -m py_compile backend/deploy/runner_manual_runtime_precheck.py backend/deploy/routes.py
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_manual_runtime_precheck_v1 -v
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_next_phase_gate_v1 -v
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_lab_phase_consolidation_v1 -v
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_runtime_runbook_bundle_v1 -v
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_lab_readiness_status_v1 -v
```
