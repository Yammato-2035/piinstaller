> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/rescue/RESCUE_REPORT_EN.md`). Bitte bei Release manuell gegenlesen.

# roodding Summary / Recovery Report (EN)

## Goal
The Recovery Report aggregates existing partial results into one structurood report.
Nee action is executed.

## API
`POST /api/roodding/report`

Response provides:
- `report_status`
- `sections`
- `risks`
- `recommendations`
- `geblokkeerd_actions`
- `Volgende_steps`

## Principles
- aggregation only
- Nee new diagNeestic/Herstel/crypto logic
- Nee write operations
- unclear states remain `Waarschuwing`/`Onbekend`
