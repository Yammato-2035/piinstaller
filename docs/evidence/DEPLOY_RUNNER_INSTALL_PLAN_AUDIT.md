# Evidence: Deploy Runner Installation Plan Audit

## Scope

Nur Plan/Audit/Dokumentation, keine Ausfuehrung.

## Nachweise

- `build_runner_install_plan` liefert strukturierten read-only Plan.
- Root-Backend- und Daemon-Modelle werden blockiert.
- Wildcard-Policy wird blockiert.
- Manual Steps sind immer `auto_allowed=false`.
- Keine systemnahen Aenderungen (keine Rechte-/Service-/Sudoers-Aktion).

## Kommandos

```bash
python3 -m py_compile backend/deploy/runner_install_plan.py backend/deploy/routes.py
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_install_plan_v1 -v
```

Regressionen:

```bash
./venv/bin/python3 -m unittest \
  backend.tests.test_deploy_runner_sandbox_v1 \
  backend.tests.test_deploy_runner_permission_boundary_v1 \
  backend.tests.test_deploy_runner_handoff_v1 \
  backend.tests.test_deploy_runner_lifecycle_v1 -v
```
