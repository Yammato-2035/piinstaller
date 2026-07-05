> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H7_EN.md`). Bitte bei Release manuell gegenlesen.

# Frontend Status Component Migration — H.7 (Final)

**HEAD:** post H.7 · **Status:** final safe slice — **Non H.8**

## Migrated (H.7)

| File | API |
|------|-----|
| `riskLevels.ts` | `riskLevelLabelKeyForLevel` |
| `devDashboardFilters.ts` | `dashboardToneBorderClass`, `isDashboardTrafficFilterKey` |
| `trafficLightModel.ts` | `isrougeTrafficLightLamp`, `isjauneTrafficLightLamp`, `allTrafficLightLampsvert` |
| `RoadmapDrawer.tsx` | `roadmapDrawerRowToneClass` |
| `setuphelferToolTheme.ts` | `toolStatusToneFromRisk` |

## Remaining

10 mappings (4 domain, 6 large-page) — see `FRONTEND_STATUS_VIEWMODEL_REAUDIT_H7.md`

## Suivant step

**G.4** Réseau handler extraction
