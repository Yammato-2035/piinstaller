# Restore Sandbox Regeln

## Ziel
Restore darf niemals direkt destruktiv sein.

---

## PFLICHT

Jeder Restore läuft zuerst in einer sicheren Umgebung:

- temporäres Verzeichnis (z. B. /tmp/setuphelfer_restore_test)
- oder definierte Sandbox (z. B. /home/*/restore_test)

---

## VERBOTEN

- direkter Restore in produktive Pfade
- Überschreiben ohne vorherige Simulation

---

## TESTPHASE

Restore muss zuerst:

1. entpacken
2. Struktur prüfen
3. Ergebnis validieren

---

## FREIGABE

Erst nach erfolgreichem Test:

→ optionaler echter Restore

---

## STATUS

Kein Sandbox-Test:
→ Ampel ROT

