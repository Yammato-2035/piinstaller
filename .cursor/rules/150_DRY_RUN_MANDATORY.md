# Dry-Run Pflicht

## Ziel
Alle kritischen Operationen müssen simulierbar sein.

---

## PFLICHT

Folgende Operationen benötigen einen Dry-Run:

- Restore
- Löschen
- Überschreiben

---

## DRY-RUN MUSS

- identische Logik verwenden
- KEINE Änderungen schreiben
- Ergebnis anzeigen:
  - welche Dateien betroffen wären
  - welche Pfade verändert würden

---

## UI

Dry-Run muss sichtbar sein:
- "Testlauf"
- "Simulation"
- "keine Änderungen"

---

## VERBOTEN

- Testmodus ohne echte Logik
- Fake-Simulation

---

## STATUS

Kein Dry-Run:
→ Feature nicht freigabefähig

