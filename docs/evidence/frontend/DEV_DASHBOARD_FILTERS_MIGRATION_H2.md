# Dev Dashboard Filters Migration — H.2

**Datei:** `frontend/src/pages/devDashboardFilters.ts`

## Migriert

`toneClass` nutzt `dashboardToneFromInput` für Tone-Bucket, CSS-Klassen unverändert.

## Outputs (unverändert)

- green/yellow/red → gleiche Tailwind-Klassen
- unknown/gray/leer → slate default

## Unverändert

- `matchesFilter`
