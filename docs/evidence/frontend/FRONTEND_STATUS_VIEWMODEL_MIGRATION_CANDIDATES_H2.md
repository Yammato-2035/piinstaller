# Frontend Status ViewModel Migration Candidates — H.2

**HEAD:** nach H.2

| Datei | Funktion/Mapping | Duplikat | H.2 geeignet | Grund |
|-------|------------------|----------|--------------|-------|
| `trafficLight/trafficLightModel.ts` | `worstTrafficLightLamp`, `trafficLightStateToLamp` | LAMP_RANK | **migrate_now** | Delegation an ViewModel; Domain-Derivation bleibt |
| `lib/devDashboard/dccCompactStatus.ts` | `deployDriftTone` | inline green/yellow/red/gray | **migrate_now** | 1:1 über `dashboardToneFromInput` |
| `pages/devDashboardFilters.ts` | `toneClass` | inline tone switch | **migrate_now** | Normalisierung via ViewModel; CSS unverändert |
| `trafficLight/trafficLightModel.ts` | `deriveAppStoreTrafficLight` etc. | Domain-Logik | keep_until_component_migration | Fachsemantik, nicht reine Normalisierung |
| `lib/devDashboard/buildStandaloneDashboard.ts` | `normalizeAmpel` | Ampel-Map | keep_until_component_migration | Markdown-Parser-Kontext |
| `components/dev-dashboard/RoadmapDrawer.tsx` | `roadmapStatusClass` | Tailwind inline | local_allowed | Komponenten-Migration H.3 |
| 27 Komponenten | inline green/yellow/red | lokal | local_allowed | H.3 |
