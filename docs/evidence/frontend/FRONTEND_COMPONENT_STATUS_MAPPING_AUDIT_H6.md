# Frontend Component Status Mapping Audit — H.6

**HEAD:** efefca4 (vor H.6) · **Baseline:** `frontend_component_local_status_mapping:count_20`

| Datei | Klassifikation | Hinweis |
|-------|----------------|---------|
| `StatusDots.tsx` | **PRESENTATION** | H.6 erledigt → `lampDotBackgroundClass`, … |
| `TrafficLight.tsx` | **PRESENTATION** | H.6 erledigt → `svgTrafficLightLampBackground`, … |
| `TrafficLightBadge.tsx` | **PRESENTATION** | H.6 erledigt → `isYellowTrafficLightLamp` |
| `governanceHistory.ts` | **SAFE** | H.6 erledigt → `governanceTrafficTransitionKind` |
| `buildStandaloneDashboard.ts` | **SAFE** | H.6 erledigt → `standaloneAmpelFromInput`, … |
| `governanceMatrix.ts` | **already_migrated** | H.5 |
| `roadmapFilter.ts` | **already_migrated** | H.5 |
| `riskLevels.ts` | **PRESENTATION** | i18n labelKeys — H.7 |
| `devDashboardFilters.ts` | **PRESENTATION** | toneClass CSS — teilweise H.2 |
| `trafficLightModel.ts` | **PRESENTATION** | Domain derive — H.2 Utility |
| `RoadmapDrawer.tsx` | **UNSAFE_LARGE_PAGE** | Eigene Tailwind |
| `CockpitBackupTargetPanel.tsx` | **DOMAIN_SPECIFIC** | Backup |
| `PartitionSafetyStatusPanel.tsx` | **DOMAIN_SPECIFIC** | Safety |
| `PartitionSafetyPreviewPanel.tsx` | **DOMAIN_SPECIFIC** | Partition |
| `partitionRoleUtils.ts` | **DOMAIN_SPECIFIC** | Partition |
| `setuphelferToolTheme.ts` | **DOMAIN_SPECIFIC** | Theme |
| `Dashboard.tsx` | **UNSAFE_LARGE_PAGE** | Ausgeschlossen |
| `BackupRestore.tsx` | **UNSAFE_LARGE_PAGE** | Ausgeschlossen |
| `ExternalDevelopmentControlCenter.tsx` | **UNSAFE_LARGE_PAGE** | Ausgeschlossen |
| `DevDashboardBody.tsx` | **UNSAFE_LARGE_PAGE** | Große Seite |
| `SecuritySetup.tsx` | **UNSAFE_LARGE_PAGE** | Ausgeschlossen |
| `MonitoringDashboard.tsx` | **UNSAFE_LARGE_PAGE** | Ausgeschlossen |

**Nach H.6:** `count_15` (20 − 5)
