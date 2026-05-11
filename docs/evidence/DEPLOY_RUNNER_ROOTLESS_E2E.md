# Deploy Runner Rootless E2E (Dry-run)

Zeitpunkt: 2026-05-08 (lokale Laufzeitprobe, rootless).

## Rootless-Kontext

- User: `gabriel`
- UID/EUID: `1002`
- Gruppen: `gabriel sudo users vboxusers setuphelfer workspace piinstaller`
- Root verwendet: **nein**
- sudo verwendet: **nein**

## Backend-Port

- Temporär gestarteter Backend-Port: `48097` (localhost)
- Start über `.venv` mit Uvicorn, danach wieder beendet

## Positiver E2E-Handoff (API)

Request an `POST /api/deploy/runner/handoff` mit:
- `final_confirmation_result.code = DEPLOY_FINAL_CONFIRMATION_READY`
- `real_write_guard_result.code = DEPLOY_REAL_WRITE_READY`
- `hardware_gate_report.readiness_level = test_ready`
- gültiges `image_inspect_result`, `write_plan`, `write_execute_result`

Antwort:

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

- Jobfile erzeugt: `backend/cache/deploy/runner-jobs/runner-job-handoff_4522061c77f72141cb0a0b84.json`
- Lock wieder freigegeben: `backend/cache/deploy/runner-locks/` leer
- Audit geschrieben: `backend/cache/deploy/runner-audit/audit-20260508.jsonl`

## Audit-Auszug

Beispielzeilen:
- `handoff_create` mit `DEPLOY_RUNNER_HANDOFF_CREATED`
- `validate` mit `DEPLOY_RUNNER_JOB_VALID`
- `lock_acquire` mit `ok`
- `transition` mit `ready`
- `completed` mit `DEPLOY_RUNNER_DRY_RUN_OK`
- `handoff_execute` mit `DEPLOY_RUNNER_HANDOFF_COMPLETED`

## Negativtests (runtime-nah)

1. `hardware_gate_report != test_ready` -> `DEPLOY_RUNNER_HANDOFF_FAILED`
2. Final confirmation ungültig -> `DEPLOY_RUNNER_HANDOFF_FAILED`
3. Guard ungültig -> `DEPLOY_RUNNER_HANDOFF_FAILED`
4. Jobfile nach Erzeugung manipuliert -> Runner blockiert (`DEPLOY_RUNNER_JOB_HASH_MISMATCH`)
5. Runner liefert invalid JSON (mocked) -> `DEPLOY_RUNNER_HANDOFF_INVALID_RESPONSE`
6. Runner timeout simuliert (mocked) -> `DEPLOY_RUNNER_HANDOFF_TIMEOUT`

## Artifact-Check

- `runner-jobs/`: nur erwartete `runner-job-*.json`
- Keine `.tmp`-Dateien unter `backend/cache/deploy`
- `runner-locks/`: leer
- `runner-audit/`: JSONL vorhanden, erwartete Eventcodes enthalten
- Keine `runner-job-*.json` außerhalb `backend/cache/deploy/runner-jobs`

## Nachweise: kein Root / kein Device-Write

- Kein `sudo`-Aufruf im Testablauf.
- Kein root-EUID.
- Keine Mount-/Partition-/dd/mkfs-Aktionen ausgeführt.
- Probeprozess zeigte keine `/dev/*`-Open-Files für den gestarteten Backend-Prozess.
- Runner bleibt dry-run (`DEPLOY_RUNNER_DRY_RUN_OK`), kein echter Deploy.

## Testkommandos und Ergebnisse

Pflicht:

```bash
python3 -m py_compile \
  backend/deploy/runner_handoff.py \
  backend/deploy/runner_lifecycle.py \
  backend/deploy/runner_sandbox.py \
  backend/tools/deploy_write_runner.py
```

```bash
./venv/bin/python3 -m unittest \
  backend.tests.test_deploy_runner_handoff_v1 \
  backend.tests.test_deploy_runner_lifecycle_v1 \
  backend.tests.test_deploy_runner_sandbox_v1 \
  backend.tests.test_deploy_write_runner_runtime_v1 -v
```

Regressionen:

```bash
./venv/bin/python3 -m unittest \
  backend.tests.test_deploy_runner_permission_boundary_v1 \
  backend.tests.test_deploy_write_runner_contract_v1 \
  backend.tests.test_deploy_real_write_guard_v1 -v
```

Alle grün.

## Abnahmeentscheidung

**Erfolgreich** für rootless E2E dry-run:
- rootless ausgeführt
- ohne sudo
- ohne Device-Write
- Handoff completed
- Runner completed
- Audit vorhanden
- Lock freigegeben
- Negativtests blockieren wie erwartet
