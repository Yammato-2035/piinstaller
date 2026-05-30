# Development Control Center — Overview (EN)

## Purpose

The **Development Control Center** is the central read-only overview for Setuphelfer development.

## Sections (tabs)

1. **Overview** — runtime gate, version, dev-server mode, blockers, next prompt
2. **Roadmap** — milestones, blockers, recommended prompt (evidence-based)
3. **Telemetry** — Development Server (= telemetry server), `local_lab` mode
4. **Rescue/Agent** — dev server → agent → developer profile → ISO pending
5. **Docs & diagnostics** — doc/FAQ/KB/evidence counts, missing DE/EN pairs
6. **Evidence** — newest evidence files
7. **Operations** — deploy, backup status (read-only)

## Key rules

- **Telemetry server** = Development Server (`/api/dev-server/*`)
- **`local_lab`** is the developer/lab mode — green when enabled + storage_ok
- **SSH disabled** is intended in this phase — not an error
- **Public uploads disabled** is intended — not an error
- Roadmap traffic lights are **evidence-based**
- Documentation statistics are **read-only** filesystem scans
- No backup/restore/ISO/SSH actions from the overview

## API

`GET /api/dev-dashboard/control-center-summary`

## Prerequisite

Local development server should be green for telemetry ingest (`enabled=true`, `storage_ok=true`).
