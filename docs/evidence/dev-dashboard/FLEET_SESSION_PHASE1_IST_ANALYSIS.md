# Fleet Session Phase 1 — IST-Analyse

**Datum:** 2026-06-02
**HEAD (Analyse):** `ea548fa`
**Branch:** `main`

## Scope und Ausgangspunkt

Ziel der Analyse war die Sichtbarkeit laufender Host-Lab-Sessions (QEMU/Smoke), auch wenn kein Gast-Report ingestet wird.
Der Legacy-Runtime-Gate liefert in `release` weiterhin Exit 20 (`/api/dev-dashboard/status` 404), daher wurde diese Analyse als **statisch** durchgeführt.

## Wo Knoten aktuell gespeichert werden

| Aspekt | Ort |
|--------|-----|
| Persistenz der Development-Server-Knoten | `backend/devserver/storage.py` (`nodes/*.json`) |
| Ingest-Pfad für Gast-Reports | `backend/devserver/ingest.py`, `POST /api/dev-server/ingest/report` |
| Dev-Server-API | `backend/devserver/routers.py` |
| Knoten-UI | `frontend/src/components/devserver/DevelopmentServerPanel.tsx` |

Aktueller Effekt: Neue VM-Knoten erscheinen erst nach erfolgreichem Ingest.

## Wo Session-/Heartbeat-Strukturen existieren

| Aspekt | Ort |
|--------|-----|
| Session-State-Core | `backend/core/fleet_session_state.py` |
| Fleet-API-Router | `backend/fleet/routers.py` |
| Fleet-Payload-Schemas | `backend/fleet/schemas.py` |
| Wrapper-API/Fallback | `scripts/rescue-live/fleet-session-api.sh` |
| Wrapper-Instrumentierung | `scripts/rescue-live/run-qemu-developer-iso-smoke.sh` |

Es existieren bereits:
- Session-Create/Heartbeat/Finish
- JSONL- und Latest-Persistenz
- Stale-/Timeout-Regeln
- JSONL-Fallback bei nicht erreichbarer API

## Welche API das Dashboard nutzt

| UI-Bereich | API |
|-----------|-----|
| Dev Control Center Summary | `GET /api/dev-dashboard/control-center-summary` |
| Lab Sessions Kachel | `GET /api/fleet/sessions`, `GET /api/fleet/sessions/summary` |
| Diagnostics in Session-Detail | `GET /api/dev-diagnostics/qemu-smokes/{run_id}/...` |

## Welche UI-Komponente Lab-Knoten zeigt

- Seite: `frontend/src/pages/ExternalDevelopmentControlCenter.tsx`
- Kachel: `frontend/src/components/dev-dashboard/LabSessionsPanel.tsx`
- API-Client: `frontend/src/api/fleetSessionsApi.ts`

## Wo QEMU-Smoke-Läufe Evidence erzeugen

- Laufverzeichnis: `docs/evidence/runtime-results/rescue/qemu/<run_id>/`
- Kernartefakte:
  - `qemu-serial.log`
  - `qemu_autopilot_result.json`
  - `dev_server_summary_before.json`
  - `dev_server_summary_after.json`
  - `dev_server_reports_after.json`

## Gap / Problemzusammenfassung

Vor Phase 1 war die Hostlauf-Sichtbarkeit im Control Center nicht robust, wenn:
- QEMU timeoutet,
- Serial leer bleibt,
- kein Gast-Report ingestet wird.

Dann blieb der Dev-Server-Knotenstand unverändert und das Dashboard wirkte „blind“.

## Phase-1 Sollbild (kurz)

Hostseitige Session muss sofort sichtbar sein:
- `starting` / `booting` / `autopilot_waiting`
- Heartbeat + Alter/Stale
- `timeout` / `failed` / `success`
- `guest_report_seen=false` explizit sichtbar
- klare Trennung: **Host-Session** vs. **Guest-Node**
