# Rescue Summary / Recovery Report (DE)

## Ziel
Der Recovery Report aggregiert bestehende Teilergebnisse in einen strukturierten Gesamtbericht.
Es werden keine Aktionen gestartet.

## API
`POST /api/rescue/report`

Response liefert:
- `report_status`
- `sections`
- `risks`
- `recommendations`
- `blocked_actions`
- `next_steps`

## Prinzipien
- rein aggregierend
- keine neue Diagnose-/Restore-/Crypto-Logik
- keine Schreiboperation
- unklare Zustände bleiben `warning`/`unknown`
