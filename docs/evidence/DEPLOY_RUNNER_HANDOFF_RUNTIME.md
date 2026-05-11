# Evidence: Deploy Runner Handoff Runtime (Dry-run)

## Scope

Nur Dry-run-Handoff: Job-Erzeugung, atomische Job-Ablage, Runner-Start im Dry-run, JSON-Auswertung, Cleanup.
Keine Device-Writes, kein sudoers-Install, kein privilegierter Start.

## Nachweise

1. `create_runner_job_handoff` schreibt ausschließlich unter `backend/cache/deploy/runner-jobs/`.
2. Schreiben ist atomisch (`.tmp` + `replace`) und mit defensivem `chmod 0600`.
3. Runner-Start über `subprocess.run` mit festen Args, `shell=False`, `timeout=30`.
4. Ungültige Runner-JSON wird als `DEPLOY_RUNNER_HANDOFF_INVALID_RESPONSE` blockiert.
5. Timeout wird als `DEPLOY_RUNNER_HANDOFF_TIMEOUT` blockiert.
6. Non-zero Exitcode wird als `DEPLOY_RUNNER_HANDOFF_FAILED` blockiert.
7. Cleanup löscht nur `runner-job-*.json` im `runner-jobs/`-Verzeichnis und nicht rekursiv.

## Runtime-Probe (read-only)

```bash
python3 -m py_compile backend/deploy/runner_handoff.py backend/tools/deploy_write_runner.py
./venv/bin/python3 -m unittest \
  backend.tests.test_deploy_runner_handoff_v1 \
  backend.tests.test_deploy_runner_lifecycle_v1 -v
```

Beispielausgabe der Probe (lokal, gekürzt):

```json
{
  "code": "DEPLOY_RUNNER_HANDOFF_COMPLETED",
  "runner_exit_code": 0,
  "runner_response": {
    "code": "DEPLOY_RUNNER_DRY_RUN_OK",
    "runner_state": "completed"
  }
}
```

Regressionen:

```bash
./venv/bin/python3 -m unittest \
  backend.tests.test_deploy_write_runner_runtime_v1 \
  backend.tests.test_deploy_write_runner_contract_v1 \
  backend.tests.test_deploy_real_write_guard_v1 \
  backend.tests.test_deploy_real_write_prototype_v1 -v
```

## Grenzen

- Kein tatsächlicher Device-Open-Nachweis per `strace` in dieser Datei; funktionale Tests belegen nur den code-path ohne Write-Operationen.
