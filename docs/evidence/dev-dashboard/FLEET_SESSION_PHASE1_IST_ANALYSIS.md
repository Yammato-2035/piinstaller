# Fleet Session Phase 1 — Ist-Analyse

**Datum:** 2026-06-01  
**HEAD (Analyse):** a6ee74d  
**Branch:** main

## Knoten & Reports (Development Server)

| Aspekt | Ort |
|--------|-----|
| Knoten-Persistenz | `backend/devserver/storage.py` → `{storage_root}/nodes/*.json` |
| Reports / Ingest | `backend/devserver/ingest.py`, `POST /api/dev-server/ingest/report` |
| API | `backend/devserver/routers.py` (`/api/dev-server/*`) |
| UI | `frontend/src/components/devserver/DevelopmentServerPanel.tsx` (Tab Telemetry) |

Knoten erscheinen **nur nach Ingest** oder manueller Lab-Registrierung — nicht beim QEMU-Start.

## QEMU-Smoke & Evidence

| Aspekt | Ort |
|--------|-----|
| Wrapper | `scripts/rescue-live/run-qemu-developer-iso-smoke.sh` |
| Evidence | `docs/evidence/runtime-results/rescue/qemu/<run_id>/` |
| Ergebnis-JSON | `qemu_autopilot_result.json` |
| Serial | `qemu-serial.log` (oft 0 B mit `quiet splash`) |

## Development Dashboard API

- `GET /api/dev-dashboard/control-center-summary` — aggregiert u. a. `dev_server`
- Cockpit: `frontend/src/pages/ExternalDevelopmentControlCenter.tsx`

## Session / Heartbeat vor Phase 1

- **Keine** Fleet-Session-API
- **Kein** Host-Heartbeat für QEMU-Läufe im UI
- Roadmap: `docs/architecture/DEV_CONTROL_CENTER_FLEET_OBSERVABILITY_ROADMAP.md`

## Lücke (Problem)

Wenn QEMU timeoutet (`exit 124`), Serial leer bleibt und kein Gast-Report ingestet wird, zeigt das Development Server Panel **keine neue VM** — das Dashboard ist blind für den laufenden/fehlgeschlagenen Host-Lauf.

## Phase-1-Ziel

Host-Session über `GET/POST /api/fleet/sessions*` + Kachel **Lab Sessions** (Telemetry-Tab), unabhängig vom Gast-Ingest.
