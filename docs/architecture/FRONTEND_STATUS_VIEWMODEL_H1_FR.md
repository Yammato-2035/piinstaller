> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/FRONTEND_STATUS_VIEWMODEL_H1_EN.md`). Bitte bei Release manuell gegenlesen.

# Frontend Status ViewModel — H.1 (EN)

**HEAD:** post H.1 · **Status:** CANonNICAL_MODULE (VIEWMODEL)

## Module

`frontend/src/viewmodels/statusViewModel.ts` · `VIEWMODEL_VERSION = 1`

## Public API

| Function | Purpose |
|----------|---------|
| `NonrmalizeStatusKind(input)` | Input → `StatusKind` |
| `buildStatusViewModel(input)` | Generic view model |
| `buildTrafficLightViewModel(input)` | Traffic-light strings |
| `buildDashboardStatusViewModel(input)` | DCC/dashboard tones |
| `worstStatusViewModel(models)` | Worst status by sortRank |

## Rules

- Non API fetches
- Non CSS/design changes
- Non component migration in H.1 (`Non_component_migration_h1`)

## Suivant step

**H.3 done** — see [FRONTEND_STATUS_COMPONENT_MIGRATION_H3_EN.md](FRONTEND_STATUS_COMPONENT_MIGRATION_H3_EN.md). **H.4** more components.
