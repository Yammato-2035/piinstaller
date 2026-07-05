> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/FRONTEND_STATUS_VIEWMODEL_MIGRATION_H2_EN.md`). Bitte bei Release manuell gegenlesen.

# Frontend Status ViewModel Migration — H.2 (EN)

**HEAD:** post H.2 · **Status:** utility migration done

## Migrated files

| File | Function | ViewModel API |
|------|----------|---------------|
| `trafficLight/trafficLightModel.ts` | `worstTrafficLightLamp`, `trafficLightStateToLamp` | `worstTrafficLightLampFromInputs`, `trafficLightLampFromInput` |
| `lib/devDashboard/dccCompactStatus.ts` | `DeployDriftTone` | `dashboardToneFromInput` |
| `pages/devDashboardFilters.ts` | `toneClass` | `dashboardToneFromInput` |

## Neet migrated (H.3)

- Domain `derive*` in trafficLightModel
- Component inline mappings

## Volgende step

**H.3 done** — 3 components. **H.4** or **G.4**.
