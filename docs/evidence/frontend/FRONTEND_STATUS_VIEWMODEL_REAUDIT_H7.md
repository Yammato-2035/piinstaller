# Frontend Status ViewModel — Re-Audit H.7

**HEAD:** nach H.7 · **Gate:** `frontend_component_local_status_mapping:count_10`

## Zusammenfassung

| Kategorie | Anzahl | Strategie |
|-----------|--------|-----------|
| **Gesamt verbleibend** | 10 | — |
| **DOMAIN_SPECIFIC** | 4 | Domain-Facade (zukünftig) |
| **UNSAFE_LARGE_PAGE** | 6 | Kein Big-Bang; Seiten-Slices separat |

## Verbleibende Dateien

### DOMAIN_SPECIFIC (4)

| Datei | Grund |
|-------|-------|
| `PartitionSafetyStatusPanel.tsx` | Safety/Restore-Risiko-CSS |
| `PartitionSafetyPreviewPanel.tsx` | Partition-Risiko-CSS |
| `CockpitBackupTargetPanel.tsx` | Backup-Traffic-Darstellung |
| `partitionRoleUtils.ts` | Backend risk_level-Heuristik |

### UNSAFE_LARGE_PAGE (6)

| Datei | Grund |
|-------|-------|
| `Dashboard.tsx` | Haupt-Dashboard-Monolith |
| `BackupRestore.tsx` | Backup/Restore-Domain |
| `ExternalDevelopmentControlCenter.tsx` | DCC-Seite |
| `DevDashboardBody.tsx` | Cockpit-Body |
| `SecuritySetup.tsx` | Security-Seite |
| `MonitoringDashboard.tsx` | Monitoring-Seite |

## Migriert (H.1–H.7 kumulativ)

- **H.1–H.2:** ViewModel-Contract + Utilities (`trafficLightModel`, `devDashboardFilters` partial, `dccCompactStatus`)
- **H.3–H.4:** 6 DCC-Komponenten
- **H.5:** 3 DCC-Libs (`governanceMatrix`, `roadmapFilter`, `buildGovernancePrompt`)
- **H.6:** 5 Presentation/Utility (`StatusDots`, `TrafficLight`, `TrafficLightBadge`, `governanceHistory`, `buildStandaloneDashboard`)
- **H.7:** 5 finale Presentation-Libs (`riskLevels`, `devDashboardFilters` vollständig, `trafficLightModel` vollständig, `RoadmapDrawer`, `setuphelferToolTheme`)

## Kanonischer Owner

`frontend/src/viewmodels/statusViewModel.ts` · `component_migration: h7_final`

## Nächster Schritt (kein H.8)

**G.4** — Network Handler Extraction aus `app.py`
