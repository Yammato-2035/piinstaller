# HW-EXEC-1 Report (Externe NVMe)

Scope: nur `HW1-01` bis `HW1-05` auf externer NVMe.  
Wichtig: reale Ausfuehrung, keine Erfolgssimulation.

## Ergebnisuebersicht

- HW1-01: **failed** -> `EVID-2026-HW1-01`
- HW1-02: **failed** -> `EVID-2026-HW1-02`
- HW1-03: **failed** -> `EVID-2026-HW1-03`
- HW1-04: **failed** -> `EVID-2026-HW1-04`
- HW1-05: **inconclusive** -> `EVID-2026-HW1-05`

## Pro-Test Bewertung (Pflichtfragen)

### HW1-01
- Diagnose plausibel: ja (`PERM-GROUP-008`, `OWNER-MODE-023`).
- Ursache korrekt: ja, Zielpfad nicht beschreibbar fuer Backend-User.
- Neue Diagnose noetig: nein.
- FAQ erweitern: nein.

### HW1-02
- Diagnose plausibel: ja (gleiches Rechteproblem wie HW1-01).
- Ursache korrekt: ja, Verschluesselungspfad wurde gar nicht erreicht.
- Neue Diagnose noetig: nein.
- FAQ erweitern: nein.

### HW1-03
- Diagnose plausibel: ja (`permission denied` beim List/Verify-Vorlauf).
- Ursache korrekt: ja, Lesezugriff auf Backup-Mount blockiert.
- Neue Diagnose noetig: nein.
- FAQ erweitern: nein.

### HW1-04
- Diagnose plausibel: ja (`no_new_privileges` blockiert sudo).
- Ursache korrekt: ja, Restore-Pfad stoppt vor eigentlicher Preview.
- Neue Diagnose noetig: **ja** -> `SYSTEMD-NNP-031` angelegt.
- FAQ erweitern: noch nicht (zunaechst weitere Evidenz sammeln).

### HW1-05
- Diagnose plausibel: ja (`APP-030` / Kette nicht validierbar).
- Ursache korrekt: ja, Vorbedingungen aus HW1-01..04 nicht erfuellt.
- Neue Diagnose noetig: nein.
- FAQ erweitern: nein.

## Abbruch-/Sicherheitsregel

Bei kritischen Fehlern wurde kein undokumentiertes Weiterprobieren durchgefuehrt.
Jeder Test hat genau einen eigenen EvidenceRecord erhalten.
