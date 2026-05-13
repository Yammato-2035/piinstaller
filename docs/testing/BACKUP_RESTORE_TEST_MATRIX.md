# Setuphelfer Backup-/Restore-Testmatrix

| ID | Test | Voraussetzung | Erwartung | Status | Evidence |
|----|------|---------------|-----------|--------|----------|
| BR-001 | Full Backup freigegebenes Ziel | Nur **`/media/gabriel/setuphelfer-back`** (ext4, USB), Gates + **`target-check`** grün; **`setuphelfer-backup-starter`** muss Ziel erlauben | Archiv + Manifest + SHA256 | Rot (blocked — Starter **`backup.starter_invalid_path`** bis Deploy Repo-Starter) | `BR-001.json`, `BR-001_full_backup_run_2026-05-13.md` |
| BR-002 | Ziel nicht beschreibbar | Rechte entzogen | harter Abbruch | Rot | docs/evidence/backup-restore/BR-002.json |
| BR-003 | `.partial` Archiv prüfen | abgebrochene Sicherung | Verify blockiert | Rot | docs/evidence/backup-restore/BR-003.json |
| BR-004 | Verify Basic gültig | **dieselbe** Archivdatei wie BR-001 | ok | Rot (blocked — BR-001) | docs/evidence/backup-restore/BR-004.json |
| BR-005 | Verify Deep gültig | **dieselbe** Archivdatei wie BR-001 | ok | Rot (blocked — BR-001) | docs/evidence/backup-restore/BR-005.json |
| BR-006 | Verify beschädigt | manipuliertes Archiv | hash_mismatch / corrupt | Rot | docs/evidence/backup-restore/BR-006.json |
| BR-007 | Restore Preview | gültiges Archiv | keine Schreiboperation | Rot | docs/evidence/backup-restore/BR-007.json |
| BR-008 | Restore externes Ziel | freigegebenes Medium | Restore erfolgreich | Rot | docs/evidence/backup-restore/BR-008.json |
| BR-009 | Interne Disk Schutz | interne Systemplatte | blockiert | Rot | docs/evidence/backup-restore/BR-009.json |
| BR-010 | Boot nach Restore | restored System | bootfähig | Rot | docs/evidence/backup-restore/BR-010.json |

## Verknüpfung Unit-/CI-Tests

Viele Szenarien haben Abdeckung unter `backend/tests/` (z. B. Backup/Restore/Write-Guard). **Grün in dieser Matrix** verlangt zusätzlich dokumentierte Läufe mit Evidence-JSON gemäß `docs/evidence/README.md`.

**STRICT-Kette (2026-05-13):** Freigegebener Pfad **`/media/gabriel/setuphelfer-back`** — **`target-check`** und Version-Gate grün; Full-Backup **`POST /api/backup/create`** scheiterte an **`backup.starter_invalid_path`**, weil der installierte Starter nur **`/mnt/setuphelfer/backups`** erlaubte — Repo-Fix **`packaging/helpers/setuphelfer-backup-starter.py`** (`ALLOWED_BACKUP_ROOTS`). Historischer STRICT-/mnt-Hinweis 2026-05-12 bleibt für ältere Runs in älterer Evidence.
