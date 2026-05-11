# Evidence: Deploy Runner Install Validator Audit

## Scope

Nur Dry-run-Validierung, keine Installation.

## Nachweise

- Validator-Modul mit read-only Path-/Snippet-/ENV-/Rollback-Pruefung
- Route `POST /api/deploy/runner/install/validate`
- Unsichere Snippets werden blockiert
- Rollback-Schritte sind verpflichtend und `auto_allowed=false`

## Kommandos

```bash
python3 -m py_compile backend/deploy/runner_install_validator.py backend/deploy/routes.py
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_install_validator_v1 -v
```
