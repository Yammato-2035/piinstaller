# Frontend Component Status Mapping Audit — H.5

**HEAD:** 35a2b22 (vor H.5) · **Baseline:** `frontend_component_local_status_mapping:count_23`

| Datei | Funktion | Klassifikation | Hinweis |
|-------|----------|----------------|---------|
| `governanceMatrix.ts` | `normTraffic`, `moduleTraffic` | **SAFE** | H.5 erledigt → ViewModel |
| `roadmapFilter.ts` | `statusBucket` | **SAFE** | H.5 erledigt → `roadmapFilterBucketFromStatus` |
| `buildGovernancePrompt.ts` | area filters, workOrder | **SAFE** | H.5 erledigt → Governance-Predicates |
| `ReadyStableSection.tsx` | — | **already_migrated** | H.4 |
| `StatusCard.tsx` | — | **already_migrated** | H.4 |
| `RiskWarningCard.tsx` | — | **already_migrated** | H.4 |
| `devDashboardFilters.ts` | `toneClass` | **already_migrated** | H.2 |
| `trafficLight/trafficLightModel.ts` | derive* | **already_migrated** | H.2 |
| `RoadmapDrawer.tsx` | `toneForStatus` | **UNSAFE_LARGE_PAGE** | Eigene Tailwind-Klassen |
| `ExternalDevelopmentControlCenter.tsx` | `trafficDot` | **UNSAFE_LARGE_PAGE** | Große Seite |
| `DevDashboardBody.tsx` | inline tones | **UNSAFE_LARGE_PAGE** | Große Seite |
| `SecuritySetup.tsx` | security lamp | **UNSAFE_LARGE_PAGE** | Seite |
| `MonitoringDashboard.tsx` | overall lamp | **UNSAFE_LARGE_PAGE** | Seite |
| `Dashboard.tsx` | diverse | **UNSAFE_LARGE_PAGE** | Explizit ausgeschlossen |
| `BackupRestore.tsx` | diverse | **UNSAFE_LARGE_PAGE** | Explizit ausgeschlossen |
| `CockpitBackupTargetPanel.tsx` | traffic className | **DOMAIN_SPECIFIC** | Backup-Domain |
| `PartitionSafetyStatusPanel.tsx` | risk levels | **DOMAIN_SPECIFIC** | Safety-Domain |
| `PartitionSafetyPreviewPanel.tsx` | risk CSS | **DOMAIN_SPECIFIC** | Partition-Domain |
| `partitionRoleUtils.ts` | risk_level | **DOMAIN_SPECIFIC** | Partition-Domain |
| `setuphelferToolTheme.ts` | risk→theme | **DOMAIN_SPECIFIC** | Theme-Domain |
| `buildStandaloneDashboard.ts` | ampel→category | **SAFE** (H.6) | Standalone-Export-Lib |
| `governanceHistory.ts` | transition | **SAFE** (H.6) | Zustandsübergänge |
| `buildGovernancePrompt.ts` (vor H.5) | — | **SAFE** | erledigt |
| `companions/StatusDots.tsx` | LampDot CSS | **SAFE** (presentation) | Darstellung, kein Tone-Normalizer |
| `companions/TrafficLight.tsx` | lamp CSS | **SAFE** (presentation) | Darstellung |
| `TrafficLightBadge.tsx` | quiet flag | **SAFE** (presentation) | Nur Quiet-Flag |
| `riskLevels.ts` | i18n labels | **SAFE** (presentation) | Label-Keys |

**Nach H.5:** `count_20` (23 − 3)
