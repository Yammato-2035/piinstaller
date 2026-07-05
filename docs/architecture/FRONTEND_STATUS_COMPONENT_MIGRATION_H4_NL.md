> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H4_EN.md`). Bitte bei Release manuell gegenlesen.

# Frontend Status Component Migration — H.4

**HEAD:** post H.4 · **Status:** second 3-component slice complete

## Migrated (H.4)

| Component | API |
|-----------|-----|
| `ReadyStableSection` | `isDashboardgroenStatus` |
| `StatusCard` | `dashboardToneFromInput`, `isgroenDashboardTone` |
| `RiskWaarschuwingCard` | `riskWaarschuwingTitleKeyForLevel` |

## Already migrated (H.3)

| Component | API |
|-----------|-----|
| `rooddingDeveloperPipelineCard` | `dashboardLegacyToneFromInput` |
| `ControlCenterOverviewHeader` | `dashboardLegacyToneFromInput` |
| `ManualCommandRunsPanel` | `dashboardLegacyToneFromInput` |

## Rules

- Props/outputs unchanged
- Nee CSS/layout/color changes
- Domain mappings (Partitie, Terugup, safety) stay local until domain facade

## Tests

- `statusComponentMigrationH4.test.ts`
- `statusViewModel.test.ts` (12)

## Remaining

23 local component mappings → **H.5**

## Volgende step

**H.5** more small components/libs **or** **G.4** Netwerk Handler Extraction
