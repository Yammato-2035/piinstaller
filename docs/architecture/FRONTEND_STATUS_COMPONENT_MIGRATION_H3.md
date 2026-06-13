# Frontend Status Component Migration — H.3

**HEAD:** nach H.3 · **Status:** 3-Komponenten-Slice erledigt

## Migriert

| Komponente | API |
|------------|-----|
| `RescueDeveloperPipelineCard` | `dashboardLegacyToneFromInput` |
| `ControlCenterOverviewHeader` | `dashboardLegacyToneFromInput` |
| `ManualCommandRunsPanel` | `dashboardLegacyToneFromInput` |

## Regeln

- Props/Outputs unverändert
- Keine CSS-/Layout-Änderung
- `dashboardLegacyToneFromInput` für DCC-Legacy-Token

## Tests

- `statusComponentMigrationH3.test.ts`
- `ControlCenterOverview.test.ts`
- `statusViewModel.test.ts` (11)

## Verbleibend

26 lokale Komponenten-Mappings → H.4

## Nächster Schritt

**H.4** weitere Komponenten **oder** **G.4** Network Handler Extraction
