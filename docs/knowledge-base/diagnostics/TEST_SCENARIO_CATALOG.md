# Test Scenario Catalog (DIAG-1.1)

Alle Szenarien sind als strukturierte Testziele zu fuehren; Fehler/Abweichungen muessen als Evidence gespeichert werden.

## Backup / Restore

- **Szenario:** Backup auf USB-Stick  
  **Ziel:** Schreib-/Verify-Faehigkeit pruefen  
  **Signale:** target writable, verify ok  
  **Diagnosefaelle:** `FS-RO-021`, `FS-FULL-022`, `PERM-GROUP-008`

- **Szenario:** Backup auf externer NVMe  
  **Ziel:** Performance + Integritaet bei grossem Medium  
  **Signale:** verify deep ok, keine hash mismatches  
  **Diagnosefaelle:** `BACKUP-HASH-003`, `BACKUP-ARCHIVE-002`

- **Szenario:** Restore auf gleiches System  
  **Ziel:** deterministischer Zielzustand inkl. Service-Start  
  **Signale:** restore result + runtime checks  
  **Diagnosefaelle:** `RESTORE-PARTIAL-005`, `RESTORE-RUNTIME-006`

- **Szenario:** Restore auf neues System  
  **Ziel:** Portabilitaet + Bootvalidierung  
  **Signale:** bootability class, service reachability  
  **Diagnosefaelle:** `PI-BOOT-024`, `UI-NO-BACKEND-015`

- **Szenario:** Verify mit beschaedigtem Archiv  
  **Ziel:** fail-fast und klare Fehlerklassifikation  
  **Diagnosefaelle:** `BACKUP-ARCHIVE-002`

- **Szenario:** Restore mit fehlendem Manifest  
  **Ziel:** Restore sicher blockieren  
  **Diagnosefaelle:** `BACKUP-MANIFEST-001`

- **Szenario:** Restore mit fehlerhaften Rechten  
  **Ziel:** Gruppenmodell statt manueller Workarounds validieren  
  **Diagnosefaelle:** `PERM-GROUP-008`, `OWNER-MODE-023`

- **Szenario:** Restore auf `/tmp` / tmpfs  
  **Ziel:** unpassendes Zielmedium erkennen  
  **Diagnosefaelle:** `RESTORE-TMPFS-007`, `FS-FULL-022`

- **Szenario:** Verschluesseltes Backup/Restore (Key vorhanden/fehlend/falsch)  
  **Ziel:** sichere Schluesselpfade und klare Blocker  
  **Diagnosefaelle:** `BACKUP-ARCHIVE-002`, `RESTORE-PATH-004`

## Rettungsmedien

- Linux-Rescue-Stick, Raspberry-Pi-Rettungsmedium, Bootstick mit Diagnosefunktionen.
- Boot-Reparaturfaelle.
- Medienwechsel/Zielwechsel.
- USB-Controller-/Erkennungsprobleme.

Pro Fall sind festzuhalten:

- Voraussetzungen
- eingesetzte Hardware
- erwartete Signale
- moegliche Diagnosefaelle
- Abbruchkriterien
- Wissensbasis-Update-Pflicht

## Plattformmatrix

- Raspberry Pi 5
- Linux-Laptop
- Linux-PC
- VM
- externe USB-Medien
- externe NVMe
- SD-Karten

## HW-TEST-1 (vor Pi-Freigabe)

Verbindliche Hardwarephase fuer Linux-Laptop mit Wechselmedien:

- Matrix: `docs/knowledge-base/test-evidence/HW_TEST_1_MATRIX.md`
- maschinenlesbar: `data/diagnostics/hw_test_1_matrix.json`
- Durchfuehrung: `docs/knowledge-base/test-evidence/HW_TEST_1_EXECUTION_GUIDE.md`
- Pi-Gate: `docs/knowledge-base/test-evidence/HW_TEST_1_PI_RELEASE_GATE.md`

Pflicht:

- Kein Pi-Haupttest ohne erfuellte HW-TEST-1-Freigabekriterien.
- Jeder reale Lauf erzeugt mindestens einen EvidenceRecord.
- `planned` ist kein Erfolg.
