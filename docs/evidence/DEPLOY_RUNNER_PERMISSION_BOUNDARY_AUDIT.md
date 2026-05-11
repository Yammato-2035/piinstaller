# Evidence: Deploy Runner Permission Boundary Audit (Read-only)

## Scope

Diese Phase implementiert nur Analyse-/Auditfunktionen für spätere Privileggrenzen.
Keine sudoers-Installation, keine Rechteänderung, keine Root-Ausführung, kein Device-Write.

## Prüfpunkte

1. Sudoers-Policy-Beispiel liefert alle required restrictions.
2. Environment-Audit markiert `LD_PRELOAD` als blockierend.
3. `PYTHONPATH` wird markiert (warning/block).
4. Relative PATH-Segmente und leere PATH-Segmente (`::`) werden erkannt.
5. Runner-Pfad muss absolut und nicht symlink-basiert sein.
6. world-writable Parent-Verzeichnisse werden blockiert.
7. Job-Verzeichnis mit Traversal/Symlink wird blockiert.
8. Keine verbotenen Systemcalls im Modul (`subprocess`, `os.system`, `sudo`, `visudo`, `dd`, `mount`, ...).

## Kommandos

```bash
python3 -m py_compile backend/deploy/runner_permission_boundary.py backend/deploy/routes.py
./venv/bin/python3 -m unittest backend.tests.test_deploy_runner_permission_boundary_v1 -v
```

Regressionen:

```bash
./venv/bin/python3 -m unittest \
  backend.tests.test_deploy_runner_handoff_v1 \
  backend.tests.test_deploy_runner_lifecycle_v1 \
  backend.tests.test_deploy_write_runner_runtime_v1 \
  backend.tests.test_deploy_write_runner_contract_v1 -v
```
