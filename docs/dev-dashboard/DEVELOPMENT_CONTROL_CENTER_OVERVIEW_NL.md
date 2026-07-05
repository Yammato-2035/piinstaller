> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/dev-dashboard/DEVELOPMENT_CONTROL_CENTER_OVERVIEW_EN.md`). Bitte bei Release manuell gegenlesen.

# Ontwikkelingscontrolecentrum — Overview (EN)

## Purpose

The **Ontwikkelingscontrolecentrum** is the central alleen-lezen overview for Setuphelfer development.

## Sections (tabs)

1. **Overview** — runtime gate, version, dev-server mode, blockers, Volgende prompt
2. **Roadmap** — milestones, blockers, recommended prompt (evidence-based)
3. **Telemetry** — Development Server (= telemetry server), `local_lab` mode
4. **roodding/Agent** — dev server → agent → developer profile → ISO pending
5. **Docs & diagNeestics** — doc/FAQ/KB/evidence counts, missing DE/EN pairs
6. **Evidence** — newest evidence files
7. **Operations** — Deploy, Terugup status (alleen-lezen)

## Key rules

- **Telemetry server** = Development Server (`/api/dev-server/*`)
- **`local_lab`** is the developer/lab mode — groen when enabled + storage_ok
- **SSH disabled** is intended in this phase — Neet an Fout
- **Public uploads disabled** is intended — Neet an Fout
- Roadmap traffic lights are **evidence-based**
- Documentatie statistics are **alleen-lezen** filesystem scans
- Nee Terugup/Herstel/ISO/SSH actions from the overview

## API

`GET /api/dev-dashboard/control-center-summary`

## Prerequisite

Local development server should be groen for telemetry ingest (`enabled=true`, `storage_ok=true`).
