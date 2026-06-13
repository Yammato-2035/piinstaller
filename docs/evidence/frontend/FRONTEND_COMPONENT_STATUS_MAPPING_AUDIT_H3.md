# Frontend Component Status Mapping Audit — H.3

**HEAD:** nach H.3 · **Baseline:** count_28 (H.2)

| Datei | Komponente/Funktion | Mapping-Art | Risiko | H.3 geeignet | Empfehlung |
|-------|---------------------|-------------|--------|--------------|------------|
| `RescueDeveloperPipelineCard.tsx` | `itemTone` | status→tone | niedrig | **migrate_now** | erledigt H.3 |
| `ControlCenterOverviewHeader.tsx` | `trafficFromGate` | gate→tone | niedrig | **migrate_now** | erledigt H.3 |
| `ManualCommandRunsPanel.tsx` | `safetyTone` | safety_class→tone | niedrig | **migrate_now** | erledigt H.3 |
| `trafficLight/trafficLightModel.ts` | derive* | Domain | mittel | already_migrated | H.2 Utility |
| `devDashboardFilters.ts` | toneClass | CSS bucket | niedrig | already_migrated | H.2 |
| `RoadmapDrawer.tsx` | `toneForStatus` | eigene Tailwind | mittel | keep_until_page_slice | andere CSS als toneClass |
| `DocumentationDiagnosticsCard.tsx` | docsTone/diagTone | Domain-Heuristik | mittel | domain_specific_allowed | nicht reine Normalisierung |
| `CockpitBackupTargetPanel.tsx` | traffic className | inline | mittel | keep_until_page_slice | Backup-Domain |
| `PartitionSafetyStatusPanel.tsx` | risk levels | Safety | hoch | unsafe | Backup/Restore |
| `RiskWarningCard.tsx` | CARD_STYLES | Darstellung | niedrig | local_allowed | Props→CSS, kein tone string |
| `companions/StatusDots.tsx` | LampDot | CSS | niedrig | local_allowed | Darstellung |
| `BackupRestore.tsx` | diverse | Domain | hoch | unsafe | explizit ausgeschlossen |
| `Dashboard.tsx` | diverse | Domain | hoch | unsafe | explizit ausgeschlossen |

**Verbleibend:** `frontend_component_local_status_mapping:count_26`
