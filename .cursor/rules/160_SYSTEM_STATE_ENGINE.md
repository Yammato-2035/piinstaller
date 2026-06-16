# System State Engine

## Ziel
Alle Statusinformationen kommen aus einer zentralen Quelle.

---

## PROBLEM AKTUELL

- Dashboard zeigt Zustand
- Backend kennt Zustand
- aber keine zentrale Logik

→ Inkonsistenz-Risiko

---

## LÖSUNG

Zentrale Statuslogik im Backend:

Beispiel:

{
  "backup": "yellow",
  "restore": "red",
  "security": "yellow",
  "updates": "green"
}

---

## PFLICHT

Frontend darf:

- Status anzeigen
- NICHT berechnen

---

## VERBOTEN

- Status im Frontend bestimmen
- mehrere Statusquellen

---

## API

Neue Route:

GET /api/system/status

---

## STATUSLOGIK

Backend bestimmt:

- GRÜN → alles ok
- GELB → teilweise ok
- ROT → kritisch

