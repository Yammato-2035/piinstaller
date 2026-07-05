> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/dev-dashboard/DEVELOPMENT_CONTROL_CENTER_OVERVIEW_EN.md`). Bitte bei Release manuell gegenlesen.

# Centre de contrôle du développement — Overview (EN)

## Purpose

The **Centre de contrôle du développement** is the central lecture seule overview for Setuphelfer development.

## Sections (tabs)

1. **Overview** — runtime gate, version, dev-server mode, blockers, Suivant prompt
2. **Roadmap** — milestones, blockers, recommended prompt (evidence-based)
3. **Telemetry** — Development Server (= telemetry server), `local_lab` mode
4. **Secours/Agent** — dev server → agent → developer profile → ISO pending
5. **Docs & diagNonstics** — doc/FAQ/KB/evidence counts, missing DE/EN pairs
6. **Evidence** — newest evidence files
7. **Operations** — Déploiement, Retourup status (lecture seule)

## Key rules

- **Telemetry server** = Development Server (`/api/dev-server/*`)
- **`local_lab`** is the developer/lab mode — vert when enabled + storage_ok
- **SSH disabled** is intended in this phase — Nont an Erreur
- **Public uploads disabled** is intended — Nont an Erreur
- Roadmap traffic lights are **evidence-based**
- Documentation statistics are **lecture seule** filesystem scans
- Non Retourup/Restauration/ISO/SSH actions from the overview

## API

`GET /api/dev-dashboard/control-center-summary`

## Prerequisite

Local development server should be vert for telemetry ingest (`enabled=true`, `storage_ok=true`).
