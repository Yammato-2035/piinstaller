# Regressionstestplan (vor Refactoring)

Ziel: kleine, rückbaubare Schritte im Monolithen ohne Funktionsabfall.

## Pflicht vor strukturellen Änderungen

1. **CI-Äquivalent lokal oder in GitHub:** `cd backend && python -m pytest tests/ -v`  
2. **Domänen-relevante Teilsets** (bei Änderungen in):
   - Backup / Preflight: `test_preflight_backup_v1.py`, `test_backup_*`, `test_fullbackup_*`
   - Restore: `test_restore_*`, `test_post_restore_validation_v1.py`, `test_rescue_restore_*`
   - Safety / Storage: `test_safe_device_storage_protection_v1.py`, `test_write_guard_v1.py`
   - Deploy/Rescue: `test_deploy_runner_rescue_*`

## Nachweise

- Jeder Lauf: Log anhängen oder in `docs/evidence/release-gates/` verlinken.  
- Neue Regression: Eintrag in `STATUS_MATRIX.md` + Issue.

## Nicht Ziel

Kein Ersatz für Hardware- oder Live-Rescue-Tests (siehe Hardware- und Rescue-Matrizen).
