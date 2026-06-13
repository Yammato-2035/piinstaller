# Frontend Status ViewModel Migration — H.2

**HEAD:** nach H.2 · **Status:** Utility-Migration erledigt

## Migrierte Dateien

| Datei | Funktion | ViewModel-API |
|-------|----------|---------------|
| `trafficLight/trafficLightModel.ts` | `worstTrafficLightLamp`, `trafficLightStateToLamp` | `worstTrafficLightLampFromInputs`, `trafficLightLampFromInput` |
| `lib/devDashboard/dccCompactStatus.ts` | `deployDriftTone` | `dashboardToneFromInput` |
| `pages/devDashboardFilters.ts` | `toneClass` | `dashboardToneFromInput` |

## Neue ViewModel-Helfer

- `dashboardToneFromInput`
- `trafficLightLampFromInput`
- `worstTrafficLightLampFromInputs`

## Nicht migriert (H.3)

- Domain-`derive*` in trafficLightModel
- `buildStandaloneDashboard.normalizeAmpel`
- Komponenten mit inline Mapping

## Tests

Vitest 18 Tests (statusViewModel, trafficLightModel, dccCompactStatus, devDashboardFilters)

## Nächster Schritt

**H.3 erledigt** — 3 Komponenten. **H.4** oder **G.4**.
