> **Phase-1 Übersetzungsmarathon** — Deutsch (automatisch aus `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H4_EN.md`). Bitte bei Release manuell gegenlesen.

# Frontend Stand Component Migration — H.4

**HEAD:** post H.4 · **Stand:** second 3-component slice complete

## Migrated (H.4)

| Component | API |
|-----------|-----|
| `ReadyStableSection` | `isDashboardGreenStand` |
| `StandCard` | `dashboardToneFromInput`, `isGreenDashboardTone` |
| `RiskWarningCard` | `riskWarningTitleKeyForLevel` |

## Already migrated (H.3)

| Component | API |
|-----------|-----|
| `RettungDeveloperPipelineCard` | `dashboardLegacyToneFromInput` |
| `ControlCenterÜberblickHeader` | `dashboardLegacyToneFromInput` |
| `ManualCommandRunsPanel` | `dashboardLegacyToneFromInput` |

## Regeln

- Props/outputs unchanged
- No CSS/layout/color changes
- Domain mappings (partition, backup, safety) stay local until domain facade

## Tests

- `statusComponentMigrationH4.test.ts`
- `statusViewModel.test.ts` (12)

## Remaining

23 local component mappings → **H.5**

## Next step

**H.5** more small components/libs **or** **G.4** Network Handler Extraktion
