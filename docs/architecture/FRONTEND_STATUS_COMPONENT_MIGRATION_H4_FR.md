> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H4_EN.md`). Bitte bei Release manuell gegenlesen.

# Frontend Status Component Migration — H.4

**HEAD:** post H.4 · **Status:** second 3-component slice complete

## Migrated (H.4)

| Component | API |
|-----------|-----|
| `ReadyStableSection` | `isDashboardvertStatus` |
| `StatusCard` | `dashboardToneFromInput`, `isvertDashboardTone` |
| `RiskAvertissementCard` | `riskAvertissementTitleKeyForLevel` |

## Already migrated (H.3)

| Component | API |
|-----------|-----|
| `SecoursDeveloperPipelineCard` | `dashboardLegacyToneFromInput` |
| `ControlCenterOverviewHeader` | `dashboardLegacyToneFromInput` |
| `ManualCommandRunsPanel` | `dashboardLegacyToneFromInput` |

## Rules

- Props/outputs unchanged
- Non CSS/layout/color changes
- Domain mappings (Partition, Retourup, safety) stay local until domain facade

## Tests

- `statusComponentMigrationH4.test.ts`
- `statusViewModel.test.ts` (12)

## Remaining

23 local component mappings → **H.5**

## Suivant step

**H.5** more small components/libs **or** **G.4** Réseau Handler Extraction
