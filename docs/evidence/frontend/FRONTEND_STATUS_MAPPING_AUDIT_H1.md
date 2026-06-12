# Frontend Status Mapping Audit — H.1

**HEAD:** nach H.1 · **Scope:** statische Analyse

## Pflichttabelle

| Datei | Status-/Ampel-Logik | Statuswerte | Farben/Badges | Risiko | Empfehlung |
|-------|---------------------|---------------|---------------|--------|------------|
| `viewmodels/statusViewModel.ts` | **kanonisch** (H.1) | ok/warning/degraded/blocked/unavailable/unknown | severity only (kein CSS) | — | canonical_candidate |
| `trafficLight/trafficLightModel.ts` | Domain-Ampel (AppStore/Backup/Monitoring) | green/yellow/red/unknown | LampDot via Badge | **hoch** | needs_viewmodel (H.2) |
| `lib/devDashboard/dccCompactStatus.ts` | `deployDriftTone` | green/yellow/red/gray | tone strings | mittel | duplicate_mapping |
| `pages/devDashboardFilters.ts` | `toneClass` | green/yellow/red/gray | Tailwind-Klassen | mittel | needs_viewmodel (H.2) |
| `lib/devDashboard/buildStandaloneDashboard.ts` | `normalizeAmpel` | green/yellow/red/gray/blocked | Kategorie-Mapping | mittel | duplicate_mapping |
| `components/dev-dashboard/RoadmapDrawer.tsx` | `roadmapStatusClass` | green/yellow/red/blocked/deferred | Tailwind inline | mittel | component_local_allowed |
| `components/dev-dashboard/ManualCommandRunsPanel.tsx` | safety→tone | green/yellow/red | toneClass | niedrig | component_local_allowed |
| `components/trafficLight/TrafficLightBadge.tsx` | Darstellung | lamp states | LampDot | niedrig | component_local_allowed |
| `components/companions/StatusDots.tsx` | LampDot CSS | red/yellow/green | Tailwind | niedrig | component_local_allowed |
| `components/dev-dashboard/StatusCard.tsx` | tone prop | string | toneClass | niedrig | component_local_allowed |

## Bewertung H.1

- **Contract:** `statusViewModel.ts` eingeführt — keine Komponentenmigration
- **Duplikate bleiben** bis H.2 schrittweise Migration
- **Backend-Facades** nicht im Frontend importiert (reine Normalisierung)
