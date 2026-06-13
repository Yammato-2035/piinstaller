# Frontend Status Component Migration — H.4

**HEAD:** nach H.4 · **Status:** zweiter 3-Komponenten-Slice erledigt

## Migriert (H.4)

| Komponente | API |
|------------|-----|
| `ReadyStableSection` | `isDashboardGreenStatus` |
| `StatusCard` | `dashboardToneFromInput`, `isGreenDashboardTone` |
| `RiskWarningCard` | `riskWarningTitleKeyForLevel` |

## Bereits migriert (H.3)

| Komponente | API |
|------------|-----|
| `RescueDeveloperPipelineCard` | `dashboardLegacyToneFromInput` |
| `ControlCenterOverviewHeader` | `dashboardLegacyToneFromInput` |
| `ManualCommandRunsPanel` | `dashboardLegacyToneFromInput` |

## Regeln

- Props/Outputs unverändert
- Keine CSS-/Layout-/Farb-Änderung
- Domain-Mappings (Partition, Backup, Safety) bleiben lokal bis Domain-Facade

## Tests

- `statusComponentMigrationH4.test.ts`
- `statusViewModel.test.ts` (12)

## Verbleibend

23 lokale Komponenten-Mappings → **H.5**

## Nächster Schritt

**H.5** weitere kleine Komponenten/Libs **oder** **G.4** Network Handler Extraction
