# Evidence: Deploy Runner Sandbox Audit (Simulated)

## Scope

Strikte Dry-run-/Simulationsphase für Sandbox-Policies.
Keine echten Signale, keine Privilegänderung, kein Device-Write.

## Modellierte Regeln

- Execution model: one-shot, no interactive shell, no background, no parallel execution
- Environment model: clear/minimal env, blocklist (`LD_PRELOAD`, `LD_LIBRARY_PATH`, `PYTHONPATH`, `PYTHONHOME`, `PYTHONINSPECT`)
- STDIO/FD model: stdin disabled, stdout/stderr capture-only, close_fds required
- Timeout model: runtime, graceful-stop, hard-stop, stale-runner, lock-cleanup
- Privilege model: never backend as root, drop-after-open recommendation
- Recovery model: stale locks, orphan audit, replay after crash, interrupted phase

## Kommandos

```bash
python3 -m py_compile backend/deploy/runner_sandbox.py backend/deploy/routes.py
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_sandbox_v1 -v
```

Regressionen:

```bash
./venv/bin/python3 -m unittest \
  backend.tests.test_deploy_runner_permission_boundary_v1 \
  backend.tests.test_deploy_runner_handoff_v1 \
  backend.tests.test_deploy_runner_lifecycle_v1 \
  backend.tests.test_deploy_write_runner_runtime_v1 -v
```
