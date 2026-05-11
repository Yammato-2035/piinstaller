# Setuphelfer Rescue-Stick-Testmatrix

| ID | Test | Erwartung | Schreibzugriff erlaubt? | Status | Evidence |
|----|------|-----------|-------------------------|--------|----------|
| RS-001 | Debian Live bootet | System startet | nein | Rot | docs/evidence/rescue-stick/RS-001.json |
| RS-002 | Setuphelfer Backend startet | API erreichbar | nein | Rot | docs/evidence/rescue-stick/RS-002.json |
| RS-003 | UI erreichbar | Web/Tauri erreichbar | nein | Rot | docs/evidence/rescue-stick/RS-003.json |
| RS-004 | Laufwerke erkennen | lsblk/findmnt erfasst | nein | Rot | docs/evidence/rescue-stick/RS-004.json |
| RS-005 | interne Platten read-only | keine Writes | nein | Rot | docs/evidence/rescue-stick/RS-005.json |
| RS-006 | Backups finden | Backup erkannt | nein | Rot | docs/evidence/rescue-stick/RS-006.json |
| RS-007 | Verify ausführen | Verify-Bericht | nein | Rot | docs/evidence/rescue-stick/RS-007.json |
| RS-008 | Abschlussbericht | JSON + Markdown | nein | Rot | docs/evidence/rescue-stick/RS-008.json |

## Read-only-Regeln (verbindlich)

- Keine Schreiboperationen auf interne Systemmedien.  
- Nur Erkennung, Backup-Fund, Verify, Bericht.  
- Restore nur nach separatem Freigabe- und Runbook-Prozess (nicht Gegenstand des ersten Rescue-MVP).
