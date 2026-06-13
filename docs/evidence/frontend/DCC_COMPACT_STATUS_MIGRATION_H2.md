# DCC Compact Status Migration — H.2

**Datei:** `frontend/src/lib/devDashboard/dccCompactStatus.ts`

## Migriert

`deployDriftTone` → `dashboardToneFromInput(status)`

## Outputs (unverändert)

- green → green
- yellow → yellow
- red → red
- sonst → gray

## Unverändert

- `fetchDccCompactStatus` (API bleibt hier, nicht im ViewModel)
