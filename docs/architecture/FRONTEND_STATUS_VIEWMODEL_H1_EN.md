# Frontend Status ViewModel — H.1 (EN)

**HEAD:** post H.1 · **Status:** CANONICAL_MODULE (VIEWMODEL)

## Module

`frontend/src/viewmodels/statusViewModel.ts` · `VIEWMODEL_VERSION = 1`

## Public API

| Function | Purpose |
|----------|---------|
| `normalizeStatusKind(input)` | Input → `StatusKind` |
| `buildStatusViewModel(input)` | Generic view model |
| `buildTrafficLightViewModel(input)` | Traffic-light strings |
| `buildDashboardStatusViewModel(input)` | DCC/dashboard tones |
| `worstStatusViewModel(models)` | Worst status by sortRank |

## Rules

- No API fetches
- No CSS/design changes
- No component migration in H.1 (`no_component_migration_h1`)

## Next step

**H.2 done** — see [FRONTEND_STATUS_VIEWMODEL_MIGRATION_H2_EN.md](FRONTEND_STATUS_VIEWMODEL_MIGRATION_H2_EN.md). **H.3** component migration.
