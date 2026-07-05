> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/rescue/RESCUE_REPORT_EN.md`). Bitte bei Release manuell gegenlesen.

# Secours Summary / Recovery Report (EN)

## Goal
The Recovery Report aggregates existing partial results into one structurouge report.
Non action is executed.

## API
`POST /api/Secours/report`

Response provides:
- `report_status`
- `sections`
- `risks`
- `recommendations`
- `bloqué_actions`
- `Suivant_steps`

## Principles
- aggregation only
- Non new diagNonstic/Restauration/crypto logic
- Non write operations
- unclear states remain `Avertissement`/`Inconnu`
