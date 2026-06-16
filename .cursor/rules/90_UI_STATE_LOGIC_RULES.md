# UI Zustandslogik (verbindlich)

## Ziel
UI zeigt immer den Zustand, nicht nur Funktionen.

---

## GRUNDREGEL

ZUSTAND → EMPFEHLUNG → AKTION

---

## VERBOTEN

- Aktionen ohne Kontext
- leere Buttons ohne Statusbezug
- mehrere gleichwertige Primäraktionen

---

## PFLICHT

Jede Aktion muss:

- einen Zustand referenzieren
- eine klare Empfehlung enthalten

---

## BEISPIEL

Falsch:
"Backup starten"

Richtig:
"Kein Backup vorhanden → Backup erstellen"

---

## PRIORITÄT

- Zustand IMMER sichtbar
- Aktionen nachgeordnet

