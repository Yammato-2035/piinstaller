# Roadmap-Sichtbarkeit — Audit

**Datum:** 2026-05-27  
**HEAD (Audit-Basis):** `20a8303`  
**Runtime-Gate:** Exit **0** (Live-API ausgewertet)

## Befund: Warum Roadmap „nicht sichtbar“ wirkte

### 1. Falsche UI-Oberfläche (Hauptursache)

| Oberfläche | Roadmap-Komponente | Governance-Matrix |
|------------|-------------------|-------------------|
| `App.tsx` → Seite `dev-dashboard` → `DevelopmentDashboard` | **Ja** (`RoadmapDrawer`, Nav „Roadmap“) | Nein |
| `CockpitApp.tsx` → `ExternalDevelopmentControlCenter` | **Nein** (vor Fix) | **Ja** |

Viele Operator-Flows nutzen das **externe Governance-Cockpit** (`CockpitApp`), nicht die volle `DevelopmentDashboard`-Seite. Dort gab es nur die **Governance-Matrix** (abgeleitete Ampeln), **keinen** Roadmap-Registry-Bereich mit Meilensteinen, Blockern und Next-Prompt.

### 2. Navigation / Layout (`DevelopmentDashboard`)

- Roadmap wird nur gerendert, wenn `section === 'overview' || section === 'roadmap'`.
- Standard ist `overview` — Roadmap steht **unter** vielen Gate-Panels und ist auf langen Viewports leicht zu übersehen.
- i18n-Keys für Roadmap sind **vollständig** (`de.json` / `en.json`).

### 3. Backend / API (nicht die Ursache bei laufender Runtime)

- `GET /api/dev-dashboard/status` liefert `dashboard.roadmap` mit **13** `areas` (Live, 2026-05-27).
- `GET /api/dev-dashboard/roadmap` liefert Registry-Bundle (`status: success`).
- Kein Feature-Flag versteckt Roadmap serverseitig.

### 4. Offline / Snapshot

- `buildRoadmapFromScan` erzeugte nur `tabs`, kein `areas[]` → `RoadmapDrawer` fiel auf leere Fallback-Liste.
- Fix: `areas` aus STATUS_MATRIX-/Modul-Tabs für ehrliche Snapshot-Darstellung.

### 5. Deploy-Drift Frontend

- `/opt/setuphelfer/frontend/dist` enthält Strings `dev-dashboard-roadmap` — UI-Code ist deployed.
- Fehlende Sichtbarkeit war **kein** fehlendes Backend, sondern **fehlende Einbindung** im Cockpit.

## Minimal-Fix (Workspace, ohne Deploy)

1. `RoadmapDrawer` + `ReadyStableSection` in `ExternalDevelopmentControlCenter.tsx`.
2. `loadDevDashboard.ts`: expliziter `/api/dev-dashboard/roadmap`-Fetch, wenn `areas` im Status fehlen.
3. `RoadmapDrawer`: Datenquellen-Banner (`live_api` / `snapshot` / `workspace`).
4. `buildStandaloneDashboard.ts`: `areas[]` für Offline.
5. Grüne Gates deutlicher (`StatusCard`, `RuntimeGatePanel`, `ReadyStableSection`) — **ohne** Statuslogik-Änderung.

## Nicht tun

- Roadmap-Ampeln erfinden
- Release/Backup/Rescue ohne Evidence auf grün
- Deploy oder Backend-Restart in diesem Auftrag
