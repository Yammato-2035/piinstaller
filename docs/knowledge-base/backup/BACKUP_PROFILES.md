# Knowledge base — Backup profiles (BR-019)

Single-page anchor for product, API, and matrix **BR-019**.

- **Implementation:** `backend/core/backup_profiles.py`, `POST /api/backup/create` in `backend/app.py`.
- **User docs:** `docs/backup/BACKUP_PROFILES_DE.md`, `docs/backup/BACKUP_PROFILES_EN.md`.
- **Tests:** `backend/tests/test_backup_profiles_v1.py`, `frontend/src/utils/backupCreateBody.test.ts`.
- **Matrix:** `docs/testing/BACKUP_RESTORE_TEST_MATRIX.md` row **BR-019**.

**Testausführung:** Die Backend-Tests benötigen `pytest` (CI oder lokale venv). Fehlt `pytest`, sind diese Läufe **nicht** als bestanden zu dokumentieren; Syntax kann mit `python3 -m py_compile` auf die genannten `.py`-Dateien geprüft werden.

**Release posture:** yellow until hardware validates recommended vs. actual `backup_runner` data sources and full-root expert path on representative systems.
