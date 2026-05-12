# Diagnosis Matching Rules

Reihenfolge ist verbindlich:

1. **Harte Signale** (`signals`), z. B.:
   - `manifest_present=false` -> `BACKUP-MANIFEST-001`
   - `backend_service_active=false` + `frontend_service_active=true` -> `UI-NO-BACKEND-015`
   - `filesystem_readonly=true` -> `FS-RO-021`
2. **Pattern-Matching** auf `question` als sekundaeres Signal.
3. **Fallback**:
   - mit Frage aber ohne harte Treffer -> `LOGS-029`
   - ohne verwertbare Eingaben -> `APP-030`

Determinismus:

- gleiche Eingabe -> gleiche Diagnose-Reihenfolge.
- Root-Cause-orientierte harte Signale haben Vorrang vor Symptom-Pattern.
