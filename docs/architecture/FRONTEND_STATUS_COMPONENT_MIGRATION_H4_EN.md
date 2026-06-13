# Frontend Status Component Migration — H.4

**HEAD:** post H.4 · **Status:** second 3-component slice complete

## Migrated (H.4)

| Component | API |
|-----------|-----|
| `ReadyStableSection` | `isDashboardGreenStatus` |
| `StatusCard` | `dashboardToneFromInput`, `isGreenDashboardTone` |
| `RiskWarningCard` | `riskWarningTitleKeyForLevel` |

## Already migrated (H.3)

| Component | API |
|-----------|-----|
| `RescueDeveloperPipelineCard` | `dashboardLegacyToneFromInput` |
| `ControlCenterOverviewHeader` | `dashboardLegacyToneFromInput` |
| `ManualCommandRunsPanel` | `dashboardLegacyToneFromInput` |

## Rules

- Props/outputs unchanged
- No CSS/layout/color changes
- Domain mappings (partition, backup, safety) stay local until domain facade

## Tests

- `statusComponentMigrationH4.test.ts`
- `statusViewModel.test.ts` (12)

## Remaining

23 local component mappings → **H.5**

## Next step

**H.5** more small components/libs **or** **G.4** Network Handler Extraction
