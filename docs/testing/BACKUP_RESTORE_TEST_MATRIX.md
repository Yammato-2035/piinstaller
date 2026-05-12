# Setuphelfer Backup-/Restore-Testmatrix

| ID | Test | Voraussetzung | Erwartung | Status | Evidence |
|----|------|---------------|-----------|--------|----------|
| BR-001 | Full Backup gültige Quelle | `/mnt/setuphelfer/backups` auf extern sdd1 + produktives target-check grün | Archiv + Manifest + SHA256 | Gelb (review_required — Ziel vorbereitet, Deploy/Verifikation offen) | docs/evidence/backup-restore/BR-001.json |
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

**STRICT-Kette (2026-05-12, Option 2):** **`/mnt/setuphelfer/backups`** — Bind auf **`/dev/sdd1`** (`setuphelfer-back`), `root:setuphelfer` **`2770`**. Media-Pfad `/media/gabriel/…` bleibt für Dienstnutzer ohne ACL problematisch; **produktiver** Pfad ist `/mnt/…`. Repo-Fixes: **findmnt-Flatten** (`app.py`) + **Klammer-SOURCE** (`safe_device`). **Produktions-`target-check`** nach Deploy/Restart verifizieren; **sudo-`setuphelfer`-Schreibprobe** optional. Kein Backup-Job. CI **25751304968** success.
