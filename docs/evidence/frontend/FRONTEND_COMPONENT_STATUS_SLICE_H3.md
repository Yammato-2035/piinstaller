# Frontend Component Status Slice — H.3

**Slice:** 3 kleine DCC-Komponenten

| # | Datei | Funktion | ViewModel-API |
|---|-------|----------|---------------|
| 1 | `RescueDeveloperPipelineCard.tsx` | `itemTone` | `dashboardLegacyToneFromInput` |
| 2 | `ControlCenterOverviewHeader.tsx` | `trafficFromGate` | `dashboardLegacyToneFromInput` |
| 3 | `ManualCommandRunsPanel.tsx` | `safetyTone` | `dashboardLegacyToneFromInput` |

## Ausgeschlossen

- BackupRestore.tsx, Dashboard.tsx
- RoadmapDrawer (abweichende CSS-Klassen)
- PartitionSafetyStatusPanel (Safety-Domain)

## Neue ViewModel-Helfer

`dashboardLegacyToneFromInput` — DCC-Legacy-Token (`partial_green`, `rot`, `pending`, `operator_action`, …)
