# Fleet Session Phase 1 — Local Runtime Acceptance

**Datum:** 2026-06-01  
**HEAD:** `1aeb2cf`  
**Commit:** `1aeb2cf` — Add dev control center fleet session visibility  
**Branch:** `main`

## NDA / Public gate

| Feld | Wert |
|------|------|
| Repository | `Yammato-2035/piinstaller` |
| Visibility | **public** |
| Push allowed | **no** |
| Push durchgeführt | **no** |
| NDA risk | **blocked** (`push_blocked_public_repository_ndA_risk`) |
| Public Dev-Control exposure | **no** (keine öffentlichen Dev-Subdomains im Code) |

## Runtime-Gate

| Check | Ergebnis |
|-------|----------|
| `check-runtime-deploy-gate.sh` | **OK** |
| `check-backend-version-gate.sh` | **OK** |
| `setuphelfer-backend.service` | active |
| `setuphelfer.service` | active |
| `project_version` | 1.7.3.0 |

## OpenAPI

| Pflichtpfad | Sichtbar |
|-------------|----------|
| `GET /api/fleet/sessions` | yes |
| `GET /api/fleet/sessions/summary` | yes |
| `GET /api/fleet/sessions/{session_id}` | yes |
| `POST /api/fleet/sessions/{session_id}/heartbeat` | yes |
| `POST /api/fleet/sessions/{session_id}/finish` | yes |
| Control-Routen (`start/stop/revive/ssh/control/execute`) | **none** |

## API-Smoke (2026-06-01T08:00:32Z)

| Schritt | Ergebnis |
|---------|----------|
| **run_id** | `manual_local_api_smoke_20260601_080032` |
| **session_id** | `fleet-manual_local_api_smoke_20260601_080032` |
| Create | `FLEET_SESSION_CREATED` |
| Heartbeat | `FLEET_SESSION_HEARTBEAT_OK`, status `autopilot_waiting`, finding `manual_heartbeat_ok` |
| Get (nach Heartbeat) | `FLEET_SESSION_OK` |
| Finish | `FLEET_SESSION_FINISHED`, status **success** |
| Get (nach Finish) | `finished_at` gesetzt, finding `manual_api_smoke_success`, `guest.report_seen=false` |
| List | `FLEET_SESSION_LIST_OK`, count=2, Test-Session enthalten |
| Summary | `FLEET_SESSION_SUMMARY_OK`, total=2, finished_count=2 |

Kein Gast-Knoten erzeugt (nur Host-Session-State).

## Persistenz

| Datei | Ort | Status |
|-------|-----|--------|
| `fleet_sessions.jsonl` | `/opt/setuphelfer/docs/evidence/runtime-results/dev-dashboard/` | yes (~8 KB) |
| `fleet_sessions_latest.json` | gleicher Pfad | yes |
| Workspace-Kopie | `docs/evidence/...` im Repo | **fehlt** (Runtime schreibt unter `/opt`) |

- Session persistiert: **yes**
- Secrets in JSONL: **none** gefunden
- Öffentliche URLs in Payload: **none**

## UI

| Prüfung | Ergebnis |
|---------|----------|
| Source: `LabSessionsPanel.tsx` + i18n DE/EN | **vorhanden** |
| Keine Start/Stop/SSH/Revive-Buttons in Panel | **bestätigt** (nur Refresh) |
| Host ≠ Gast Hinweis (`hostSessionNote`) | **in i18n** |
| `/opt/setuphelfer/frontend/dist` enthält Lab Sessions | **no** (Build vor Feature) |
| Browser-Abnahme Cockpit Tab Telemetry | **pending** — `npm run build` + Frontend-Deploy nötig |

Statische UI-Abnahme: **review_required**  
API-/Backend-Abnahme: **green**

## QEMU

| Punkt | Wert |
|-------|------|
| QEMU in diesem Auftrag gestartet | **no** |
| `qemu_smoke_next_step_allowed` | **true** |

Voraussetzungen erfüllt: Runtime-Gate grün, Fleet-API live, vollständiger API-Smoke, keine Control-Routen, Push weiter blockiert.

Empfohlener nächster Befehl (separater Auftrag):

```bash
scripts/rescue-live/run-qemu-developer-iso-smoke.sh \
  qemu_rescue_developer_autopilot_$(date -u +%Y%m%d_%H%M%S) \
  --operator-confirm-qemu --autopilot \
  --proxy-port 8001 --timeout-seconds 1200
```

## Nicht durchgeführt

Kein ISO, USB, dd, Backup, Restore, apt, Push, öffentliches Deployment.

## Offene Risiken

1. **UI dist veraltet** — Lab Sessions im Cockpit erst nach Frontend-Rebuild sichtbar.
2. **Persistenz unter `/opt`** — Evidence im Git-Workspace nicht automatisch gespiegelt.
3. **Public GitHub** — kein Push von Dev-Control-Artefakten.

## Gesamtstatus Phase 1 Runtime

**Backend/API: green** | **UI Browser: pending** | **Public Push: blocked**
