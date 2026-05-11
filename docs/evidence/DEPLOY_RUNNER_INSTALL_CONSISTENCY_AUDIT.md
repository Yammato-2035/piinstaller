# Evidence: Deploy Runner Install Consistency Audit

## Scope

Nur Konsistenzpruefung/Cross-Validation, keine Installation.

## Nachweise

- Modul `validate_runner_install_consistency(...)`
- Route `POST /api/deploy/runner/install/consistency`
- Abgleich von Pfaden, Rechten, Sudoers-Regeln, Rollback- und Validation-Steps

## Kommandos

```bash
python3 -m py_compile backend/deploy/runner_install_consistency.py backend/deploy/routes.py
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_install_consistency_v1 -v
```
