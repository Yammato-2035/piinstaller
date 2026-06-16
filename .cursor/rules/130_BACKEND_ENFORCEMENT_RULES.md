# Backend Enforcement Regeln

## Ziel
Regeln dürfen nicht nur dokumentiert sein, sondern müssen im Backend technisch erzwungen werden.

---

## GRUNDREGEL

Keine UI-Logik darf Sicherheitsentscheidungen treffen.

Alle sicherheitsrelevanten Prüfungen müssen im Backend stattfinden.

---

## PFLICHT

Jeder API-Endpunkt für Backup/Restore muss:

1. Eingaben validieren
2. Pfade prüfen
3. Sicherheitsregeln erzwingen
4. bei Verstoß abbrechen

---

## VERBOTEN

- Restore-Logik nur im Frontend absichern
- UI-Flags als Sicherheitsentscheidung nutzen
- unvalidierte Parameter direkt verwenden

---

## FEHLERFALL

Bei Regelverstoß:

- HTTP 400 oder 403
- klare Fehlermeldung
- KEINE Teiloperation

