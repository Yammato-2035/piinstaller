> **Phase-1 Übersetzungsmarathon** — Deutsch (automatisch aus `docs/architecture/FRONTEND_STATUS_VIEWMODEL_H1_EN.md`). Bitte bei Release manuell gegenlesen.

# Frontend Stand ViewModel — H.1 (EN)

**HEAD:** post H.1 · **Stand:** CANONICAL_MODULE (VIEWMODEL)

## Module

`frontend/src/viewmodels/statusViewModel.ts` · `VIEWMODEL_VERSION = 1`

## Public API

| Function | Purpose |
|----------|---------|
| `normalizeStandKind(input)` | Input → `StandKind` |
| `buildStandViewModel(input)` | Generic view model |
| `buildTrafficLightViewModel(input)` | Traffic-light strings |
| `buildDashboardStandViewModel(input)` | DCC/dashboard tones |
| `worstStandViewModel(models)` | Worst status by sortRank |

## Regeln

- No API fetches
- No CSS/design changes
- No component migration in H.1 (`no_component_migration_h1`)

## Next step

**H.3 done** — see [FRONTEND_STATUS_COMPONENT_MIGRATION_H3_EN.md](FRONTEND_STATUS_COMPONENT_MIGRATION_H3_EN.md). **H.4** more components.
