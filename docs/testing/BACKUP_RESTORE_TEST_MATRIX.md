# Setuphelfer Backup-/Restore-Testmatrix

| ID | Test | Voraussetzung | Erwartung | Status | Evidence |
|----|------|---------------|-----------|--------|----------|
| BR-001 | Full Backup gültige Quelle | Ziel beschreibbar | Archiv + Manifest + SHA256 | Rot | docs/evidence/backup-restore/BR-001.json |
| BR-002 | Ziel nicht beschreibbar | Rechte entzogen | harter Abbruch | Rot | docs/evidence/backup-restore/BR-002.json |
| BR-003 | `.partial` Archiv prüfen | abgebrochene Sicherung | Verify blockiert | Rot | docs/evidence/backup-restore/BR-003.json |
| BR-004 | Verify Basic gültig | gültiges Archiv | ok | Gelb | docs/evidence/backup-restore/BR-004.json |
| BR-005 | Verify Deep gültig | gültiges Archiv | ok | Gelb | docs/evidence/backup-restore/BR-005.json |
| BR-006 | Verify beschädigt | manipuliertes Archiv | hash_mismatch / corrupt | Rot | docs/evidence/backup-restore/BR-006.json |
| BR-007 | Restore Preview | gültiges Archiv | keine Schreiboperation | Rot | docs/evidence/backup-restore/BR-007.json |
| BR-008 | Restore externes Ziel | freigegebenes Medium | Restore erfolgreich | Rot | docs/evidence/backup-restore/BR-008.json |
| BR-009 | Interne Disk Schutz | interne Systemplatte | blockiert | Rot | docs/evidence/backup-restore/BR-009.json |
| BR-010 | Boot nach Restore | restored System | bootfähig | Rot | docs/evidence/backup-restore/BR-010.json |

## Verknüpfung Unit-/CI-Tests

Viele Szenarien haben Abdeckung unter `backend/tests/` (z. B. Backup/Restore/Write-Guard). **Grün in dieser Matrix** verlangt zusätzlich dokumentierte Läufe mit Evidence-JSON gemäß `docs/evidence/README.md`.

**Hinweis Gelb (BR-004/BR-005):** API-Nachweis mit Referenzarchiv liegt vor; vollständige Kettenfreigabe mit erfolgreichem BR-001-Full-Backup auf freigegebenem Ziel fehlt noch (`STRICT_CI_BR_GATE_RUN_REPORT_2026-05-11.md`).
