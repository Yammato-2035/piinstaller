# Frontend Status ViewModel — H.1

**HEAD:** nach H.1 · **Status:** CANONICAL_MODULE (VIEWMODEL)

## Modul

`frontend/src/viewmodels/statusViewModel.ts` · `VIEWMODEL_VERSION = 1`

## Öffentliche API

| Funktion | Zweck |
|----------|-------|
| `normalizeStatusKind(input)` | Eingabe → `StatusKind` |
| `buildStatusViewModel(input)` | Generisches ViewModel |
| `buildTrafficLightViewModel(input)` | Ampel-Strings (green/yellow/red) |
| `buildDashboardStatusViewModel(input)` | DCC/Dashboard-Töne |
| `worstStatusViewModel(models)` | Schlechtester Status (sortRank) |

## Statuswerte

**StatusKind:** ok, warning, degraded, blocked, unavailable, unknown

**StatusSeverity:** info, success, warning, danger, neutral

## Regeln

- Keine API-Fetches
- Kein CSS/Design
- Keine Komponentenmigration in H.1 (`no_component_migration_h1`)

## Tests

`frontend/src/viewmodels/statusViewModel.test.ts` — Vitest 7 Tests

## Nächster Schritt

**H.2** — schrittweise Komponentenmigration (`trafficLightModel`, `dccCompactStatus`, `toneClass`)

Evidence: [FRONTEND_STATUS_MAPPING_AUDIT_H1.md](../evidence/frontend/FRONTEND_STATUS_MAPPING_AUDIT_H1.md)
