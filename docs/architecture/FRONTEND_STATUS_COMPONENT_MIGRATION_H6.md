# Frontend Status Component Migration — H.6

**HEAD:** nach H.6 · **Status:** Presentation + Utility Slice erledigt

## Migriert (H.6)

| Datei | API |
|-------|-----|
| `StatusDots.tsx` | Lamp presentation helpers |
| `TrafficLight.tsx` | SVG lamp helpers |
| `TrafficLightBadge.tsx` | `isYellowTrafficLightLamp` |
| `governanceHistory.ts` | `governanceTrafficTransitionKind` |
| `buildStandaloneDashboard.ts` | Standalone ampel helpers |

## Tests

- `statusComponentMigrationH6.test.ts`
- `governanceHistory.test.ts`
- `statusViewModel.test.ts` (12)

## Verbleibend

15 lokale Mappings → **H.7**

## Nächster Schritt

**H.7** `riskLevels.ts`, `devDashboardFilters` toneClass **oder** **G.4**
