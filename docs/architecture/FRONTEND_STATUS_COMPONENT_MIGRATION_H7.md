# Frontend Status Component Migration — H.7 (Final)

**HEAD:** nach H.7 · **Status:** finaler Safe-Slice — **kein H.8**

## Migriert (H.7)

| Datei | API |
|-------|-----|
| `riskLevels.ts` | `riskLevelLabelKeyForLevel` |
| `devDashboardFilters.ts` | `dashboardToneBorderClass`, `isDashboardTrafficFilterKey` |
| `trafficLightModel.ts` | `isRedTrafficLightLamp`, `isYellowTrafficLightLamp`, `allTrafficLightLampsGreen` |
| `RoadmapDrawer.tsx` | `roadmapDrawerRowToneClass` |
| `setuphelferToolTheme.ts` | `toolStatusToneFromRisk` |

## Verbleibend

10 Mappings (4 Domain, 6 Large-Page) — siehe `FRONTEND_STATUS_VIEWMODEL_REAUDIT_H7.md`

## Nächster Schritt

**G.4** Network Handler Extraction
