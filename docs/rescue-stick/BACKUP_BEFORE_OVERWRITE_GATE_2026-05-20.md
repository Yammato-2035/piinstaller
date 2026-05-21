# Backup-before-overwrite Gate

**Stand:** 2026-05-20  
**Modul:** `backend/core/backup_before_write_gate.py` → `evaluate_backup_before_write_requirement()`

---

## Zweck

Entscheidet, ob vor Restore/Overwrite auf ein Ziel mit **bestehenden Daten** ein Backup nötig ist. **Keine** Backup- oder Schreibausführung.

## Status

| Status | Bedeutung |
|--------|-----------|
| `satisfied` | Leeres Ziel oder nachweisbare Backup-Evidence |
| `required` | Daten vorhanden, Evidence fehlt |
| `review_required` | Operator-Override ohne Evidence |
| `blocked` | Bevölkertes internes Ziel ohne Evidence |

## Regeln

- Leeres/unklassifiziertes Ziel → `backup_required: false`, `satisfied`
- Dateisystem/OS/Nutzerdaten erkannt → `backup_required: true`
- Evidence mit `backup_completed` oder `status: ok` → `satisfied`
- Operator-Override → höchstens `review_required`, **nie** automatisch `satisfied`

## Nutzung

Wird von `build_rescue_restore_preview_plan()` vor Freigabe eines Preview-Plans aufgerufen.
