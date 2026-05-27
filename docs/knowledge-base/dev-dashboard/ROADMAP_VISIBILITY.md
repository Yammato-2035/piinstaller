# Roadmap im Developer Dashboard

## Warum war der Roadmap-Bereich nicht sichtbar?

1. **Governance-Cockpit** (`CockpitApp` / `ExternalDevelopmentControlCenter`) zeigte nur die Governance-Matrix, nicht die Roadmap-Registry.
2. **Development Dashboard** (`?page=dev-dashboard`) hat Roadmap unter Navigation **Übersicht** oder **Roadmap** — oft unterhalb vieler Panels.
3. **Offline:** Snapshot ohne `areas[]` zeigte leere Roadmap (behoben: Ableitung aus STATUS_MATRIX).

## Datenquelle

| Modus | Quelle |
|-------|--------|
| Live | `GET /api/dev-dashboard/status` → `dashboard.roadmap` und/oder `GET /api/dev-dashboard/roadmap` |
| Snapshot | `frontend/public/dev-dashboard.snapshot.json` + STATUS_MATRIX-Zeilen |
| Workspace | Tauri-Scan / Matrix-Text |

Das UI zeigt die **Datenquelle** im Roadmap-Panel (`roadmap_data_source`).

## Kein Fake-Green

Roadmap-Status kommt aus `docs/roadmap/setuphelfer_roadmap.json` und Runtime-Overlay — nicht aus Frontend-Farben allein.
