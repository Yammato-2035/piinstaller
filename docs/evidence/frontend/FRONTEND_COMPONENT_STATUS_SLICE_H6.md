# Frontend Component Status Slice — H.6

**Slice:** 5 Dateien (Presentation + Small Utility)

| # | Datei | ViewModel-API |
|---|-------|---------------|
| 1 | `StatusDots.tsx` | `lampDotBackgroundClass`, `lampAreaBorderClass`, `isYellowTrafficLightLamp` |
| 2 | `TrafficLight.tsx` | `svgTrafficLightLampBackground`, `svgTrafficLightLampBoxShadow` |
| 3 | `TrafficLightBadge.tsx` | `isYellowTrafficLightLamp` |
| 4 | `governanceHistory.ts` | `governanceTrafficTransitionKind` |
| 5 | `buildStandaloneDashboard.ts` | `standaloneAmpelFromInput`, `standaloneMatrixCategoryFromAmpel`, `worstStandaloneAmpelOverall` |

## Verbleibend (Presentation)

- `riskLevels.ts` — i18n label mapping

## Output-Garantie

CSS-Klassen, SVG-Farben, Transition-Kinds und Standalone-Kategorien unverändert (1:1).
