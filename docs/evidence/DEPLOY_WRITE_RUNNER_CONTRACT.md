# Evidence: DEPLOY_WRITE_RUNNER_CONTRACT (Dry-Run-Phase)

## Datum

2026-05-08.

## Umsetzung

- `backend/deploy/real_write_runner_contract.py` — Job-Build, Hash, Validierung
- `backend/tools/deploy_write_runner.py` — CLI nur `--dry-run`
- Tests: `backend/tests/test_deploy_write_runner_contract_v1.py`

## Checks

- `python3 -m py_compile backend/deploy/real_write_runner_contract.py backend/tools/deploy_write_runner.py` — OK
- `python3 -m unittest tests.test_deploy_write_runner_contract_v1` — OK
- Regression: `tests.test_deploy_real_write_prototype_v1`, `tests.test_deploy_real_write_failure_injection_v1`, `backend.tests.test_deploy_real_write_guard_v1` — OK (guard mit Projekt-`.venv` falls nötig)

## Abnahme (Phase)

- Kein Device-Open, kein Write: **erfüllt**
- `job_hash` Pflicht: **erfüllt**
- Keine verbotenen Substrings in Runner/Contract-Quellen laut Test: **erfüllt**
