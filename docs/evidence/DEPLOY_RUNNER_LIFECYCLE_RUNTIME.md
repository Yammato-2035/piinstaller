# Evidence: Deploy Runner Lifecycle (Runtime, Dry-run)

**Datum:** 2026-05-08  
**Phase:** kein Device-Write, keine sudoers-Installation, kein privilegierter Dauerbetrieb.

## Nachweise

1. **State-Machine:** Unit-Tests in `backend/tests/test_deploy_runner_lifecycle_v1.py` (illegale Übergänge, Terminalzustände).
2. **Locking:** `O_EXCL`-Erzeugung der Lock-Datei; Duplikat → `DEPLOY_RUNNER_LOCK_BUSY`; Stale-Cleanup über PID/TTL.
3. **TOCTOU:** Drei `recheck_runner_consistency`-Aufrufe im Dry-run-Flow; Drift-Tests für Snapshot/Mount/Readonly.
4. **Audit:** Append-only `audit-YYYYMMDD.jsonl`; keine vollen Checksummen in Zeilen.
5. **Keine verbotenen Aufrufe:** Statische Tests auf `subprocess`/`os.system`/`dd`/`mount` in `runner_lifecycle.py`.
6. **Kein Device-Write:** Runner öffnet keine `/dev/*`-Pfade (reiner JSON/Pfad/Lock-Pfad-I/O).

## Kommandos

```bash
python3 -m py_compile backend/deploy/runner_lifecycle.py backend/tools/deploy_write_runner.py
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_lifecycle_v1 \
  backend.tests.test_deploy_write_runner_runtime_v1 -v
```

Regressionen: `backend.tests.test_deploy_write_runner_contract_v1`, `backend.tests.test_deploy_real_write_guard_v1`, `backend.tests.test_deploy_real_write_prototype_v1`.

## Grenzen

- Replay-Schutz `DEPLOY_RUNNER_REPLAY_GUARD` bleibt prozesslokal (siehe Runner-Contract-Doku).
- TOCTOU-Metadaten (`_runtime_*`) müssen bei echtem Betrieb aus derselben Quelle wie das Gate kommen — aktuell Default aus Job ohne diese Keys.

## Abnahme

Alle obigen Tests grün; Lifecycle fail-closed; Stale/Duplikat-Locks beherrscht; Audit wächst deterministisch bei erfolgreichem Dry-run.
