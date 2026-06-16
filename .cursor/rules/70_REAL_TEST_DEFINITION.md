# Real-Test Definition (verbindlich)

## Ziel
Ein Feature gilt nur dann als fertig, wenn es real getestet wurde.

---

## WAS IST EIN REAL-TEST

Ein Real-Test bedeutet:

- echte Dateien
- echte Pfade
- echte Ausführung
- echtes Ergebnis

Nicht ausreichend:
- Code lesen
- Simulation ohne reale Wirkung
- nur Fehlerfälle

---

## MINDESTANFORDERUNGEN BACKUP/RESTORE

### Verify

- gültiges Backup prüfen
- ungültigen Pfad prüfen
- beschädigtes Backup prüfen

### Restore

- Restore in kontrolliertes Testverzeichnis
- Ergebnis prüfen:
  - Dateien vorhanden
  - Struktur korrekt

---

## DOKUMENTATIONSPFLICHT

Jeder Test muss dokumentieren:

- Eingabedatei
- Zielpfad
- ausgeführter Befehl
- Ergebnis
- Fehlerfälle

---

## STATUS

Wenn kein Real-Test:
→ Feature ist NICHT FERTIG

Wenn nur Teiltests:
→ GELB

Wenn vollständig getestet:
→ GRÜN

