> **Phase-1 Übersetzungsmarathon** — Deutsch (automatisch aus `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H7_EN.md`). Bitte bei Release manuell gegenlesen.

# Frontend Stand Component Migration — H.7 (Final)

**HEAD:** post H.7 · **Stand:** final safe slice — **no H.8**

## Migrated (H.7)

| File | API |
|------|-----|
| `riskLevels.ts` | `riskLevelLabelKeyForLevel` |
| `devDashboardFilters.ts` | `dashboardToneBorderClass`, `isDashboardTrafficFilterKey` |
| `trafficLightModel.ts` | `isRedTrafficLightLamp`, `isYellowTrafficLightLamp`, `allTrafficLightLampsGreen` |
| `RoadmapDrawer.tsx` | `roadmapDrawerRowToneClass` |
| `setuphelferToolTheme.ts` | `toolStandToneFromRisk` |

## Remaining

10 mappings (4 domain, 6 large-page) — see `FRONTEND_STATUS_VIEWMODEL_REAUDIT_H7.md`

## Next step

**G.4** network handler extraction
