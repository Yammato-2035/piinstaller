# API Contract Regeln

## Ziel
Klare, stabile Schnittstellen zwischen Frontend und Backend

---

## PFLICHT

Jede API muss:

- definierte Request-Struktur haben
- definierte Response-Struktur haben
- Fehler klar definieren

---

## RESPONSE STANDARD

{
  "status": "ok|warning|error",
  "message": "...",
  "data": {}
}

---

## VERBOTEN

- uneinheitliche Antworten
- fehlende Fehlercodes
- unklare Statuswerte

---

## BACKUP/RESTORE SPEZIFISCH

Verify:

- valid
- invalid
- error

Restore:

- preview
- success
- aborted

