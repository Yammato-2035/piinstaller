# Frontend Component Status Mapping Audit — H.4

**HEAD:** 7e058fb (vor H.4) · **Baseline:** `frontend_component_local_status_mapping:count_26`

| Datei | Funktion | Bewertung | Hinweis |
|-------|----------|-----------|---------|
| `ReadyStableSection.tsx` | `isGreenStatus` | **migrate_now** | → `isDashboardGreenStatus` (H.4 erledigt) |
| `StatusCard.tsx` | `isOk` | **migrate_now** | → `isGreenDashboardTone` + `dashboardToneFromInput` (H.4 erledigt) |
| `RiskWarningCard.tsx` | `defaultTitle` | **migrate_now** | → `riskWarningTitleKeyForLevel` (H.4 erledigt) |
| `RescueDeveloperPipelineCard.tsx` | `itemTone` | **already_migrated** | H.3 |
| `ControlCenterOverviewHeader.tsx` | `trafficFromGate` | **already_migrated** | H.3 |
| `ManualCommandRunsPanel.tsx` | `safetyTone` | **already_migrated** | H.3 |
| `trafficLight/trafficLightModel.ts` | derive* | **already_migrated** | H.2 Utility |
| `devDashboardFilters.ts` | `toneClass` | **already_migrated** | H.2 (CSS-Bucket) |
| `governanceMatrix.ts` | `normTraffic` | **migrate_now** | H.5-Kandidat (Lib) |
| `roadmapFilter.ts` | `statusBucket` | **keep_until_page_slice** | `partial_green`→green-Bucket, abweichend von Legacy-Tone |
| `RoadmapDrawer.tsx` | `toneForStatus` | **keep_until_page_slice** | Eigene Tailwind-Klassen |
| `DocumentationDiagnosticsCard.tsx` | docsTone/diagTone | **domain_specific_allowed** | Domain-Heuristik |
| `CockpitBackupTargetPanel.tsx` | traffic className | **domain_specific_allowed** | Backup-Domain |
| `PartitionSafetyStatusPanel.tsx` | risk levels | **domain_specific_allowed** | Safety/Restore-Domain |
| `PartitionSafetyPreviewPanel.tsx` | risk CSS | **domain_specific_allowed** | Partition-Domain |
| `partitionRoleUtils.ts` | risk_level | **domain_specific_allowed** | Partition-Domain |
| `setuphelferToolTheme.ts` | risk→theme | **domain_specific_allowed** | Theme-Domain |
| `companions/StatusDots.tsx` | LampDot | **local_allowed** | Darstellung |
| `companions/TrafficLight.tsx` | lamp CSS | **local_allowed** | Darstellung |
| `TrafficLightBadge.tsx` | quiet | **local_allowed** | `lamp === 'yellow'` nur Quiet-Flag |
| `riskLevels.ts` | i18n labels | **local_allowed** | Kein Tone-String |
| `buildGovernancePrompt.ts` | area filter | **keep_until_page_slice** | Governance-Prompt-Lib |
| `buildStandaloneDashboard.ts` | ampel→category | **keep_until_page_slice** | Standalone-Export |
| `governanceHistory.ts` | transition | **keep_until_page_slice** | Zustandsübergänge |
| `ExternalDevelopmentControlCenter.tsx` | `trafficDot` | **keep_until_page_slice** | Große Seite |
| `DevDashboardBody.tsx` | inline tones | **keep_until_page_slice** | Große Seite |
| `SecuritySetup.tsx` | security lamp | **keep_until_page_slice** | Seite |
| `MonitoringDashboard.tsx` | overall lamp | **keep_until_page_slice** | Seite |
| `BackupRestore.tsx` | diverse | **unsafe** | Explizit ausgeschlossen |
| `Dashboard.tsx` | diverse | **unsafe** | Explizit ausgeschlossen |

**Nach H.4:** `count_23` (26 − 3)
