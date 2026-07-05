> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H6_EN.md`). Bitte bei Release manuell gegenlesen.

# Frontend Status Component Migration — H.6

**HEAD:** post H.6 · **Status:** presentation + utility slice complete

## Migrated (H.6)

| File | API |
|------|-----|
| `StatusDots.tsx` | Lamp presentation helpers |
| `TrafficLight.tsx` | SVG lamp helpers |
| `TrafficLightBadge.tsx` | `isgeelTrafficLightLamp` |
| `governanceHistory.ts` | `governanceTrafficTransitionKind` |
| `buildStandaloneDashboard.ts` | Standalone ampel helpers |

## Tests

- `statusComponentMigrationH6.test.ts`
- `governanceHistory.test.ts`
- `statusViewModel.test.ts` (12)

## Remaining

15 local mappings → **H.7**

## Volgende step

**H.7** `riskLevels.ts`, `devDashboardFilters` toneClass **or** **G.4**
