# Frontend Component Status Mapping Audit — H.7

**HEAD:** 2ac97be (vor H.7) · **Baseline:** `frontend_component_local_status_mapping:count_15`

| Datei | Klassifikation | H.7 |
|-------|----------------|-----|
| `riskLevels.ts` | **PRESENTATION** | migriert → `riskLevelLabelKeyForLevel` |
| `devDashboardFilters.ts` | **PRESENTATION** | migriert → `dashboardToneBorderClass`, `isDashboardTrafficFilterKey` |
| `trafficLightModel.ts` | **PRESENTATION** | migriert → `isRedTrafficLightLamp`, `allTrafficLightLampsGreen` |
| `RoadmapDrawer.tsx` | **PRESENTATION** | migriert → `roadmapDrawerRowToneClass` |
| `setuphelferToolTheme.ts` | **PRESENTATION** | migriert → `toolStatusToneFromRisk` |
| `PartitionSafetyStatusPanel.tsx` | **DOMAIN_SPECIFIC** | verbleibt |
| `PartitionSafetyPreviewPanel.tsx` | **DOMAIN_SPECIFIC** | verbleibt |
| `CockpitBackupTargetPanel.tsx` | **DOMAIN_SPECIFIC** | verbleibt |
| `partitionRoleUtils.ts` | **DOMAIN_SPECIFIC** | verbleibt |
| `Dashboard.tsx` | **UNSAFE_LARGE_PAGE** | ausgeschlossen |
| `BackupRestore.tsx` | **UNSAFE_LARGE_PAGE** | ausgeschlossen |
| `ExternalDevelopmentControlCenter.tsx` | **UNSAFE_LARGE_PAGE** | ausgeschlossen |
| `DevDashboardBody.tsx` | **UNSAFE_LARGE_PAGE** | ausgeschlossen |
| `SecuritySetup.tsx` | **UNSAFE_LARGE_PAGE** | ausgeschlossen |
| `MonitoringDashboard.tsx` | **UNSAFE_LARGE_PAGE** | ausgeschlossen |

**Nach H.7:** `count_10` (15 − 5) · **Kein weiterer Frontend-Slice geplant**
