# Frontend Status ViewModel Migration — H.2 (EN)

**HEAD:** post H.2 · **Status:** utility migration done

## Migrated files

| File | Function | ViewModel API |
|------|----------|---------------|
| `trafficLight/trafficLightModel.ts` | `worstTrafficLightLamp`, `trafficLightStateToLamp` | `worstTrafficLightLampFromInputs`, `trafficLightLampFromInput` |
| `lib/devDashboard/dccCompactStatus.ts` | `deployDriftTone` | `dashboardToneFromInput` |
| `pages/devDashboardFilters.ts` | `toneClass` | `dashboardToneFromInput` |

## Not migrated (H.3)

- Domain `derive*` in trafficLightModel
- Component inline mappings

## Next step

**H.3** — component migration **or** **G.4** network handler extraction
