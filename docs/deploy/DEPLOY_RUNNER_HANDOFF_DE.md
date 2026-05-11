# Deploy Runner Handoff (Dry-run)

## Zweck

Sichere Übergabe vom Backend an den isolierten Runner über eine lokale Jobdatei:
Backend validiert Vorbedingungen, schreibt Job atomisch, startet Runner nur im Dry-run, liest JSON-Ergebnis, protokolliert Audit.

## Modul

- `backend/deploy/runner_handoff.py`
- Funktionen:
  - `create_runner_job_handoff(...)`
  - `execute_runner_dryrun_handoff(...)`
  - `cleanup_runner_job_handoff(...)`

## Job-Ablage

- Nur unter `backend/cache/deploy/runner-jobs/`
- Dateiname: `runner-job-<job_id>.json`
- Atomisch: `.tmp` schreiben, `fsync`, `replace`
- Defensiv `chmod 0600` (best effort)
- Kein Traversal/Symlink-Ziel außerhalb Prefix

## Ablauf

1. `real_write_guard_result.code == DEPLOY_REAL_WRITE_READY`
2. `final_confirmation_result.code == DEPLOY_FINAL_CONFIRMATION_READY`
3. `hardware_gate_report.readiness_level == test_ready`
4. `build_real_write_job(...)`
5. Jobdatei schreiben
6. Runner starten: `python3 backend/tools/deploy_write_runner.py --job <path> --dry-run`
7. Runner-JSON lesen und validieren
8. Audit ergänzen
9. Handoff-Response zurückgeben

## Runner-Start-Sicherheit

- `subprocess.run(..., shell=False, timeout=30, capture_output=True)`
- Keine freien Kommandoargumente
- Kontrollierter `cwd` (Repo-Root)
- Minimale Umgebung (kein `PYTHONPATH`, kein `LD_PRELOAD`)

## Response-Codes

- `DEPLOY_RUNNER_HANDOFF_CREATED`
- `DEPLOY_RUNNER_HANDOFF_COMPLETED`
- `DEPLOY_RUNNER_HANDOFF_FAILED`
- `DEPLOY_RUNNER_HANDOFF_TIMEOUT`
- `DEPLOY_RUNNER_HANDOFF_INVALID_RESPONSE`

## Grenzen

- Kein echter Device-Write
- Kein privilegierter Runner-Start
- Kein sudoers-Install
